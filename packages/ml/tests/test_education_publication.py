import hashlib
import json
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import joblib
import pytest
from churn_ml.education_analysis import publish_education_analysis
from churn_ml.infrastructure.filesystem.education_analysis_store import (
    EducationAnalysisStore,
    read_education_sources,
)


def test_publication_is_reproducible_source_bound_and_readable(education_source: Path) -> None:
    before = read_education_sources(education_source, "education-test")
    result = publish_education_analysis(
        education_source, "education-test", "analysis-1", shap_samples=8, permutation_samples=20
    )
    after = read_education_sources(education_source, "education-test")
    assert before.hashes == after.hashes
    assert result["run_id"] == "education-test"
    assert result["analysis_id"] == "analysis-1"
    assert result["source_hashes"] == before.hashes
    assert result["schema_version"] == 1
    assert result["decision_support_only"] is True
    assert EducationAnalysisStore(education_source).read("education-test", "analysis-1") == result
    assert "Student_ID" not in json.dumps(result)
    with pytest.raises(ValueError, match="already exists"):
        publish_education_analysis(education_source, "education-test", "analysis-1")
    assert result == EducationAnalysisStore(education_source).read("education-test", "analysis-1")


def test_relocated_manifest_uses_only_expected_local_paths(education_source: Path) -> None:
    manifest = education_source / "models/education-test/completion.json"
    payload = json.loads(manifest.read_bytes())
    payload["members"] = {
        "/nonexistent/old-root/" + "/".join(Path(path).parts[-3:]): value
        for path, value in payload["members"].items()
    }
    manifest.write_text(json.dumps(payload))
    assert publish_education_analysis(education_source, "education-test", "relocated")["run_id"]


def test_bad_source_is_rejected_before_deserialization(education_source: Path) -> None:
    binary = education_source / "models/education-test/model.joblib"
    binary.write_bytes(b"untrusted pickle")
    with patch("joblib.load") as load:
        with pytest.raises(ValueError, match="checksum"):
            publish_education_analysis(education_source, "education-test", "bad")
        load.assert_not_called()
    assert not (education_source / "education/education-test/bad").exists()


def test_duplicate_is_rejected_before_loading_sources(education_source: Path) -> None:
    publish_education_analysis(education_source, "education-test", "duplicate")
    with patch("joblib.load", side_effect=AssertionError("Duplicate loaded model")):
        # Missing source must not obscure the earlier duplicate rejection.
        (education_source / "models/education-test/model.joblib").write_bytes(b"changed")
        with pytest.raises(
            ValueError, match="^Analysis identity already exists; use a new analysis ID$"
        ):
            publish_education_analysis(education_source, "education-test", "duplicate")


@pytest.mark.parametrize("field", ["model_name", "feature_columns", "row_count"])
def test_input_adapter_preserves_metadata_checks(education_source: Path, field: str) -> None:
    original_load = joblib.load

    def mismatched_model(stream: object) -> object:
        model = original_load(stream)
        if field != "row_count":
            return replace(model, **{field: "other" if field == "model_name" else ("other",)})
        return model

    if field == "row_count":
        path = education_source / "processed/education-test/train.metadata.json"
        metadata = json.loads(path.read_bytes())
        metadata["row_count"] += 1
        path.write_text(json.dumps(metadata))
    message = "row count mismatch" if field == "row_count" else "metadata disagree"
    with patch("joblib.load", side_effect=mismatched_model) as load:
        with pytest.raises(ValueError, match=message):
            publish_education_analysis(education_source, "education-test", "mismatch")
        assert load.call_count == 1
    assert not (education_source / "education/education-test/mismatch").exists()


def test_changed_source_rejected_after_analysis_without_reloading_model(
    education_source: Path,
) -> None:
    from churn_ml.infrastructure.sklearn.education_analysis_engine import analyze_education_model

    def change_source(*args: object, **kwargs: object) -> dict:
        result = analyze_education_model(*args, **kwargs)
        with (education_source / "processed/education-test/test.csv").open("a") as stream:
            stream.write("\n")
        return result

    with (
        patch("joblib.load", wraps=joblib.load) as load,
        patch(
            "churn_ml.infrastructure.sklearn.education_analysis_engine.analyze_education_model",
            side_effect=change_source,
        ),
    ):
        with pytest.raises(ValueError, match="^Analysis source changed during computation$"):
            publish_education_analysis(education_source, "education-test", "changed")
        assert load.call_count == 1
    assert not (education_source / "education/education-test/changed").exists()


@pytest.mark.parametrize("member", ["analysis.json", "completion.json"])
def test_corrupt_analysis_is_rejected(education_source: Path, member: str) -> None:
    publish_education_analysis(education_source, "education-test", "analysis-1")
    path = education_source / "education/education-test/analysis-1" / member
    path.write_text("{}")
    with pytest.raises(ValueError):
        EducationAnalysisStore(education_source).read("education-test", "analysis-1")


def test_analysis_rejects_changed_split_and_nonfinite_payload(education_source: Path) -> None:
    publish_education_analysis(education_source, "education-test", "analysis-1")
    directory = education_source / "education/education-test/analysis-1"
    data_path = directory / "analysis.json"
    completion = directory / "completion.json"
    payload = json.loads(data_path.read_bytes())
    payload["coefficients"][0]["coefficient"] = float("nan")
    data_path.write_text(json.dumps(payload))
    manifest = json.loads(completion.read_bytes())
    manifest["payload_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    completion.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="finite"):
        EducationAnalysisStore(education_source).read("education-test", "analysis-1")
    publish_education_analysis(education_source, "education-test", "analysis-2")
    with (education_source / "processed/education-test/test.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="source"):
        EducationAnalysisStore(education_source).read("education-test", "analysis-2")


@pytest.mark.parametrize("name", ["../escape", "/tmp/escape", "", "..", "a/b"])
def test_invalid_identity_is_rejected(education_source: Path, name: str) -> None:
    with pytest.raises(ValueError, match="identity"):
        publish_education_analysis(education_source, "education-test", name)


def test_public_cli_reports_success_and_duplicate_failure(education_source: Path) -> None:
    env = {**os.environ, "PYTHONPATH": "packages/ml/src"}
    command = [
        sys.executable,
        "-m",
        "churn_ml.education_analysis",
        "--artifact-root",
        str(education_source),
        "--run-id",
        "education-test",
        "--analysis-id",
        "cli-test",
        "--shap-samples",
        "8",
        "--permutation-samples",
        "20",
    ]
    result = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "Published education analysis: education-test/cli-test" in result.stdout
    before = (education_source / "education/education-test/cli-test/analysis.json").read_bytes()
    again = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
    assert again.returncode == 2
    assert "already exists" in again.stderr
    assert (
        education_source / "education/education-test/cli-test/analysis.json"
    ).read_bytes() == before


@pytest.mark.parametrize(
    "section,key,value",
    [
        ("coefficients", "coefficient", "not-a-number"),
        ("importance", "mean_abs_shap", -1),
        ("cohorts", "observed_high_rate", 1.5),
        ("cohorts", "count", -10),
        ("associations", "test", {"count": 80, "missing_count": 0, "point_biserial": 5}),
    ],
)
def test_invalid_but_checksummed_contract_is_rejected(
    education_source: Path,
    section: str,
    key: str,
    value: object,
) -> None:
    publish_education_analysis(education_source, "education-test", "invalid-contract")
    directory = education_source / "education/education-test/invalid-contract"
    path = directory / "analysis.json"
    payload = json.loads(path.read_bytes())
    payload[section][0][key] = value
    path.write_text(json.dumps(payload))
    completion_path = directory / "completion.json"
    completion = json.loads(completion_path.read_bytes())
    completion["payload_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    completion_path.write_text(json.dumps(completion))
    with pytest.raises(ValueError):
        EducationAnalysisStore(education_source).read("education-test", "invalid-contract")

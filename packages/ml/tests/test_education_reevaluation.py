import hashlib
from pathlib import Path

import pytest
from churn_ml.experiments import reevaluate_education
from churn_ml.infrastructure.filesystem.experiment_reports import read_report


def hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_reevaluation_preserves_sources_and_uses_full_precision(
    education_source: Path, tmp_path: Path
) -> None:
    before = hashes(education_source)
    with pytest.raises(ValueError, match="trusted"):
        reevaluate_education(education_source, "education-test")
    result = reevaluate_education(education_source, "education-test", trusted_model=True)
    assert hashes(education_source) == before
    assert result["evaluation"]["diagnostics"]["count"] == 80
    assert result["historical_metrics"]["pr_auc"] == 0.8
    assert result["source_hashes"]
    assert result["protocol"] == "historical_snapshot_not_independent_test"
    assert result["prediction_precision"] == "full_model_output"
    from churn_ml.infrastructure.filesystem.experiment_reports import publish_report

    directory = publish_report(
        tmp_path.with_name(tmp_path.name + "-reports"), "reevaluation-v1", result
    )
    assert read_report(directory) == result
    assert hashes(education_source) == before


def test_reevaluation_rejects_modified_model_before_deserialization(
    education_source: Path, monkeypatch
) -> None:
    import joblib

    monkeypatch.setattr(joblib, "load", lambda *args: pytest.fail("unsafe deserialize"))
    (education_source / "models/education-test/model.joblib").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        reevaluate_education(education_source, "education-test", trusted_model=True)

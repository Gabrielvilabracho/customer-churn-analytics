"""Regression probes retained from independent education verification."""

import hashlib
import io
import json
from pathlib import Path
from typing import Any

import joblib
import pytest
from churn_api.main import create_runtime_app
from churn_ml.education_analysis import publish_education_analysis
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "field,value",
    [
        ("warnings", "not-a-list"),
        ("model_name", "another-model"),
        ("dataset_id", "another-dataset"),
    ],
)
def test_rejects_invalid_or_mismatched_publication(
    education_source: Path,
    field: str,
    value: str,
) -> None:
    payload = publish_education_analysis(education_source, "education-test", "verification")
    directory = education_source / "education/education-test/verification"
    payload[field] = value
    data = directory / "analysis.json"
    data.write_text(json.dumps(payload))
    completion = directory / "completion.json"
    manifest = json.loads(completion.read_bytes())
    manifest["payload_sha256"] = hashlib.sha256(data.read_bytes()).hexdigest()
    completion.write_text(json.dumps(manifest))
    before = {path: path.read_bytes() for path in education_source.rglob("*") if path.is_file()}
    client = TestClient(
        create_runtime_app(
            {
                "CHURN_ARTIFACT_ROOT": str(education_source),
                "CHURN_ARTIFACT_RUN_ID": "education-test",
                "CHURN_EDUCATION_ANALYSIS_ID": "verification",
            }
        )
    )
    response = client.get("/analytics/education")
    assert all(path.read_bytes() == content for path, content in before.items())
    assert response.status_code == 503


def test_deserializes_exact_verified_bytes(
    education_source: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = (education_source / "models/education-test/model.joblib").read_bytes()
    original_load = joblib.load
    calls = []

    def checked_load(stream: Any) -> Any:
        assert isinstance(stream, io.BytesIO)
        assert stream.getvalue() == expected
        calls.append(True)
        return original_load(stream)

    monkeypatch.setattr(joblib, "load", checked_load)
    publish_education_analysis(education_source, "education-test", "verified-bytes")
    assert calls == [True]

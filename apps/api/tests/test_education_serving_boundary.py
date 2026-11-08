"""Reject malformed and private publication extensions before HTTP serving."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from churn_api.main import create_runtime_app
from churn_ml.education_analysis import publish_education_analysis
from fastapi.testclient import TestClient


@pytest.mark.parametrize("case", ["source-members-list", "raw-csv", "nested-raw-csv"])
def test_education_rejects_unsafe_publication(education_source: Path, case: str) -> None:
    root = education_source
    payload = publish_education_analysis(root, "education-test", "boundary")
    directory = root / "education/education-test/boundary"
    if case == "source-members-list":
        path = root / "models/education-test/completion.json"
        manifest = json.loads(path.read_bytes())
        manifest["members"] = []
        path.write_text(json.dumps(manifest))
    else:
        destination = payload if case == "raw-csv" else payload["shap"]["samples"][0]
        destination["raw_csv"] = (root / "processed/education-test/test.csv").read_text()
        data = directory / "analysis.json"
        data.write_text(json.dumps(payload))
        completion = directory / "completion.json"
        manifest = json.loads(completion.read_bytes())
        manifest["payload_sha256"] = hashlib.sha256(data.read_bytes()).hexdigest()
        completion.write_text(json.dumps(manifest))

    def hashes() -> dict[str, str]:
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*")
            if path.is_file()
        }

    before = hashes()
    config = {
        "CHURN_ARTIFACT_ROOT": str(root),
        "CHURN_ARTIFACT_RUN_ID": "education-test",
        "CHURN_EDUCATION_ANALYSIS_ID": "boundary",
    }
    with patch("joblib.load", side_effect=AssertionError("request-time deserialization")) as load:
        response = TestClient(create_runtime_app(config), raise_server_exceptions=False).get(
            "/analytics/education"
        )
    assert hashes() == before
    load.assert_not_called()
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert isinstance(response.json()["reason"], str)
    assert "Student_ID" not in response.text

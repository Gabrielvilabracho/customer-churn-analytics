from pathlib import Path
from unittest.mock import patch

from churn_api.main import create_app, create_runtime_app
from churn_ml.education_analysis import publish_education_analysis
from fastapi.testclient import TestClient


def test_education_endpoint_serves_real_publication_without_loading_model(
    education_source: Path,
) -> None:
    publish_education_analysis(education_source, "education-test", "analysis-1")
    app = create_runtime_app(
        {
            "CHURN_ARTIFACT_ROOT": str(education_source),
            "CHURN_ARTIFACT_RUN_ID": "education-test",
            "CHURN_EDUCATION_ANALYSIS_ID": "analysis-1",
        }
    )
    with patch("joblib.load", side_effect=AssertionError("No request-time deserialization")):
        response = TestClient(app).get("/analytics/education")
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "education-test"
    assert data["analysis_id"] == "analysis-1"
    assert data["summary"]["test_count"] == 80
    assert data["shap"]["units"] == "log_odds"
    assert data["decision_support_only"] is True
    assert data["qualified_human_review_required"] is True
    assert "Student_ID" not in response.text


def test_education_configuration_is_optional_and_legacy_default_is_unchanged() -> None:
    client = TestClient(create_app())
    assert client.get("/analytics/education").status_code == 503
    assert client.get("/health").json() == {
        "status": "degraded",
        "reason": "No artifact reader configured",
    }
    assert (
        client.post("/predict", json={"customer_features": {"tenure_months": 4}}).status_code == 503
    )


def test_education_degrades_for_changed_source_or_missing_publication(
    education_source: Path,
) -> None:
    config = {
        "CHURN_ARTIFACT_ROOT": str(education_source),
        "CHURN_ARTIFACT_RUN_ID": "education-test",
        "CHURN_EDUCATION_ANALYSIS_ID": "analysis-1",
    }
    client = TestClient(create_runtime_app(config))
    assert client.get("/analytics/education").status_code == 503
    publish_education_analysis(education_source, "education-test", "analysis-1")
    assert client.get("/analytics/education").status_code == 200
    (education_source / "processed/education-test/test.csv").write_text("changed")
    response = client.get("/analytics/education")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert "source" in response.json()["reason"].lower()


def test_invalid_analysis_selection_does_not_break_legacy_runtime(education_source: Path) -> None:
    app = create_runtime_app(
        {
            "CHURN_ARTIFACT_ROOT": str(education_source),
            "CHURN_ARTIFACT_RUN_ID": "education-test",
            "CHURN_EDUCATION_ANALYSIS_ID": "../../escape",
        }
    )
    client = TestClient(app)
    assert client.get("/health").status_code == 200
    assert client.get("/analytics/education").status_code == 503

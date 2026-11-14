from typing import Any

from churn_api.adapters.scoring import StubChurnScorer
from churn_api.domain.artifacts import ArtifactSnapshot, ModelMetadata
from churn_api.main import create_app
from fastapi.testclient import TestClient


class _ReadyArtifacts:
    selected_run_id = "run-contract-001"

    def load_current_snapshot(self) -> ArtifactSnapshot:
        return ArtifactSnapshot(
            model=ModelMetadata(
                run_id=self.selected_run_id,
                dataset_id="synthetic-review",
                model_name="deterministic_stub_host",
                created_at_utc="2026-11-14T00:00:00Z",
                feature_schema={"tenure_months": "number", "contract_type": "string"},
            ),
            metrics={"recall": 0.81, "precision": 0.64},
            threshold=0.42,
            prediction_samples=(
                {
                    "customer_id": "not-public",
                    "churn_probability": "0.78",
                    "actual_churn": "Yes",
                    "Contract": "Month-to-month",
                    "tenure": "4",
                    "PaymentMethod": "Electronic check",
                    "MonthlyCharges": "88.20",
                    "InternetService": "Fiber optic",
                },
            ),
            freshness={"metrics_created_at_utc": "2026-11-14T00:00:00Z"},
        )


def _response_schema(operation: dict[str, Any], status: int) -> dict[str, Any]:
    return operation["responses"][str(status)]["content"]["application/json"]["schema"]


def test_openapi_documents_stable_routes_and_typed_response_contracts() -> None:
    schema = create_app().openapi()

    assert set(schema["paths"]) == {
        "/health",
        "/model/metadata",
        "/analytics/dashboard",
        "/analytics/education",
        "/predict",
    }

    expected_operations = {
        ("/health", "get"): ("HealthResponse", {503: "DegradedResponse"}),
        ("/model/metadata", "get"): ("ModelMetadataResponse", {503: "DegradedResponse"}),
        ("/analytics/dashboard", "get"): (
            "DashboardResponse",
            {503: "DegradedResponse"},
        ),
        ("/analytics/education", "get"): (
            "EducationAnalyticsResponse",
            {503: "DegradedResponse"},
        ),
        ("/predict", "post"): (
            "PredictionResponse",
            {503: "DegradedResponse"},
        ),
    }
    for (path, method), (success_model, error_models) in expected_operations.items():
        operation = schema["paths"][path][method]
        assert _response_schema(operation, 200) == {
            "$ref": f"#/components/schemas/{success_model}"
        }
        for status, error_model in error_models.items():
            assert _response_schema(operation, status) == {
                "$ref": f"#/components/schemas/{error_model}"
            }

    predict = schema["paths"]["/predict"]["post"]
    assert predict["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/PredictionRequest"
    }
    assert _response_schema(predict, 422) == {
        "anyOf": [
            {"$ref": "#/components/schemas/PredictionErrorResponse"},
            {"$ref": "#/components/schemas/RequestValidationErrorResponse"},
        ],
        "title": "Response 422 Predict Predict Post",
    }


def test_typed_legacy_routes_preserve_realistic_runtime_payload_bytes() -> None:
    client = TestClient(
        create_app(artifact_reader=_ReadyArtifacts(), scorer=StubChurnScorer())
    )

    health = client.get("/health")
    metadata = client.get("/model/metadata")
    dashboard = client.get("/analytics/dashboard")
    prediction = client.post(
        "/predict",
        json={"customer_features": {"tenure_months": 4, "contract_type": "month-to-month"}},
    )

    assert health.status_code == 200
    assert health.content == (
        b'{"status":"ready","model_version":"run-contract-001",'
        b'"artifact_version":"run-contract-001",'
        b'"freshness":{"metrics_created_at_utc":"2026-11-14T00:00:00Z"}}'
    )
    assert metadata.status_code == 200
    assert metadata.content == (
        b'{"run_id":"run-contract-001","dataset_id":"synthetic-review",'
        b'"model_name":"deterministic_stub_host",'
        b'"created_at_utc":"2026-11-14T00:00:00Z",'
        b'"feature_schema":{"tenure_months":"number","contract_type":"string"}}'
    )
    assert dashboard.status_code == 200
    assert dashboard.content == (
        b'{"artifact_version":"run-contract-001",'
        b'"freshness":{"metrics_created_at_utc":"2026-11-14T00:00:00Z"},'
        b'"kpis":{"recall":0.81,"precision":0.64},"threshold":0.42,'
        b'"prediction_samples":[{"sample_id":"sample-001",'
        b'"display_reference":"Sample 001","Contract":"Month-to-month",'
        b'"tenure":"4","PaymentMethod":"Electronic check",'
        b'"MonthlyCharges":"88.20","InternetService":"Fiber optic",'
        b'"churn_probability":"0.78"}],"risk_distribution":{"high":1},'
        b'"decision_support_only":true,"qualified_human_review_required":true}'
    )
    assert prediction.status_code == 200
    assert prediction.content == (
        b'{"churn_probability":0.78,"risk_segment":"high",'
        b'"threshold_decision":"above_threshold","retention_priority":"urgent",'
        b'"model_version":"run-contract-001","top_drivers":["tenure_months"],'
        b'"decision_support_only":true,"qualified_human_review_required":true}'
    )

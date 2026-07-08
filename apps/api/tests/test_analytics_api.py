import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from churn_api.adapters.filesystem import FilesystemArtifactSnapshotReader
from churn_api.adapters.scoring import StubChurnScorer
from churn_api.domain.artifacts import ArtifactSnapshot, ModelMetadata
from churn_api.domain.predictions import PredictionResult
from churn_api.main import create_app
from churn_ml.domain.artifacts import (
    ArtifactBundle,
    ArtifactManifest,
    ClassificationMetricSet,
    ThresholdSelection,
)
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from fastapi.testclient import TestClient


@dataclass
class _RecordingScorer:
    probability: float = 0.82
    calls: int = 0

    def score(self, features: dict[str, float | str]) -> PredictionResult:
        self.calls += 1
        return PredictionResult(
            churn_probability=self.probability,
            risk_segment="high",
            retention_priority="urgent",
            top_drivers=("contract_type", "tenure_months"),
        )


class _ReadyArtifacts:
    def __init__(self) -> None:
        self.snapshot = ArtifactSnapshot(
            model=ModelMetadata(
                run_id="run-2026-07-02",
                dataset_id="telco-churn",
                model_name="candidate_ranker",
                created_at_utc="2026-07-02T00:00:00Z",
                feature_schema={"tenure_months": "number", "contract_type": "string"},
            ),
            metrics={"recall": 0.81, "precision": 0.64, "pr_auc": 0.72},
            threshold=0.42,
            prediction_samples=(
                {
                    "customer_id": "C001",
                    "churn_probability": "0.82",
                    "actual_churn": "Yes",
                    "Contract": "Month-to-month",
                    "tenure": "3",
                    "PaymentMethod": "Electronic check",
                    "MonthlyCharges": "88.20",
                    "InternetService": "Fiber optic",
                },
                {
                    "customer_id": "C002",
                    "churn_probability": "0.18",
                    "actual_churn": "No",
                    "Contract": "Two year",
                    "tenure": "40",
                    "PaymentMethod": "Credit card",
                    "MonthlyCharges": "49.10",
                    "InternetService": "DSL",
                },
            ),
            freshness={"metrics_created_at_utc": "2026-07-02T00:00:00Z"},
        )

    def load_current_snapshot(self) -> ArtifactSnapshot:
        return self.snapshot


class _MissingArtifacts:
    def load_current_snapshot(self) -> ArtifactSnapshot:
        raise FileNotFoundError("metrics artifact is missing")


def _client(
    *,
    artifacts: Any | None = None,
    scorer: _RecordingScorer | None = None,
) -> tuple[TestClient, _RecordingScorer]:
    active_scorer = scorer or _RecordingScorer()
    app = create_app(artifact_reader=artifacts or _ReadyArtifacts(), scorer=active_scorer)
    return TestClient(app), active_scorer


def test_health_reports_ready_with_model_and_artifact_freshness() -> None:
    client, _ = _client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "model_version": "run-2026-07-02",
        "artifact_version": "run-2026-07-02",
        "freshness": {"metrics_created_at_utc": "2026-07-02T00:00:00Z"},
    }


def test_health_reports_degraded_when_required_artifacts_are_missing() -> None:
    client, _ = _client(artifacts=_MissingArtifacts())

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "reason": "metrics artifact is missing",
    }


def test_dashboard_reports_degraded_without_fabricated_analytics() -> None:
    client, _ = _client(artifacts=_MissingArtifacts())

    response = client.get("/analytics/dashboard")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "reason": "metrics artifact is missing",
    }


def test_default_app_reports_degraded_without_configured_artifacts() -> None:
    client = TestClient(create_app())

    health = client.get("/health")
    metadata = client.get("/model/metadata")
    dashboard = client.get("/analytics/dashboard")
    prediction = client.post("/predict", json={"customer_features": {"tenure_months": 4}})

    assert health.status_code == 503
    assert health.json() == {
        "status": "degraded",
        "reason": "No artifact reader configured",
    }
    assert dashboard.status_code == 503
    assert dashboard.json() == {
        "status": "degraded",
        "reason": "No artifact reader configured",
    }
    assert metadata.status_code == 503
    assert metadata.json() == {
        "status": "degraded",
        "reason": "No artifact reader configured",
    }
    assert prediction.status_code == 503
    assert prediction.json() == {
        "status": "degraded",
        "reason": "No artifact reader configured",
    }


def test_stub_churn_scorer_marks_short_tenure_as_high_urgency() -> None:
    prediction = StubChurnScorer().score({"tenure_months": 4, "contract_type": "month-to-month"})

    assert prediction.churn_probability == 0.78
    assert prediction.risk_segment == "high"
    assert prediction.retention_priority == "urgent"
    assert prediction.top_drivers == ("tenure_months",)


def test_stub_churn_scorer_marks_established_tenure_as_low_monitoring() -> None:
    prediction = StubChurnScorer().score({"tenure_months": 24, "contract_type": "annual"})

    assert prediction.churn_probability == 0.31
    assert prediction.risk_segment == "low"
    assert prediction.retention_priority == "monitor"
    assert prediction.top_drivers == ("tenure_months",)


def test_model_metadata_and_dashboard_analytics_are_artifact_backed() -> None:
    client, _ = _client()

    metadata = client.get("/model/metadata")
    dashboard = client.get("/analytics/dashboard")

    assert metadata.status_code == 200
    assert metadata.json()["run_id"] == "run-2026-07-02"
    assert metadata.json()["feature_schema"] == {
        "tenure_months": "number",
        "contract_type": "string",
    }
    assert dashboard.status_code == 200
    assert dashboard.json()["artifact_version"] == "run-2026-07-02"
    assert dashboard.json()["kpis"] == {"recall": 0.81, "precision": 0.64, "pr_auc": 0.72}
    assert dashboard.json()["threshold"] == 0.42
    assert dashboard.json()["risk_distribution"] == {"high": 1, "low": 1}


def test_dashboard_exposes_sanitized_prediction_samples_for_cohort_visualizations() -> None:
    client, _ = _client()

    response = client.get("/analytics/dashboard")

    assert response.status_code == 200
    samples = response.json()["prediction_samples"]
    assert samples == [
        {
            "sample_id": "sample-001",
            "display_reference": "Sample 001",
            "churn_probability": "0.82",
            "Contract": "Month-to-month",
            "tenure": "3",
            "PaymentMethod": "Electronic check",
            "MonthlyCharges": "88.20",
            "InternetService": "Fiber optic",
        },
        {
            "sample_id": "sample-002",
            "display_reference": "Sample 002",
            "churn_probability": "0.18",
            "Contract": "Two year",
            "tenure": "40",
            "PaymentMethod": "Credit card",
            "MonthlyCharges": "49.10",
            "InternetService": "DSL",
        },
    ]


def test_dashboard_sample_sanitization_removes_raw_identifiers_and_actual_churn() -> None:
    client, _ = _client()

    response = client.get("/analytics/dashboard")

    assert response.status_code == 200
    first_sample = response.json()["prediction_samples"][0]
    assert "customer_id" not in first_sample
    assert "customerID" not in first_sample
    assert "actual_churn" not in first_sample
    assert first_sample["sample_id"] == "sample-001"
    assert first_sample["display_reference"] == "Sample 001"


def test_prediction_contract_returns_risk_decision_and_driver_payload() -> None:
    client, scorer = _client(scorer=_RecordingScorer(probability=0.82))

    response = client.post(
        "/predict",
        json={"customer_features": {"tenure_months": 4, "contract_type": "month-to-month"}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "churn_probability": 0.82,
        "risk_segment": "high",
        "threshold_decision": "above_threshold",
        "retention_priority": "urgent",
        "model_version": "run-2026-07-02",
        "top_drivers": ["contract_type", "tenure_months"],
    }
    assert scorer.calls == 1


def test_invalid_prediction_payload_returns_structured_error_without_scoring() -> None:
    client, scorer = _client()

    response = client.post(
        "/predict",
        json={"customer_features": {"tenure_months": "not-a-number"}},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": "invalid_prediction_request",
        "details": [
            "Missing required feature: contract_type",
            "Feature tenure_months must be a number",
        ],
    }
    assert scorer.calls == 0


def test_boolean_feature_value_is_rejected_for_numeric_schema_without_scoring() -> None:
    client, scorer = _client()

    response = client.post(
        "/predict",
        json={"customer_features": {"tenure_months": True, "contract_type": "monthly"}},
    )

    assert response.status_code == 422
    assert response.json() == {
        "error": "invalid_prediction_request",
        "details": ["Feature tenure_months must be a number"],
    }
    assert scorer.calls == 0


def test_filesystem_artifact_reader_maps_versioned_metrics_into_api_snapshot(
    tmp_path: Path,
) -> None:
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id="run-2026-07-02",
            dataset_id="telco-churn",
            model_name="candidate_ranker",
            created_at_utc="2026-07-02T00:00:00Z",
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.72,
            roc_auc=0.8,
            precision=0.64,
            recall=0.81,
            accuracy=0.77,
            top_risk_capture=0.7,
            workload_at_threshold=0.35,
        ),
        threshold=ThresholdSelection(
            threshold=0.42,
            tradeoff="Balance recall and retention workload.",
        ),
        prediction_samples=(
            {"customer_id": "C001", "churn_probability": "0.82", "actual_churn": "Yes"},
        ),
    )
    FilesystemArtifactStore(root=tmp_path).save_bundle(bundle)

    snapshot = FilesystemArtifactSnapshotReader(
        root=tmp_path,
        run_id="run-2026-07-02",
    ).load_current_snapshot()

    assert snapshot.model.run_id == "run-2026-07-02"
    assert snapshot.model.dataset_id == "telco-churn"
    assert snapshot.metrics == {"recall": 0.81, "precision": 0.64, "pr_auc": 0.72}
    assert snapshot.threshold == 0.42
    assert snapshot.freshness == {"metrics_created_at_utc": "2026-07-02T00:00:00Z"}


def test_filesystem_artifact_reader_maps_persisted_feature_schema_into_api_snapshot(
    tmp_path: Path,
) -> None:
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id="run-2026-07-02",
            dataset_id="telco-churn",
            model_name="candidate_ranker",
            created_at_utc="2026-07-02T00:00:00Z",
            feature_schema={"tenure_months": "number", "contract_type": "string"},
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.72,
            roc_auc=0.8,
            precision=0.64,
            recall=0.81,
            accuracy=0.77,
            top_risk_capture=0.7,
            workload_at_threshold=0.35,
        ),
        threshold=ThresholdSelection(
            threshold=0.42,
            tradeoff="Balance recall and retention workload.",
        ),
        prediction_samples=(
            {"customer_id": "C001", "churn_probability": "0.82", "actual_churn": "Yes"},
        ),
    )

    FilesystemArtifactStore(root=tmp_path).save_bundle(bundle)
    model_metadata_path = tmp_path / "models" / "run-2026-07-02" / "model_metadata.json"
    assert json.loads(model_metadata_path.read_text(encoding="utf-8"))["feature_schema"] == {
        "tenure_months": "number",
        "contract_type": "string",
    }

    snapshot = FilesystemArtifactSnapshotReader(
        root=tmp_path,
        run_id="run-2026-07-02",
    ).load_current_snapshot()

    assert snapshot.model.feature_schema == {
        "tenure_months": "number",
        "contract_type": "string",
    }

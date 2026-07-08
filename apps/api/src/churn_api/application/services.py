from typing import Any

from churn_api.application.dashboard_contract import to_public_prediction_sample_dtos
from churn_api.application.ports.artifacts import ArtifactSnapshotReader
from churn_api.application.ports.scoring import ChurnScorer
from churn_api.domain.predictions import PredictionValidationError


class AnalyticsService:
    def __init__(self, artifact_reader: ArtifactSnapshotReader) -> None:
        self._artifact_reader = artifact_reader

    def health(self) -> dict[str, Any]:
        snapshot = self._artifact_reader.load_current_snapshot()
        return {
            "status": "ready",
            "model_version": snapshot.model.run_id,
            "artifact_version": snapshot.model.run_id,
            "freshness": snapshot.freshness,
        }

    def model_metadata(self) -> dict[str, Any]:
        model = self._artifact_reader.load_current_snapshot().model
        return {
            "run_id": model.run_id,
            "dataset_id": model.dataset_id,
            "model_name": model.model_name,
            "created_at_utc": model.created_at_utc,
            "feature_schema": model.feature_schema,
        }

    def dashboard(self) -> dict[str, Any]:
        snapshot = self._artifact_reader.load_current_snapshot()
        return {
            "artifact_version": snapshot.model.run_id,
            "freshness": snapshot.freshness,
            "kpis": snapshot.metrics,
            "threshold": snapshot.threshold,
            "prediction_samples": to_public_prediction_sample_dtos(
                snapshot.prediction_samples
            ),
            "risk_distribution": _risk_distribution(
                snapshot.prediction_samples,
                snapshot.threshold,
            ),
        }


class PredictionService:
    def __init__(self, artifact_reader: ArtifactSnapshotReader, scorer: ChurnScorer) -> None:
        self._artifact_reader = artifact_reader
        self._scorer = scorer

    def predict(self, customer_features: dict[str, float | str | bool]) -> dict[str, Any]:
        snapshot = self._artifact_reader.load_current_snapshot()
        _validate_features(customer_features, snapshot.model.feature_schema)
        prediction = self._scorer.score(customer_features)
        return {
            "churn_probability": prediction.churn_probability,
            "risk_segment": prediction.risk_segment,
            "threshold_decision": _threshold_decision(
                prediction.churn_probability,
                snapshot.threshold,
            ),
            "retention_priority": prediction.retention_priority,
            "model_version": snapshot.model.run_id,
            "top_drivers": list(prediction.top_drivers),
        }


def _validate_features(features: dict[str, float | str | bool], schema: dict[str, str]) -> None:
    errors: list[str] = []
    for name in schema:
        if name not in features:
            errors.append(f"Missing required feature: {name}")
            continue
    for name, expected_type in schema.items():
        if name not in features:
            continue
        value = features[name]
        if expected_type == "number" and (
            isinstance(value, bool) or not isinstance(value, int | float)
        ):
            errors.append(f"Feature {name} must be a number")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Feature {name} must be a string")
    if errors:
        raise PredictionValidationError(errors)


def _threshold_decision(probability: float, threshold: float) -> str:
    if probability >= threshold:
        return "above_threshold"
    return "below_threshold"


def _risk_distribution(samples: tuple[dict[str, str], ...], threshold: float) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for sample in samples:
        probability = float(sample["churn_probability"])
        segment = "high" if probability >= threshold else "low"
        distribution[segment] = distribution.get(segment, 0) + 1
    return distribution

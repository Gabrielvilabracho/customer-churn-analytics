from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelMetadata:
    run_id: str
    dataset_id: str
    model_name: str
    created_at_utc: str
    feature_schema: dict[str, str]


@dataclass(frozen=True)
class ArtifactSnapshot:
    model: ModelMetadata
    metrics: dict[str, float]
    threshold: float
    prediction_samples: tuple[dict[str, str], ...]
    freshness: dict[str, str]


@dataclass(frozen=True)
class PredictionResult:
    churn_probability: float
    risk_segment: str
    retention_priority: str
    top_drivers: tuple[str, ...]


class PredictionValidationError(ValueError):
    def __init__(self, details: list[str]) -> None:
        super().__init__("Invalid prediction request.")
        self.details = details


class AnalyticsService:
    def __init__(self, artifact_reader: Any) -> None:
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
            "risk_distribution": _risk_distribution(
                snapshot.prediction_samples,
                snapshot.threshold,
            ),
        }


class PredictionService:
    def __init__(self, artifact_reader: Any, scorer: Any) -> None:
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

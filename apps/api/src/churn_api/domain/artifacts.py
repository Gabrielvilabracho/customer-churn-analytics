from dataclasses import dataclass


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

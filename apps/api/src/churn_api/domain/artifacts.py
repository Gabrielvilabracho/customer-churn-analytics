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


class ArtifactUnavailableError(Exception):
    """The selected run cannot serve analytics.

    Raised when the run is missing, unpublished, or fails integrity
    validation. The reason is a deterministic, operator-readable message
    that never exposes artifact contents.
    """

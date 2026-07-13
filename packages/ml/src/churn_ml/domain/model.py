from dataclasses import dataclass
from typing import Any

type PositiveLabel = str | int
type PositiveLabels = frozenset[PositiveLabel]

POSITIVE_LABELS: PositiveLabels = frozenset({"High"})


@dataclass(frozen=True)
class ModelRunMetadata:
    run_id: str
    dataset_id: str
    model_name: str
    feature_names: tuple[str, ...]


@dataclass(frozen=True)
class ChurnPrediction:
    customer_id: str
    churn_probability: float
    risk_segment: str


def risk_segment_for_probability(probability: float) -> str:
    if probability >= 0.7:
        return "high"
    if probability >= 0.4:
        return "medium"
    return "low"


TELCO_POSITIVE_LABELS: PositiveLabels = frozenset({1, "1", "Yes", "yes"})


def label_to_int(value: Any, *, positive_labels: PositiveLabels = POSITIVE_LABELS) -> int:
    return 1 if value in positive_labels else 0

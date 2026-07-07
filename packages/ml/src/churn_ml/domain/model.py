from dataclasses import dataclass
from typing import Any


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


def label_to_int(value: Any) -> int:
    return 1 if value in {1, "1", "Yes", "yes"} else 0

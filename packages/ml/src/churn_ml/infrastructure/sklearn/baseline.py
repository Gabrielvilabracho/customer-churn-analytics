from dataclasses import dataclass
from typing import Any

from churn_ml.domain.model import POSITIVE_LABELS


@dataclass(frozen=True)
class ConstantProbabilityModel:
    model_name: str
    probability: float

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        return tuple(self.probability for _ in rows)


class BaselineChurnRateTrainer:
    def train(
        self,
        rows: list[dict[str, Any]],
        *,
        target_column: str,
        positive_labels: frozenset[str] = POSITIVE_LABELS,
    ) -> ConstantProbabilityModel:
        if not rows:
            raise ValueError("At least one row is required to train the baseline model.")
        positives = sum(1 for row in rows if row[target_column] in positive_labels)
        return ConstantProbabilityModel(
            model_name="baseline_churn_rate",
            probability=positives / len(rows),
        )

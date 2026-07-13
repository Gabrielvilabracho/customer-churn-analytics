from typing import Any, Protocol

from churn_ml.domain.model import PositiveLabels


class ProbabilityModel(Protocol):
    @property
    def model_name(self) -> str: ...

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]: ...


class ModelTrainer(Protocol):
    def train(
        self,
        rows: list[dict[str, Any]],
        *,
        target_column: str,
        positive_labels: PositiveLabels = ...,
    ) -> ProbabilityModel: ...

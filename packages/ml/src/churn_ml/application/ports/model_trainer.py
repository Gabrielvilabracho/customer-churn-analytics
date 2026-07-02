from typing import Any, Protocol


class ProbabilityModel(Protocol):
    model_name: str

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]: ...


class ModelTrainer(Protocol):
    def train(self, rows: list[dict[str, Any]], *, target_column: str) -> ProbabilityModel: ...

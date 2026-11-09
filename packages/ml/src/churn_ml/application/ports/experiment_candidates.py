"""Inward-facing candidate construction and model inspection contracts."""

from typing import Any, Protocol

from churn_ml.application.ports.model_trainer import ModelTrainer, ProbabilityModel


class ExperimentCandidateProvider(Protocol):
    def trainers(
        self,
        feature_columns: tuple[str, ...],
        *,
        seed: int,
        c_values: tuple[float, ...],
    ) -> tuple[ModelTrainer, ...]: ...

    def assert_supported(self, model: ProbabilityModel) -> None: ...

    def parameters(self, model: ProbabilityModel) -> dict[str, Any]: ...

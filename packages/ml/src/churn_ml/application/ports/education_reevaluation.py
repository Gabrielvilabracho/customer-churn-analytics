"""Inward-facing contracts for trusted historical education reevaluation."""

from dataclasses import dataclass
from typing import Any, Protocol

from churn_ml.application.ports.model_trainer import ProbabilityModel


@dataclass(frozen=True)
class EducationReevaluationInputs:
    model: ProbabilityModel
    test_rows: list[dict[str, Any]]
    threshold: float
    source_hashes: dict[str, str]
    historical_metrics: dict[str, float]


class EducationReevaluationInputLoader(Protocol):
    def load(self, run_id: str) -> EducationReevaluationInputs: ...

    def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None: ...

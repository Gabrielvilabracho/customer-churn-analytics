"""Framework-independent inputs and boundaries for offline education analysis."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class EducationAnalysisInputs:
    model: object
    train_rows: list[dict[str, Any]]
    test_rows: list[dict[str, Any]]
    dataset_id: str
    model_name: str
    threshold: float
    source_hashes: dict[str, str]
    model_metrics: dict[str, Any]
    versions: dict[str, str]


class EducationAnalysisInputLoader(Protocol):
    def load(self, run_id: str) -> EducationAnalysisInputs: ...

    def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None: ...


class EducationAnalysisEngine(Protocol):
    def analyze(
        self,
        inputs: EducationAnalysisInputs,
        *,
        seed: int,
        shap_samples: int,
        permutation_samples: int,
        min_cohort_size: int,
    ) -> dict[str, Any]: ...


class EducationAnalysisPublisher(Protocol):
    def assert_available(self, run_id: str, analysis_id: str) -> None: ...

    def publish(self, payload: dict[str, Any]) -> None: ...

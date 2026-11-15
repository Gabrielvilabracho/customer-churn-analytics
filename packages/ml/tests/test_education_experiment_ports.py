from pathlib import Path
from typing import Any

from churn_ml.application.pipelines.experiments import run_experiment
from churn_ml.application.ports.model_trainer import ModelTrainer, ProbabilityModel


class DeterministicModel:
    model_name = "deterministic"

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        return tuple(0.9 if row["Burnout_Risk_Level"] == "High" else 0.1 for row in rows)


class DeterministicTrainer:
    model_name = "deterministic"

    def train(
        self,
        rows: list[dict[str, Any]],
        *,
        target_column: str,
        positive_labels: frozenset[str] = frozenset({"High"}),
    ) -> ProbabilityModel:
        assert rows
        assert target_column == "Burnout_Risk_Level"
        assert positive_labels == frozenset({"High"})
        return DeterministicModel()


class RecordingCandidates:
    def __init__(self) -> None:
        self.request: tuple[tuple[str, ...], int, tuple[float, ...]] | None = None
        self.supported_calls = 0

    def trainers(
        self,
        feature_columns: tuple[str, ...],
        *,
        seed: int,
        c_values: tuple[float, ...],
    ) -> tuple[ModelTrainer, ...]:
        self.request = feature_columns, seed, c_values
        return (DeterministicTrainer(),)

    def assert_supported(self, model: ProbabilityModel) -> None:
        self.supported_calls += 1
        assert model.model_name == "deterministic"

    def parameters(self, model: ProbabilityModel) -> dict[str, Any]:
        assert model.model_name == "deterministic"
        return {"strategy": "deterministic-test"}


class FixedIdentity:
    def capture(self) -> dict[str, Any]:
        return {
            "git_head": "test-revision",
            "source_sha256": "b" * 64,
            "python": "3.13.0",
            "libraries": {"scikit-learn": "1", "pandas": "2", "numpy": "3"},
        }


def student_rows() -> list[dict[str, str]]:
    return [
        {
            "Student_ID": f"student-{index}",
            "Weekly_GenAI_Hours": str(index % 5),
            "Burnout_Risk_Level": ("Low", "Medium", "High")[index % 3],
        }
        for index in range(150)
    ]


def test_experiment_uses_candidate_and_identity_ports() -> None:
    candidates = RecordingCandidates()

    result = run_experiment(
        student_rows(),
        candidate_provider=candidates,
        identity_provider=FixedIdentity(),
        c_values=(0.25, 1.0),
    )

    assert candidates.request == (("Weekly_GenAI_Hours",), 42, (0.25, 1.0))
    assert candidates.supported_calls == 1
    assert result.report["selection"]["model_name"] == "deterministic"
    assert result.report["validation_candidates"][0]["parameters"] == {
        "strategy": "deterministic-test"
    }


def test_experiment_application_does_not_import_outward_adapters() -> None:
    source = (
        Path(__file__).parents[1] / "src/churn_ml/application/pipelines/experiments.py"
    ).read_text(encoding="utf-8")

    assert "churn_ml.infrastructure" not in source

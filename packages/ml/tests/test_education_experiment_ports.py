from pathlib import Path
from typing import Any

from churn_ml.application.pipelines.experiments import (
    CandidateValidation,
    run_experiment,
    select_comparable_candidate,
)
from churn_ml.application.ports.model_trainer import ModelTrainer, ProbabilityModel
from churn_ml.domain.artifacts import ClassificationMetricSet


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

    def family(self, model: ProbabilityModel) -> str:
        assert model.model_name == "deterministic"
        return "logistic"


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


class NamedModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        return tuple(0.5 for _ in rows)


def validation_candidate(
    model_name: str,
    family: str,
    *,
    average_precision: float,
    recall: float = 0.8,
    brier_score: float = 0.2,
    false_positive_rate: float = 0.2,
    flagged_fraction: float = 0.3,
) -> CandidateValidation:
    return CandidateValidation(
        model=NamedModel(model_name),
        family=family,
        threshold=0.5,
        metrics=ClassificationMetricSet(
            pr_auc=average_precision,
            roc_auc=average_precision,
            precision=average_precision,
            recall=recall,
            accuracy=0.75,
            top_risk_capture=0.7,
            workload_at_threshold=flagged_fraction,
        ),
        diagnostics={
            "brier_score": brier_score,
            "false_positive_rate": false_positive_rate,
            "flagged_fraction": flagged_fraction,
        },
    )


def test_advanced_candidate_requires_meaningful_validation_gain() -> None:
    logistic = validation_candidate("logistic", "logistic", average_precision=0.60)
    advanced = validation_candidate("xgboost", "xgboost", average_precision=0.609)

    decision = select_comparable_candidate((logistic, advanced))

    assert decision.selected.model.model_name == "logistic"
    assert decision.advanced_gates[0]["average_precision"] is False
    assert decision.advanced_gates[0]["qualified"] is False


def test_exact_minimum_average_precision_gain_qualifies() -> None:
    logistic = validation_candidate("logistic", "logistic", average_precision=0.56)
    advanced = validation_candidate("xgboost", "xgboost", average_precision=0.57)

    decision = select_comparable_candidate((logistic, advanced))

    assert decision.advanced_gates[0]["average_precision"] is True
    assert decision.advanced_gates[0]["qualified"] is True
    assert decision.selected.model.model_name == "xgboost"


def test_logistic_is_retained_when_an_advanced_guardrail_regresses() -> None:
    logistic = validation_candidate("logistic", "logistic", average_precision=0.60)
    advanced = validation_candidate(
        "lightgbm",
        "lightgbm",
        average_precision=0.70,
        brier_score=0.201,
    )

    decision = select_comparable_candidate((logistic, advanced))

    assert decision.selected.model.model_name == "logistic"
    assert decision.advanced_gates[0]["brier_score"] is False
    assert decision.advanced_gates[0]["qualified"] is False


def test_comparable_candidate_ordering_is_deterministic() -> None:
    logistic_b = validation_candidate("logistic-b", "logistic", average_precision=0.60)
    logistic_a = validation_candidate("logistic-a", "logistic", average_precision=0.60)
    xgboost = validation_candidate("xgboost-b", "xgboost", average_precision=0.70)
    lightgbm = validation_candidate("lightgbm-a", "lightgbm", average_precision=0.70)

    decision = select_comparable_candidate((logistic_b, xgboost, logistic_a, lightgbm))

    assert decision.reference.model.model_name == "logistic-a"
    assert decision.selected.model.model_name == "lightgbm-a"


class ScoredModel:
    def __init__(self, model_name: str, *, perfect: bool) -> None:
        self.model_name = model_name
        self.perfect = perfect
        self.predict_calls = 0

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        self.predict_calls += 1
        scores = []
        for row in rows:
            positive = row["Burnout_Risk_Level"] == "High"
            index = int(str(row["Student_ID"]).rsplit("-", 1)[1])
            if self.perfect:
                scores.append(0.9 if positive else 0.1)
            elif positive:
                scores.append(0.2 if index % 5 == 0 else 0.6)
            else:
                scores.append(0.55 if index % 3 == 0 else 0.1)
        return tuple(scores)


class ExistingModelTrainer:
    def __init__(self, model: ScoredModel) -> None:
        self.model = model

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
        return self.model


class ComparableCandidates:
    def __init__(self, logistic: ScoredModel, advanced: ScoredModel) -> None:
        self.logistic = logistic
        self.advanced = advanced

    def trainers(
        self,
        feature_columns: tuple[str, ...],
        *,
        seed: int,
        c_values: tuple[float, ...],
    ) -> tuple[ModelTrainer, ...]:
        assert feature_columns == ("Weekly_GenAI_Hours",)
        assert seed == 42
        assert c_values == (0.1, 1.0, 10.0)
        return ExistingModelTrainer(self.logistic), ExistingModelTrainer(self.advanced)

    def assert_supported(self, model: ProbabilityModel) -> None:
        assert model in (self.logistic, self.advanced)

    def parameters(self, model: ProbabilityModel) -> dict[str, Any]:
        return {"perfect": model is self.advanced}

    def family(self, model: ProbabilityModel) -> str:
        return "xgboost" if model is self.advanced else "logistic"


def test_comparable_report_freezes_selection_before_one_final_test_prediction() -> None:
    logistic = ScoredModel("logistic", perfect=False)
    advanced = ScoredModel("xgboost", perfect=True)

    result = run_experiment(
        student_rows(),
        candidate_provider=ComparableCandidates(logistic, advanced),
        identity_provider=FixedIdentity(),
    )

    assert result.report["schema_version"] == 2
    assert result.report["selection"]["reference_model_name"] == "logistic"
    assert result.report["selection"]["model_name"] == "xgboost"
    assert result.report["selection"]["advanced_gates"][0]["qualified"] is True
    assert logistic.predict_calls == 1
    assert advanced.predict_calls == 2

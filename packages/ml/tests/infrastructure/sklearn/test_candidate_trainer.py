from typing import Any
from unittest.mock import patch

import pytest
from churn_ml.application.pipelines.evaluate import EvaluationError, select_threshold_tradeoff
from churn_ml.application.pipelines.train import train_and_evaluate_model_candidate
from churn_ml.application.ports.model_trainer import ProbabilityModel
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer
from churn_ml.infrastructure.sklearn.candidate import (
    SklearnLogisticRegressionTrainer,
    _FallbackModel,
)

FEATURE_COLUMNS = ("tenure", "MonthlyCharges", "Contract")


def test_sklearn_candidate_beats_churn_rate_baseline_on_usefulness_metrics() -> None:
    result = _evaluate_candidate(
        train_rows=[
            _row("C001", 1, 92, "Month-to-month", "Yes"),
            _row("C002", 2, 88, "Month-to-month", "Yes"),
            _row("C003", 4, 83, "Month-to-month", "Yes"),
            _row("C004", 30, 52, "Two year", "No"),
            _row("C005", 36, 48, "Two year", "No"),
            _row("C006", 42, 44, "One year", "No"),
        ],
        evaluation_rows=[
            _row("C101", 3, 90, "Month-to-month", "Yes"),
            _row("C102", 40, 49, "Two year", "No"),
            _row("C103", 5, 86, "Month-to-month", "Yes"),
            _row("C104", 33, 51, "One year", "No"),
        ],
    )

    assert result.comparison.baseline_model_name == "baseline_churn_rate"
    assert result.comparison.candidate_model_name == "candidate_logistic_regression"
    assert result.comparison.selected_model_name == "candidate_logistic_regression"
    assert result.metrics.recall == 1.0
    assert result.metrics.top_risk_capture == 1.0


def test_training_evaluation_selects_threshold_with_documented_tradeoff() -> None:
    result = _evaluate_candidate(
        train_rows=[
            _row("C001", 1, 94, "Month-to-month", "Yes"),
            _row("C002", 3, 87, "Month-to-month", "Yes"),
            _row("C003", 25, 66, "One year", "No"),
            _row("C004", 44, 43, "Two year", "No"),
        ],
        evaluation_rows=[
            _row("C101", 2, 91, "Month-to-month", "Yes"),
            _row("C102", 28, 64, "One year", "No"),
            _row("C103", 6, 82, "Month-to-month", "Yes"),
            _row("C104", 48, 41, "Two year", "No"),
        ],
        candidate_thresholds=(0.8, 0.6, 0.4),
        min_recall=1.0,
        min_top_risk_capture=1.0,
    )

    # Highest threshold satisfying min_recall=1.0 with random_state=7.
    assert result.threshold.threshold == 0.6
    assert "recall" in result.threshold.tradeoff
    assert "workload" in result.threshold.tradeoff
    assert 0 < result.metrics.workload_at_threshold <= 1


def test_training_evaluation_rejects_misleading_accuracy_for_candidate() -> None:
    with pytest.raises(EvaluationError, match="misleading accuracy"):
        _evaluate_candidate(
            train_rows=[
                _row("C001", 1, 50, "Month-to-month", "No"),
                _row("C002", 2, 51, "Month-to-month", "No"),
                _row("C003", 3, 52, "Month-to-month", "No"),
                _row("C004", 4, 53, "Month-to-month", "No"),
                _row("C005", 5, 54, "Month-to-month", "No"),
                _row("C006", 6, 55, "Month-to-month", "Yes"),
            ],
            evaluation_rows=[
                *[_row(f"C10{i}", 20 - i, 60 - i, "Month-to-month", "No") for i in range(1, 10)],
                _row("C110", 1, 50, "Month-to-month", "Yes"),
            ],
            candidate_thresholds=(1.0,),
            min_recall=0.0,
        )


def _evaluate_candidate(
    *,
    train_rows: list[dict[str, str]],
    evaluation_rows: list[dict[str, str]],
    candidate_thresholds: tuple[float, ...] = (0.7, 0.5, 0.3),
    min_recall: float = 0.8,
    min_top_risk_capture: float = 0.8,
):
    return train_and_evaluate_model_candidate(
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=7,
        ),
        train_rows=train_rows,
        evaluation_rows=evaluation_rows,
        target_column="Churn",
        candidate_thresholds=candidate_thresholds,
        min_recall=min_recall,
        min_top_risk_capture=min_top_risk_capture,
        top_risk_fraction=0.5,
    )


def _row(customer_id: str, tenure: int, charges: int, contract: str, churn: str) -> dict[str, str]:
    return {
        "customerID": customer_id,
        "tenure": str(tenure),
        "MonthlyCharges": f"{charges:.1f}",
        "Contract": contract,
        "Churn": churn,
    }


# ---------------------------------------------------------------------------
# C3 — _FallbackModel is used when sklearn is unavailable
# ---------------------------------------------------------------------------


def test_fallback_model_used_when_sklearn_import_fails() -> None:
    """When sklearn import raises ModuleNotFoundError, _FallbackModel must be used."""
    rows = [
        {"tenure": "1", "MonthlyCharges": "72.5", "Churn": "Yes"},
        {"tenure": "24", "MonthlyCharges": "41.0", "Churn": "No"},
        {"tenure": "6", "MonthlyCharges": "65.0", "Churn": "Yes"},
        {"tenure": "36", "MonthlyCharges": "30.0", "Churn": "No"},
        {"tenure": "12", "MonthlyCharges": "55.0", "Churn": "Yes"},
    ]
    trainer = SklearnLogisticRegressionTrainer(
        model_name="test_fallback",
        feature_columns=("tenure", "MonthlyCharges"),
        random_state=42,
    )

    with patch(
        "churn_ml.infrastructure.sklearn.candidate.import_module",
        side_effect=ModuleNotFoundError("No module named 'sklearn'"),
    ):
        model = trainer.train(rows, target_column="Churn")

    assert model is not None
    assert isinstance(model.estimator, _FallbackModel)


def test_fallback_model_predictions_are_valid_probabilities() -> None:
    """_FallbackModel must return floats in [0, 1] for every row."""
    rows = [
        {"tenure": "1", "MonthlyCharges": "72.5", "Churn": "Yes"},
        {"tenure": "24", "MonthlyCharges": "41.0", "Churn": "No"},
        {"tenure": "6", "MonthlyCharges": "65.0", "Churn": "Yes"},
        {"tenure": "36", "MonthlyCharges": "30.0", "Churn": "No"},
        {"tenure": "12", "MonthlyCharges": "55.0", "Churn": "No"},
    ]
    trainer = SklearnLogisticRegressionTrainer(
        model_name="test_fallback",
        feature_columns=("tenure", "MonthlyCharges"),
        random_state=42,
    )

    with patch(
        "churn_ml.infrastructure.sklearn.candidate.import_module",
        side_effect=ModuleNotFoundError("No module named 'sklearn'"),
    ):
        model = trainer.train(rows, target_column="Churn")

    probs = model.predict_probabilities(rows)
    assert len(probs) == len(rows)
    for prob in probs:
        assert isinstance(prob, float)
        assert 0.0 <= prob <= 1.0


# ---------------------------------------------------------------------------
# C4 — "No threshold satisfies recall" path raises EvaluationError
# ---------------------------------------------------------------------------


def test_select_threshold_tradeoff_raises_when_no_threshold_satisfies_min_recall() -> None:
    """select_threshold_tradeoff must raise EvaluationError containing 'recall'
    when no candidate threshold achieves the minimum recall requirement."""
    # The single positive example gets probability 0.3, which is below all candidate
    # thresholds; recall is 0 at every threshold so min_recall=1.0 is unsatisfiable.
    with pytest.raises(EvaluationError, match="recall"):
        select_threshold_tradeoff(
            actual_labels=(1, 0, 0),
            probabilities=(0.3, 0.4, 0.5),
            candidate_thresholds=(0.5, 0.4),
            min_recall=1.0,
            top_risk_fraction=0.5,
        )


# ---------------------------------------------------------------------------
# F2 — candidate must be trained exactly once
# ---------------------------------------------------------------------------

class _CountingTrainer:
    """Wraps a real trainer and counts how many times train() is called."""

    def __init__(self, delegate: SklearnLogisticRegressionTrainer) -> None:
        self._delegate = delegate
        self.train_call_count = 0

    def train(self, rows: list[dict[str, Any]], *, target_column: str) -> ProbabilityModel:
        self.train_call_count += 1
        return self._delegate.train(rows, target_column=target_column)


def test_candidate_trained_exactly_once_during_train_and_evaluate() -> None:
    """train_and_evaluate_model_candidate must not train the candidate model twice."""
    counting = _CountingTrainer(
        SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=7,
        )
    )
    train_rows = [
        _row("C001", 1, 92, "Month-to-month", "Yes"),
        _row("C002", 2, 88, "Month-to-month", "Yes"),
        _row("C003", 30, 52, "Two year", "No"),
        _row("C004", 36, 48, "Two year", "No"),
    ]
    evaluation_rows = [
        _row("C101", 3, 90, "Month-to-month", "Yes"),
        _row("C102", 40, 49, "Two year", "No"),
    ]
    train_and_evaluate_model_candidate(
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=counting,
        train_rows=train_rows,
        evaluation_rows=evaluation_rows,
        target_column="Churn",
        candidate_thresholds=(0.7, 0.5, 0.3),
        min_recall=0.5,
        min_top_risk_capture=0.5,
        top_risk_fraction=0.5,
    )
    assert counting.train_call_count == 1, (
        f"Expected candidate to be trained once, got {counting.train_call_count}."
    )

from typing import Any

import pytest
from churn_ml.application.pipelines.evaluate import (
    EvaluationError,
    evaluate_predictions,
    reject_misleading_accuracy,
    select_threshold_tradeoff,
)
from churn_ml.application.pipelines.features import deterministic_train_test_split
from churn_ml.application.pipelines.train import compare_model_candidates
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer


class _FixedProbabilityModel:
    def __init__(self, model_name: str, probabilities: tuple[float, ...]) -> None:
        self.model_name = model_name
        self._probabilities = probabilities

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        return self._probabilities[: len(rows)]


class _FixedTrainer:
    def __init__(self, model_name: str, probabilities: tuple[float, ...]) -> None:
        self._model_name = model_name
        self._probabilities = probabilities

    def train(self, rows: list[dict[str, Any]], *, target_column: str) -> _FixedProbabilityModel:
        return _FixedProbabilityModel(self._model_name, self._probabilities)


def test_deterministic_train_test_split_is_stable_for_same_seed() -> None:
    rows = [
        {
            "customer_id": f"C00{index}",
            "monthly_charges": 40 + index,
            "churn": "Yes" if index % 3 == 0 else "No",
        }
        for index in range(1, 7)
    ]

    first = deterministic_train_test_split(rows, test_fraction=0.33, seed=42)
    second = deterministic_train_test_split(rows, test_fraction=0.33, seed=42)

    assert len(first.train_rows) == 4
    assert len(first.test_rows) == 2
    assert sorted(row["customer_id"] for row in first.train_rows + first.test_rows) == [
        "C001",
        "C002",
        "C003",
        "C004",
        "C005",
        "C006",
    ]
    assert first == second


def test_deterministic_train_test_split_changes_with_seed_without_losing_rows() -> None:
    rows = [
        {
            "customer_id": f"C00{index}",
            "monthly_charges": 40 + index,
            "churn": "Yes" if index % 2 == 0 else "No",
        }
        for index in range(1, 7)
    ]

    first = deterministic_train_test_split(rows, test_fraction=0.5, seed=1)
    second = deterministic_train_test_split(rows, test_fraction=0.5, seed=2)

    assert [row["customer_id"] for row in first.train_rows] != [
        row["customer_id"] for row in second.train_rows
    ]
    assert sorted(row["customer_id"] for row in first.train_rows + first.test_rows) == [
        "C001",
        "C002",
        "C003",
        "C004",
        "C005",
        "C006",
    ]


def test_evaluate_predictions_reports_business_oriented_metrics() -> None:
    metrics = evaluate_predictions(
        actual_labels=(1, 0, 1, 0, 1),
        probabilities=(0.9, 0.6, 0.7, 0.3, 0.2),
        threshold=0.5,
        top_risk_fraction=0.4,
    )

    assert metrics.precision == pytest.approx(2 / 3)
    assert metrics.recall == pytest.approx(2 / 3)
    assert metrics.accuracy == pytest.approx(0.6)
    assert metrics.top_risk_capture == pytest.approx(2 / 3)
    assert metrics.workload_at_threshold == pytest.approx(0.6)
    assert metrics.pr_auc > 0
    assert metrics.roc_auc > 0


def test_misleading_accuracy_is_rejected_for_executive_reporting() -> None:
    metrics = evaluate_predictions(
        actual_labels=(0, 0, 0, 0, 0, 0, 0, 0, 1, 1),
        probabilities=(0.1, 0.1, 0.2, 0.2, 0.15, 0.18, 0.22, 0.24, 0.25, 0.3),
        threshold=0.5,
        top_risk_fraction=0.2,
    )

    with pytest.raises(EvaluationError, match="misleading accuracy"):
        reject_misleading_accuracy(metrics, min_recall=0.5, min_top_risk_capture=0.5)


def test_threshold_selection_documents_recall_workload_tradeoff() -> None:
    selection = select_threshold_tradeoff(
        actual_labels=(1, 0, 1, 0, 1),
        probabilities=(0.91, 0.72, 0.63, 0.42, 0.37),
        candidate_thresholds=(0.7, 0.6, 0.3),
        min_recall=0.65,
        top_risk_fraction=0.4,
    )

    assert selection.threshold == 0.6
    assert "recall" in selection.tradeoff
    assert "workload" in selection.tradeoff


def test_baseline_trainer_uses_training_churn_rate_without_sklearn_dependency() -> None:
    rows = [
        {"customer_id": "C001", "churn": "Yes"},
        {"customer_id": "C002", "churn": "No"},
        {"customer_id": "C003", "churn": "Yes"},
        {"customer_id": "C004", "churn": "No"},
    ]

    model = BaselineChurnRateTrainer().train(
        rows, target_column="churn", positive_labels=frozenset({"Yes"})
    )

    assert model.model_name == "baseline_churn_rate"
    assert model.predict_probabilities(rows) == (0.5, 0.5, 0.5, 0.5)


def test_model_candidate_comparison_selects_candidate_with_better_churn_usefulness() -> None:
    train_rows = [
        {"customer_id": "C001", "churn": "Yes"},
        {"customer_id": "C002", "churn": "No"},
        {"customer_id": "C003", "churn": "No"},
        {"customer_id": "C004", "churn": "No"},
    ]
    evaluation_rows = [
        {"customer_id": "C101", "churn": "Yes"},
        {"customer_id": "C102", "churn": "No"},
        {"customer_id": "C103", "churn": "Yes"},
        {"customer_id": "C104", "churn": "No"},
    ]

    comparison = compare_model_candidates(
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=_FixedTrainer("candidate_ranker", (0.91, 0.2, 0.82, 0.1)),
        train_rows=train_rows,
        evaluation_rows=evaluation_rows,
        target_column="churn",
        threshold=0.5,
        top_risk_fraction=0.5,
        positive_labels=frozenset({"Yes"}),
    )

    assert comparison.baseline_model_name == "baseline_churn_rate"
    assert comparison.candidate_model_name == "candidate_ranker"
    assert comparison.baseline_metrics.recall == 0.0
    assert comparison.candidate_metrics.recall == 1.0
    assert comparison.candidate_metrics.top_risk_capture == 1.0
    assert comparison.selected_model_name == "candidate_ranker"
    assert comparison.selection_reason == "candidate has stronger churn usefulness metrics"

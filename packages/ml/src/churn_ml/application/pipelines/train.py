import logging
from dataclasses import dataclass, field
from typing import Any

from churn_ml.application.pipelines.evaluate import (
    EvaluationError,
    evaluate_predictions,
    reject_misleading_accuracy,
    select_threshold_tradeoff,
)
from churn_ml.application.ports.model_trainer import ModelTrainer, ProbabilityModel
from churn_ml.domain.artifacts import ClassificationMetricSet, ThresholdSelection
from churn_ml.domain.model import POSITIVE_LABELS, label_to_int

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainedModelCandidate:
    name: str
    model: ProbabilityModel


@dataclass(frozen=True)
class ModelComparison:
    baseline_model_name: str
    candidate_model_name: str
    baseline_metrics: ClassificationMetricSet
    candidate_metrics: ClassificationMetricSet
    selected_model_name: str
    selection_reason: str


@dataclass(frozen=True)
class TrainingEvaluationResult:
    comparison: ModelComparison
    threshold: ThresholdSelection
    metrics: ClassificationMetricSet
    # Excluded from eq/hash: holds the trained model object, not part of result identity.
    trained_candidate: ProbabilityModel | None = field(hash=False, compare=False, default=None)


def train_model_candidate(
    trainer: ModelTrainer,
    rows: list[dict[str, Any]],
    *,
    target_column: str,
    positive_labels: frozenset[str] = POSITIVE_LABELS,
) -> TrainedModelCandidate:
    try:
        model = trainer.train(rows, target_column=target_column, positive_labels=positive_labels)
    except TypeError:
        model = trainer.train(rows, target_column=target_column)
    return TrainedModelCandidate(name=model.model_name, model=model)


def compare_model_candidates(
    *,
    baseline_trainer: ModelTrainer,
    candidate_trainer: ModelTrainer,
    train_rows: list[dict[str, Any]],
    evaluation_rows: list[dict[str, Any]],
    target_column: str,
    threshold: float,
    top_risk_fraction: float,
    pretrained_candidate: TrainedModelCandidate | None = None,
    positive_labels: frozenset[str] = POSITIVE_LABELS,
) -> ModelComparison:
    baseline = train_model_candidate(
        baseline_trainer, train_rows, target_column=target_column, positive_labels=positive_labels
    )
    # Reuse a pre-trained candidate when provided to avoid training the same model twice.
    candidate = (
        pretrained_candidate
        if pretrained_candidate is not None
        else train_model_candidate(
            candidate_trainer,
            train_rows,
            target_column=target_column,
            positive_labels=positive_labels,
        )
    )
    actual_labels = tuple(
        label_to_int(row[target_column], positive_labels=positive_labels)
        for row in evaluation_rows
    )
    baseline_metrics = evaluate_predictions(
        actual_labels=actual_labels,
        probabilities=baseline.model.predict_probabilities(evaluation_rows),
        threshold=threshold,
        top_risk_fraction=top_risk_fraction,
    )
    candidate_metrics = evaluate_predictions(
        actual_labels=actual_labels,
        probabilities=candidate.model.predict_probabilities(evaluation_rows),
        threshold=threshold,
        top_risk_fraction=top_risk_fraction,
    )
    selected_name = _select_model_name(
        baseline_name=baseline.name,
        candidate_name=candidate.name,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
    )
    reason = (
        "candidate has stronger churn usefulness metrics"
        if selected_name == candidate.name
        else "baseline remains stronger or equivalent on churn usefulness metrics"
    )
    return ModelComparison(
        baseline_model_name=baseline.name,
        candidate_model_name=candidate.name,
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        selected_model_name=selected_name,
        selection_reason=reason,
    )


def train_and_evaluate_model_candidate(
    *,
    baseline_trainer: ModelTrainer,
    candidate_trainer: ModelTrainer,
    train_rows: list[dict[str, Any]],
    evaluation_rows: list[dict[str, Any]],
    target_column: str,
    candidate_thresholds: tuple[float, ...],
    min_recall: float,
    min_top_risk_capture: float,
    top_risk_fraction: float,
    positive_labels: frozenset[str] = POSITIVE_LABELS,
) -> TrainingEvaluationResult:
    candidate = train_model_candidate(
        candidate_trainer, train_rows, target_column=target_column, positive_labels=positive_labels
    )
    actual_labels = tuple(
        label_to_int(row[target_column], positive_labels=positive_labels)
        for row in evaluation_rows
    )
    candidate_probabilities = candidate.model.predict_probabilities(evaluation_rows)
    try:
        threshold = select_threshold_tradeoff(
            actual_labels=actual_labels,
            probabilities=candidate_probabilities,
            candidate_thresholds=candidate_thresholds,
            min_recall=min_recall,
            top_risk_fraction=top_risk_fraction,
        )
    except EvaluationError as exc:
        logger.warning("Threshold selection failed: %s", exc)
        raise
    metrics = evaluate_predictions(
        actual_labels=actual_labels,
        probabilities=candidate_probabilities,
        threshold=threshold.threshold,
        top_risk_fraction=top_risk_fraction,
    )
    try:
        reject_misleading_accuracy(
            metrics,
            min_recall=min_recall,
            min_top_risk_capture=min_top_risk_capture,
        )
    except EvaluationError as exc:
        logger.warning("Evaluation rejected — misleading accuracy: %s", exc)
        raise
    comparison = compare_model_candidates(
        baseline_trainer=baseline_trainer,
        candidate_trainer=candidate_trainer,
        train_rows=train_rows,
        evaluation_rows=evaluation_rows,
        target_column=target_column,
        threshold=threshold.threshold,
        top_risk_fraction=top_risk_fraction,
        pretrained_candidate=candidate,
        positive_labels=positive_labels,
    )
    return TrainingEvaluationResult(
        comparison=comparison,
        threshold=threshold,
        metrics=metrics,
        trained_candidate=candidate.model,
    )


def _select_model_name(
    *,
    baseline_name: str,
    candidate_name: str,
    baseline_metrics: ClassificationMetricSet,
    candidate_metrics: ClassificationMetricSet,
) -> str:
    baseline_score = _churn_usefulness_score(baseline_metrics)
    candidate_score = _churn_usefulness_score(candidate_metrics)
    if candidate_score > baseline_score:
        return candidate_name
    return baseline_name


def _churn_usefulness_score(metrics: ClassificationMetricSet) -> tuple[float, float, float, float]:
    return (metrics.recall, metrics.top_risk_capture, metrics.pr_auc, metrics.precision)



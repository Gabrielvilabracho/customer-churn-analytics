from churn_ml.domain.artifacts import ClassificationMetricSet, ThresholdSelection


class EvaluationError(ValueError):
    """Raised when model metrics are unsafe for executive reporting."""


def evaluate_predictions(
    *,
    actual_labels: tuple[int, ...],
    probabilities: tuple[float, ...],
    threshold: float,
    top_risk_fraction: float,
) -> ClassificationMetricSet:
    if len(actual_labels) != len(probabilities):
        raise EvaluationError("Labels and probabilities must have the same length.")
    if not actual_labels:
        raise EvaluationError("At least one prediction is required for evaluation.")
    if not 0 < top_risk_fraction <= 1:
        raise EvaluationError("top_risk_fraction must be between 0 and 1.")

    predictions = tuple(1 if probability >= threshold else 0 for probability in probabilities)
    pairs = tuple(zip(actual_labels, predictions, strict=True))
    true_positives = sum(1 for actual, predicted in pairs if actual == predicted == 1)
    false_positives = sum(1 for actual, predicted in pairs if actual == 0 and predicted == 1)
    false_negatives = sum(1 for actual, predicted in pairs if actual == 1 and predicted == 0)
    correct = sum(1 for actual, predicted in pairs if actual == predicted)
    predicted_positive = sum(predictions)

    return ClassificationMetricSet(
        pr_auc=_average_precision(actual_labels, probabilities),
        roc_auc=_roc_auc(actual_labels, probabilities),
        precision=_safe_divide(true_positives, true_positives + false_positives),
        recall=_safe_divide(true_positives, true_positives + false_negatives),
        accuracy=correct / len(actual_labels),
        top_risk_capture=_top_risk_capture(actual_labels, probabilities, top_risk_fraction),
        workload_at_threshold=predicted_positive / len(actual_labels),
    )


def reject_misleading_accuracy(
    metrics: ClassificationMetricSet,
    *,
    min_recall: float,
    min_top_risk_capture: float,
) -> None:
    if metrics.accuracy >= 0.8 and (
        metrics.recall < min_recall or metrics.top_risk_capture < min_top_risk_capture
    ):
        raise EvaluationError(
            "Model has misleading accuracy and is unsuitable for executive reporting."
        )


def select_threshold_tradeoff(
    *,
    actual_labels: tuple[int, ...],
    probabilities: tuple[float, ...],
    candidate_thresholds: tuple[float, ...],
    min_recall: float,
    top_risk_fraction: float,
) -> ThresholdSelection:
    if not candidate_thresholds:
        raise EvaluationError("At least one candidate threshold is required.")

    ranked_candidates = sorted(candidate_thresholds, reverse=True)
    for threshold in ranked_candidates:
        metrics = evaluate_predictions(
            actual_labels=actual_labels,
            probabilities=probabilities,
            threshold=threshold,
            top_risk_fraction=top_risk_fraction,
        )
        if metrics.recall >= min_recall:
            return ThresholdSelection(
                threshold=threshold,
                tradeoff=(
                    f"Selected threshold {threshold:.2f} to reach recall "
                    f"{metrics.recall:.2f} with workload {metrics.workload_at_threshold:.2f}."
                ),
            )

    raise EvaluationError("No threshold satisfies the minimum recall requirement.")


def _top_risk_capture(
    actual_labels: tuple[int, ...], probabilities: tuple[float, ...], fraction: float
) -> float:
    churn_count = sum(actual_labels)
    if churn_count == 0:
        return 0.0
    top_count = max(1, round(len(probabilities) * fraction))
    captured = 0.0
    remaining = top_count
    for count, positives in _score_groups(actual_labels, probabilities):
        # Expected capture under a uniformly random, label-blind boundary tie.
        captured += positives * min(remaining, count) / count
        remaining -= min(remaining, count)
        if remaining == 0:
            break
    return captured / churn_count


def _average_precision(actual_labels: tuple[int, ...], probabilities: tuple[float, ...]) -> float:
    positives = sum(actual_labels)
    if positives == 0:
        return 0.0
    precision_sum = 0.0
    found_positives = 0
    found_rows = 0
    for count, group_positives in _score_groups(actual_labels, probabilities):
        found_rows += count
        found_positives += group_positives
        precision_sum += group_positives * found_positives / found_rows
    return precision_sum / positives


def _score_groups(
    actual_labels: tuple[int, ...], probabilities: tuple[float, ...]
) -> list[tuple[int, int]]:
    from itertools import groupby

    ranked = sorted(zip(probabilities, actual_labels, strict=True), key=lambda x: -x[0])
    groups = []
    for _, group in groupby(ranked, key=lambda x: x[0]):
        labels = [label for _, label in group]
        groups.append((len(labels), sum(labels)))
    return groups


def _roc_auc(actual_labels: tuple[int, ...], probabilities: tuple[float, ...]) -> float:
    positives = [
        score for score, actual in zip(probabilities, actual_labels, strict=True) if actual == 1
    ]
    negatives = [
        score for score, actual in zip(probabilities, actual_labels, strict=True) if actual == 0
    ]
    if not positives or not negatives:
        return 0.0
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def _safe_divide(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator

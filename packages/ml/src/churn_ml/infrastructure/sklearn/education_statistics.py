"""Descriptive associations and held-out cohorts, not causal estimates."""

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, pointbiserialr, spearmanr
from sklearn.metrics import precision_score, recall_score


def associations(
    train: Any,
    test: Any,
    train_y: Any,
    test_y: Any,
    numeric: list[str],
) -> list[dict[str, Any]]:
    def measure(frame: Any, labels: Any, feature: str) -> dict[str, Any]:
        values = frame[feature]
        result: dict[str, Any] = {"count": len(values), "missing_count": int(values.isna().sum())}
        if feature in numeric:
            defined = values.nunique() > 1 and len(set(labels)) > 1
            result.update(
                point_biserial=float(pointbiserialr(labels, values).statistic) if defined else None,
                spearman=float(spearmanr(values, labels).statistic) if defined else None,
            )
        else:
            table = pd.crosstab(values, labels)
            divisor = min(table.shape) - 1
            result["cramers_v"] = (
                float(
                    np.sqrt(
                        chi2_contingency(table, correction=False).statistic
                        / (len(values) * divisor)
                    )
                )
                if divisor > 0
                else None
            )
        return result

    return [
        {
            "feature": feature,
            "kind": "numeric" if feature in numeric else "categorical",
            "train": measure(train, train_y, feature),
            "test": measure(test, test_y, feature),
        }
        for feature in train.columns
    ]


def wilson_interval(successes: int, count: int) -> list[float]:
    z = 1.959963984540054
    rate = successes / count
    denominator = 1 + z * z / count
    center = (rate + z * z / (2 * count)) / denominator
    half = z * np.sqrt(rate * (1 - rate) / count + z * z / (4 * count * count)) / denominator
    return [max(0.0, float(center - half)), min(1.0, float(center + half))]


def cohorts(
    train: Any,
    test: Any,
    labels: Any,
    probabilities: Any,
    *,
    numeric: list[str],
    threshold: float,
    minimum: int,
) -> list[dict[str, Any]]:
    results = []
    overall = float(np.mean(labels))
    for feature in test.columns:
        if feature in numeric:
            # Training-only quantiles keep the held-out cohort definition honest.
            cuts = np.unique(np.quantile(train[feature].astype(float), [0.25, 0.5, 0.75]))
            edges = np.concatenate(([-np.inf], cuts, [np.inf]))
            groups = pd.cut(test[feature].astype(float), edges, include_lowest=True).astype(str)
        else:
            groups = test[feature].astype(str)
        for group in sorted(groups.unique()):
            mask = (groups == group).to_numpy()
            count = int(mask.sum())
            small = count < minimum
            actual = labels[mask]
            prediction = probabilities[mask] >= threshold
            rate = float(np.mean(actual))
            results.append(
                {
                    "feature": feature,
                    "group": str(group),
                    "count": count,
                    "suppressed": small,
                    "observed_high_rate": None if small else rate,
                    "observed_ci": None if small else wilson_interval(int(actual.sum()), count),
                    "average_predicted_risk": None if small else float(probabilities[mask].mean()),
                    "difference_from_overall": None if small else rate - overall,
                    "precision": None
                    if small
                    else float(precision_score(actual, prediction, zero_division=0)),
                    "recall": None
                    if small
                    else float(recall_score(actual, prediction, zero_division=0)),
                }
            )
    return results

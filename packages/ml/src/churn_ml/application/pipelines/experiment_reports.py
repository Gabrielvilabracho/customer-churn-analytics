"""Aggregate diagnostics and immutable local reports; no individual predictions."""

import hashlib
import json
from math import isfinite, log
from typing import Any


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def diagnostics(
    labels: tuple[int, ...], scores: tuple[float, ...], threshold: float
) -> dict[str, Any]:
    if not labels or len(labels) != len(scores) or any(y not in (0, 1) for y in labels):
        raise ValueError("Nonempty paired binary labels and probabilities are required")
    if not isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between zero and one")
    if any(not isfinite(p) or not 0 <= p <= 1 for p in scores):
        raise ValueError("Finite probabilities between zero and one are required")
    pairs = list(zip(labels, scores, strict=True))
    tp = sum(y == 1 and p >= threshold for y, p in pairs)
    fp = sum(y == 0 and p >= threshold for y, p in pairs)
    fn = sum(y == 1 and p < threshold for y, p in pairs)
    tn = sum(y == 0 and p < threshold for y, p in pairs)
    reliability = []
    for index in range(10):
        group = [(y, p) for y, p in pairs if min(int(p * 10), 9) == index]
        reliability.append(
            {
                "lower": index / 10,
                "upper": (index + 1) / 10,
                "count": len(group),
                "mean_score": sum(p for _, p in group) / len(group) if group else None,
                "observed_rate": sum(y for y, _ in group) / len(group) if group else None,
            }
        )
    clipped = [(y, min(max(p, 1e-15), 1 - 1e-15)) for y, p in pairs]
    return {
        "count": len(pairs),
        "observed_high_rate": sum(labels) / len(labels),
        "mean_score": sum(scores) / len(scores),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "flagged_count": tp + fp,
        "flagged_fraction": (tp + fp) / len(labels),
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "brier_score": sum((p - y) ** 2 for y, p in pairs) / len(pairs),
        "log_loss": -sum(y * log(p) + (1 - y) * log(1 - p) for y, p in clipped) / len(pairs),
        "reliability": reliability,
    }

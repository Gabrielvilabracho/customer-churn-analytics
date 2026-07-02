from dataclasses import dataclass
from random import Random
from typing import Any

from churn_ml.domain.customer import FeatureDictionary


@dataclass(frozen=True)
class SplitResult:
    train_rows: list[dict[str, Any]]
    test_rows: list[dict[str, Any]]


def deterministic_train_test_split(
    rows: list[dict[str, Any]],
    *,
    test_fraction: float,
    seed: int,
) -> SplitResult:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1.")
    if len(rows) < 2:
        raise ValueError("At least two rows are required for a train/test split.")

    shuffled = [dict(row) for row in rows]
    Random(seed).shuffle(shuffled)
    test_count = max(1, round(len(shuffled) * test_fraction))
    test_count = min(test_count, len(shuffled) - 1)
    return SplitResult(
        train_rows=shuffled[:-test_count],
        test_rows=shuffled[-test_count:],
    )


def build_feature_dictionary(
    rows: list[dict[str, Any]],
    *,
    customer_key: str,
    target_column: str,
) -> FeatureDictionary:
    return FeatureDictionary.from_rows(
        rows,
        customer_key=customer_key,
        target_column=target_column,
    )

import csv
from dataclasses import dataclass
from pathlib import Path
from random import Random
from typing import Any

from churn_ml.application.pipelines.profile import screen_dataset_profile
from churn_ml.application.ports.artifact_store import ArtifactStore
from churn_ml.domain.artifacts import CleanedSplitArtifact
from churn_ml.domain.customer import LEAKAGE_COLUMNS, FeatureDictionary


@dataclass(frozen=True)
class SplitResult:
    train_rows: list[dict[str, Any]]
    test_rows: list[dict[str, Any]]


@dataclass(frozen=True)
class PreprocessingResult:
    train_rows: list[dict[str, str]]
    test_rows: list[dict[str, str]]
    feature_columns: tuple[str, ...]
    train_fit_metadata: dict[str, Any]


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


def prepare_training_splits_from_csv(
    csv_path: Path,
    *,
    artifact_store: ArtifactStore,
    run_id: str,
    dataset_id: str,
    customer_key: str,
    target_column: str,
    test_fraction: float,
    seed: int,
    excluded_feature_columns: frozenset[str] = LEAKAGE_COLUMNS,
) -> PreprocessingResult:
    rows = _read_csv_rows(csv_path)
    screen_dataset_profile(
        rows,
        target_column=target_column,
        excluded_identifier_columns=(customer_key,),
    )
    dictionary = build_feature_dictionary(
        rows,
        customer_key=customer_key,
        target_column=target_column,
        excluded_feature_columns=excluded_feature_columns,
    )
    feature_columns = tuple(feature.name for feature in dictionary.features)
    split = stratified_train_test_split(
        rows,
        target_column=target_column,
        test_fraction=test_fraction,
        seed=seed,
    )
    train_rows = [_stringify_row(row) for row in split.train_rows]
    test_rows = [_stringify_row(row) for row in split.test_rows]

    artifact_store.save_cleaned_split(
        CleanedSplitArtifact(
            run_id=run_id,
            dataset_id=dataset_id,
            split_name="train",
            feature_columns=feature_columns,
            target_column=target_column,
            rows=tuple(train_rows),
        )
    )
    artifact_store.save_cleaned_split(
        CleanedSplitArtifact(
            run_id=run_id,
            dataset_id=dataset_id,
            split_name="test",
            feature_columns=feature_columns,
            target_column=target_column,
            rows=tuple(test_rows),
        )
    )
    return PreprocessingResult(
        train_rows=train_rows,
        test_rows=test_rows,
        feature_columns=feature_columns,
        train_fit_metadata=_build_train_fit_metadata(train_rows, feature_columns=feature_columns),
    )


def stratified_train_test_split(
    rows: list[dict[str, Any]],
    *,
    target_column: str,
    test_fraction: float,
    seed: int,
) -> SplitResult:
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1.")
    grouped_rows: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped_rows.setdefault(str(row[target_column]), []).append(dict(row))
    if any(len(group) < 2 for group in grouped_rows.values()):
        raise ValueError("Each target class needs at least two rows for stratified split.")

    train_rows: list[dict[str, Any]] = []
    test_rows: list[dict[str, Any]] = []
    random = Random(seed)
    for target_value in sorted(grouped_rows):
        group = grouped_rows[target_value]
        random.shuffle(group)
        test_count = max(1, round(len(group) * test_fraction))
        test_count = min(test_count, len(group) - 1)
        train_rows.extend(group[:-test_count])
        test_rows.extend(group[-test_count:])

    random.shuffle(train_rows)
    random.shuffle(test_rows)
    return SplitResult(train_rows=train_rows, test_rows=test_rows)


def build_feature_dictionary(
    rows: list[dict[str, Any]],
    *,
    customer_key: str,
    target_column: str,
    excluded_feature_columns: frozenset[str] = LEAKAGE_COLUMNS,
) -> FeatureDictionary:
    return FeatureDictionary.from_rows(
        rows,
        customer_key=customer_key,
        target_column=target_column,
        excluded_feature_columns=excluded_feature_columns,
    )


def _read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as raw_file:
        return [dict(row) for row in csv.DictReader(raw_file)]


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in row.items()}


def _build_train_fit_metadata(
    train_rows: list[dict[str, str]], *, feature_columns: tuple[str, ...]
) -> dict[str, Any]:
    categorical_levels = {
        column: tuple(sorted({row[column] for row in train_rows}))
        for column in feature_columns
        if not _is_numeric_column(train_rows, column)
    }
    return {
        "feature_columns": feature_columns,
        "categorical_levels": categorical_levels,
    }


def _is_numeric_column(rows: list[dict[str, str]], column: str) -> bool:
    try:
        for row in rows:
            float(row[column])
    except ValueError:
        return False
    return True

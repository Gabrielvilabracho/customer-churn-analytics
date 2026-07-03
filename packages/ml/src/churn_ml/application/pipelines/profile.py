from dataclasses import dataclass
from typing import Any


class DatasetProfileError(ValueError):
    """Raised when a dataset cannot be approved for modeling."""


@dataclass(frozen=True)
class DatasetProfileResult:
    modeling_ready: bool
    row_count: int
    identifier_only_columns: tuple[str, ...]
    limitations: tuple[str, ...]


def screen_dataset_profile(
    rows: list[dict[str, Any]],
    *,
    target_column: str,
    excluded_identifier_columns: tuple[str, ...] = (),
) -> DatasetProfileResult:
    if not rows:
        raise DatasetProfileError("Dataset contains no rows.")
    _validate_required_columns(rows, target_column=target_column)
    if any(not row.get(target_column) for row in rows):
        raise DatasetProfileError("Dataset contains missing target labels.")
    if len({_row_signature(row) for row in rows}) != len(rows):
        raise DatasetProfileError("Dataset contains duplicate rows.")

    leakage_columns = tuple(
        column
        for column in rows[0]
        if column != target_column and target_column.lower() in column.lower()
    )
    if leakage_columns:
        raise DatasetProfileError(f"Dataset contains target leakage columns: {leakage_columns}.")

    identifier_columns = tuple(
        column
        for column in rows[0]
        if column != target_column
        and column not in excluded_identifier_columns
        and column.lower().endswith("id")
    )
    if identifier_columns:
        raise DatasetProfileError(
            f"Dataset contains identifier-only columns: {identifier_columns}."
        )

    return DatasetProfileResult(
        modeling_ready=True,
        row_count=len(rows),
        identifier_only_columns=identifier_columns,
        limitations=("Small local validation sample", "Full profiling must run before modeling."),
    )


def _row_signature(row: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in row.items()))


def _validate_required_columns(rows: list[dict[str, Any]], *, target_column: str) -> None:
    columns = set(rows[0])
    if target_column not in columns:
        raise DatasetProfileError(f"Dataset is missing required target column: {target_column}.")
    if any(set(row) != columns for row in rows):
        raise DatasetProfileError("Dataset rows must share an equivalent schema.")

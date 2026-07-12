from dataclasses import dataclass
from typing import Any, Self

LEAKAGE_COLUMNS: frozenset[str] = frozenset({"Post_Semester_GPA", "Skill_Retention_Score"})


class FeatureSchemaError(ValueError):
    """Raised when rows cannot produce a safe modeling feature schema."""


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    semantic_role: str


@dataclass(frozen=True)
class FeatureDictionary:
    customer_key: str
    target_column: str
    features: tuple[FeatureDefinition, ...]

    @classmethod
    def from_rows(
        cls,
        rows: list[dict[str, Any]],
        *,
        customer_key: str,
        target_column: str,
        excluded_feature_columns: frozenset[str] = LEAKAGE_COLUMNS,
    ) -> Self:
        if not rows:
            raise FeatureSchemaError("Feature dictionary requires at least one row.")

        columns = set(rows[0])
        if customer_key not in columns:
            raise FeatureSchemaError(f"Dataset is missing customer key column: {customer_key}.")
        if target_column not in columns:
            raise FeatureSchemaError(f"Dataset is missing target column: {target_column}.")

        for row in rows:
            if set(row) != columns:
                raise FeatureSchemaError("Dataset rows must share an equivalent schema.")

        feature_names = tuple(
            column
            for column in rows[0]
            if column not in {customer_key, target_column} | excluded_feature_columns
        )
        if not feature_names:
            raise FeatureSchemaError("Dataset must include at least one model feature.")

        return cls(
            customer_key=customer_key,
            target_column=target_column,
            features=tuple(
                FeatureDefinition(
                    name=feature_name,
                    semantic_role=_infer_semantic_role(rows, feature_name),
                )
                for feature_name in feature_names
            ),
        )


def _infer_semantic_role(rows: list[dict[str, Any]], column: str) -> str:
    values = [row[column] for row in rows if row[column] not in {None, ""}]
    if values and all(
        isinstance(value, int | float) and not isinstance(value, bool) for value in values
    ):
        return "numeric"
    return "categorical"

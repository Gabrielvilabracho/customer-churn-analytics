from dataclasses import dataclass
from math import exp, log
from typing import Any, cast


@dataclass(frozen=True)
class SklearnLogisticRegressionTrainer:
    model_name: str
    feature_columns: tuple[str, ...]
    random_state: int = 42

    def train(self, rows: list[dict[str, Any]], *, target_column: str) -> "SklearnProbabilityModel":
        if len(rows) < 2:
            raise ValueError("At least two rows are required to train a candidate model.")
        labels = tuple(_label_to_int(row[target_column]) for row in rows)
        if len(set(labels)) < 2:
            raise ValueError("Candidate training requires both churn and non-churn examples.")

        sklearn_model = _fit_sklearn_model(
            rows,
            labels=labels,
            feature_columns=self.feature_columns,
            random_state=self.random_state,
        )
        if sklearn_model is not None:
            return SklearnProbabilityModel(
                model_name=self.model_name,
                feature_columns=self.feature_columns,
                estimator=sklearn_model,
            )

        return SklearnProbabilityModel(
            model_name=self.model_name,
            feature_columns=self.feature_columns,
            estimator=_fit_fallback_model(
                rows, labels=labels, feature_columns=self.feature_columns
            ),
        )


@dataclass(frozen=True)
class SklearnProbabilityModel:
    model_name: str
    feature_columns: tuple[str, ...]
    estimator: Any

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        if hasattr(self.estimator, "predict_proba"):
            frame = _build_pandas_frame(rows, self.feature_columns)
            probabilities = self.estimator.predict_proba(frame)[:, 1]
            return cast(
                tuple[float, ...], tuple(float(probability) for probability in probabilities)
            )
        return cast(tuple[float, ...], self.estimator.predict_probabilities(rows))


@dataclass(frozen=True)
class _FallbackModel:
    feature_columns: tuple[str, ...]
    numeric_weights: dict[str, tuple[float, float, float]]
    categorical_weights: dict[str, dict[str, float]]
    bias: float

    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        probabilities: list[float] = []
        for row in rows:
            score = self.bias
            for column, (weight, midpoint, scale) in self.numeric_weights.items():
                score += weight * ((_to_float(row[column]) - midpoint) / scale)
            for column, weights in self.categorical_weights.items():
                score += weights.get(str(row[column]), 0.0)
            probabilities.append(_sigmoid(score))
        return tuple(probabilities)


def _fit_sklearn_model(
    rows: list[dict[str, Any]],
    *,
    labels: tuple[int, ...],
    feature_columns: tuple[str, ...],
    random_state: int,
) -> Any | None:
    try:
        from sklearn.compose import ColumnTransformer  # type: ignore[import-untyped]
        from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
        from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
        from sklearn.preprocessing import (  # type: ignore[import-untyped]
            OneHotEncoder,
            StandardScaler,
        )
    except ModuleNotFoundError:
        return None

    try:
        frame = _build_pandas_frame(rows, feature_columns)
    except RuntimeError:
        return None
    numeric_columns = [column for column in feature_columns if _is_numeric_column(rows, column)]
    categorical_columns = [column for column in feature_columns if column not in numeric_columns]
    transformer = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), numeric_columns),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocess", transformer),
            (
                "classifier",
                LogisticRegression(random_state=random_state, class_weight="balanced"),
            ),
        ]
    )
    model.fit(frame, labels)
    return model


def _fit_fallback_model(
    rows: list[dict[str, Any]],
    *,
    labels: tuple[int, ...],
    feature_columns: tuple[str, ...],
) -> _FallbackModel:
    positive_count = sum(labels)
    prior = positive_count / len(labels)
    numeric_weights: dict[str, tuple[float, float, float]] = {}
    categorical_weights: dict[str, dict[str, float]] = {}
    for column in feature_columns:
        if _is_numeric_column(rows, column):
            positive_values = [
                _to_float(row[column]) for row, label in zip(rows, labels, strict=True) if label
            ]
            negative_values = [
                _to_float(row[column]) for row, label in zip(rows, labels, strict=True) if not label
            ]
            all_values = positive_values + negative_values
            scale = max(all_values) - min(all_values) or 1.0
            midpoint = (
                sum(positive_values) / len(positive_values)
                + sum(negative_values) / len(negative_values)
            ) / 2
            weight = (
                sum(positive_values) / len(positive_values)
                - sum(negative_values) / len(negative_values)
            ) / scale
            numeric_weights[column] = (weight * 4, midpoint, scale)
        else:
            categorical_weights[column] = _categorical_churn_lift(rows, labels, column, prior)
    return _FallbackModel(
        feature_columns=feature_columns,
        numeric_weights=numeric_weights,
        categorical_weights=categorical_weights,
        bias=_logit(prior),
    )


def _build_pandas_frame(rows: list[dict[str, Any]], feature_columns: tuple[str, ...]) -> Any:
    try:
        import pandas as pd  # type: ignore[import-untyped]
    except ModuleNotFoundError as error:
        raise RuntimeError("pandas is required for sklearn model prediction") from error
    return pd.DataFrame([{column: row[column] for column in feature_columns} for row in rows])


def _categorical_churn_lift(
    rows: list[dict[str, Any]], labels: tuple[int, ...], column: str, prior: float
) -> dict[str, float]:
    grouped: dict[str, list[int]] = {}
    for row, label in zip(rows, labels, strict=True):
        grouped.setdefault(str(row[column]), []).append(label)
    return {value: ((sum(group) / len(group)) - prior) * 3 for value, group in grouped.items()}


def _is_numeric_column(rows: list[dict[str, Any]], column: str) -> bool:
    try:
        for row in rows:
            _to_float(row[column])
    except (TypeError, ValueError):
        return False
    return True


def _to_float(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("Boolean values are not numeric features.")
    return float(value)


def _label_to_int(value: Any) -> int:
    return 1 if value in {1, "1", "Yes", "yes"} else 0


def _sigmoid(value: float) -> float:
    return 1 / (1 + exp(-value))


def _logit(value: float) -> float:
    bounded = min(max(value, 0.001), 0.999)
    return log(bounded / (1 - bounded))

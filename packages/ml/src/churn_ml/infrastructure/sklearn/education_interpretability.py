"""Exact independent linear SHAP and held-out education model inspection.

For this additive model, phi_j = beta_j * (z_j - E_train[z_j]). These
are interventional SHAP values in log-odds, not probability differences.
Correlated-feature credit sharing is deliberately not claimed.
"""

from typing import Any

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn_ml.domain.model import label_to_int
from churn_ml.infrastructure.sklearn.candidate import SklearnProbabilityModel, _build_pandas_frame
from churn_ml.infrastructure.sklearn.education_statistics import associations, cohorts


def _sample_positions(labels: Any, limit: int, seed: int) -> Any:
    if limit >= len(labels):
        return np.arange(len(labels))
    rng = np.random.default_rng(seed)
    positive = np.flatnonzero(labels == 1)
    negative = np.flatnonzero(labels == 0)
    n_positive = min(len(positive), max(1, round(limit * len(positive) / len(labels))))
    n_positive = max(n_positive, limit - len(negative))
    n_positive = min(n_positive, limit - 1)
    selected = np.concatenate(
        (
            rng.choice(positive, n_positive, replace=False),
            rng.choice(negative, limit - n_positive, replace=False),
        )
    )
    return np.sort(selected)


def _frame(rows: list[dict[str, Any]], features: tuple[str, ...], numeric: list[str]) -> Any:
    if not rows or any(
        row.get("Burnout_Risk_Level") not in {"High", "Medium", "Low"} for row in rows
    ):
        raise ValueError("Education target must contain only High, Medium or Low labels")
    frame = _build_pandas_frame(rows, features)
    for feature in frame:
        if feature in numeric:
            frame[feature] = pd.to_numeric(frame[feature], errors="raise")
            if not np.isfinite(frame[feature].to_numpy(dtype=float)).all():
                raise ValueError("Numeric features must be finite")
        elif frame[feature].isna().any() or frame[feature].astype(str).str.strip().eq("").any():
            raise ValueError("Categorical features must not be missing")
    return frame


def _coefficients(preprocess: Any, classifier: Any) -> tuple[list[dict[str, Any]], list[str]]:
    beta = classifier.coef_[0]
    names = preprocess.get_feature_names_out()
    rows = []
    owners = []
    for name, transformer, columns in preprocess.transformers_:
        if name == "remainder":
            continue
        offset = preprocess.output_indices_[name].start
        if isinstance(transformer, StandardScaler):
            for index, feature in enumerate(columns):
                value = float(beta[offset + index])
                rows.append(
                    {
                        "feature": feature,
                        "term": str(names[offset + index]),
                        "category": None,
                        "coefficient": value,
                        "term_coefficient": value,
                        "original_unit_coefficient": value / float(transformer.scale_[index]),
                        "unit": "per training standard deviation",
                        "reference": None,
                    }
                )
                owners.append(feature)
        elif isinstance(transformer, OneHotEncoder) and transformer.drop is None:
            for feature, categories in zip(columns, transformer.categories_, strict=True):
                reference_beta = float(beta[offset])
                for category in categories:
                    term_beta = float(beta[offset])
                    rows.append(
                        {
                            "feature": feature,
                            "term": str(names[offset]),
                            "category": str(category),
                            "coefficient": term_beta - reference_beta,
                            "term_coefficient": term_beta,
                            "original_unit_coefficient": None,
                            "unit": "category contrast",
                            "reference": str(categories[0]),
                        }
                    )
                    owners.append(feature)
                    offset += 1
        else:
            raise ValueError("Unsupported logistic preprocessing; expected scaler and full one-hot")
    if len(owners) != len(beta) or not np.isfinite(beta).all():
        raise ValueError("Incompatible logistic coefficient schema")
    for row in rows:
        value = row["coefficient"]
        row["direction"] = "positive" if value > 0 else "negative" if value < 0 else "neutral"
        ratio = float(np.exp(value))
        if not np.isfinite(ratio):
            raise ValueError("Nonfinite odds ratio")
        row["odds_ratio"] = ratio
    return rows, owners


def analyze_education_model(
    model: Any,
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    threshold: float,
    seed: int = 42,
    shap_samples: int = 256,
    permutation_samples: int = 2000,
    min_cohort_size: int = 20,
) -> dict[str, Any]:
    """Inspect, never refit, a supported education estimator on disjoint splits."""
    if not isinstance(model, SklearnProbabilityModel) or not isinstance(model.estimator, Pipeline):
        raise ValueError("Analysis requires a fitted education logistic pipeline")
    pipeline = model.estimator
    preprocess = pipeline.named_steps.get("preprocess")
    classifier = pipeline.named_steps.get("classifier")
    if (
        not isinstance(preprocess, ColumnTransformer)
        or not isinstance(classifier, LogisticRegression)
        or list(classifier.classes_) != [0, 1]
        or list(pipeline.named_steps) != ["preprocess", "classifier"]
    ):
        raise ValueError("Unsupported logistic pipeline")
    if not 0 < threshold < 1 or min(shap_samples, permutation_samples) < 2 or min_cohort_size < 2:
        raise ValueError("Invalid threshold, sample limits or minimum cohort size")
    train_ids = [row.get("Student_ID") for row in train_rows]
    test_ids = [row.get("Student_ID") for row in test_rows]
    if (
        None in train_ids
        or None in test_ids
        or len(set(train_ids)) != len(train_ids)
        or len(set(test_ids)) != len(test_ids)
        or set(train_ids) & set(test_ids)
    ):
        raise ValueError("Student identifiers must be unique and not overlap across splits")
    numeric = list(preprocess.transformers_[0][2])
    features = model.feature_columns
    if set(features) & {
        "Student_ID",
        "Burnout_Risk_Level",
        "Post_Semester_GPA",
        "Skill_Retention_Score",
    }:
        raise ValueError("Unsafe education feature schema")
    train = _frame(train_rows, features, numeric)
    test = _frame(test_rows, features, numeric)
    train_y = np.array([label_to_int(r["Burnout_Risk_Level"]) for r in train_rows])
    test_y = np.array([label_to_int(r["Burnout_Risk_Level"]) for r in test_rows])
    if len(set(train_y)) != 2 or len(set(test_y)) != 2:
        raise ValueError("Both binary target classes are required in each split")
    coefficient_rows, owners = _coefficients(preprocess, classifier)
    background = preprocess.transform(train)
    background_mean = np.asarray(background.mean(axis=0)).ravel()
    positions = _sample_positions(test_y, shap_samples, seed)
    explained = test.iloc[positions]
    transformed = preprocess.transform(explained)
    z = transformed.toarray() if hasattr(transformed, "toarray") else np.asarray(transformed)
    contributions = (z - background_mean) * classifier.coef_[0]
    base = float(classifier.intercept_[0] + background_mean @ classifier.coef_[0])
    grouped = np.column_stack(
        [contributions[:, np.array(owners) == feature].sum(axis=1) for feature in features]
    )
    output = pipeline.decision_function(explained)
    probabilities = pipeline.predict_proba(test)[:, 1]
    if not (
        np.allclose(base + grouped.sum(axis=1), output, atol=1e-10)
        and np.allclose(expit(output), probabilities[positions], atol=1e-10)
    ):
        raise ValueError("SHAP additivity or probability parity failed")
    permutation_positions = _sample_positions(test_y, permutation_samples, seed)
    evaluation = test.iloc[permutation_positions].copy()
    labels = test_y[permutation_positions]
    baseline = float(average_precision_score(labels, pipeline.predict_proba(evaluation)[:, 1]))
    rng = np.random.default_rng(seed)
    importance = []
    for index, feature in enumerate(features):
        drops = []
        for _ in range(5):
            shuffled = evaluation.copy()
            shuffled[feature] = rng.permutation(shuffled[feature].to_numpy())
            score = average_precision_score(labels, pipeline.predict_proba(shuffled)[:, 1])
            drops.append(baseline - float(score))
        importance.append(
            {
                "feature": feature,
                "mean_abs_shap": float(np.abs(grouped[:, index]).mean()),
                "permutation_mean": float(np.mean(drops)),
                "permutation_std": float(np.std(drops)),
            }
        )
    samples = [
        {
            "sample_id": f"sample-{i + 1:04d}",
            "base_value": base,
            "output_value": float(output[i]),
            "predicted_probability": float(probabilities[position]),
            "contributions": [
                {
                    "feature": feature,
                    "value": str(explained.iloc[i][feature]),
                    "shap_value": float(grouped[i, index]),
                }
                for index, feature in enumerate(features)
            ],
        }
        for i, position in enumerate(positions)
    ]
    return {
        "summary": {
            "train_count": len(train),
            "test_count": len(test),
            "threshold": threshold,
            "observed_high_rate": float(test_y.mean()),
            "average_predicted_risk": float(probabilities.mean()),
            "minimum_cohort_size": min_cohort_size,
        },
        "coefficients": coefficient_rows,
        "importance": importance,
        "associations": associations(train, test, train_y, test_y, numeric),
        "cohorts": cohorts(
            train,
            test,
            test_y,
            probabilities,
            numeric=numeric,
            threshold=threshold,
            minimum=min_cohort_size,
        ),
        "shap": {
            "method": "exact_independent_linear",
            "units": "log_odds",
            "background_count": len(train),
            "sample_count": len(samples),
            "samples": samples,
        },
        "methodology": {
            "seed": seed,
            "permutation_count": len(evaluation),
            "permutation_repeats": 5,
            "permutation_metric": "average_precision",
            "cohort_bins": "training quartiles for numeric variables",
            "positive_label": "High",
            "negative_labels": ["Low", "Medium"],
        },
        "warnings": [
            "Associations and model contributions are not causal effects or clinical diagnoses.",
            "Class-balanced logistic probabilities are not necessarily calibrated "
            "population risks.",
            "Independent SHAP ignores feature dependence; correlated predictors can share credit.",
            "Categorical effects contrast with the named reference, not an omitted category.",
            "Original training-split provenance is not authenticated by the legacy publication.",
        ],
        "decision_support_only": True,
        "qualified_human_review_required": True,
    }

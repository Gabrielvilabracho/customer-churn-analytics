import json
from typing import Any

import numpy as np
import pytest
from churn_ml.infrastructure.sklearn.candidate import SklearnLogisticRegressionTrainer
from churn_ml.infrastructure.sklearn.education_interpretability import analyze_education_model


def education_rows(start: int = 0) -> list[dict[str, Any]]:
    return [
        {
            "Student_ID": str(start + i),
            "Weekly_GenAI_Hours": str(i % 20),
            "Major_Category": "Arts" if i % 2 else "Engineering",
            "Burnout_Risk_Level": "High" if i % 20 >= 10 else "Low",
        }
        for i in range(80)
    ]


@pytest.fixture
def education_model() -> Any:
    return SklearnLogisticRegressionTrainer(
        model_name="education-test",
        feature_columns=("Weekly_GenAI_Hours", "Major_Category"),
    ).train(education_rows(), target_column="Burnout_Risk_Level")


def test_analysis_explains_fitted_coefficients_and_grouped_shap(education_model: Any) -> None:
    result = analyze_education_model(
        education_model,
        education_rows(),
        education_rows(1000),
        threshold=0.3,
        seed=7,
        shap_samples=24,
        permutation_samples=60,
        min_cohort_size=5,
    )
    numeric = next(c for c in result["coefficients"] if c["feature"] == "Weekly_GenAI_Hours")
    assert numeric["coefficient"] > 0
    assert numeric["direction"] == "positive"
    assert numeric["odds_ratio"] == pytest.approx(np.exp(numeric["coefficient"]))
    assert numeric["unit"] == "per training standard deviation"
    categorical = [c for c in result["coefficients"] if c["feature"] == "Major_Category"]
    assert len(categorical) == 2
    assert categorical[0]["reference"] == categorical[1]["reference"]
    assert result["shap"]["units"] == "log_odds"
    assert result["shap"]["background_count"] == 80
    assert len(result["shap"]["samples"]) == 24
    for sample in result["shap"]["samples"]:
        logit = sample["base_value"] + sum(c["shap_value"] for c in sample["contributions"])
        assert logit == pytest.approx(sample["output_value"], abs=1e-10)
        assert 1 / (1 + np.exp(-logit)) == pytest.approx(sample["predicted_probability"])
        assert {c["feature"] for c in sample["contributions"]} == {
            "Weekly_GenAI_Hours",
            "Major_Category",
        }
    for feature in result["importance"]:
        values = [
            next(c["shap_value"] for c in s["contributions"] if c["feature"] == feature["feature"])
            for s in result["shap"]["samples"]
        ]
        assert feature["mean_abs_shap"] == pytest.approx(np.mean(np.abs(values)))
    assert "Student_ID" not in json.dumps(result)


def test_analysis_reports_associations_cohorts_and_deterministic_importance(
    education_model: Any,
) -> None:
    kwargs = {"threshold": 0.3, "shap_samples": 10, "permutation_samples": 40}
    result = analyze_education_model(
        education_model, education_rows(), education_rows(1000), **kwargs
    )
    assert result == analyze_education_model(
        education_model,
        education_rows(),
        education_rows(1000),
        **kwargs,
    )
    association = next(a for a in result["associations"] if a["feature"] == "Weekly_GenAI_Hours")
    assert association["train"]["point_biserial"] > 0.8
    assert association["test"]["spearman"] > 0.8
    category = next(a for a in result["associations"] if a["feature"] == "Major_Category")
    assert category["test"]["cramers_v"] == pytest.approx(0)
    majors = [c for c in result["cohorts"] if c["feature"] == "Major_Category"]
    assert sum(c["count"] for c in majors) == 80
    assert all(c["observed_high_rate"] == 0.5 for c in majors)
    assert all(c["observed_ci"][0] < 0.5 < c["observed_ci"][1] for c in majors)
    assert all(0 <= c["average_predicted_risk"] <= 1 for c in majors)
    assert result["summary"]["train_count"] == result["summary"]["test_count"] == 80


def test_analysis_suppresses_small_groups_and_marks_constant_associations(
    education_model: Any,
) -> None:
    test = education_rows(1000)
    for row in test:
        row["Weekly_GenAI_Hours"] = "5"
    result = analyze_education_model(
        education_model,
        education_rows(),
        test,
        threshold=0.3,
        min_cohort_size=100,
    )
    assert all(c["suppressed"] and c["observed_high_rate"] is None for c in result["cohorts"])
    numeric = next(a for a in result["associations"] if a["feature"] == "Weekly_GenAI_Hours")
    assert numeric["test"]["point_biserial"] is None
    assert numeric["test"]["spearman"] is None


@pytest.mark.parametrize("invalid", ["Unexpected", "", None])
def test_analysis_rejects_invalid_targets(education_model: Any, invalid: Any) -> None:
    test = education_rows(1000)
    test[0]["Burnout_Risk_Level"] = invalid
    with pytest.raises(ValueError, match="target"):
        analyze_education_model(education_model, education_rows(), test, threshold=0.3)


def test_analysis_rejects_unsupported_models_and_overlapping_students(education_model: Any) -> None:
    with pytest.raises(ValueError, match="logistic"):
        analyze_education_model(object(), education_rows(), education_rows(1000), threshold=0.3)
    with pytest.raises(ValueError, match="overlap"):
        analyze_education_model(education_model, education_rows(), education_rows(), threshold=0.3)

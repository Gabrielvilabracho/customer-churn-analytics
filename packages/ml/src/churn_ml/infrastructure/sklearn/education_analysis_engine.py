"""Adapt the existing statistical implementation to the application analysis port."""

from typing import Any

from churn_ml.application.ports.education_analysis import EducationAnalysisInputs
from churn_ml.infrastructure.sklearn.education_interpretability import analyze_education_model


class SklearnEducationAnalysisEngine:
    def analyze(
        self,
        inputs: EducationAnalysisInputs,
        *,
        seed: int,
        shap_samples: int,
        permutation_samples: int,
        min_cohort_size: int,
    ) -> dict[str, Any]:
        return analyze_education_model(
            inputs.model,
            inputs.train_rows,
            inputs.test_rows,
            threshold=inputs.threshold,
            seed=seed,
            shap_samples=shap_samples,
            permutation_samples=permutation_samples,
            min_cohort_size=min_cohort_size,
        )

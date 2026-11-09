"""Scikit-learn experiment candidate construction and introspection."""

from typing import Any

from churn_ml.application.ports.model_trainer import ModelTrainer, ProbabilityModel
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer
from churn_ml.infrastructure.sklearn.candidate import SklearnLogisticRegressionTrainer


class SklearnExperimentCandidates:
    def trainers(
        self,
        feature_columns: tuple[str, ...],
        *,
        seed: int,
        c_values: tuple[float, ...],
    ) -> tuple[ModelTrainer, ...]:
        return (
            BaselineChurnRateTrainer(),
            *(
                SklearnLogisticRegressionTrainer(
                    f"logistic_C_{c!r}",
                    feature_columns,
                    random_state=seed,
                    regularization=c,
                )
                for c in c_values
            ),
        )

    def assert_supported(self, model: ProbabilityModel) -> None:
        estimator = getattr(model, "estimator", None)
        if estimator is not None and not hasattr(estimator, "named_steps"):
            raise ValueError("Experiments require a real sklearn pipeline, not a fallback")

    def parameters(self, model: ProbabilityModel) -> dict[str, Any]:
        estimator = getattr(model, "estimator", None)
        if estimator is None:
            return {"strategy": "training_prevalence"}
        return dict(estimator.named_steps["classifier"].get_params())

"""Rescore explicitly trusted local source bytes without rewriting publications."""

from dataclasses import asdict
from typing import Any

from churn_ml.application.pipelines.evaluate import evaluate_predictions
from churn_ml.application.pipelines.experiment_reports import diagnostics
from churn_ml.application.ports.education_reevaluation import EducationReevaluationInputLoader
from churn_ml.application.ports.experiment_identity import ExperimentIdentityProvider
from churn_ml.domain.model import label_to_int


def reevaluate_education(
    run_id: str,
    *,
    input_loader: EducationReevaluationInputLoader,
    identity_provider: ExperimentIdentityProvider,
    trusted_model: bool = False,
) -> dict[str, Any]:
    if not trusted_model:
        raise ValueError("Explicitly trusted local model required: deserialization executes code")
    inputs = input_loader.load(run_id)
    rows = inputs.test_rows
    if not rows or any(
        row.get("Burnout_Risk_Level") not in ("Low", "Medium", "High") for row in rows
    ):
        raise ValueError("Invalid education evaluation labels")
    labels = tuple(label_to_int(row["Burnout_Risk_Level"]) for row in rows)
    scores = inputs.model.predict_probabilities(rows)
    threshold = inputs.threshold
    checks = diagnostics(labels, scores, threshold)
    metrics = asdict(
        evaluate_predictions(
            actual_labels=labels, probabilities=scores, threshold=threshold, top_risk_fraction=0.2
        )
    )
    input_loader.assert_unchanged(run_id, inputs.source_hashes)
    return {
        "schema_version": 1,
        "kind": "education_reevaluation",
        "source_run_id": run_id,
        "source_hashes": inputs.source_hashes,
        "code": identity_provider.capture(),
        "protocol": "historical_snapshot_not_independent_test",
        "prediction_precision": "full_model_output",
        "threshold": threshold,
        "top_risk_fraction": 0.2,
        "historical_metrics": inputs.historical_metrics,
        "evaluation": {"split": "historical_test", "metrics": metrics, "diagnostics": checks},
        "metric_delta": {
            key: value - inputs.historical_metrics[key] for key, value in metrics.items()
        },
        "warnings": [
            "Historical test was used for selection; this is not independent final validation.",
            "Current splits are hashed, but the original manifest did not bind their provenance.",
            "Top-risk fraction 0.2 follows the standard CLI default, not a persisted setting.",
            "Class-balanced scores are not established calibrated probabilities.",
        ],
    }

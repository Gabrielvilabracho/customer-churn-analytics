"""Independent selection and final evaluation, separate from legacy publications."""

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from churn_ml.application.pipelines.evaluate import EvaluationError, evaluate_predictions
from churn_ml.application.pipelines.experiment_reports import diagnostics, digest
from churn_ml.application.pipelines.features import (
    build_feature_dictionary,
    stratified_train_test_split,
)
from churn_ml.application.pipelines.profile import screen_dataset_profile
from churn_ml.application.pipelines.train import train_model_candidate
from churn_ml.application.ports.experiment_candidates import ExperimentCandidateProvider
from churn_ml.application.ports.experiment_identity import ExperimentIdentityProvider
from churn_ml.application.ports.model_trainer import ProbabilityModel
from churn_ml.domain.model import label_to_int

TARGET = "Burnout_Risk_Level"
IDENTIFIER = "Student_ID"


@dataclass(frozen=True)
class ExperimentResult:
    report: dict[str, Any]
    model: ProbabilityModel


def run_experiment(
    rows: list[dict[str, Any]],
    *,
    candidate_provider: ExperimentCandidateProvider,
    identity_provider: ExperimentIdentityProvider,
    seed: int = 42,
    c_values: tuple[float, ...] = (0.1, 1.0, 10.0),
    thresholds: tuple[float, ...] = (0.7, 0.5, 0.3),
    min_recall: float = 0.7,
) -> ExperimentResult:
    if not c_values or any(not isfinite(c) or c <= 0 for c in c_values):
        raise ValueError("C values must be finite and positive")
    if not thresholds or any(not isfinite(t) or not 0 <= t <= 1 for t in thresholds):
        raise ValueError("Thresholds must be finite probabilities")
    if not isfinite(min_recall) or not 0 <= min_recall <= 1:
        raise ValueError("Minimum recall must be between zero and one")
    screen_dataset_profile(rows, target_column=TARGET, excluded_identifier_columns=(IDENTIFIER,))
    identifiers = [row.get(IDENTIFIER) for row in rows]
    if any(not value for value in identifiers) or len(set(identifiers)) != len(rows):
        raise ValueError("Student identifiers must be present and unique")
    if any(row[TARGET] not in ("Low", "Medium", "High") for row in rows):
        raise ValueError("Education labels must be Low, Medium or High")
    held_out = stratified_train_test_split(rows, target_column=TARGET, test_fraction=0.2, seed=seed)
    development = stratified_train_test_split(
        held_out.train_rows, target_column=TARGET, test_fraction=0.25, seed=seed
    )
    train, validation, test = development.train_rows, development.test_rows, held_out.test_rows
    for split in (train, validation, test):
        if {label_to_int(row[TARGET]) for row in split} != {0, 1}:
            raise ValueError("Each split must contain both binary outcomes")
    features = tuple(
        feature.name
        for feature in build_feature_dictionary(
            train, customer_key=IDENTIFIER, target_column=TARGET
        ).features
    )
    trainers = candidate_provider.trainers(
        features,
        seed=seed,
        c_values=c_values,
    )
    validation_labels = tuple(label_to_int(row[TARGET]) for row in validation)
    candidates: list[dict[str, Any]] = []
    selected: tuple[tuple[float, ...], ProbabilityModel, float] | None = None
    for trainer in trainers:
        model = train_model_candidate(trainer, train, target_column=TARGET).model
        candidate_provider.assert_supported(model)
        scores = model.predict_probabilities(validation)
        choices: list[dict[str, Any]] = []
        for threshold in sorted(set(thresholds), reverse=True):
            checks = diagnostics(validation_labels, scores, threshold)
            metrics = asdict(
                evaluate_predictions(
                    actual_labels=validation_labels,
                    probabilities=scores,
                    threshold=threshold,
                    top_risk_fraction=0.2,
                )
            )
            choices.append({"threshold": threshold, "metrics": metrics, "diagnostics": checks})
        eligible = [choice for choice in choices if choice["metrics"]["recall"] >= min_recall]
        chosen = eligible[0] if eligible else None
        parameters = candidate_provider.parameters(model)
        candidates.append(
            {
                "model_name": model.model_name,
                "parameters": parameters,
                "thresholds": choices,
                "eligible": chosen is not None,
            }
        )
        if chosen:
            metrics = chosen["metrics"]
            rank = (metrics["pr_auc"], metrics["roc_auc"], metrics["precision"])
            if selected is None or rank > selected[0]:
                selected = rank, model, chosen["threshold"]
    if selected is None:
        raise EvaluationError("No validation candidate satisfies minimum recall")
    _, model, threshold = selected
    # All model/threshold decisions are frozen before any final test prediction.
    labels = tuple(label_to_int(row[TARGET]) for row in test)
    scores = model.predict_probabilities(test)
    final_diagnostics = diagnostics(labels, scores, threshold)
    report = {
        "schema_version": 1,
        "kind": "independent_education_experiment",
        "dataset_id": "ai-student-impact",
        "dataset_sha256": digest(rows),
        "code": identity_provider.capture(),
        "configuration": {
            "seed": seed,
            "c_values": list(c_values),
            "thresholds": list(thresholds),
            "min_recall": min_recall,
            "top_risk_fraction": 0.2,
        },
        "features": list(features),
        "splits": {
            name: {"count": len(split), "sha256": digest(split)}
            for name, split in (("train", train), ("validation", validation), ("test", test))
        },
        "validation_candidates": candidates,
        "selection": {
            "split": "validation",
            "model_name": model.model_name,
            "threshold": threshold,
            "criterion": "AP, ROC-AUC, precision; recall gate",
        },
        "evaluation": {
            "split": "test",
            "metrics": asdict(
                evaluate_predictions(
                    actual_labels=labels,
                    probabilities=scores,
                    threshold=threshold,
                    top_risk_fraction=0.2,
                )
            ),
            "diagnostics": final_diagnostics,
        },
        "warnings": [
            "This dataset has already been explored; this is not new external validation.",
            "Calibration is diagnosed, not fitted. Class balancing may distort probabilities.",
            "No operational false-positive budget has been supplied; no deployment approval.",
            "No diagnosis, causal interpretation or automatic student decision is supported.",
        ],
    }
    return ExperimentResult(report, model)

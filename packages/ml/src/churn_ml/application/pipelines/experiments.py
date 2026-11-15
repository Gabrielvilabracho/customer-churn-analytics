"""Independent selection and final evaluation, separate from legacy publications."""

from dataclasses import asdict, dataclass
from math import isclose, isfinite
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
from churn_ml.domain.artifacts import ClassificationMetricSet
from churn_ml.domain.model import label_to_int

TARGET = "Burnout_Risk_Level"
IDENTIFIER = "Student_ID"


@dataclass(frozen=True)
class ExperimentResult:
    report: dict[str, Any]
    model: ProbabilityModel


@dataclass(frozen=True)
class CandidateValidation:
    model: ProbabilityModel
    family: str
    threshold: float
    metrics: ClassificationMetricSet
    diagnostics: dict[str, Any]


@dataclass(frozen=True)
class ComparableCandidateDecision:
    reference: CandidateValidation
    selected: CandidateValidation
    advanced_gates: tuple[dict[str, Any], ...]


def select_comparable_candidate(
    candidates: tuple[CandidateValidation, ...],
    *,
    min_recall: float = 0.7,
    minimum_average_precision_gain: float = 0.01,
) -> ComparableCandidateDecision:
    logistic_candidates = [
        candidate
        for candidate in candidates
        if candidate.family == "logistic" and candidate.metrics.recall >= min_recall
    ]
    if not logistic_candidates:
        raise EvaluationError("No logistic validation candidate satisfies minimum recall")
    reference = min(
        logistic_candidates,
        key=lambda candidate: (
            -candidate.metrics.pr_auc,
            -candidate.metrics.roc_auc,
            -candidate.metrics.precision,
            candidate.model.model_name,
        ),
    )
    reference_brier = float(reference.diagnostics["brier_score"])
    reference_fpr = float(reference.diagnostics["false_positive_rate"])
    reference_flagged = float(reference.diagnostics["flagged_fraction"])
    evaluated: list[tuple[CandidateValidation, dict[str, Any]]] = []
    for candidate in candidates:
        if candidate.family in {"logistic", "baseline"}:
            continue
        brier_score = float(candidate.diagnostics["brier_score"])
        false_positive_rate = float(candidate.diagnostics["false_positive_rate"])
        flagged_fraction = float(candidate.diagnostics["flagged_fraction"])
        gate = {
            "model_name": candidate.model.model_name,
            "family": candidate.family,
            "recall": candidate.metrics.recall >= min_recall,
            "average_precision": (
                candidate.metrics.pr_auc - reference.metrics.pr_auc
                >= minimum_average_precision_gain
                or isclose(
                    candidate.metrics.pr_auc - reference.metrics.pr_auc,
                    minimum_average_precision_gain,
                    abs_tol=1e-12,
                )
            ),
            "brier_score": brier_score <= reference_brier,
            "false_positive_rate": false_positive_rate <= reference_fpr,
            "flagged_fraction": flagged_fraction <= reference_flagged,
            "deltas": {
                "average_precision": candidate.metrics.pr_auc - reference.metrics.pr_auc,
                "brier_score": brier_score - reference_brier,
                "false_positive_rate": false_positive_rate - reference_fpr,
                "flagged_fraction": flagged_fraction - reference_flagged,
            },
        }
        gate["qualified"] = all(
            gate[name]
            for name in (
                "recall",
                "average_precision",
                "brier_score",
                "false_positive_rate",
                "flagged_fraction",
            )
        )
        evaluated.append((candidate, gate))
    qualified = [candidate for candidate, gate in evaluated if gate["qualified"]]
    selected = (
        min(
            qualified,
            key=lambda candidate: (
                -candidate.metrics.pr_auc,
                float(candidate.diagnostics["brier_score"]),
                float(candidate.diagnostics["false_positive_rate"]),
                float(candidate.diagnostics["flagged_fraction"]),
                candidate.model.model_name,
            ),
        )
        if qualified
        else reference
    )
    return ComparableCandidateDecision(
        reference=reference,
        selected=selected,
        advanced_gates=tuple(gate for _, gate in evaluated),
    )


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
    eligible_validations: list[CandidateValidation] = []
    for trainer in trainers:
        model = train_model_candidate(trainer, train, target_column=TARGET).model
        candidate_provider.assert_supported(model)
        family = candidate_provider.family(model)
        scores = model.predict_probabilities(validation)
        choices: list[dict[str, Any]] = []
        for threshold in sorted(set(thresholds), reverse=True):
            checks = diagnostics(validation_labels, scores, threshold)
            metric_set = evaluate_predictions(
                actual_labels=validation_labels,
                probabilities=scores,
                threshold=threshold,
                top_risk_fraction=0.2,
            )
            choices.append(
                {"threshold": threshold, "metrics": asdict(metric_set), "diagnostics": checks}
            )
        eligible = [choice for choice in choices if choice["metrics"]["recall"] >= min_recall]
        chosen = eligible[0] if eligible else None
        parameters = candidate_provider.parameters(model)
        candidates.append(
            {
                "model_name": model.model_name,
                "family": family,
                "parameters": parameters,
                "thresholds": choices,
                "eligible": chosen is not None,
            }
        )
        if chosen:
            eligible_validations.append(
                CandidateValidation(
                    model=model,
                    family=family,
                    threshold=chosen["threshold"],
                    metrics=ClassificationMetricSet(**chosen["metrics"]),
                    diagnostics=chosen["diagnostics"],
                )
            )
    decision = select_comparable_candidate(tuple(eligible_validations), min_recall=min_recall)
    model = decision.selected.model
    threshold = decision.selected.threshold
    # All model/threshold decisions are frozen before any final test prediction.
    labels = tuple(label_to_int(row[TARGET]) for row in test)
    scores = model.predict_probabilities(test)
    final_diagnostics = diagnostics(labels, scores, threshold)
    report = {
        "schema_version": 2,
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
            "reference_model_name": decision.reference.model.model_name,
            "model_name": model.model_name,
            "threshold": threshold,
            "criterion": "advanced AP gain and non-regression guardrails; logistic fallback",
            "advanced_gates": list(decision.advanced_gates),
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

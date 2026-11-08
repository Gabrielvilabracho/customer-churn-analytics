"""Closed public shape for an already validated education publication.

The offline format can retain extra local fields. HTTP serving must not forward
those fields, including nested extensions containing identifiers or raw records.
Reject extensions instead of silently changing the selected publication.
"""

from typing import Any


def _record(value: Any, fields: str, *, nested: str = "") -> None:
    if not isinstance(value, dict) or set(value) != set(fields.split()):
        raise ValueError("Unexpected education response fields")
    containers = set(nested.split())
    if any(
        isinstance(child, dict | list) and key not in containers for key, child in value.items()
    ):
        raise ValueError("Unexpected nested education response fields")


def validate_public_education_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    """Retain the complete declared payload, never an arbitrary local extension."""
    _record(
        payload,
        "schema_version run_id analysis_id dataset_id model_name created_at_utc "
        "source_hashes model_metrics versions summary coefficients importance "
        "associations cohorts shap methodology warnings decision_support_only "
        "qualified_human_review_required",
        nested="source_hashes model_metrics versions summary coefficients importance "
        "associations cohorts shap methodology warnings",
    )
    _record(
        payload["summary"],
        "train_count test_count threshold observed_high_rate average_predicted_risk "
        "minimum_cohort_size",
    )
    for coefficient in payload["coefficients"]:
        _record(
            coefficient,
            "feature term category coefficient term_coefficient original_unit_coefficient "
            "unit reference direction odds_ratio",
        )
    for importance in payload["importance"]:
        _record(importance, "feature mean_abs_shap permutation_mean permutation_std")
    for association in payload["associations"]:
        _record(association, "feature kind train test", nested="train test")
        measures = "point_biserial spearman" if association["kind"] == "numeric" else "cramers_v"
        for split in ("train", "test"):
            _record(association[split], f"count missing_count {measures}")
    for cohort in payload["cohorts"]:
        _record(
            cohort,
            "feature group count suppressed observed_high_rate observed_ci "
            "average_predicted_risk difference_from_overall precision recall",
            nested="observed_ci",
        )
    shap = payload["shap"]
    _record(shap, "method units background_count sample_count samples", nested="samples")
    for sample in shap["samples"]:
        _record(
            sample,
            "sample_id base_value output_value predicted_probability contributions",
            nested="contributions",
        )
        for contribution in sample["contributions"]:
            _record(contribution, "feature value shap_value")
    _record(
        payload["methodology"],
        "seed permutation_count permutation_repeats permutation_metric cohort_bins "
        "positive_label negative_labels",
        nested="negative_labels",
    )
    if any(not isinstance(label, str) for label in payload["methodology"]["negative_labels"]):
        raise ValueError("Invalid education response labels")
    # These maps have dynamic keys but only scalar values in the public contract.
    for name in ("source_hashes", "model_metrics", "versions"):
        if not isinstance(payload[name], dict) or any(
            isinstance(value, dict | list) for value in payload[name].values()
        ):
            raise ValueError("Unexpected nested education metadata")
    return payload

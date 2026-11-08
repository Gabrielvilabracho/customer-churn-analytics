"""Framework-independent validation of the public education analysis contract."""

import math
import re
from typing import Any


def _number(value: Any, low: float = -math.inf, high: float = math.inf) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or not low <= value <= high
    ):
        raise ValueError("Analysis numbers must be finite and within the declared range")
    return float(value)


def _count(value: Any, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError("Invalid analysis count")
    return value


def validate_identity(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", value):
        raise ValueError("Invalid analysis/run identity")
    return value


def validate_analysis(payload: Any) -> dict[str, Any]:
    def inspect(value: Any) -> None:
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("Analysis numbers must be finite")
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "Student_ID":
                    raise ValueError("Student identifiers are not public analysis fields")
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    inspect(payload)
    try:
        if payload["schema_version"] != 1:
            raise ValueError("Unsupported analysis schema")
        validate_identity(payload["run_id"])
        validate_identity(payload["analysis_id"])
        if (
            payload["decision_support_only"] is not True
            or payload["qualified_human_review_required"] is not True
        ):
            raise ValueError("Missing education decision-support safeguards")
        required = {"coefficients", "importance", "associations", "cohorts"}
        if any(not isinstance(payload[key], list) or not payload[key] for key in required):
            raise ValueError("Incomplete education analysis")
        features = {item["feature"] for item in payload["importance"]}
        if (
            not features
            or len(features) != len(payload["importance"])
            or features & {"Student_ID", "Burnout_Risk_Level"}
        ):
            raise ValueError("Invalid analysis feature schema")
        for key in required:
            if any(item["feature"] not in features for item in payload[key]):
                raise ValueError("Inconsistent analysis feature schema")
        summary = payload["summary"]
        for key in ("train_count", "test_count", "minimum_cohort_size"):
            _count(summary[key], 2)
        for key in ("threshold", "observed_high_rate", "average_predicted_risk"):
            _number(summary[key], 0, 1)
        if (
            not 0 < summary["threshold"] < 1
            or min(summary["train_count"], summary["test_count"]) < 2
        ):
            raise ValueError("Invalid analysis summary")
        shap = payload["shap"]
        if shap["units"] != "log_odds" or shap["method"] != "exact_independent_linear":
            raise ValueError("Unsupported SHAP semantics")
        if len(shap["samples"]) != shap["sample_count"] or not shap["samples"]:
            raise ValueError("Missing SHAP samples")
        if (
            shap["background_count"] != summary["train_count"]
            or not 2 <= _count(shap["sample_count"]) <= summary["test_count"]
        ):
            raise ValueError("Invalid SHAP sampling metadata")
        for sample in shap["samples"]:
            values = sample["contributions"]
            for key in ("base_value", "output_value", "predicted_probability"):
                _number(sample[key])
            for value in values:
                _number(value["shap_value"])
                if not isinstance(value["value"], str):
                    raise ValueError("Invalid SHAP feature value")
            if (
                not re.fullmatch(r"sample-\d{4,}", sample["sample_id"])
                or {v["feature"] for v in values} != features
                or len(values) != len(features)
                or not 0 <= sample["predicted_probability"] <= 1
                or not math.isclose(
                    sample["base_value"] + sum(v["shap_value"] for v in values),
                    sample["output_value"],
                    abs_tol=1e-8,
                )
            ):
                raise ValueError("Invalid SHAP explanation")
            logit = sample["output_value"]
            probability = (
                1 / (1 + math.exp(-logit))
                if logit >= 0
                else math.exp(logit) / (1 + math.exp(logit))
            )
            if not math.isclose(probability, sample["predicted_probability"], abs_tol=1e-8):
                raise ValueError("Invalid SHAP probability parity")
        for item in payload["coefficients"]:
            coefficient = _number(item["coefficient"])
            _number(item["term_coefficient"])
            _number(item["odds_ratio"], 0)
            if item["original_unit_coefficient"] is not None:
                _number(item["original_unit_coefficient"])
            if item["direction"] not in {"positive", "negative", "neutral"}:
                raise ValueError("Invalid coefficient direction")
            if item["odds_ratio"] <= 0 or not item["unit"]:
                raise ValueError("Invalid coefficient units")
            expected_direction = (
                "positive" if coefficient > 0 else "negative" if coefficient < 0 else "neutral"
            )
            if item["direction"] != expected_direction:
                raise ValueError("Coefficient sign and direction disagree")
            if not math.isclose(math.log(item["odds_ratio"]), coefficient, abs_tol=1e-8):
                raise ValueError("Invalid coefficient odds ratio")
        for item in payload["importance"]:
            _number(item["mean_abs_shap"], 0)
            _number(item["permutation_std"], 0)
            _number(item["permutation_mean"])
        for item in payload["associations"]:
            if item["kind"] not in {"numeric", "categorical"}:
                raise ValueError("Invalid association kind")
            keys = ("point_biserial", "spearman") if item["kind"] == "numeric" else ("cramers_v",)
            for split in ("train", "test"):
                measures = item[split]
                if _count(measures["count"]) != summary[f"{split}_count"]:
                    raise ValueError("Association count mismatch")
                _count(measures["missing_count"])
                for key in keys:
                    if measures[key] is not None:
                        _number(measures[key], 0 if key == "cramers_v" else -1, 1)
        cohort_fields = ("observed_high_rate", "average_predicted_risk", "precision", "recall")
        for item in payload["cohorts"]:
            count = _count(item["count"], 1)
            if item["suppressed"] is not (count < summary["minimum_cohort_size"]):
                raise ValueError("Cohort suppression does not match its size")
            for key in (*cohort_fields, "difference_from_overall", "observed_ci"):
                if item["suppressed"] and item[key] is not None:
                    raise ValueError("Small-cohort statistics must be suppressed")
            for key in cohort_fields:
                if item[key] is not None:
                    _number(item[key], 0, 1)
            if item["difference_from_overall"] is not None:
                _number(item["difference_from_overall"], -1, 1)
            if item["observed_ci"] is not None:
                low, high = item["observed_ci"]
                _number(low, 0, 1)
                _number(high, low, 1)
        for feature in features:
            if (
                sum(c["count"] for c in payload["cohorts"] if c["feature"] == feature)
                != summary["test_count"]
            ):
                raise ValueError("Cohort totals do not match held-out count")
        for metric in payload["model_metrics"].values():
            _number(metric, 0, 1)
        if not isinstance(payload["source_hashes"], dict) or not payload["source_hashes"]:
            raise ValueError("Missing source binding")
        if any(
            not re.fullmatch(r"[a-f0-9]{64}", value) for value in payload["source_hashes"].values()
        ):
            raise ValueError("Invalid source checksum")
        if (
            not isinstance(payload["warnings"], list)
            or not payload["warnings"]
            or any(not isinstance(item, str) or not item.strip() for item in payload["warnings"])
            or payload["methodology"]["positive_label"] != "High"
        ):
            raise ValueError("Missing methodology")
        return dict(payload)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError("Malformed education analysis contract") from exc

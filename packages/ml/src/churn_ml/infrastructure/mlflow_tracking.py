"""Opt-in local MLflow. Explicit clients never inherit remote tracking settings."""

import hashlib
import json
import math
import re
import tempfile
from pathlib import Path
from typing import Any, cast
from urllib.parse import unquote, urlparse

from churn_ml.infrastructure.filesystem.experiment_reports import read_report


class LocalMlflowTracker:
    def __init__(self, directory: Path | str) -> None:
        if "://" in str(directory):
            raise ValueError("MLflow requires a local directory, not a server URI")
        self.root = Path(directory).resolve()
        self.uri = f"sqlite:///{self.root / 'tracking.db'}"

    def log(self, directory: Path) -> str:
        # Reading verifies report/model checksums without deserializing anything.
        report = read_report(directory)
        if report.get("kind") != "independent_education_experiment":
            raise ValueError("Only aggregate experiment reports can be tracked")
        _validate_tracking_fields(report)
        model_path = _validate_tracking_members(directory)
        tracking_report = _tracking_payload(report)
        artifact_root = self.root / "artifacts"
        for path in (self.root / "tracking.db", artifact_root):
            if path.resolve() != path:
                raise ValueError("Local tracking symlinks are forbidden")
        from mlflow import MlflowClient

        self.root.mkdir(parents=True, exist_ok=True)
        client = MlflowClient(tracking_uri=self.uri, registry_uri=self.uri)
        experiment = client.get_experiment_by_name("education-experiments")
        if experiment is None:
            identifier = client.create_experiment(
                "education-experiments", artifact_location=artifact_root.as_uri()
            )
        else:
            if not _local_artifact_path(experiment.artifact_location, artifact_root):
                raise ValueError("Existing experiment does not use the selected local root")
            identifier = experiment.experiment_id
        run = client.create_run(identifier)
        run_id: str = run.info.run_id
        try:
            if not _local_artifact_path(run.info.artifact_uri, artifact_root, descendant=True):
                raise ValueError("Run artifact destination is not local to the selected directory")
            selected = next(
                candidate
                for candidate in report["validation_candidates"]
                if candidate["model_name"] == report["selection"]["model_name"]
            )
            params = {
                "dataset_sha256": report["dataset_sha256"],
                "source_sha256": report["code"]["source_sha256"],
                "git_head": report["code"]["git_head"],
                "selected_model": report["selection"]["model_name"],
                "selected_threshold": report["selection"]["threshold"],
                **report["configuration"],
                **{f"model.{key}": value for key, value in selected["parameters"].items()},
            }
            for key, value in params.items():
                encoded = json.dumps(value) if isinstance(value, list) else value
                client.log_param(run_id, key, encoded)
            for key, value in report["evaluation"]["metrics"].items():
                client.log_metric(run_id, f"test.{key}", value)
            validation = next(
                choice
                for choice in selected["thresholds"]
                if choice["threshold"] == report["selection"]["threshold"]
            )
            for key, value in validation["metrics"].items():
                client.log_metric(run_id, f"validation.{key}", value)
            for key in ("brier_score", "log_loss", "false_positive_rate", "flagged_count"):
                value = report["evaluation"]["diagnostics"][key]
                if value is not None:
                    client.log_metric(run_id, f"test.{key}", value)
            report_bytes = json.dumps(
                tracking_report, sort_keys=True, indent=2, allow_nan=False
            ).encode()
            completion = {
                "schema_version": 1,
                "members": {
                    "report.json": hashlib.sha256(report_bytes).hexdigest(),
                    "model.joblib": hashlib.sha256(model_path.read_bytes()).hexdigest(),
                },
            }
            with tempfile.TemporaryDirectory(prefix=".tracking-", dir=self.root) as temp_name:
                temp = Path(temp_name)
                (temp / "report.json").write_bytes(report_bytes)
                (temp / "completion.json").write_text(
                    json.dumps(completion, sort_keys=True), encoding="utf-8"
                )
                for path in (temp / "report.json", temp / "completion.json", model_path):
                    client.log_artifact(run_id, str(path))
            client.set_terminated(run_id, status="FINISHED")
        except Exception:
            client.set_terminated(run_id, status="FAILED")
            raise
        return run_id


def _only_fields(value: Any, allowed: set[str]) -> None:
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError("Tracking refuses fields outside the aggregate privacy allowlist")


def _require_private_safe(condition: bool) -> None:
    if not condition:
        raise ValueError("Tracking refuses fields outside the aggregate privacy allowlist")


def _is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, bool)) or _is_number(value)


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_version(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9][0-9A-Za-z.+-]*", value) is not None


def _is_safe_parameter(name: str, value: Any) -> bool:
    allowed_strings = {
        "class_weight": {"balanced"},
        "penalty": {"l1", "l2", "elasticnet", "deprecated"},
        "solver": {"lbfgs", "liblinear", "newton-cg", "newton-cholesky", "sag", "saga"},
        "strategy": {"training_prevalence"},
    }
    if isinstance(value, str):
        return value in allowed_strings.get(name, set())
    return _is_scalar(value)


def _require_string_list(value: Any) -> None:
    _require_private_safe(isinstance(value, list) and all(isinstance(item, str) for item in value))


def _require_number_list(value: Any) -> None:
    _require_private_safe(isinstance(value, list) and all(_is_number(item) for item in value))


def _validate_tracking_fields(report: dict[str, Any]) -> None:
    """Reject unreviewed fields before any MLflow import, database or artifact write."""
    _only_fields(
        report,
        {
            "schema_version",
            "kind",
            "dataset_id",
            "dataset_sha256",
            "code",
            "configuration",
            "features",
            "splits",
            "validation_candidates",
            "selection",
            "evaluation",
            "warnings",
            "input_csv_sha256",
        },
    )
    _require_private_safe(report["schema_version"] == 1)
    _require_private_safe(report["kind"] == "independent_education_experiment")
    _require_private_safe(report["dataset_id"] == "ai-student-impact")
    _require_private_safe(_is_digest(report["dataset_sha256"]))
    if "input_csv_sha256" in report:
        _require_private_safe(_is_digest(report["input_csv_sha256"]))
    _require_string_list(report["features"])
    _require_string_list(report["warnings"])
    _only_fields(
        report["configuration"],
        {
            "seed",
            "c_values",
            "thresholds",
            "min_recall",
            "top_risk_fraction",
        },
    )
    _require_private_safe(
        isinstance(report["configuration"]["seed"], int)
        and not isinstance(report["configuration"]["seed"], bool)
    )
    for key in ("c_values", "thresholds"):
        _require_number_list(report["configuration"][key])
    for key in ("min_recall", "top_risk_fraction"):
        _require_private_safe(_is_number(report["configuration"][key]))
    _only_fields(report["code"], {"git_head", "source_sha256", "python", "libraries"})
    _only_fields(report["code"]["libraries"], {"scikit-learn", "pandas", "numpy"})
    _require_private_safe(
        (
            report["code"]["git_head"] == "unavailable"
            or (
                isinstance(report["code"]["git_head"], str)
                and re.fullmatch(r"[0-9a-f]{40}", report["code"]["git_head"]) is not None
            )
        )
        and _is_digest(report["code"]["source_sha256"])
        and _is_version(report["code"]["python"])
        and all(_is_version(value) for value in report["code"]["libraries"].values())
    )
    _only_fields(report["splits"], {"train", "validation", "test"})
    for split in report["splits"].values():
        _only_fields(split, {"count", "sha256"})
        _require_private_safe(
            isinstance(split["count"], int)
            and not isinstance(split["count"], bool)
            and _is_digest(split["sha256"])
        )
    _only_fields(report["selection"], {"split", "model_name", "threshold", "criterion"})
    _require_private_safe(
        all(isinstance(report["selection"][key], str) for key in ("model_name", "criterion"))
        and report["selection"]["split"] == "validation"
        and _is_number(report["selection"]["threshold"])
    )
    _require_private_safe(isinstance(report["validation_candidates"], list))
    names = [candidate["model_name"] for candidate in report["validation_candidates"]]
    expected_names = [
        "baseline_churn_rate",
        *(f"logistic_C_{value!r}" for value in report["configuration"]["c_values"]),
    ]
    if names != expected_names or len(names) != len(set(names)):
        raise ValueError("Ambiguous candidate identities cannot be tracked")
    parameter_names = {
        "C",
        "class_weight",
        "dual",
        "fit_intercept",
        "intercept_scaling",
        "l1_ratio",
        "max_iter",
        "n_jobs",
        "penalty",
        "random_state",
        "solver",
        "tol",
        "verbose",
        "warm_start",
        "strategy",
    }
    for candidate in report["validation_candidates"]:
        _only_fields(candidate, {"model_name", "parameters", "thresholds", "eligible"})
        _only_fields(candidate["parameters"], parameter_names)
        _require_private_safe(
            isinstance(candidate["eligible"], bool)
            and all(
                _is_safe_parameter(name, value) for name, value in candidate["parameters"].items()
            )
            and isinstance(candidate["thresholds"], list)
        )
        for choice in candidate["thresholds"]:
            _only_fields(choice, {"threshold", "metrics", "diagnostics"})
            _require_private_safe(_is_number(choice["threshold"]))
            _validate_aggregate_metrics(choice)
    _only_fields(report["evaluation"], {"split", "metrics", "diagnostics"})
    _require_private_safe(report["evaluation"]["split"] == "test")
    _validate_aggregate_metrics(report["evaluation"])


def _validate_tracking_members(directory: Path) -> Path:
    completion = json.loads((directory / "completion.json").read_bytes())
    _only_fields(completion, {"report_id", "members"})
    _require_private_safe(completion["report_id"] == directory.name)
    _only_fields(completion["members"], {"report.json", "model.joblib"})
    _require_private_safe(set(completion["members"]) == {"report.json", "model.joblib"})
    for name, expected in completion["members"].items():
        path = directory / name
        _require_private_safe(
            _is_digest(expected)
            and path.is_file()
            and not path.is_symlink()
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        )
    return directory / "model.joblib"


def _tracking_payload(report: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": 1,
        "kind": "education_experiment_tracking",
        "dataset_sha256": report["dataset_sha256"],
        "code": report["code"],
        "configuration": report["configuration"],
        "splits": report["splits"],
        "validation_candidates": report["validation_candidates"],
        "selection": {
            key: report["selection"][key] for key in ("split", "model_name", "threshold")
        },
        "evaluation": report["evaluation"],
    }
    return cast(dict[str, Any], json.loads(json.dumps(payload, allow_nan=False)))


def _validate_aggregate_metrics(value: dict[str, Any]) -> None:
    _only_fields(
        value["metrics"],
        {
            "pr_auc",
            "roc_auc",
            "precision",
            "recall",
            "accuracy",
            "top_risk_capture",
            "workload_at_threshold",
        },
    )
    _require_private_safe(all(_is_number(metric) for metric in value["metrics"].values()))
    _only_fields(
        value["diagnostics"],
        {
            "count",
            "observed_high_rate",
            "mean_score",
            "confusion",
            "flagged_count",
            "flagged_fraction",
            "false_positive_rate",
            "brier_score",
            "log_loss",
            "reliability",
        },
    )
    for key in (
        "count",
        "observed_high_rate",
        "mean_score",
        "flagged_count",
        "flagged_fraction",
        "false_positive_rate",
        "brier_score",
        "log_loss",
    ):
        _require_private_safe(
            value["diagnostics"][key] is None or _is_number(value["diagnostics"][key])
        )
    _only_fields(value["diagnostics"]["confusion"], {"tp", "fp", "fn", "tn"})
    _require_private_safe(
        all(
            isinstance(count, int) and not isinstance(count, bool)
            for count in value["diagnostics"]["confusion"].values()
        )
        and isinstance(value["diagnostics"]["reliability"], list)
    )
    for group in value["diagnostics"]["reliability"]:
        _only_fields(group, {"lower", "upper", "count", "mean_score", "observed_rate"})
        _require_private_safe(
            isinstance(group["count"], int)
            and not isinstance(group["count"], bool)
            and all(
                group[key] is None or _is_number(group[key])
                for key in ("lower", "upper", "mean_score", "observed_rate")
            )
        )


def _local_artifact_path(uri: Any, expected: Path, *, descendant: bool = False) -> bool:
    parsed = urlparse(str(uri))
    if parsed.scheme != "file" or parsed.netloc:
        return False
    path = Path(unquote(parsed.path))
    if path.resolve() != path:
        return False
    return path.is_relative_to(expected) if descendant else path == expected

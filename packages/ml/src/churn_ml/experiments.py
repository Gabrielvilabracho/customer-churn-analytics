"""Additive CLI for immutable reevaluation and independently selected experiments."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from churn_ml.application.pipelines.experiments import (
    ExperimentResult,
)
from churn_ml.application.pipelines.experiments import (
    run_experiment as _run_experiment,
)
from churn_ml.application.pipelines.reevaluate_education import (
    reevaluate_education as _reevaluate_education,
)
from churn_ml.infrastructure.experiment_identity import LocalExperimentIdentity
from churn_ml.infrastructure.filesystem.education_reevaluation_inputs import (
    FilesystemEducationReevaluationInputs,
)
from churn_ml.infrastructure.filesystem.experiment_reports import publish_report
from churn_ml.infrastructure.sklearn.experiment_candidates import SklearnExperimentCandidates


def reevaluate_education(root: Path, run_id: str, *, trusted_model: bool = False) -> dict[str, Any]:
    return _reevaluate_education(
        run_id,
        input_loader=FilesystemEducationReevaluationInputs(root),
        identity_provider=LocalExperimentIdentity(),
        trusted_model=trusted_model,
    )


def run_experiment(
    rows: list[dict[str, Any]],
    *,
    seed: int = 42,
    c_values: tuple[float, ...] = (0.1, 1.0, 10.0),
    thresholds: tuple[float, ...] = (0.7, 0.5, 0.3),
    min_recall: float = 0.7,
) -> ExperimentResult:
    return _run_experiment(
        rows,
        candidate_provider=SklearnExperimentCandidates(),
        identity_provider=LocalExperimentIdentity(),
        seed=seed,
        c_values=c_values,
        thresholds=thresholds,
        min_recall=min_recall,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    reevaluate = commands.add_parser("reevaluate", help="Rescore a trusted published model")
    reevaluate.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    reevaluate.add_argument("--run-id", required=True)
    reevaluate.add_argument(
        "--trusted-model", action="store_true", help="Allow trusted joblib loading"
    )
    experiment = commands.add_parser(
        "run", help="Fit/select/evaluate using separate 60/20/20 splits"
    )
    experiment.add_argument("--csv", type=Path, required=True)
    experiment.add_argument("--seed", type=int, default=42)
    experiment.add_argument("--c-values", type=float, nargs="+", default=[0.1, 1.0, 10.0])
    experiment.add_argument("--min-recall", type=float, default=0.7)
    experiment.add_argument(
        "--mlflow-dir", help="Opt-in local SQLite tracking directory (no server URI)"
    )
    for command in (reevaluate, experiment):
        command.add_argument("--report-id", required=True, help="New immutable report identity")
        command.add_argument("--output-root", type=Path, default=Path("artifacts/experiments"))
    args = parser.parse_args(argv)
    try:
        # Refuse reused destinations before training, loading a model or tracking.
        from churn_ml.domain.education import validate_identity

        validate_identity(args.report_id)
        destination = args.output_root.resolve() / args.report_id
        if destination.exists() or destination.is_symlink():
            raise ValueError("Report identity already exists; choose a new ID")
        tracker = None
        if args.command == "run" and args.mlflow_dir is not None:
            from churn_ml.infrastructure.mlflow_tracking import LocalMlflowTracker

            tracker = LocalMlflowTracker(args.mlflow_dir)
        model = None
        if args.command == "reevaluate":
            report = reevaluate_education(
                args.artifact_root, args.run_id, trusted_model=args.trusted_model
            )
        else:
            data = args.csv.read_bytes()
            rows = list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
            result = run_experiment(
                rows, seed=args.seed, c_values=tuple(args.c_values), min_recall=args.min_recall
            )
            report, model = result.report, result.model
            report["input_csv_sha256"] = hashlib.sha256(data).hexdigest()
        directory = publish_report(args.output_root, args.report_id, report, model=model)
        if tracker is not None:
            try:
                tracking_id = tracker.log(directory)
            except Exception as exc:
                print(
                    f"Local report preserved at {directory}; tracking failed: {exc}",
                    file=sys.stderr,
                )
                return 2
            print(f"MLflow run: {tracking_id}")
        print(
            json.dumps(
                {"report": str(directory), "evaluation": report["evaluation"]}, sort_keys=True
            )
        )
    except (ValueError, OSError, ImportError) as exc:
        print(f"Experiment failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

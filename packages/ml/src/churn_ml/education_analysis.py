"""Offline education interpretability CLI; run only against trusted local models."""

import argparse
from pathlib import Path
from typing import Any

from churn_ml.application.pipelines.analyze_education import (
    publish_education_analysis as _publish_education_analysis,
)
from churn_ml.domain.education import validate_identity
from churn_ml.infrastructure.filesystem.education_analysis_adapters import (
    FilesystemEducationAnalysisInputs,
    FilesystemEducationAnalysisPublisher,
)
from churn_ml.infrastructure.filesystem.education_analysis_store import EducationAnalysisStore
from churn_ml.infrastructure.sklearn.education_analysis_engine import SklearnEducationAnalysisEngine


def publish_education_analysis(
    root: Path,
    run_id: str,
    analysis_id: str,
    *,
    seed: int = 42,
    shap_samples: int = 256,
    permutation_samples: int = 2000,
    min_cohort_size: int = 20,
) -> dict[str, Any]:
    """Compose trusted local adapters for the offline publication use case."""
    validate_identity(run_id)
    validate_identity(analysis_id)
    return _publish_education_analysis(
        run_id,
        analysis_id,
        input_loader=FilesystemEducationAnalysisInputs(root),
        engine=SklearnEducationAnalysisEngine(),
        publisher=FilesystemEducationAnalysisPublisher(EducationAnalysisStore(root)),
        seed=seed,
        shap_samples=shap_samples,
        permutation_samples=permutation_samples,
        min_cohort_size=min_cohort_size,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explain a trusted local education logistic model without retraining it.",
        epilog="Joblib models execute Python code: use only your own trusted local publications. "
        "Existing runs are never modified; select a new analysis ID for each publication.",
    )
    parser.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    parser.add_argument("--run-id", required=True, help="Exact published education model run.")
    parser.add_argument("--analysis-id", required=True, help="New immutable analysis identity.")
    parser.add_argument(
        "--seed", type=int, default=42, help="Deterministic sampling/permutation seed."
    )
    parser.add_argument("--shap-samples", type=int, default=256, help="Held-out SHAP sample limit.")
    parser.add_argument(
        "--permutation-samples",
        type=int,
        default=2000,
        help="Held-out permutation sample limit (five repeats per variable).",
    )
    parser.add_argument(
        "--min-cohort-size",
        type=int,
        default=20,
        help="Suppress statistics for cohorts smaller than this count.",
    )
    args = parser.parse_args()
    try:
        publish_education_analysis(
            args.artifact_root,
            args.run_id,
            args.analysis_id,
            seed=args.seed,
            shap_samples=args.shap_samples,
            permutation_samples=args.permutation_samples,
            min_cohort_size=args.min_cohort_size,
        )
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Published education analysis: {args.run_id}/{args.analysis_id}")


if __name__ == "__main__":
    main()

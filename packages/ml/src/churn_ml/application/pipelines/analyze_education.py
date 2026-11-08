"""Orchestrate verified education analysis through inward-facing ports."""

from datetime import UTC, datetime
from typing import Any

from churn_ml.application.ports.education_analysis import (
    EducationAnalysisEngine,
    EducationAnalysisInputLoader,
    EducationAnalysisPublisher,
)
from churn_ml.domain.education import validate_identity


def publish_education_analysis(
    run_id: str,
    analysis_id: str,
    *,
    input_loader: EducationAnalysisInputLoader,
    engine: EducationAnalysisEngine,
    publisher: EducationAnalysisPublisher,
    seed: int = 42,
    shap_samples: int = 256,
    permutation_samples: int = 2000,
    min_cohort_size: int = 20,
) -> dict[str, Any]:
    validate_identity(run_id)
    validate_identity(analysis_id)
    publisher.assert_available(run_id, analysis_id)
    inputs = input_loader.load(run_id)
    payload = engine.analyze(
        inputs,
        seed=seed,
        shap_samples=shap_samples,
        permutation_samples=permutation_samples,
        min_cohort_size=min_cohort_size,
    )
    payload.update(
        schema_version=1,
        run_id=run_id,
        analysis_id=analysis_id,
        dataset_id=inputs.dataset_id,
        model_name=inputs.model_name,
        created_at_utc=datetime.now(UTC).isoformat(),
        source_hashes=inputs.source_hashes,
        model_metrics=inputs.model_metrics,
        versions=inputs.versions,
    )
    # Recheck source stability after computation; no mixed snapshot publication.
    input_loader.assert_unchanged(run_id, inputs.source_hashes)
    publisher.publish(payload)
    return payload

from datetime import UTC, datetime
from pathlib import Path

from churn_ml.application.pipelines.features import prepare_training_splits_from_csv
from churn_ml.application.pipelines.train import (
    TrainingEvaluationResult,
    train_and_evaluate_model_candidate,
)
from churn_ml.application.ports.artifact_store import ArtifactStore
from churn_ml.application.ports.model_trainer import ModelTrainer
from churn_ml.domain.artifacts import ArtifactBundle, ArtifactManifest


def run_training(
    csv_path: Path,
    *,
    artifact_store: ArtifactStore,
    run_id: str,
    dataset_id: str,
    customer_key: str,
    target_column: str,
    baseline_trainer: ModelTrainer,
    candidate_trainer: ModelTrainer,
    test_fraction: float = 0.2,
    seed: int = 42,
    candidate_thresholds: tuple[float, ...] = (0.7, 0.5, 0.3),
    min_recall: float = 0.7,
    min_top_risk_capture: float = 0.7,
    top_risk_fraction: float = 0.2,
) -> TrainingEvaluationResult:
    """Orchestrate the full training pipeline from raw CSV to versioned artifacts.

    Raises DatasetProfileError if the input CSV fails schema screening.
    No artifact writes occur when screening raises.
    Model binary persistence is the caller's responsibility, using the
    concrete store's save_model_binary (e.g. FilesystemArtifactStore),
    via result.trained_candidate.
    """
    preprocessing = prepare_training_splits_from_csv(
        csv_path,
        artifact_store=artifact_store,
        run_id=run_id,
        dataset_id=dataset_id,
        customer_key=customer_key,
        target_column=target_column,
        test_fraction=test_fraction,
        seed=seed,
    )

    eval_result = train_and_evaluate_model_candidate(
        baseline_trainer=baseline_trainer,
        candidate_trainer=candidate_trainer,
        train_rows=preprocessing.train_rows,
        evaluation_rows=preprocessing.test_rows,
        target_column=target_column,
        candidate_thresholds=candidate_thresholds,
        min_recall=min_recall,
        min_top_risk_capture=min_top_risk_capture,
        top_risk_fraction=top_risk_fraction,
    )

    categorical_columns = set(
        preprocessing.train_fit_metadata.get("categorical_levels", {}).keys()
    )
    feature_schema = {
        col: "string" if col in categorical_columns else "number"
        for col in preprocessing.feature_columns
    }

    prediction_samples = _build_prediction_samples(
        eval_result,
        test_rows=preprocessing.test_rows,
        target_column=target_column,
        customer_key=customer_key,
    )

    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id=run_id,
            dataset_id=dataset_id,
            model_name=eval_result.comparison.candidate_model_name,
            created_at_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            feature_schema=feature_schema,
        ),
        metrics=eval_result.metrics,
        threshold=eval_result.threshold,
        prediction_samples=prediction_samples,
    )
    artifact_store.save_bundle(bundle)

    return eval_result


def _build_prediction_samples(
    eval_result: TrainingEvaluationResult,
    *,
    test_rows: list[dict[str, str]],
    target_column: str,
    customer_key: str,
) -> tuple[dict[str, str], ...]:
    if eval_result.trained_candidate is None or not test_rows:
        return ()
    probabilities = eval_result.trained_candidate.predict_probabilities(test_rows)
    return tuple(
        {
            customer_key: str(row[customer_key]),
            "churn_probability": f"{prob:.4f}",
            "actual_churn": str(row[target_column]),
        }
        for row, prob in zip(test_rows, probabilities, strict=True)
    )

from pathlib import Path
from unittest.mock import patch

import pytest
from churn_ml.application.pipelines.profile import DatasetProfileError
from churn_ml.application.pipelines.run_training import (
    PREDICTION_SAMPLE_COHORT_FIELDS,
    _build_prediction_samples,
    run_training,
)
from churn_ml.application.pipelines.train import ModelComparison, TrainingEvaluationResult
from churn_ml.domain.artifacts import ClassificationMetricSet, ThresholdSelection
from churn_ml.domain.model import TELCO_POSITIVE_LABELS
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer
from churn_ml.infrastructure.sklearn.candidate import SklearnLogisticRegressionTrainer

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"

FEATURE_COLUMNS = ("gender", "SeniorCitizen", "tenure", "MonthlyCharges")


def test_run_training_writes_processed_splits_and_versioned_artifact_bundle(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    result = run_training(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="entrypoint-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        positive_labels=TELCO_POSITIVE_LABELS,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=42,
        ),
    )

    # Processed splits written
    assert (tmp_path / "processed" / "entrypoint-001" / "train.csv").is_file()
    assert (tmp_path / "processed" / "entrypoint-001" / "test.csv").is_file()

    # Metrics bundle written
    assert (tmp_path / "metrics" / "entrypoint-001" / "metrics.json").is_file()
    assert (tmp_path / "metrics" / "entrypoint-001" / "prediction_samples.csv").is_file()

    # model_metadata.json is written by save_bundle (called inside run_training);
    # model.joblib is written by __main__ via save_model_binary (not called here).
    assert (tmp_path / "models" / "entrypoint-001" / "model_metadata.json").is_file()

    # Result contains meaningful evaluation data
    assert result.comparison.baseline_model_name == "baseline_churn_rate"
    assert result.comparison.candidate_model_name == "candidate_logistic_regression"
    # Deterministic with random_state=42 and the committed fixture.
    assert result.metrics.recall >= 0.95
    assert result.threshold.threshold > 0.0
    assert result.trained_candidate is not None


def test_run_training_prediction_samples_contain_churn_probability_field(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    run_training(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="entrypoint-samples-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        positive_labels=TELCO_POSITIVE_LABELS,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=42,
        ),
    )

    loaded = store.load_bundle("entrypoint-samples-001")
    assert len(loaded.prediction_samples) > 0
    for sample in loaded.prediction_samples:
        assert "churn_probability" in sample
        probability = float(sample["churn_probability"])
        assert 0.0 <= probability <= 1.0


def test_run_training_uses_real_sklearn_estimator_not_fallback_model(
    tmp_path: Path,
) -> None:
    from churn_ml.infrastructure.sklearn.candidate import _FallbackModel

    store = FilesystemArtifactStore(root=tmp_path)

    result = run_training(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="entrypoint-sklearn-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        positive_labels=TELCO_POSITIVE_LABELS,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=42,
        ),
    )

    assert result.trained_candidate is not None
    assert not isinstance(result.trained_candidate.estimator, _FallbackModel)


def test_run_training_writes_no_artifacts_when_schema_screening_fails(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    with pytest.raises(DatasetProfileError, match="missing required target column"):
        run_training(
            FIXTURE_DIR / "telco_churn_missing_target.csv",
            artifact_store=store,
            run_id="invalid-schema",
            dataset_id="telco-sample",
            customer_key="customerID",
            target_column="Churn",
            positive_labels=TELCO_POSITIVE_LABELS,
            baseline_trainer=BaselineChurnRateTrainer(),
            candidate_trainer=SklearnLogisticRegressionTrainer(
                model_name="candidate_logistic_regression",
                feature_columns=FEATURE_COLUMNS,
                random_state=42,
            ),
        )

    assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# F1 — manifest model_name must always be the candidate's name
# ---------------------------------------------------------------------------

def test_run_training_manifest_names_candidate_when_baseline_wins(
    tmp_path: Path,
) -> None:
    """Manifest model_name is always the candidate's name, even when baseline wins."""
    fake_metrics = ClassificationMetricSet(
        pr_auc=0.5,
        roc_auc=0.6,
        precision=0.5,
        recall=0.5,
        accuracy=0.7,
        top_risk_capture=0.5,
        workload_at_threshold=0.3,
    )
    baseline_wins_comparison = ModelComparison(
        baseline_model_name="baseline_churn_rate",
        candidate_model_name="candidate_logistic_regression",
        baseline_metrics=fake_metrics,
        candidate_metrics=fake_metrics,
        selected_model_name="baseline_churn_rate",
        selection_reason="baseline remains stronger or equivalent on churn usefulness metrics",
    )

    store = FilesystemArtifactStore(root=tmp_path)
    with patch(
        "churn_ml.application.pipelines.train.compare_model_candidates",
        return_value=baseline_wins_comparison,
    ):
        run_training(
            FIXTURE_DIR / "telco_churn_sample.csv",
            artifact_store=store,
            run_id="manifest-baseline-wins-001",
            dataset_id="telco-sample",
            customer_key="customerID",
            target_column="Churn",
            positive_labels=TELCO_POSITIVE_LABELS,
            baseline_trainer=BaselineChurnRateTrainer(),
            candidate_trainer=SklearnLogisticRegressionTrainer(
                model_name="candidate_logistic_regression",
                feature_columns=FEATURE_COLUMNS,
                random_state=42,
            ),
        )

    loaded = store.load_bundle("manifest-baseline-wins-001")
    assert loaded.manifest.model_name == "candidate_logistic_regression"


# ---------------------------------------------------------------------------
# F6 — prediction samples must include customer_id from customer_key column
# ---------------------------------------------------------------------------

def test_run_training_prediction_samples_include_customer_key_field(
    tmp_path: Path,
) -> None:
    """Each prediction sample must carry the customer identifier (customer_key column)."""
    store = FilesystemArtifactStore(root=tmp_path)

    run_training(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="entrypoint-customer-key-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        positive_labels=TELCO_POSITIVE_LABELS,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=42,
        ),
    )

    loaded = store.load_bundle("entrypoint-customer-key-001")
    assert len(loaded.prediction_samples) > 0
    for sample in loaded.prediction_samples:
        assert "customerID" in sample, f"customerID missing from sample: {sample}"


def test_run_training_prediction_samples_include_dashboard_cohort_fields(
    tmp_path: Path,
) -> None:
    """Prediction samples must carry cohort fields needed by the dashboard."""
    store = FilesystemArtifactStore(root=tmp_path)

    run_training(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="entrypoint-dashboard-cohorts-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        positive_labels=TELCO_POSITIVE_LABELS,
        baseline_trainer=BaselineChurnRateTrainer(),
        candidate_trainer=SklearnLogisticRegressionTrainer(
            model_name="candidate_logistic_regression",
            feature_columns=FEATURE_COLUMNS,
            random_state=42,
        ),
    )

    loaded = store.load_bundle("entrypoint-dashboard-cohorts-001")
    assert len(loaded.prediction_samples) > 0
    first_sample = loaded.prediction_samples[0]
    assert first_sample["Contract"] in {"Month-to-month", "One year", "Two year"}
    assert first_sample["PaymentMethod"] in {
        "Bank transfer",
        "Credit card",
        "Electronic check",
        "Mailed check",
    }
    assert first_sample["InternetService"] in {"DSL", "Fiber optic", "No"}
    assert int(first_sample["tenure"]) >= 0
    assert float(first_sample["MonthlyCharges"]) > 0


def test_prediction_sample_cohort_fields_match_public_api_contract() -> None:
    from churn_api.application.dashboard_contract import PUBLIC_PREDICTION_SAMPLE_FIELDS

    assert tuple(PREDICTION_SAMPLE_COHORT_FIELDS) == tuple(
        field
        for field in PUBLIC_PREDICTION_SAMPLE_FIELDS
        if field != "churn_probability"
    )


# ---------------------------------------------------------------------------
# R3-W4 — empty raw_test_rows early-return path in _build_prediction_samples
# ---------------------------------------------------------------------------


def test_build_prediction_samples_returns_empty_when_no_raw_test_rows() -> None:
    """_build_prediction_samples must return () immediately when raw_test_rows is empty."""
    from churn_ml.application.pipelines.train import ModelComparison

    fake_metrics = ClassificationMetricSet(
        pr_auc=0.5,
        roc_auc=0.6,
        precision=0.5,
        recall=0.5,
        accuracy=0.7,
        top_risk_capture=0.5,
        workload_at_threshold=0.3,
    )
    comparison = ModelComparison(
        baseline_model_name="baseline",
        candidate_model_name="candidate",
        baseline_metrics=fake_metrics,
        candidate_metrics=fake_metrics,
        selected_model_name="candidate",
        selection_reason="test",
    )
    trained_model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    eval_result = TrainingEvaluationResult(
        comparison=comparison,
        threshold=ThresholdSelection(threshold=0.5, tradeoff="test"),
        metrics=fake_metrics,
        trained_candidate=trained_model,
    )

    samples = _build_prediction_samples(
        eval_result,
        raw_test_rows=[],
        target_column="churn",
        customer_key="customerID",
    )
    assert samples == ()

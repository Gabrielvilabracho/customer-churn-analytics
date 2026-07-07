from pathlib import Path

from churn_api.adapters.filesystem import FilesystemArtifactSnapshotReader
from churn_ml.domain.artifacts import (
    ArtifactBundle,
    ArtifactManifest,
    ClassificationMetricSet,
    ThresholdSelection,
)
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer


def _make_bundle(run_id: str) -> ArtifactBundle:
    return ArtifactBundle(
        manifest=ArtifactManifest(
            run_id=run_id,
            dataset_id="telco-churn",
            model_name="candidate_logistic_regression",
            created_at_utc="2026-07-03T00:00:00Z",
            feature_schema={"tenure": "number", "Contract": "string"},
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.72,
            roc_auc=0.80,
            precision=0.64,
            recall=0.81,
            accuracy=0.77,
            top_risk_capture=0.70,
            workload_at_threshold=0.35,
        ),
        threshold=ThresholdSelection(
            threshold=0.42,
            tradeoff="Selected threshold 0.42 to reach recall 0.81 with workload 0.35.",
        ),
        prediction_samples=(
            {"churn_probability": "0.82", "actual_churn": "Yes"},
            {"churn_probability": "0.18", "actual_churn": "No"},
        ),
    )


def test_snapshot_reader_loads_bundle_shape_from_store_without_model_binary(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    store.save_bundle(_make_bundle("run-api-001"))

    snapshot = FilesystemArtifactSnapshotReader(
        root=tmp_path, run_id="run-api-001"
    ).load_current_snapshot()

    assert snapshot.model.run_id == "run-api-001"
    assert snapshot.model.dataset_id == "telco-churn"
    assert snapshot.model.model_name == "candidate_logistic_regression"
    assert snapshot.model.created_at_utc == "2026-07-03T00:00:00Z"
    assert snapshot.model.feature_schema == {"tenure": "number", "Contract": "string"}
    assert snapshot.metrics == {"recall": 0.81, "precision": 0.64, "pr_auc": 0.72}
    assert snapshot.threshold == 0.42
    assert snapshot.freshness == {"metrics_created_at_utc": "2026-07-03T00:00:00Z"}
    assert len(snapshot.prediction_samples) == 2
    assert snapshot.prediction_samples[0]["churn_probability"] == "0.82"


def test_snapshot_reader_bundle_shape_is_unchanged_after_model_binary_is_saved(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    bundle = _make_bundle("run-api-002")
    store.save_bundle(bundle)

    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id="run-api-002")

    snapshot = FilesystemArtifactSnapshotReader(
        root=tmp_path, run_id="run-api-002"
    ).load_current_snapshot()

    assert snapshot.model.run_id == "run-api-002"
    assert snapshot.metrics["recall"] == 0.81
    assert snapshot.threshold == 0.42
    assert len(snapshot.prediction_samples) == 2

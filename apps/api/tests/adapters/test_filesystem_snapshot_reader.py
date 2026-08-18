import hashlib
import json
from pathlib import Path

import pytest
from churn_api.adapters.filesystem import FilesystemArtifactSnapshotReader
from churn_api.domain.artifacts import ArtifactUnavailableError
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


def _publish_run(store: FilesystemArtifactStore, bundle: ArtifactBundle) -> None:
    store.save_bundle(bundle)
    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id=bundle.manifest.run_id)
    store.publish_run(bundle.manifest.run_id)


def test_reader_exposes_selected_run_id(tmp_path: Path) -> None:
    reader = FilesystemArtifactSnapshotReader(root=tmp_path, run_id="run-api-001")

    assert reader.selected_run_id == "run-api-001"


def test_snapshot_reader_loads_published_bundle_shape_from_store(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    _publish_run(store, _make_bundle("run-api-001"))

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


def test_snapshot_reader_rejects_unpublished_run(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    store.save_bundle(_make_bundle("run-api-002"))

    with pytest.raises(ArtifactUnavailableError, match="not published"):
        FilesystemArtifactSnapshotReader(
            root=tmp_path, run_id="run-api-002"
        ).load_current_snapshot()


def test_snapshot_reader_rejects_absent_run(tmp_path: Path) -> None:
    with pytest.raises(ArtifactUnavailableError, match="not published"):
        FilesystemArtifactSnapshotReader(
            root=tmp_path, run_id="run-api-absent"
        ).load_current_snapshot()


def test_snapshot_reader_rejects_tampered_member_after_publication(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    _publish_run(store, _make_bundle("run-api-003"))
    metrics_path = tmp_path / "metrics" / "run-api-003" / "metrics.json"
    metrics_path.write_text(metrics_path.read_text(encoding="utf-8") + " ")

    with pytest.raises(ArtifactUnavailableError, match="checksum mismatch"):
        FilesystemArtifactSnapshotReader(
            root=tmp_path, run_id="run-api-003"
        ).load_current_snapshot()


def test_snapshot_reader_rejects_manifest_identity_mismatch(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    _publish_run(store, _make_bundle("run-api-004"))
    metrics_path = tmp_path / "metrics" / "run-api-004" / "metrics.json"
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    payload["manifest"]["run_id"] = "run-api-other"
    metrics_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    completion_path = tmp_path / "models" / "run-api-004" / "completion.json"
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion["members"][str(metrics_path)] = hashlib.sha256(
        metrics_path.read_bytes()
    ).hexdigest()
    completion_path.write_text(
        json.dumps(completion, indent=2, sort_keys=True), encoding="utf-8"
    )

    with pytest.raises(ArtifactUnavailableError, match="identity does not match"):
        FilesystemArtifactSnapshotReader(
            root=tmp_path, run_id="run-api-004"
        ).load_current_snapshot()

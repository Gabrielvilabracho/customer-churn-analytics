from pathlib import Path

from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore

from churn_api.domain.artifacts import ArtifactSnapshot, ModelMetadata


class FilesystemArtifactSnapshotReader:
    def __init__(self, *, root: Path, run_id: str) -> None:
        self._store = FilesystemArtifactStore(root=root)
        self._run_id = run_id

    def load_current_snapshot(self) -> ArtifactSnapshot:
        bundle = self._store.load_bundle(self._run_id)
        return ArtifactSnapshot(
            model=ModelMetadata(
                run_id=bundle.manifest.run_id,
                dataset_id=bundle.manifest.dataset_id,
                model_name=bundle.manifest.model_name,
                created_at_utc=bundle.manifest.created_at_utc,
                feature_schema=bundle.manifest.feature_schema,
            ),
            metrics={
                "recall": bundle.metrics.recall,
                "precision": bundle.metrics.precision,
                "pr_auc": bundle.metrics.pr_auc,
            },
            threshold=bundle.threshold.threshold,
            prediction_samples=bundle.prediction_samples,
            freshness={"metrics_created_at_utc": bundle.manifest.created_at_utc},
        )

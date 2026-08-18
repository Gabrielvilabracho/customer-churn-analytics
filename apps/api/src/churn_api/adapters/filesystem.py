from pathlib import Path

from churn_ml.infrastructure.filesystem.artifact_store import (
    ArtifactNotFoundError,
    FilesystemArtifactStore,
    IntegrityError,
)

from churn_api.domain.artifacts import (
    ArtifactSnapshot,
    ArtifactUnavailableError,
    ModelMetadata,
)


class FilesystemArtifactSnapshotReader:
    def __init__(self, *, root: Path, run_id: str) -> None:
        self._store = FilesystemArtifactStore(root=root)
        self._run_id = run_id

    @property
    def selected_run_id(self) -> str:
        return self._run_id

    def load_current_snapshot(self) -> ArtifactSnapshot:
        # Serving reads validate the exact bytes identified by the run's
        # completion manifest before loading, so an altered, missing, or
        # unpublished member degrades deterministically instead of 500.
        try:
            self._store.verify_run_integrity(self._run_id)
        except IntegrityError as exc:
            raise ArtifactUnavailableError(str(exc)) from exc
        try:
            bundle = self._store.load_bundle(self._run_id)
        except ArtifactNotFoundError as exc:
            raise ArtifactUnavailableError(str(exc)) from exc
        if bundle.manifest.run_id != self._run_id:
            raise ArtifactUnavailableError(
                f"Run {self._run_id!r} manifest identity does not match its run"
            )
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

import os
import re
from collections.abc import Mapping
from pathlib import Path

from fastapi import FastAPI

from churn_api.adapters.filesystem import FilesystemArtifactSnapshotReader
from churn_api.adapters.scoring import StubChurnScorer
from churn_api.application.ports.artifacts import ArtifactSnapshotReader
from churn_api.application.ports.scoring import ChurnScorer
from churn_api.application.services import AnalyticsService, PredictionService
from churn_api.domain.artifacts import ArtifactSnapshot, ArtifactUnavailableError
from churn_api.presentation.http.routes import create_router

_RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]+")
_DEFAULT_ARTIFACT_ROOT = "artifacts"


def create_app(
    *,
    artifact_reader: ArtifactSnapshotReader | None = None,
    scorer: ChurnScorer | None = None,
) -> FastAPI:
    if artifact_reader is None:
        artifact_reader = _UnavailableArtifactReader()
    if scorer is None:
        scorer = StubChurnScorer()

    app = FastAPI(title="Customer Churn Analytics API", version="0.1.0")
    app.include_router(
        create_router(
            analytics_service=AnalyticsService(artifact_reader),
            prediction_service=PredictionService(artifact_reader, scorer),
        )
    )
    return app


def create_runtime_app(environ: Mapping[str, str] | None = None) -> FastAPI:
    """Compose the API from runtime settings without import-time artifact I/O.

    ``CHURN_ARTIFACT_RUN_ID`` selects an exact published run; a blank or
    invalid value keeps the app degraded. ``CHURN_ARTIFACT_ROOT`` locates the
    artifact store and defaults to the repository-relative ``artifacts``
    directory. No ``latest`` discovery is performed. Explicit dependencies
    supplied to :func:`create_app` always win over these settings.
    """
    settings = os.environ if environ is None else environ
    run_id = settings.get("CHURN_ARTIFACT_RUN_ID", "").strip()
    if not _RUN_ID_PATTERN.fullmatch(run_id):
        return create_app()

    root = Path(settings.get("CHURN_ARTIFACT_ROOT", _DEFAULT_ARTIFACT_ROOT))
    reader = FilesystemArtifactSnapshotReader(root=root, run_id=run_id)
    return create_app(artifact_reader=reader)


class _UnavailableArtifactReader:
    selected_run_id: str | None = None

    def load_current_snapshot(self) -> ArtifactSnapshot:
        raise ArtifactUnavailableError("No artifact reader configured")


app = create_runtime_app()

from typing import Any

from fastapi import FastAPI

from churn_api.adapters.scoring import StubChurnScorer
from churn_api.application.services import AnalyticsService, PredictionService
from churn_api.presentation.http.routes import create_router


def create_app(*, artifact_reader: Any | None = None, scorer: Any | None = None) -> FastAPI:
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


class _UnavailableArtifactReader:
    def load_current_snapshot(self) -> Any:
        raise FileNotFoundError("No artifact reader configured")

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from churn_api.application.services import (
    AnalyticsService,
    PredictionService,
)
from churn_api.domain.artifacts import ArtifactUnavailableError
from churn_api.domain.predictions import PredictionValidationError
from churn_api.presentation.http.schemas import PredictionRequest

logger = logging.getLogger(__name__)


def _degraded_response(
    *,
    operation: str,
    run_id: str | None,
    error: ArtifactUnavailableError,
) -> JSONResponse:
    """Emit a structured degradation event and return the 503 contract.

    The event carries the endpoint or operation, the selected run ID when
    known, and the deterministic reason, without exposing artifact contents.
    """
    logger.warning(
        "artifact_degraded",
        extra={
            "event": "artifact_degraded",
            "operation": operation,
            "run_id": run_id,
            "reason": str(error),
        },
    )
    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "reason": str(error)},
    )


def create_router(
    *,
    analytics_service: AnalyticsService,
    prediction_service: PredictionService,
) -> APIRouter:
    router = APIRouter()

    @router.get("/health", response_model=None)
    def health() -> Any:
        try:
            return analytics_service.health()
        except ArtifactUnavailableError as error:
            return _degraded_response(
                operation="GET /health",
                run_id=analytics_service.selected_run_id,
                error=error,
            )

    @router.get("/model/metadata", response_model=None)
    def model_metadata() -> Any:
        try:
            return analytics_service.model_metadata()
        except ArtifactUnavailableError as error:
            return _degraded_response(
                operation="GET /model/metadata",
                run_id=analytics_service.selected_run_id,
                error=error,
            )

    @router.get("/analytics/dashboard", response_model=None)
    def dashboard() -> Any:
        try:
            return analytics_service.dashboard()
        except ArtifactUnavailableError as error:
            return _degraded_response(
                operation="GET /analytics/dashboard",
                run_id=analytics_service.selected_run_id,
                error=error,
            )

    @router.post("/predict", response_model=None)
    def predict(request: PredictionRequest) -> Any:
        try:
            return prediction_service.predict(request.customer_features)
        except ArtifactUnavailableError as error:
            return _degraded_response(
                operation="POST /predict",
                run_id=prediction_service.selected_run_id,
                error=error,
            )
        except PredictionValidationError as error:
            return JSONResponse(
                status_code=422,
                content={"error": "invalid_prediction_request", "details": error.details},
            )

    return router
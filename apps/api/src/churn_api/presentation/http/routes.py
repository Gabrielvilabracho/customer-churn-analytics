from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from churn_api.application.services import (
    AnalyticsService,
    PredictionService,
)
from churn_api.domain.predictions import PredictionValidationError
from churn_api.presentation.http.schemas import PredictionRequest


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
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "reason": str(error)},
            )

    @router.get("/model/metadata", response_model=None)
    def model_metadata() -> Any:
        try:
            return analytics_service.model_metadata()
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "reason": str(error)},
            )

    @router.get("/analytics/dashboard", response_model=None)
    def dashboard() -> Any:
        try:
            return analytics_service.dashboard()
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "reason": str(error)},
            )

    @router.post("/predict", response_model=None)
    def predict(request: PredictionRequest) -> Any:
        try:
            return prediction_service.predict(request.customer_features)
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "reason": str(error)},
            )
        except PredictionValidationError as error:
            return JSONResponse(
                status_code=422,
                content={"error": "invalid_prediction_request", "details": error.details},
            )

    return router

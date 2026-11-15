from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from churn_api.application.education_contract import validate_public_education_analysis
from churn_api.application.ports.education import EducationAnalysisReader
from churn_api.domain.artifacts import ArtifactUnavailableError
from churn_api.presentation.http.routes import DEGRADED_RESPONSE, _degraded_response
from churn_api.presentation.http.schemas import EducationAnalyticsResponse


def create_education_router(reader: EducationAnalysisReader | None) -> APIRouter:
    router = APIRouter()

    @router.get(
        "/analytics/education",
        response_model=EducationAnalyticsResponse,
        responses=DEGRADED_RESPONSE,
    )
    def education() -> Any:
        try:
            if reader is None:
                raise ArtifactUnavailableError("No education analysis configured")
            payload = reader.read()
            try:
                validated = validate_public_education_analysis(payload)
                return JSONResponse(content=validated)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise ArtifactUnavailableError(
                    "Invalid public education analysis contract"
                ) from exc
        except ArtifactUnavailableError as exc:
            return _degraded_response(operation="GET /analytics/education", run_id=None, error=exc)

    return router

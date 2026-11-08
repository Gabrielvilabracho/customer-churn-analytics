from typing import Any

from fastapi import APIRouter

from churn_api.application.education_contract import validate_public_education_analysis
from churn_api.application.ports.education import EducationAnalysisReader
from churn_api.domain.artifacts import ArtifactUnavailableError
from churn_api.presentation.http.routes import _degraded_response


def create_education_router(reader: EducationAnalysisReader | None) -> APIRouter:
    router = APIRouter()

    @router.get("/analytics/education", response_model=None)
    def education() -> Any:
        try:
            if reader is None:
                raise ArtifactUnavailableError("No education analysis configured")
            payload = reader.read()
            try:
                return validate_public_education_analysis(payload)
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                raise ArtifactUnavailableError(
                    "Invalid public education analysis contract"
                ) from exc
        except ArtifactUnavailableError as exc:
            return _degraded_response(operation="GET /analytics/education", run_id=None, error=exc)

    return router

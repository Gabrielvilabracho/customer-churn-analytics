from pathlib import Path
from typing import Any

from churn_ml.infrastructure.filesystem.education_analysis_store import EducationAnalysisStore

from churn_api.domain.artifacts import ArtifactUnavailableError


class FilesystemEducationReader:
    def __init__(self, root: Path, run_id: str, analysis_id: str) -> None:
        self._store = EducationAnalysisStore(root)
        self._run_id = run_id
        self._analysis_id = analysis_id

    def read(self) -> dict[str, Any]:
        try:
            return self._store.read(self._run_id, self._analysis_id)
        except ValueError as exc:
            raise ArtifactUnavailableError(str(exc)) from exc
        except (AttributeError, KeyError, TypeError) as exc:
            raise ArtifactUnavailableError("Education source metadata is malformed") from exc

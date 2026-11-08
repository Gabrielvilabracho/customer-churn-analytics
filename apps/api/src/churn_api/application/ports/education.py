from typing import Any, Protocol


class EducationAnalysisReader(Protocol):
    def read(self) -> dict[str, Any]: ...

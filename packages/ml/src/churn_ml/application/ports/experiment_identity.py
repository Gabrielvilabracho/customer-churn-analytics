"""Inward-facing source and runtime identity contract for experiment reports."""

from typing import Any, Protocol


class ExperimentIdentityProvider(Protocol):
    def capture(self) -> dict[str, Any]: ...

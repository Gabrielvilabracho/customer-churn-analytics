from typing import Protocol

from churn_api.domain.artifacts import ArtifactSnapshot


class ArtifactSnapshotReader(Protocol):
    @property
    def selected_run_id(self) -> str | None: ...

    def load_current_snapshot(self) -> ArtifactSnapshot: ...

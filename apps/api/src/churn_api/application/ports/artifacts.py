from typing import Protocol

from churn_api.domain.artifacts import ArtifactSnapshot


class ArtifactSnapshotReader(Protocol):
    def load_current_snapshot(self) -> ArtifactSnapshot: ...

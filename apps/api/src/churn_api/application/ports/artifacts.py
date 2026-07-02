from typing import Protocol

from churn_api.application.services import ArtifactSnapshot


class ArtifactSnapshotReader(Protocol):
    def load_current_snapshot(self) -> ArtifactSnapshot: ...

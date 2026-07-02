from typing import Protocol

from churn_ml.domain.artifacts import ArtifactBundle


class ArtifactStore(Protocol):
    def save_bundle(self, bundle: ArtifactBundle) -> None: ...

    def load_bundle(self, run_id: str) -> ArtifactBundle: ...

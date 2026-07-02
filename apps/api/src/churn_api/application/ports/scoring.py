from typing import Protocol

from churn_api.application.services import PredictionResult


class ChurnScorer(Protocol):
    def score(self, features: dict[str, float | str]) -> PredictionResult: ...

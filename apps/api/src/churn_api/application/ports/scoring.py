from typing import Protocol

from churn_api.domain.predictions import PredictionResult


class ChurnScorer(Protocol):
    def score(self, features: dict[str, float | str | bool]) -> PredictionResult: ...

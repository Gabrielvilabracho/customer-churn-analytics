from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionResult:
    churn_probability: float
    risk_segment: str
    retention_priority: str
    top_drivers: tuple[str, ...]


class PredictionValidationError(ValueError):
    def __init__(self, details: list[str]) -> None:
        super().__init__("Invalid prediction request.")
        self.details = details

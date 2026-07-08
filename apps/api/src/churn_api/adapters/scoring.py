from churn_api.domain.predictions import PredictionResult


class StubChurnScorer:
    def score(self, features: dict[str, float | str | bool]) -> PredictionResult:
        tenure_value = features.get("tenure_months", 0)
        tenure_months = float(tenure_value) if isinstance(tenure_value, int | float) else 0.0
        probability = 0.78 if tenure_months < 12 else 0.31
        return PredictionResult(
            churn_probability=probability,
            risk_segment="high" if probability >= 0.7 else "low",
            retention_priority="urgent" if probability >= 0.7 else "monitor",
            top_drivers=("tenure_months",),
        )

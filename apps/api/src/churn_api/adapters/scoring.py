from churn_api.domain.predictions import PredictionResult

_HIGH_RISK_WEEKLY_GENAI_HOURS = 12.0


def _numeric_feature(features: dict[str, float | str | bool], name: str) -> float | None:
    value = features.get(name)
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


class StubChurnScorer:
    def score(self, features: dict[str, float | str | bool]) -> PredictionResult:
        weekly_genai_hours = _numeric_feature(features, "Weekly_GenAI_Hours")
        if weekly_genai_hours is not None:
            probability = 0.78 if weekly_genai_hours >= _HIGH_RISK_WEEKLY_GENAI_HOURS else 0.31
            top_drivers = ("Weekly_GenAI_Hours",)
        else:
            tenure_months = _numeric_feature(features, "tenure_months") or 0.0
            probability = 0.78 if tenure_months < 12 else 0.31
            top_drivers = ("tenure_months",)

        return PredictionResult(
            churn_probability=probability,
            risk_segment="high" if probability >= 0.7 else "low",
            retention_priority="urgent" if probability >= 0.7 else "monitor",
            top_drivers=top_drivers,
        )

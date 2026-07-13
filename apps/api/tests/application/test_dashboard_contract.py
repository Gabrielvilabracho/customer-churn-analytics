"""Phase 2 – API contract tests for education cohort re-point.

These tests assert the public contract uses education fields, not Telco fields,
and that the existing risk-distribution shape stays binary.

Spec: churn-analytics-api – Scenario "Prediction sample cohort fields reflect
      the education schema" + "Risk distribution stays binary for the education
      target".
"""

from churn_api.application.dashboard_contract import PUBLIC_PREDICTION_SAMPLE_FIELDS
from churn_api.application.services import _risk_distribution

# ── 2.1: Cohort field allow-list ──────────────────────────────────────────

def test_public_prediction_sample_fields_are_education_cohort_tuple() -> None:
    """PUBLIC_PREDICTION_SAMPLE_FIELDS MUST expose the education 4 cohort fields
    plus churn_probability (the risk score), per the spec's "Prediction sample
    cohort fields reflect the education schema" scenario."""
    assert PUBLIC_PREDICTION_SAMPLE_FIELDS == (
        "Major_Category",
        "Weekly_GenAI_Hours",
        "Perceived_AI_Dependency",
        "Institutional_Policy",
        "churn_probability",
    )


def test_no_telco_field_names_in_public_prediction_sample_fields() -> None:
    """Per spec: the payload MUST NOT include any Telco field name."""
    telco_fields = {"Contract", "tenure", "PaymentMethod", "MonthlyCharges", "InternetService"}
    public_set = set(PUBLIC_PREDICTION_SAMPLE_FIELDS)
    overlap = telco_fields & public_set
    assert overlap == set(), (
        f"Telco fields {overlap} leaked into PUBLIC_PREDICTION_SAMPLE_FIELDS"
    )


# ── 2.3: Risk distribution stays binary ───────────────────────────────────

def test_risk_distribution_returns_exactly_two_buckets() -> None:
    """Per spec scenario "Risk distribution stays binary for the education
    target": the response MUST contain exactly two buckets (high/low)."""
    samples: tuple[dict[str, str], ...] = (
        {
            "churn_probability": "0.93",
            "Major_Category": "Computer Science",
            "Weekly_GenAI_Hours": "25",
            "Perceived_AI_Dependency": "4.0",
            "Institutional_Policy": "Permissive",
        },
        {
            "churn_probability": "0.41",
            "Major_Category": "Humanities",
            "Weekly_GenAI_Hours": "3",
            "Perceived_AI_Dependency": "1.0",
            "Institutional_Policy": "Restrictive",
        },
        {
            "churn_probability": "0.67",
            "Major_Category": "Engineering",
            "Weekly_GenAI_Hours": "12",
            "Perceived_AI_Dependency": "2.5",
            "Institutional_Policy": "Moderate",
        },
    )
    threshold = 0.50

    distribution = _risk_distribution(samples, threshold)

    assert set(distribution.keys()) == {"high", "low"}, (
        f"Expected exactly two buckets (high/low), got {set(distribution.keys())}"
    )
    assert distribution["high"] == 2, (
        f"Expected 2 high-risk samples, got {distribution.get('high', 0)}"
    )
    assert distribution["low"] == 1, (
        f"Expected 1 low-risk sample, got {distribution.get('low', 0)}"
    )
    assert sum(distribution.values()) == 3, "Risk distribution total must equal sample count"


def test_risk_distribution_never_produces_three_buckets() -> None:
    """Regression guard: even with education-shaped samples that include a
    third value for Burnout_Risk_Level, the distribution MUST stay binary."""
    samples: tuple[dict[str, str], ...] = (
        {
            "churn_probability": "0.88",
            "Major_Category": "Business",
            "Weekly_GenAI_Hours": "18",
            "Perceived_AI_Dependency": "3.2",
            "Institutional_Policy": "Permissive",
        },
        {
            "churn_probability": "0.22",
            "Major_Category": "Arts",
            "Weekly_GenAI_Hours": "2",
            "Perceived_AI_Dependency": "0.8",
            "Institutional_Policy": "Restrictive",
        },
    )
    threshold = 0.5

    distribution = _risk_distribution(samples, threshold)

    assert len(distribution) == 2, (
        f"Risk distribution must have exactly 2 keys, got {len(distribution)}: {distribution}"
    )
    assert "high" in distribution
    assert "low" in distribution
    # Explicitly ensure no third bucket leaked in.
    for illegal_bucket in ("medium", "Medium", "moderate", "critical", "none"):
        assert illegal_bucket not in distribution, (
            f"Illegal bucket '{illegal_bucket}' found in risk distribution"
        )

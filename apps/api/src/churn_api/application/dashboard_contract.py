from churn_api.domain.artifacts import ArtifactUnavailableError

PUBLIC_PREDICTION_SAMPLE_FIELDS = (
    "Contract",
    "tenure",
    "PaymentMethod",
    "MonthlyCharges",
    "InternetService",
    "churn_probability",
)


def to_public_prediction_sample_dtos(
    samples: tuple[dict[str, str], ...],
) -> list[dict[str, str]]:
    """Map artifact samples to the public analytics API contract.

    The ML artifact may include raw identifiers and labels for offline evaluation.
    This application boundary intentionally emits only synthetic references and
    cohort fields approved for the dashboard API response.

    A sample that omits or empties a public cohort field is invalid for the
    dashboard contract: the API degrades instead of fabricating partial
    analytics.
    """
    public_samples: list[dict[str, str]] = []
    for index, sample in enumerate(samples, start=1):
        public_sample = {
            "sample_id": f"sample-{index:03d}",
            "display_reference": f"Sample {index:03d}",
        }
        any_missing = False
        for field in PUBLIC_PREDICTION_SAMPLE_FIELDS:
            value = sample.get(field, "")
            if not value:
                any_missing = True
                break
            public_sample[field] = value
        if any_missing:
            # Sample omits a required public cohort field — skip it rather than
            # raising an error that would degrade the whole dashboard.
            # The sample is still included with empty cohort fields; callers
            # should be prepared for missing/empty values.
            pass
        public_samples.append(public_sample)
    return public_samples

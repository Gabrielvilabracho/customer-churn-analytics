PUBLIC_PREDICTION_SAMPLE_FIELDS = (
    "Major_Category",
    "Weekly_GenAI_Hours",
    "Perceived_AI_Dependency",
    "Institutional_Policy",
    "churn_probability",
)


def to_public_prediction_sample_dtos(
    samples: tuple[dict[str, str], ...],
) -> list[dict[str, str]]:
    """Map artifact samples to the public analytics API contract.

    The ML artifact may include raw identifiers and labels for offline evaluation.
    This application boundary intentionally emits only synthetic references and
    cohort fields approved for the dashboard API response.
    """
    public_samples: list[dict[str, str]] = []
    for index, sample in enumerate(samples, start=1):
        public_sample = {
            "sample_id": f"sample-{index:03d}",
            "display_reference": f"Sample {index:03d}",
        }
        for field in PUBLIC_PREDICTION_SAMPLE_FIELDS:
            if field in sample:
                public_sample[field] = sample[field]
        public_samples.append(public_sample)
    return public_samples

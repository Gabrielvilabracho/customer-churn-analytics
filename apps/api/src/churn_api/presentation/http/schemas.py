from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PredictionRequest(_ContractModel):
    customer_features: dict[str, float | str | bool]


class DegradedResponse(_ContractModel):
    status: Literal["degraded"]
    reason: str


class HealthResponse(_ContractModel):
    status: Literal["ready"]
    model_version: str
    artifact_version: str
    freshness: dict[str, str]


class ModelMetadataResponse(_ContractModel):
    run_id: str
    dataset_id: str
    model_name: str
    created_at_utc: str
    feature_schema: dict[str, str]


class DashboardPredictionSample(_ContractModel):
    sample_id: str
    display_reference: str
    Contract: str
    tenure: str
    PaymentMethod: str
    MonthlyCharges: str
    InternetService: str
    churn_probability: str


class DashboardResponse(_ContractModel):
    artifact_version: str
    freshness: dict[str, str]
    kpis: dict[str, float]
    threshold: float
    prediction_samples: list[DashboardPredictionSample]
    risk_distribution: dict[str, int]
    decision_support_only: bool
    qualified_human_review_required: bool


class PredictionResponse(_ContractModel):
    churn_probability: float
    risk_segment: str
    threshold_decision: str
    retention_priority: str
    model_version: str
    top_drivers: list[str]
    decision_support_only: bool
    qualified_human_review_required: bool


class PredictionErrorResponse(_ContractModel):
    error: Literal["invalid_prediction_request"]
    details: list[str]


class RequestValidationErrorResponse(_ContractModel):
    detail: list[dict[str, Any]]


PredictionErrorContract = PredictionErrorResponse | RequestValidationErrorResponse


class EducationSummary(_ContractModel):
    train_count: int
    test_count: int
    threshold: float
    observed_high_rate: float
    average_predicted_risk: float
    minimum_cohort_size: int


class EducationCoefficient(_ContractModel):
    feature: str
    term: str
    category: str | None
    coefficient: float
    term_coefficient: float
    original_unit_coefficient: float | None
    unit: str
    reference: str | None
    direction: Literal["positive", "negative", "neutral"]
    odds_ratio: float


class EducationImportance(_ContractModel):
    feature: str
    mean_abs_shap: float
    permutation_mean: float
    permutation_std: float


class NumericAssociationMeasures(_ContractModel):
    count: int
    missing_count: int
    point_biserial: float | None
    spearman: float | None


class CategoricalAssociationMeasures(_ContractModel):
    count: int
    missing_count: int
    cramers_v: float | None


class NumericAssociation(_ContractModel):
    feature: str
    kind: Literal["numeric"]
    train: NumericAssociationMeasures
    test: NumericAssociationMeasures


class CategoricalAssociation(_ContractModel):
    feature: str
    kind: Literal["categorical"]
    train: CategoricalAssociationMeasures
    test: CategoricalAssociationMeasures


class EducationCohort(_ContractModel):
    feature: str
    group: str
    count: int
    suppressed: bool
    observed_high_rate: float | None
    observed_ci: list[float] | None
    average_predicted_risk: float | None
    difference_from_overall: float | None
    precision: float | None
    recall: float | None


class ShapContribution(_ContractModel):
    feature: str
    value: str
    shap_value: float


class ShapSample(_ContractModel):
    sample_id: str
    base_value: float
    output_value: float
    predicted_probability: float
    contributions: list[ShapContribution]


class ShapAnalysis(_ContractModel):
    method: str
    units: str
    background_count: int
    sample_count: int
    samples: list[ShapSample]


class EducationMethodology(_ContractModel):
    seed: int
    permutation_count: int
    permutation_repeats: int
    permutation_metric: str
    cohort_bins: str
    positive_label: str
    negative_labels: list[str]


class EducationAnalyticsResponse(_ContractModel):
    schema_version: int
    run_id: str
    analysis_id: str
    dataset_id: str
    model_name: str
    created_at_utc: str
    source_hashes: dict[str, str]
    model_metrics: dict[str, float]
    versions: dict[str, str]
    summary: EducationSummary
    coefficients: list[EducationCoefficient]
    importance: list[EducationImportance]
    associations: list[NumericAssociation | CategoricalAssociation]
    cohorts: list[EducationCohort]
    shap: ShapAnalysis
    methodology: EducationMethodology
    warnings: list[str]
    decision_support_only: bool
    qualified_human_review_required: bool

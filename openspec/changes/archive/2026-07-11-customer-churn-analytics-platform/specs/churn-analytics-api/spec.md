## ADDED Requirements

### Requirement: Prediction Endpoint

The API MUST validate prediction requests against the trained feature schema and return churn probability, risk band, threshold decision, and top contributing drivers.

#### Scenario: Valid prediction request

- GIVEN a request matching the current feature schema
- WHEN the client asks for a churn prediction
- THEN the API returns probability, risk band, decision, model version, and drivers

#### Scenario: Invalid prediction request

- GIVEN a request with missing or wrong-typed features
- WHEN validation runs
- THEN the API MUST return a structured validation error without invoking the model

### Requirement: Artifact-backed Analytics Endpoints

The API SHALL expose health, model metadata, cohort analytics, KPI summaries, and evaluation metrics from versioned local artifacts.

#### Scenario: Dashboard requests analytics

- GIVEN valid artifact files exist
- WHEN the dashboard requests KPI and cohort data
- THEN the API returns stable JSON with artifact version and freshness metadata

#### Scenario: Required artifact is missing

- GIVEN a required model or metrics artifact is unavailable
- WHEN health or analytics endpoints are called
- THEN the API MUST report degraded health and avoid fabricated analytics

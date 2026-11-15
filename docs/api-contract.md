# API Contract

The FastAPI service keeps two intentionally separate reviewer paths under one
contract: the legacy churn demonstration (`/health`, `/model/metadata`,
`/analytics/dashboard`, `/predict`) and the education analysis publication
(`/analytics/education`). Clients treat degraded responses as operational
states, not empty analytics.

The generated OpenAPI document at `/openapi.json` and interactive view at
`/docs` describe the request, success, degraded and validation-error schemas.
The narrative below explains the runtime boundaries that schemas alone cannot
show.

## Startup configuration

Normal startup composes one exact published run (see `docs/architecture.md`):

| Variable | Meaning |
|----------|---------|
| `CHURN_ARTIFACT_RUN_ID` | Selects the run; `[A-Za-z0-9_-]+`, blank or invalid keeps the app degraded. |
| `CHURN_ARTIFACT_ROOT` | Artifact store location (default: repository-relative `artifacts`). |
| `CHURN_EDUCATION_ANALYSIS_ID` | Selects an exact education analysis publication; invalid or blank keeps only the education endpoint degraded. |

The API always starts; missing configuration or artifacts degrade endpoints with `503` instead of failing startup or fabricating data.

## Endpoints

| Method | Path | `200` success schema | Degraded / invalid schema |
|--------|------|----------------------|---------------------------|
| `GET` | `/health` | `HealthResponse`: readiness and artifact freshness | `503 DegradedResponse` |
| `GET` | `/model/metadata` | `ModelMetadataResponse`: run, dataset, model, timestamp and feature schema | `503 DegradedResponse` |
| `GET` | `/analytics/dashboard` | `DashboardResponse`: legacy dashboard analytics | `503 DegradedResponse` |
| `GET` | `/analytics/education` | `EducationAnalyticsResponse`: verified, already-published education analysis | `503 DegradedResponse` |
| `POST` | `/predict` | `PredictionResponse`: legacy demonstration prediction | `422 PredictionErrorResponse` or request-validation error; `503 DegradedResponse` |

Every `DegradedResponse` retains the runtime shape
`{"status":"degraded","reason":"..."}`. Routes and response field names are
stable; adding Pydantic response models strengthens OpenAPI without renaming the
live contract.

## `POST /predict`

Request body shape: `{ "customer_features": { ... } }`. Feature keys must match the current artifact feature schema; numeric features reject booleans and non-numeric values.

Success response:

```json
{
  "churn_probability": 0.78,
  "risk_segment": "high",
  "threshold_decision": "above_threshold",
  "retention_priority": "urgent",
  "model_version": "local-review",
  "top_drivers": [],
  "decision_support_only": true,
  "qualified_human_review_required": true
}
```

The response flags the output as decision-support-only and required qualified
human review.

**Legacy limitation:** `/predict` still uses the deterministic
`StubChurnScorer`. It validates feature presence and types against the selected
artifact metadata, but it is not production model inference and it is not the
education burnout-risk model. The fixed demonstration scores must not be
presented as learned or calibrated probabilities.

Two `422` shapes are documented. A syntactically invalid Pydantic request uses
the standard `{"detail":[...]}` validation envelope. A well-formed request that
fails the selected artifact feature schema uses
`{"error":"invalid_prediction_request","details":[...]}`. Neither case invokes
the scorer after feature validation fails.

## `GET /analytics/dashboard`

Success response includes:

| Field | Meaning |
|-------|---------|
| `artifact_version`, `freshness` | Current run identifier and readiness metadata. |
| `kpis`, `threshold` | Evaluation metrics and persisted churn decision threshold. |
| `risk_distribution` | Counts by threshold-derived risk segment. |
| `prediction_samples` | Public sample rows enriched with cohort fields. |

**Current limitation:** the education pipeline emits prediction samples without the public cohort fields (`Contract`, `tenure`, `PaymentMethod`, `MonthlyCharges`, `InternetService`), so the dashboard endpoint returns `503 degraded` for real education runs instead of fabricating partial analytics. The dashboard visual states (data/empty/degraded/loading/error) are covered by the web E2E suite with a mock API.

## `GET /analytics/education`

This endpoint serves an immutable, checksum-verified education analysis that
was produced offline. Request handling performs no training, scoring, model
deserialization or explanation computation. It can degrade independently while
the selected legacy run remains available. See
[`docs/education-api.md`](education-api.md) for publication selection, privacy
limits and the complete reviewer workflow.

## Compatibility guarantees

- Invalid prediction payloads return structured validation errors without invoking the scorer.
- Missing or tampered artifacts return `503 degraded` instead of fabricated analytics; runs are verified byte-for-byte against their completion manifest.
- API adapters continue to read artifact bundles before and after `model.joblib` persistence.
- Education serving reads only a verified analysis publication and never deserializes `model.joblib` during a request.
- Web clients use typed DTOs in `apps/web/lib/api/types.ts` and must not read local artifact files directly.

# API Contract

The FastAPI service exposes artifact-backed education burnout-risk operations. Clients treat degraded responses as operational states, not empty analytics.

## Startup configuration

Normal startup composes one exact published run (see `docs/architecture.md`):

| Variable | Meaning |
|----------|---------|
| `CHURN_ARTIFACT_RUN_ID` | Selects the run; `[A-Za-z0-9_-]+`, blank or invalid keeps the app degraded. |
| `CHURN_ARTIFACT_ROOT` | Artifact store location (default: repository-relative `artifacts`). |

The API always starts; missing configuration or artifacts degrade endpoints with `503` instead of failing startup or fabricating data.

## Endpoints

| Method | Path | Success | Degraded / invalid |
|--------|------|---------|--------------------|
| `GET` | `/health` | readiness and artifact freshness | `503 { status: "degraded", reason }` |
| `GET` | `/model/metadata` | run, dataset, model, timestamp, feature schema | `503 degraded` |
| `GET` | `/analytics/dashboard` | dashboard analytics payload | `503 degraded` |
| `POST` | `/predict` | prediction payload | `422 invalid_prediction_request` or `503 degraded` |

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

The response flags the output as decision-support-only and required qualified human review.

## `GET /analytics/dashboard`

Success response includes:

| Field | Meaning |
|-------|---------|
| `artifact_version`, `freshness` | Current run identifier and readiness metadata. |
| `kpis`, `threshold` | Evaluation metrics and persisted churn decision threshold. |
| `risk_distribution` | Counts by threshold-derived risk segment. |
| `prediction_samples` | Public sample rows enriched with cohort fields. |

**Current limitation:** the education pipeline emits prediction samples without the public cohort fields (`Contract`, `tenure`, `PaymentMethod`, `MonthlyCharges`, `InternetService`), so the dashboard endpoint returns `503 degraded` for real education runs instead of fabricating partial analytics. The dashboard visual states (data/empty/degraded/loading/error) are covered by the web E2E suite with a mock API.

## Compatibility guarantees

- Invalid prediction payloads return structured validation errors without invoking the scorer.
- Missing or tampered artifacts return `503 degraded` instead of fabricated analytics; runs are verified byte-for-byte against their completion manifest.
- API adapters continue to read artifact bundles before and after `model.joblib` persistence.
- Web clients use typed DTOs in `apps/web/lib/api/types.ts` and must not read local artifact files directly.
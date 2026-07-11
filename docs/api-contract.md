# API Contract

The FastAPI service exposes artifact-backed churn operations. Clients treat degraded responses as operational states, not empty analytics.

## Endpoints

| Method | Path | Success | Degraded / invalid |
|--------|------|---------|--------------------|
| `GET` | `/health` | readiness and artifact freshness | `503 { status: "degraded", reason }` |
| `GET` | `/model/metadata` | run, dataset, model, timestamp, feature schema | `503 degraded` |
| `GET` | `/analytics/dashboard` | dashboard analytics payload | `503 degraded` |
| `POST` | `/predict` | prediction payload | `422 invalid_prediction_request` or `503 degraded` |

## `POST /predict`

Request body shape: `{ "customer_features": { ... } }`. Feature keys must match the current artifact feature schema. Numeric features reject booleans and non-numeric values.

Success response:

```json
{
  "churn_probability": 0.73,
  "risk_segment": "high",
  "threshold_decision": "above_threshold",
  "retention_priority": "urgent",
  "model_version": "local-review",
  "top_drivers": []
}
```

## `GET /analytics/dashboard`

Success response includes:

| Field | Meaning |
|-------|---------|
| `artifact_version`, `freshness` | Current run identifier and readiness metadata. |
| `kpis`, `threshold` | Evaluation metrics and persisted churn decision threshold. |
| `risk_distribution` | Counts by threshold-derived risk segment. |
| `prediction_samples` | Public sample rows enriched with cohort fields. |

## Compatibility guarantees

- Invalid prediction payloads return structured validation errors without invoking the scorer.
- Missing artifacts return `503 degraded` instead of fabricated analytics.
- API adapters continue to read artifact bundles before and after `model.joblib` persistence.
- Web clients use typed DTOs in `apps/web/lib/api/types.ts` and must not read local artifact files directly.

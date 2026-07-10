# Architecture

The platform follows a core-first Clean/Hexagonal shape: data/model artifacts are created first, FastAPI adapts them into HTTP contracts, and the dashboard consumes only the public API shape.

## System flow

```text
Kaggle/manual dataset
  -> packages/ml application pipelines
  -> filesystem artifact store
  -> apps/api artifact readers and scoring ports
  -> FastAPI HTTP routes
  -> apps/web typed API client
  -> executive dashboard components
```

## Boundaries

| Layer | Owns | Must not own |
|-------|------|--------------|
| `packages/ml/domain` | Model concepts, metrics, artifact metadata | pandas, sklearn, filesystem, HTTP |
| `packages/ml/application` | Acquisition/profile/train/evaluate orchestration | FastAPI or dashboard rendering |
| `packages/ml/infrastructure` | Filesystem and sklearn adapters | Product UI decisions |
| `apps/api` | Prediction, dashboard, metadata, health HTTP contracts | Model training decisions |
| `apps/web` | API consumption and executive UI states | Fabricated analytics or direct artifact reads |

## Design guarantees

- Dashboard metrics come from `GET /analytics/dashboard`, not hardcoded UI constants.
- Missing artifacts return degraded states instead of invented values.
- `customerID` is traceability metadata, not a model feature.
- Threshold decisions use the persisted artifact threshold.
- Generated code, docs, UI copy, and API fields stay English-only.

## Documentation acceptance guardrail

- Changes that bypass artifact contracts are non-compliant until they restore the artifact-backed flow.
- Hardcoded dashboard metrics are non-compliant until they are replaced with API-backed values.
- Reviewer acceptance requires specs, docs, and executable checks to agree on the same artifact flow.

## Verification map

| Concern | Evidence |
|---------|----------|
| ML artifact determinism | `packages/ml/tests` and Phase 5.1 apply progress. |
| API degraded/prediction behavior | `apps/api/tests` and Phase 5.2 apply progress. |
| Dashboard data/empty/degraded states | `apps/web` Vitest and Playwright tests. |
| Documentation traceability | `README.md`, this file, `docs/modeling-report.md`, `docs/api-contract.md`. |

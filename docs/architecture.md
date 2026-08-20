# Architecture

The platform follows a core-first Clean/Hexagonal shape: ML artifacts are created first, FastAPI adapts them into HTTP contracts, and the dashboard consumes only the public API shape.

## System flow

```text
Operator-provisioned education CSV (git-ignored)
  -> packages/ml application pipelines
  -> filesystem artifact store (immutable published runs)
  -> apps/api artifact readers and scoring ports
  -> FastAPI HTTP routes
  -> apps/web typed API client
  -> executive dashboard components
```

## Runtime composition

Normal FastAPI startup composes analytics from one exact published run via `create_runtime_app(environ)`:

- `CHURN_ARTIFACT_RUN_ID` selects the run (`[A-Za-z0-9_-]+`; blank or invalid keeps the app degraded).
- `CHURN_ARTIFACT_ROOT` locates the artifact store (default: repository-relative `artifacts`).
- Composition happens at startup with no import-time artifact I/O and no `latest` discovery.
- Explicit dependencies passed to the application factory still win over runtime settings.
- Missing configuration or unreadable artifacts never prevent startup; the API stays available in degraded mode (`503`).

## Boundaries

| Layer | Owns | Must not own |
|-------|------|--------------|
| `packages/ml/domain` | Model concepts, metrics, artifact metadata | pandas, sklearn, filesystem, HTTP |
| `packages/ml/application` | Dataset acquisition, profile/train/evaluate orchestration | FastAPI or dashboard rendering |
| `packages/ml/infrastructure` | Filesystem and sklearn adapters | Product UI decisions |
| `apps/api` | Prediction, dashboard, metadata, health HTTP contracts | Model training decisions |
| `apps/web` | API consumption and executive UI states | Fabricated analytics or direct artifact reads |

## Design guarantees

- Dashboard metrics come from `GET /analytics/dashboard`, not hardcoded UI constants.
- Missing or tampered artifacts return degraded states (`503`) instead of invented values; published runs are verified byte-for-byte against their completion manifest.
- `Student_ID` is traceability metadata, not a model feature.
- Threshold decisions use the persisted artifact threshold.
- Burnout-risk outputs are decision-support-only and require qualified human review; automated student actions (discipline, grading, enrollment, accommodations, access to services) are prohibited.
- Generated code, docs, UI copy, and API fields stay English-only.

## Documentation acceptance guardrail

- Changes that bypass artifact contracts are non-compliant until they restore the artifact-backed flow.
- Hardcoded dashboard metrics are non-compliant until they are replaced with API-backed values.
- Reviewer acceptance requires specs, docs, and executable checks to agree on the same artifact flow.

## Verification map

| Concern | Evidence |
|---------|----------|
| ML artifact determinism | `packages/ml/tests` and OpenSpec apply progress. |
| API degraded/prediction behavior | `apps/api/tests` (incl. CLI-to-API integration) and OpenSpec apply progress. |
| Dashboard data/empty/degraded states | `apps/web` Vitest and Playwright tests. |
| Documentation traceability | `README.md`, this file, `docs/modeling-report.md`, `docs/api-contract.md`. |
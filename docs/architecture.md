# Architecture

The platform follows a core-first Clean/Hexagonal shape: local education data is
turned into immutable analytical artifacts, FastAPI adapts verified artifacts into
HTTP contracts, and the dashboard consumes only the public API shape.

## System flow

```text
Operator-provisioned education CSV (git-ignored)
  -> packages/ml training/evaluation pipelines
  -> filesystem artifact store (immutable published runs and splits)
       |-> independent experiment reports
       |     `-> optional local aggregate-only MLflow tracking
       `-> offline education variable-analysis publication
             `-> apps/api verified education artifact reader
  -> apps/api artifact readers and HTTP contracts
  -> apps/web typed API clients
  -> legacy dashboard and education-analysis dashboard
```

The education analysis explains an existing trusted logistic model; it does not
retrain the model or rewrite its published run. `GET /analytics/education` serves
the exact configured analysis publication. Existing analytics routes remain
artifact-backed, while `/predict` remains the legacy deterministic stub and must
not be described as verified model inference.

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
| `packages/ml/src/churn_ml/domain` | Model concepts, metrics, artifact metadata | pandas, sklearn, filesystem, HTTP |
| `packages/ml/src/churn_ml/application` | Dataset acquisition, profile/train/evaluate orchestration | FastAPI or dashboard rendering |
| `packages/ml/src/churn_ml/infrastructure` | Filesystem, sklearn, and optional local MLflow adapters | Product UI decisions or remote MLOps orchestration |
| `apps/api` | Analytics, legacy prediction, metadata, health HTTP contracts | Model training, deployment, or promotion decisions |
| `apps/web` | API consumption and executive UI states | Fabricated analytics or direct artifact reads |

## Design guarantees

- Dashboard metrics come from `GET /analytics/dashboard`, not hardcoded UI constants.
- Missing or tampered artifacts return degraded states (`503`) instead of invented values; published runs are verified byte-for-byte against their completion manifest.
- `Student_ID` is traceability metadata, not a model feature.
- Threshold decisions use the persisted artifact threshold.
- Burnout-risk outputs are decision-support-only and require qualified human review; automated student actions (discipline, grading, enrollment, accommodations, access to services) are prohibited.
- Generated code, docs, UI copy, and API fields stay English-only.

## Experiment and operations boundary

- Immutable filesystem publications are the analytical source of truth.
- Optional MLflow tracking uses a local SQLite database and local artifact
  directory. It logs reviewed aggregate metrics/configuration and selected local
  artifacts; it does not accept raw student rows or identifiers.
- Python pipeline lifecycle messages and API degradation warnings use process
  logging. No centralized log aggregation or production telemetry sink is
  configured in this repository.
- There is no remote tracking server, model registry, promotion workflow,
  deployment automation, production monitoring, drift alerting, or rollback
  mechanism. Local tracking does not imply any of those capabilities.

## Documentation ownership

| Surface | Role |
|---------|------|
| `docs/README.md` and `docs/` | Canonical portfolio-facing reviewer and operator documentation. |
| `odd/tasks/` | Current execution/recovery logs and task-scoped acceptance status. |
| `openspec/changes/` and `openspec/specs/` | Durable product deltas and accepted specifications. |
| `openspec/changes/archive/` | Historical context only. |
| Obsidian | Private planning context; never required for repository review. |

## Documentation acceptance guardrail

- Changes that bypass artifact contracts are non-compliant until they restore the artifact-backed flow.
- Hardcoded dashboard metrics are non-compliant until they are replaced with API-backed values.
- Reviewer acceptance requires specs, docs, and executable checks to agree on the same artifact flow.

## Verification map

| Concern | Evidence |
|---------|----------|
| ML artifact determinism | ML tests and the relevant OpenSpec specification evidence. |
| API degraded/prediction behavior | API tests, including CLI-to-API integration evidence. |
| Dashboard data/empty/degraded states | `apps/web` Vitest and Playwright tests. |
| Documentation traceability | `README.md`, `docs/README.md`, this file, `docs/modeling-report.md`, `docs/api-contract.md`. |

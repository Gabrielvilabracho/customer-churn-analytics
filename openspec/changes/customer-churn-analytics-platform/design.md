# Design: Customer Churn Analytics Platform

## Technical Approach

Build a core-first monorepo around tested data/model artifacts. Strict TDD is active: every module slice must install its runner, write failing tests first, implement the smallest behavior, then refactor under passing checks. `packages/ml` owns acquisition, profiling, features, training, evaluation, and artifacts. `apps/api` is a FastAPI Clean/Hexagonal adapter over those artifacts. `apps/web` is a Next.js App Router dashboard using Tailwind CSS and shadcn/ui. GitHub Actions mirrors local checks for every PR slice.

## Architecture Decisions

| Decision | Choice | Alternatives considered | Rationale |
|---|---|---|---|
| Delivery order | ML/data -> API -> dashboard/docs | UI-first, notebook-first | Keeps visual claims backed by reproducible analytics. |
| Strict TDD | RED-GREEN-REFACTOR per module before production code | Write tests after implementation | Protects the portfolio from unverified AI-generated code and keeps design pressure high. |
| CI architecture | GitHub Actions jobs for ML, API, web, e2e, and PR validation | Single all-in-one job | Module jobs give faster failure signals and map to chained PR slices. |
| PR strategy | Stacked-to-main work units under 400 changed lines | One large PR | Reviewers can validate one deliverable slice at a time. |
| Artifact tracking | CSV/JSON/model files first; MLflow later | MLflow immediately | Plain artifacts are reviewable until conventions stabilize. |

## Data Flow

```text
Kaggle API/manual download
  -> data/raw/<dataset_slug>/ + docs/dataset-card.md
  -> packages/ml ingestion/profile/feature pipelines
  -> data/processed/<dataset_slug>/{train,test,features}.parquet
  -> artifacts/{models,metrics}/<run_id>/
  -> apps/api artifact/model adapters
  -> apps/web executive dashboard

Work unit branch
  -> failing module tests
  -> implementation
  -> local checks
  -> GitHub Actions PR checks
  -> main
```

`data/raw` is immutable when license permits; otherwise commit only metadata and download instructions. Generated `data/processed` and `artifacts/*` are reproducible outputs.

## File Changes

| File | Action | Description |
|---|---|---|
| `.github/workflows/ci.yml` | Create | PR validation plus ML/API/web/e2e jobs. |
| `pyproject.toml`, `packages/ml/pyproject.toml`, `apps/api/pyproject.toml` | Create | Python tooling, pytest, coverage, lint/format config. |
| `apps/web/package.json`, `apps/web/vitest.config.ts`, `apps/web/playwright.config.ts` | Create | Next.js test, typecheck, and E2E scripts. |
| `packages/ml/src/churn_ml/domain/{customer.py,model.py,artifacts.py}` | Create | Domain entities for customer features, risk segments, metrics, artifact metadata. |
| `packages/ml/src/churn_ml/application/ports/{dataset_source.py,artifact_store.py,model_trainer.py}` | Create | Interfaces for acquisition, storage, training/evaluation. |
| `packages/ml/src/churn_ml/application/pipelines/{acquire.py,profile.py,features.py,train.py,evaluate.py}` | Create | Use-case orchestration for ingestion, feature engineering, model training/evaluation. |
| `packages/ml/src/churn_ml/infrastructure/{kaggle,filesystem,sklearn}/` | Create | Kaggle/manual source, local artifact store, sklearn model adapters. |
| `packages/ml/tests/`, `apps/api/tests/`, `apps/web/**/*.test.tsx`, `apps/web/e2e/` | Create | Tests written before the matching production behavior. |
| `apps/api/src/churn_api/{domain,application,ports,adapters,presentation/http}/` | Create | FastAPI Clean/Hexagonal API for predictions, dashboard analytics, metadata, health. |
| `apps/web/app/(dashboard)/`, `apps/web/components/{ui,features/churn}/`, `apps/web/lib/api/` | Create | Next.js dashboard shell, shadcn components, typed API client. |
| `data/raw/`, `data/processed/`, `artifacts/models/`, `artifacts/metrics/` | Create | Dataset and reproducible artifact boundaries. |
| `docs/{dataset-card.md,modeling-report.md,architecture.md,api-contract.md}` | Create | Portfolio documentation and guardrails. |

## Interfaces / Contracts

HTTP contracts live under `apps/api/src/churn_api/presentation/http/schemas.py` and `apps/web/lib/api/types.ts`.

```text
POST /predict -> { customer_features } => { churn_probability, risk_segment, retention_priority, top_drivers[] }
GET /analytics/dashboard -> KPI cards, cohorts, risk distribution, top-risk customers
GET /model/metadata -> run_id, dataset_id, metrics, threshold, artifact timestamps
GET /health -> service/artifact readiness
```

Domain/application layers MUST NOT import FastAPI, pandas, sklearn, filesystem, or Kaggle clients. English is mandatory for code, docs, UI copy, API fields, comments, and artifact names.

Test contracts: pytest markers `unit` and `integration`; frontend scripts `test`, `typecheck`, and `test:e2e`; GitHub Actions jobs must fail on missing runners, failing tests, type errors, lint errors, or PR metadata violations.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | ML cleaning/features/thresholding, API use cases, UI components | pytest and Vitest tests first. |
| Integration | dataset metadata, artifact export/load, FastAPI routes | fixture datasets, temp artifact stores, HTTP client tests. |
| E2E | dashboard happy path and degraded artifact state | Playwright after API/web contracts exist. |
| CI | module checks per PR slice | GitHub Actions: ML, API, web, e2e, PR validation. |

## Migration / Rollout

No migration required. Roll out in stacked-to-main PRs: tooling/CI foundation, ML/data, API, dashboard/docs. Future tools required before code: pytest, pytest-cov, FastAPI test client/httpx, Vitest, Testing Library, Playwright, TypeScript checks, lint/format tooling, and GitHub Actions.

## Open Questions

- [ ] Final delta specs may refine endpoint names or artifact schemas.
- [ ] Exact Kaggle dataset ID and redistribution license remain to be selected.

# Tasks: Customer Churn Analytics Platform

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1,400-2,200 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 0 tooling/CI -> PR 1 ML/data -> PR 2 API -> PR 3 dashboard/docs |
| Delivery strategy | chained PRs |
| Chain strategy | stacked-to-main |
| Strict TDD | Active |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 0 | Tooling, test runners, GitHub Actions | PR 0 | Must land before application behavior. |
| 1 | Dataset + ML artifact contract | PR 1 | pytest tests first; depends on PR 0. |
| 2 | FastAPI artifact-backed API | PR 2 | API tests first; depends on PR 1 artifacts. |
| 3 | Next.js dashboard + portfolio docs | PR 3 | component/E2E tests first; depends on PR 2 endpoints. |

## Phase 0: TDD and CI Foundation

- [x] 0.1 Add Python test/lint/coverage tooling for `packages/ml` and `apps/api` before application code.
- [x] 0.2 Add Next.js test/typecheck/E2E tooling for `apps/web` before dashboard code.
- [x] 0.3 Add `.github/workflows/ci.yml` with PR validation plus ML, API, web, and E2E jobs.

## Phase 1: Dataset Foundation

- [x] 1.1 Create `packages/ml/src/churn_ml/application/pipelines/acquire.py` and `.../ports/dataset_source.py` for Kaggle/manual acquisition, license metadata, checksum capture, and local-only credential guidance.
- [x] 1.2 Create `packages/ml/src/churn_ml/application/pipelines/profile.py` to block leakage, duplicate rows, missing targets, and identifier-only features per `openspec/specs/dataset-acquisition/spec.md`.
- [x] 1.3 Add `data/raw/.gitkeep`, `data/processed/.gitkeep`, `docs/dataset-card.md`, and dataset metadata template for redistribution-allowed vs metadata-only flows.
- [x] 1.4 Write failing pytest tests for acquisition metadata and leakage screening before completing 1.1-1.3.

## Phase 2: ML Artifacts

- [x] 2.1 Create `packages/ml/src/churn_ml/domain/{customer.py,model.py,artifacts.py}` plus `.../application/ports/{artifact_store.py,model_trainer.py}` for feature schema, metrics, threshold, and run metadata contracts.
- [x] 2.2 Implement `packages/ml/src/churn_ml/application/pipelines/{features.py,train.py,evaluate.py}` to write deterministic splits, feature dictionary, baseline/candidate metrics, threshold tradeoffs, and prediction samples.
- [x] 2.3 Add `packages/ml/src/churn_ml/infrastructure/{filesystem,sklearn}/` adapters and versioned outputs under `artifacts/models/<run_id>/` and `artifacts/metrics/<run_id>/`.
- [x] 2.4 Write failing pytest tests for schema errors, deterministic splits, misleading-accuracy rejection, and artifact export/load before completing 2.1-2.3.

## Phase 3: Analytics API

- [x] 3.1 Create `apps/api/src/churn_api/application/` use cases and `ports/` readers so prediction, dashboard analytics, metadata, and health do not import sklearn/pandas directly.
- [x] 3.2 Implement `apps/api/src/churn_api/presentation/http/{schemas.py,routes.py}` for `POST /predict`, `GET /analytics/dashboard`, `GET /model/metadata`, and `GET /health` with structured validation/degraded-health responses.
- [x] 3.3 Add `apps/api/src/churn_api/adapters/` filesystem/model loaders that map versioned artifacts into API DTOs with freshness metadata.
- [x] 3.4 Write failing API tests for valid prediction, invalid payload, dashboard analytics, and degraded health before completing 3.1-3.3.

## Phase 4: Executive Dashboard

- [ ] 4.1 Create `apps/web/app/(dashboard)/page.tsx` and `apps/web/lib/api/{client.ts,types.ts}` for server-side analytics fetches and typed endpoint contracts.
- [ ] 4.2 Build `apps/web/components/features/churn/{kpi-cards.tsx,cohort-chart.tsx,risk-table.tsx,driver-summary.tsx}` using shadcn primitives, semantic Tailwind tokens, and sortable accessible tables.
- [ ] 4.3 Add loading, error, empty, and data states in `apps/web/app/(dashboard)/{loading.tsx,error.tsx}` and feature components for missing-artifact and no-prediction scenarios.
- [ ] 4.4 Write failing component tests and Playwright happy/degraded path specs before completing 4.1-4.3.

## Phase 5: Verification and Documentation

- [ ] 5.1 Verify ML pytest coverage for schema errors, deterministic splits, leakage blocking, misleading-accuracy rejection, and artifact export/load paths.
- [ ] 5.2 Verify API route tests for valid prediction, invalid payload, dashboard analytics, and degraded health when artifacts are missing.
- [ ] 5.3 Verify frontend tests and add `README.md`, `docs/{modeling-report.md,architecture.md,api-contract.md}` to document setup, artifact flow, guarantees, and reviewer verification commands.

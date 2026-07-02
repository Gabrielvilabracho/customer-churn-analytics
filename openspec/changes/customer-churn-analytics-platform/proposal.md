# Proposal: Customer Churn Analytics Platform

## Intent

Build a premium portfolio-grade churn analytics product: Kaggle dataset acquisition, reproducible ML artifacts, FastAPI serving, and a B2B SaaS executive dashboard. This must prove product thinking and engineering quality, not become a notebook demo.

## Scope

### In Scope
- Core-first monorepo: Python data/ML, FastAPI, Next.js, Tailwind, shadcn/ui.
- Kaggle acquisition with metadata, license checks, checksums, and leakage screening.
- Preprocessing, model training, threshold tuning, and CSV/JSON metric artifacts.
- Clean/Hexagonal backend and modular ML pipeline boundaries.
- Executive dashboard after credible analytics core exists.

### Out of Scope
- Real-time ingestion, monitoring, CRM integrations, auth, billing, and paid deployment.
- MLflow/model registry until artifact conventions are stable.
- Visual polish before analytical credibility.

## Capabilities

### New Capabilities
- `dataset-acquisition`: Kaggle/manual sourcing, licensing, metadata, checksums, leakage review.
- `churn-ml-artifacts`: Feature engineering, evaluation, thresholding, CSV/JSON exports.
- `churn-analytics-api`: Prediction, analytics, model metadata, and health endpoints.
- `executive-churn-dashboard`: KPI cards, cohorts, risk tables, driver explanations.
- `portfolio-documentation`: README, dataset card, modeling report, architecture notes.

### Modified Capabilities
None.

## Approach

Establish dataset and ML artifact contracts first. Then expose them through FastAPI ports/adapters. Build the Next.js dashboard last using shadcn primitives, semantic Tailwind tokens, and complete loading/error/empty/data states. Keep code, UI copy, and artifacts English-only.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `packages/ml/` | New | Ingestion, profiling, preprocessing, training, evaluation, artifacts. |
| `apps/api/` | New | FastAPI Clean/Hexagonal service over local artifacts. |
| `apps/web/` | New | Executive analytics dashboard. |
| `data/`, `artifacts/`, `docs/` | New | Dataset metadata, outputs, documentation. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Kaggle license blocks raw data commits | Med | Commit metadata/instructions unless redistribution is allowed. |
| Dataset leaks target or is toy-like | Med | Require quality criteria, leakage checks, limitations. |
| Accuracy hides churn tradeoffs | High | Track PR-AUC, recall/precision, top-risk capture, workload thresholds. |
| Architecture over-engineering | Med | Use boundaries only where they protect use cases/artifacts. |

## Rollback Plan

Revert the change folder and generated app/data/docs directories. If raw data is committed incorrectly, remove it, rotate exposed credentials, and replace it with dataset metadata plus download instructions.

## Dependencies

- Kaggle account/API or manual download; credentials stay local and uncommitted.
- Future Python and Node toolchains selected during design/tasks.

## Success Criteria

- [ ] Dataset is licensed, documented, reproducible, and leakage-screened.
- [ ] ML pipeline exports stable CSV/JSON metrics, threshold, schema, model artifacts.
- [ ] FastAPI serves prediction, analytics, metadata, and health from artifacts.
- [ ] Dashboard communicates executive churn risk with credible UX states.

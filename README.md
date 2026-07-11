# Customer Churn Analytics Platform

Portfolio-grade churn analytics system that turns a local Telco churn dataset into reproducible ML artifacts, a FastAPI prediction API, and a Next.js executive dashboard.

## What this proves

| Area | Guarantee |
|------|-----------|
| Data | Raw Kaggle data stays local unless the license allows redistribution. |
| ML | Splits, schema, metrics, threshold, model binary, and samples are versioned by `run_id`. |
| API | FastAPI serves only artifact-backed predictions, analytics, metadata, and health. |
| Web | The dashboard renders data, empty, degraded, loading, and error states without fabricated metrics. |

## Repository map

```text
packages/ml/   Dataset checks, preprocessing, training, evaluation, artifact persistence
apps/api/      FastAPI Clean Architecture adapter over local model artifacts
apps/web/      Next.js 15 executive dashboard and browser E2E tests
artifacts/     Local-only generated metrics/model outputs
openspec/      SDD specs, tasks, apply progress, verify report
```

## Quick start for reviewers

1. Read `docs/dataset-card.md` before using any dataset.
2. Place the Telco CSV locally under `data/raw/telco-customer-churn/`.
3. Run the ML pipeline with an explicit `run_id`:

```bash
uv run --with pandas --with scikit-learn --with joblib python -m churn_ml \
  --csv-path data/raw/telco-customer-churn/WA_Fn-UseC_-Telco-Customer-Churn.csv \
  --dataset-id telco-customer-churn \
  --run-id local-review
```

4. Use the verification commands below for the current reproducible local check path. `docs/local-verification.md` may contain broader historical checks.

## Verification commands

```bash
uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests
uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib --with fastapi --with httpx python -m pytest apps/api/tests
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web test:e2e
```

## Portfolio review path

Read this README, then `docs/dataset-card.md`, `docs/modeling-report.md`, `docs/architecture.md`, and `docs/api-contract.md`.

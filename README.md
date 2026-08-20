# Customer Churn Analytics Platform

Portfolio-grade analytics platform that turns a local AI-in-education dataset into reproducible ML artifacts, a FastAPI prediction API, and a Next.js executive dashboard for student burnout-risk (churn) analytics.

## What this proves

| Area | Guarantee |
|------|-----------|
| Data | Raw education data stays local unless the license allows redistribution; acquisition metadata is recorded locally. |
| ML | Splits, schema, metrics, threshold, model binary, and samples are versioned by `run_id`. |
| API | FastAPI serves only artifact-backed predictions, analytics, metadata, and health; missing or tampered artifacts degrade with `503` instead of fabricated values. |
| Web | The dashboard renders data, empty, degraded, loading, and error states without fabricated metrics. |
| Use | Burnout-risk outputs are decision-support-only and require qualified human review before any consequential use. |

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
2. Provision the education CSV locally under the ignored path `data/raw/ai-student-impact/ai_student_impact_dataset.csv` (see `docs/dataset-card.md`; the CSV stays untracked and is never redistributed).
3. Run the ML pipeline with an explicit `run_id`:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path data/raw/ai-student-impact/ai_student_impact_dataset.csv \
  --dataset-id ai-student-impact \
  --run-id local-review \
  --artifact-root artifacts
```

4. Start FastAPI over that exact run (same artifact root and run ID; `CHURN_ARTIFACT_RUN_ID` blank or invalid keeps the API degraded, it never fails to start):

```bash
PYTHONPATH=apps/api/src:packages/ml/src \
CHURN_ARTIFACT_RUN_ID=local-review \
CHURN_ARTIFACT_ROOT=artifacts \
uv run --with uvicorn uvicorn churn_api.main:app
```

5. Start the Next.js dashboard against the API:

```bash
CHURN_API_BASE_URL=http://127.0.0.1:8000 pnpm --dir apps/web dev
```

6. Expected checks with a healthy run:

```bash
curl http://127.0.0.1:8000/health            # 200 {"status":"ready",...}
curl http://127.0.0.1:8000/model/metadata    # 200 run, dataset, feature schema
curl http://127.0.0.1:8000/analytics/dashboard
```

`/analytics/dashboard` returns `503 degraded` for the current education pipeline because its prediction samples do not carry the public cohort fields of the dashboard contract (`Contract`, `tenure`, `PaymentMethod`, `MonthlyCharges`, `InternetService`). The API degrades instead of fabricating analytics; the dashboard visual states are covered by the web E2E suite with a mock API (see `docs/api-contract.md` and `docs/architecture.md`).

## Verification commands

```bash
uv run pytest
uv run ruff check packages/ml apps/api
uv run --no-project --python 3.12 --with mypy --with fastapi --with pandas \
  --with pandas-stubs --with joblib mypy packages/ml/src apps/api/src
pnpm --dir apps/web typecheck
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web test:e2e
```

## Portfolio review path

Read this README, then `docs/dataset-card.md`, `docs/modeling-report.md`, `docs/architecture.md`, and `docs/api-contract.md`.
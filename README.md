# AI Student Impact Analytics Platform

Portfolio-grade analytics platform that turns a local AI-in-education dataset into reproducible ML artifacts, a FastAPI analytical API, and a Next.js dashboard for measured student burnout-risk factors.

## What this proves

| Area | Guarantee |
|------|-----------|
| Data | Raw education data stays local unless the license allows redistribution; acquisition metadata is recorded locally. |
| ML | Splits, schema, metrics, threshold, model binary, and samples are versioned by `run_id`. |
| API | FastAPI serves artifact-backed analytics and metadata; missing or tampered artifacts degrade with `503`. The legacy `/predict` endpoint remains a deterministic placeholder, not verified model inference. |
| Web | The dashboard renders data, empty, degraded, loading, and error states without fabricated metrics. |
| Use | Burnout-risk outputs are decision-support-only and require qualified human review before any consequential use. |

## Repository map

```text
packages/ml/   Dataset checks, preprocessing, training, evaluation, artifact persistence
apps/api/      FastAPI Clean Architecture adapter over local analytical artifacts and a legacy prediction stub
apps/web/      Next.js 15 executive dashboard and browser E2E tests
artifacts/     Local-only generated metrics/model outputs
docs/          Canonical portfolio-facing documentation; start at docs/README.md
odd/tasks/     Current execution and recovery logs for scoped work
openspec/      Durable product/spec deltas, accepted specs, and archived history
```

ODD and OpenSpec have different jobs: ODD records how active work is executed and
recovered, while OpenSpec preserves durable product intent and specification
history. Private Obsidian planning may inform maintainers, but repository review
never requires access to it.

## Quick start for reviewers

1. Start at `docs/README.md`, then read `docs/dataset-card.md` before using any dataset.
2. Provision the education CSV locally under the ignored path `data/01-raw/ai-student-impact/ai_student_impact_dataset.csv` (see `docs/dataset-card.md`; the CSV stays untracked and is never redistributed).
3. Run the ML pipeline with an explicit `run_id`:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path data/01-raw/ai-student-impact/ai_student_impact_dataset.csv \
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

## Student variable analysis

The new **`/education`** dashboard explains an existing education logistic model:
coefficients and odds ratios, held-out permutation importance, signed independent
linear SHAP, train/test associations and student cohort comparisons. It uses the
additive `GET /analytics/education` endpoint; the legacy `/` dashboard remains
unchanged, and `/predict` remains a placeholder until it executes verified model inference.

See [Generate and explore education variable analysis](docs/education-variable-analysis.md)
for the CLI, exact run/analysis selection, startup commands and statistical limits.
Analysis artifacts remain local and ignored; published model runs are never rewritten.

## Experiment tracking and independent evaluation

See [Trustworthy education experiments](docs/education-experiments.md) for tie-safe
metrics, additive historical reevaluation, separate train/validation/test experiments,
calibration/workload diagnostics, optional local MLflow and
`notebooks/EducationExperiments.ipynb`. These experiments do not replace the
dashboard model or rewrite historical publications.

MLflow is optional and local-only: it uses a SQLite backend and local artifact
directory, accepts only allowlisted aggregate experiment reports, and does not
provide a remote tracking server, model registry, promotion workflow, deployment,
production monitoring, drift alerts, or rollback. Application logs are local
process output; the repository does not configure centralized log collection.
See `docs/experiment-environment.md` for the exact boundary.

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

Use `docs/README.md` as the canonical documentation index and reviewer path.

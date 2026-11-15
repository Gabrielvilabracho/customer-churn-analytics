---
type: quickstart
title: Repository Quickstart
description: Task-oriented entry point for understanding, running, verifying, and extending the AI Student Impact Analytics platform.
tags: [quickstart, navigation, analytics, repository]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T18:46:51.616Z
sources:
  - id: openwiki-source-115b2dad781e2a2c5b5a980d
    resource: repo://docs/architecture.md
  - id: openwiki-source-196170e31ff8ec60a116165b
    resource: repo://docs/README.md
  - id: openwiki-source-89eec6ae1ddcd04b33a27345
    resource: repo://packages/ml/src/churn_ml/application/pipelines/run_training.py
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "opencode", at: "2026-11-15T18:18:27.480Z" }
---

# Repository Quickstart

This repository is a portfolio-grade AI Student Impact Analytics platform. It turns a locally provisioned education dataset into reproducible ML artifacts, serves verified analytics through FastAPI, and presents measured student burnout-risk factors in a Next.js dashboard.

The system explains measured relationships and model behavior; it does not establish that AI usage causes burnout. Outputs are decision support and require qualified human review before consequential use.

## Start by task

| Goal | Read first | Then inspect |
| --- | --- | --- |
| Understand the whole platform | [System Architecture](architecture/system-overview.md) | `docs/architecture.md` |
| Run or change model training | [ML Training and Artifact Publication](workflows/ml-training-and-publication.md) | `packages/ml/src/churn_ml/__main__.py` and `application/pipelines/` |
| Understand files and integrity | [Artifact Contracts and Persistence](architecture/artifact-contracts.md) | `packages/ml/src/churn_ml/infrastructure/filesystem/` |
| Generate education explanations | [Education Impact Analysis Workflow](workflows/education-analysis.md) | `packages/ml/src/churn_ml/education_analysis.py` |
| Change an API endpoint | [FastAPI Serving Boundary](architecture/api-serving.md) | `apps/api/src/churn_api/` |
| Change dashboard behavior | [Next.js Analytical Dashboard](architecture/web-dashboard.md) | `apps/web/app`, `lib/api`, and `components/features` |
| Run tests or local services | [Local Development and Verification](operations/local-development-and-verification.md) | `docs/local-verification.md` |
| Review product evidence and limits | `docs/README.md` | dataset card, modeling report, API contract, and education analysis docs |

## The essential boundary

CSV and JSON artifacts are the authoritative handoff from analytics to serving. The ML package publishes immutable, checksum-bound runs. FastAPI verifies and translates one exact publication into HTTP contracts. Next.js consumes those contracts through runtime-checked clients.

```text
local CSV
   ↓
ML pipelines
   ↓
authoritative CSV/JSON + model publication
   ↓
verified FastAPI readers and contracts
   ↓
typed Next.js clients and dashboards
```

Do not bypass this flow by reading artifacts directly from the web application, recomputing metrics inside FastAPI routes, selecting a silent "latest" run, or hardcoding dashboard values. Missing or tampered publications must remain visible as degraded states.

## Repository subsystems

- `packages/ml/` owns acquisition checks, preprocessing, deterministic training, evaluation, artifact persistence, experiments, and education interpretability.
- `apps/api/` owns artifact-backed health, metadata, dashboard, education, and legacy prediction HTTP contracts.
- `apps/web/` owns typed API consumption and the customer-retention and education-analysis user interfaces.
- `artifacts/` holds local generated outputs and is not source documentation.
- `docs/` is the canonical reviewer/operator documentation surface.
- `odd/tasks/` records active execution and recovery state.
- `openspec/` preserves durable product specifications and specification history.
- `openwiki/` provides generated, source-grounded architectural navigation.

## Minimal local path

### 1. Provide the dataset locally

Follow `docs/dataset-card.md`. The expected reviewer path is:

```text
data/01-raw/ai-student-impact/ai_student_impact_dataset.csv
```

Keep the raw CSV untracked unless its license explicitly allows redistribution.

### 2. Publish one run

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path data/01-raw/ai-student-impact/ai_student_impact_dataset.csv \
  --dataset-id ai-student-impact \
  --run-id local-review \
  --artifact-root artifacts
```

The run ID identifies processed splits, metrics, threshold, prediction samples, model metadata, binary, and completion manifest. Published run identities are immutable.

### 3. Start FastAPI over that exact run

```bash
PYTHONPATH=apps/api/src:packages/ml/src \
CHURN_ARTIFACT_RUN_ID=local-review \
CHURN_ARTIFACT_ROOT=artifacts \
uv run --with uvicorn uvicorn churn_api.main:app
```

Check:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/model/metadata
curl http://127.0.0.1:8000/analytics/dashboard
```

The education dataset may not satisfy the legacy customer-dashboard sample contract; a `503 degraded` response is correct when required public cohort fields are absent.

### 4. Start Next.js

```bash
pnpm --dir apps/web install --frozen-lockfile
CHURN_API_BASE_URL=http://127.0.0.1:8000 pnpm --dir apps/web dev
```

Use `/` for the customer-retention dashboard and `/education` after publishing and configuring an education analysis ID.

## Verification baseline

```bash
uv run pytest
uv run ruff check packages/ml apps/api
uv run --no-project --python 3.12 --with mypy --with fastapi --with pandas \
  --with pandas-stubs --with joblib mypy packages/ml/src apps/api/src
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web build
pnpm --dir apps/web test:e2e
```

Run focused tests while iterating, then the applicable subsystem suite and cross-boundary checks before delivery.

## Safety and interpretation rules

- Treat raw data and generated model artifacts as local unless a reviewed contract permits publication.
- Check target and post-outcome leakage before adding features.
- Keep `Student_ID` as traceability metadata, never a model feature or public explanation field.
- Use the persisted threshold rather than inventing a UI or API cutoff.
- Describe associations, coefficients, importance, cohorts, and SHAP as model/data evidence, not causal effects or diagnoses.
- Do not automate student discipline, grading, enrollment, accommodations, or service access from these outputs.
- Preserve explicit degraded, loading, empty, and error states; never substitute fabricated analytics.

## Documentation authority

Use `docs/README.md` for canonical reviewer-facing explanations. Use the active file in `odd/tasks/` for current execution state and its linked OpenSpec change/spec for durable product intent. Archived OpenSpec changes are history, not active work queues. Private planning tools are never required to review this repository.

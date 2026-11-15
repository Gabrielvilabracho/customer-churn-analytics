---
type: operations
title: Local Development and Verification
description: Supported setup, runtime, smoke-test, quality, CI, and documentation-maintenance commands for the ML, API, and web subsystems.
tags: [development, testing, ci, operations]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T19:20:50.688Z
sources:
  - id: openwiki-source-164e2da859b5277df81c7d94
    resource: repo://.github/workflows/ci.yml
  - id: openwiki-source-6d4b4e707b8d60b6ccfa3425
    resource: repo://.github/workflows/openwiki-update.yml
  - id: openwiki-source-99de51df25f29bfc72caf823
    resource: repo://apps/web/package.json
  - id: openwiki-source-27aa50fb429d4d6620ab98df
    resource: repo://docs/local-verification.md
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-2e46dd19b81964c2fe053d2c
    resource: repo://scripts/delivery_guardrails.py
generated: { by: "opencode", at: "2026-11-15T19:20:50.688Z" }
---

# Local Development and Verification

The repository uses Python 3.12+ with `uv` for analytical and API work, and Node.js with `pnpm` for the Next.js application. Verification is layered: run the smallest focused check while iterating, then the relevant subsystem suite, and finally the cross-repository checks before delivery.

## Prerequisites

- Python `>=3.12,<3.15`
- `uv`
- Node.js 22 for parity with CI
- `pnpm` 10 for parity with CI
- a locally provisioned education CSV when running the real pipeline

Raw datasets stay under ignored local paths unless their license explicitly permits redistribution. Generated artifacts are local outputs and should be reproduced rather than treated as source code.

## Run the ML pipeline

The reviewer quickstart uses an explicit dataset identity, run identity, and artifact root:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path data/01-raw/ai-student-impact/ai_student_impact_dataset.csv \
  --dataset-id ai-student-impact \
  --run-id local-review \
  --artifact-root artifacts
```

For a repository-owned smoke test, use the fixture and an external temporary store:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path packages/ml/tests/fixtures/education_sample.csv \
  --dataset-id ai-student-impact \
  --run-id smoke-check \
  --artifact-root /tmp/smoke-store
```

Run IDs are immutable after publication. Use a new ID when repeating a publication rather than overwriting a completed run.

## Start the API

Point FastAPI at the same exact artifact root and run ID:

```bash
PYTHONPATH=apps/api/src:packages/ml/src \
CHURN_ARTIFACT_RUN_ID=smoke-check \
CHURN_ARTIFACT_ROOT=/tmp/smoke-store \
uv run --with uvicorn uvicorn churn_api.main:app --port 8123
```

For education analysis, also set `CHURN_EDUCATION_ANALYSIS_ID` to the exact published analysis ID. Invalid or absent identifiers do not prevent startup; affected endpoints return `503 degraded`.

Smoke the artifact-backed boundary:

```bash
curl http://127.0.0.1:8123/health
curl http://127.0.0.1:8123/model/metadata
curl http://127.0.0.1:8123/analytics/dashboard
curl http://127.0.0.1:8123/analytics/education
```

With the education fixture, health and metadata should identify `smoke-check`. The legacy dashboard may correctly return `503` because education prediction samples do not contain the legacy public customer-cohort fields. Tampering with a published `metrics.json` should also turn health into a checksum-mismatch degradation rather than serving altered bytes.

## Start the web application

Install locked dependencies and start Next.js against the API:

```bash
pnpm --dir apps/web install --frozen-lockfile
CHURN_API_BASE_URL=http://127.0.0.1:8123 pnpm --dir apps/web dev
```

The customer dashboard is available at `/`; education analysis is available at `/education` after the API is configured with an analysis publication.

## Python verification

Run one focused test while iterating, for example:

```bash
uv run pytest packages/ml/tests/test_ml_evaluation_pipeline.py
uv run pytest apps/api/tests/test_analytics_api.py
```

Then run the complete Python checks:

```bash
uv run pytest
uv run ruff check packages/ml apps/api
uv run --no-project --python 3.12 --with mypy --with fastapi --with pandas \
  --with pandas-stubs --with joblib mypy packages/ml/src apps/api/src
```

Pytest uses strict markers, covers both `packages/ml/src` and `apps/api/src`, and discovers tests from the two subsystem test directories. The mypy invocation intentionally installs `pandas-stubs`, matching CI and the transitive imports exercised by CLI-to-API integration tests.

## Web verification

Run unit, lint, type, and build checks independently:

```bash
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web build
```

Run browser checks with:

```bash
pnpm --dir apps/web test:e2e
```

Playwright starts the application against controlled API fixtures. On macOS, another process may occupy common development ports and make the Playwright web server appear to hang; use a temporary alternate Playwright config on a known free port rather than weakening the browser assertions.

## Contract-focused checks

Choose checks by boundary:

| Change | Primary evidence |
| --- | --- |
| artifact schema or publication | ML artifact-contract and integration tests |
| threshold/evaluation behavior | ML evaluation pipeline tests |
| FastAPI route or response shape | API analytics, education, and OpenAPI tests |
| filesystem serving integrity | API snapshot-reader tests |
| TypeScript API parsing | web API-client tests |
| view-model transformation | dashboard-model tests |
| loading, empty, degraded UI | Playwright E2E tests |
| delivery metadata or review size | delivery guardrail tests and CLI |

## Delivery guardrails and CI

`scripts/delivery_guardrails.py` exposes checks for PR metadata, workflow shape, documentation alignment, and the 400-line review budget. The GitHub Actions workflow runs:

- PR metadata and delivery guardrails;
- Python tests, Ruff, and strict mypy;
- web unit tests, ESLint, TypeScript, and production build;
- Playwright Chromium tests after the web job succeeds.

Local commit-review wrapper checks, when that tooling changes, are:

```bash
bash -n entrypoint/review-bin/opencode .git/hooks/pre-commit
python -m pytest --no-cov \
  packages/ml/tests/test_gga_opencode_wrapper.py \
  packages/ml/tests/test_gga_review_output.py
```

## OpenWiki maintenance

`.github/workflows/openwiki-update.yml` can be dispatched manually and is scheduled daily at `08:00 UTC`. Its read-only `generate` job checks out full history without persisted credentials, installs the pinned OpenWiki version, runs the update with provider secrets, removes transient run state, and uploads only the generated wiki and managed setup files.

The separate `publish` job is the only job with repository and pull-request write permissions. It clears the generated paths before downloading the artifact so deletions are preserved, then opens or refreshes the `openwiki/update` pull request. The workflow requires repository secrets for its configured model provider and LangSmith code connector. If generation fails after producing partial pages, the publisher still preserves that progress in the pull request and then propagates the failure so maintainers see that the update was incomplete.

## Related pages

- [Repository Quickstart](../quickstart.md)
- [ML Training and Artifact Publication](../workflows/ml-training-and-publication.md)
- [FastAPI Serving Boundary](../architecture/api-serving.md)
- [Next.js Analytical Dashboard](../architecture/web-dashboard.md)

# Local Verification

Use these commands to validate the current project slices locally before opening
or updating a PR.

## Python checks

```bash
uv run pytest
uv run ruff check packages/ml apps/api
uv run --no-project --python 3.12 --with mypy --with fastapi --with pandas \
  --with pandas-stubs --with joblib mypy packages/ml/src apps/api/src
```

The mypy command matches CI: `pandas-stubs` are required because the CLI-to-API
integration test imports `churn_ml.__main__`, which transitively imports
`pandas`.

## CLI/API smoke

Publish one education run and serve it with the exact same root and run ID:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path packages/ml/tests/fixtures/education_sample.csv \
  --dataset-id ai-student-impact --run-id smoke-check --artifact-root /tmp/smoke-store

PYTHONPATH=apps/api/src:packages/ml/src \
CHURN_ARTIFACT_RUN_ID=smoke-check CHURN_ARTIFACT_ROOT=/tmp/smoke-store \
uv run --with uvicorn uvicorn churn_api.main:app --port 8123

curl http://127.0.0.1:8123/health            # 200 ready, artifact_version smoke-check
curl http://127.0.0.1:8123/model/metadata    # 200 run_id smoke-check
curl http://127.0.0.1:8123/analytics/dashboard  # 503 degraded (no public cohort fields)
```

Tamper `metrics.json` and re-check `/health` to confirm the run degrades with
`checksum mismatch` instead of serving altered bytes.

## Web checks

```bash
pnpm --dir apps/web install --frozen-lockfile
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
```

Playwright E2E runs against a mock dashboard API on a fixed port. On macOS,
VS Code may occupy ports 3000/3001/8080 (the Playwright web server hangs
silently); use a temporary `playwright.alt.config.ts` with the web on a free
port (for example 3222) and `reuseExistingServer: true`.

## CI

GitHub Actions runs PR metadata validation, Python tests/lint/type checks, web
tests/lint/type checks, and Playwright E2E checks.
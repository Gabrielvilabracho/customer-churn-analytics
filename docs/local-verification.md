# Local Verification

Use these commands to validate the current project slices locally before opening
or updating a PR.

## Python checks

```bash
uv run --no-project --python 3.12 --with pytest --with pytest-cov pytest packages/ml/tests apps/api/tests
uv run --no-project --python 3.12 --with ruff ruff check packages/ml apps/api
uv run --no-project --python 3.12 --with mypy mypy packages/ml/src apps/api/src
```

## Web checks

```bash
pnpm --dir apps/web install --lockfile=false
pnpm --dir apps/web test
pnpm --dir apps/web lint
pnpm --dir apps/web typecheck
pnpm --dir apps/web test:e2e
```

## CI

GitHub Actions runs PR metadata validation, Python tests/lint/type checks, web
tests/lint/type checks, and Playwright E2E checks for the tooling skeleton.

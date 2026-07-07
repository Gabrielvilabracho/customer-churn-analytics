# Verify Report: customer-churn-analytics-platform (PR1B-B)

## Change
customer-churn-analytics-platform — Phase 2B tasks 2B.5 and 2B.6

## Branch
feat/phase-2b-pr1b-b-entrypoint

## Mode
Strict TDD / Full artifacts (proposal + specs + design + tasks + apply-progress)

## Verdict
**PASS** — 0 CRITICAL, 1 WARNING, 1 SUGGESTION

---

## Completeness Table

| Task | Checkbox | Status |
|------|----------|--------|
| 2B.5 RED/GREEN: training entrypoint + run_training.py + __main__.py | [x] | COMPLETE |
| 2B.6 REFACTOR: save_model_binary/load_model_binary + API adapter contract | [x] | COMPLETE |
| Phase 4 tasks 4.1–4.4 | [ ] | PENDING (not in scope) |
| Phase 5 tasks 5.1–5.3 | [ ] | PENDING (not in scope) |

---

## Gate 1: Test Suite

```
uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests apps/api/tests -v
```

**Result: 53 passed, 0 failed** (2.54s)

| Test File | Tests | Result |
|-----------|-------|--------|
| packages/ml/tests/integration/test_training_entrypoint.py | 4 | PASSED |
| packages/ml/tests/application/test_real_training_pipeline.py | 4 | PASSED |
| packages/ml/tests/infrastructure/sklearn/test_candidate_trainer.py | 3 | PASSED |
| packages/ml/tests/test_ml_artifact_contracts.py | 6 | PASSED |
| packages/ml/tests/test_ml_evaluation_pipeline.py | 7 | PASSED |
| packages/ml/tests/test_dataset_acquisition.py | 6 | PASSED |
| packages/ml/tests/test_dataset_profile.py | 5 | PASSED |
| packages/ml/tests/test_ml_tooling_bootstrap.py | 1 | PASSED |
| apps/api/tests/adapters/test_filesystem_snapshot_reader.py | 2 | PASSED |
| apps/api/tests/test_analytics_api.py | 12 | PASSED |
| apps/api/tests/test_api_tooling_bootstrap.py | 1 | PASSED |

Overall coverage: 84% (772 stmts / 124 missed)

---

## Gate 2: Linter

```
uv run --no-project --python 3.12 --with ruff ruff check packages/ml apps/api
```

**Result: All checks passed**

---

## Gate 3: Type Checker

```
uv run --no-project --python 3.12 --with mypy --with fastapi mypy packages/ml/src apps/api/src
```

**Result: Success — no issues found in 38 source files**

---

## Strict TDD Evidence

| Task | RED Evidence | GREEN Evidence | REFACTOR Evidence |
|------|-------------|----------------|-------------------|
| 2B.5 | ImportError for missing run_training module | 4 integration tests pass | Ruff/mypy clean |
| 2B.6 | AttributeError for missing save_model_binary | 2+2 tests pass (artifact_contracts + api adapter) | joblib type-ignore scoped correctly |

TDD evidence sourced from apply-progress Engram observation #3690.

---

## Spec Compliance Matrix

Spec: `openspec/specs/churn-ml-artifacts/spec.md`

| Spec Scenario | Covering Test | Result |
|---------------|---------------|--------|
| Cleaning pipeline completes: writes cleaned splits + deterministic output | test_run_training_writes_processed_splits_and_versioned_artifact_bundle | PASS |
| Invalid input schema: fail with schema error and write no training artifacts | test_run_training_writes_no_artifacts_when_schema_screening_fails | PASS |
| Model evaluated for churn usefulness: reports PR-AUC, ROC-AUC, precision, recall, top-risk capture, threshold | test_run_training_writes_processed_splits_and_versioned_artifact_bundle (checks metrics + threshold) | PASS |
| Accuracy is misleading: flag model as unsuitable | test_training_evaluation_rejects_misleading_accuracy_for_candidate (from 2B.3 suite) | PASS |
| Versioned artifact layout under artifacts/models/<run_id>/ and artifacts/metrics/<run_id>/ | test_run_training_writes_processed_splits_and_versioned_artifact_bundle | PASS |

---

## Architecture Constraint Check

Design constraint: Domain/application layers MUST NOT import pandas, sklearn, FastAPI, or filesystem clients directly.

```
grep -rn "import pandas|import sklearn|from pandas|from sklearn|import fastapi|from fastapi" packages/ml/src/churn_ml/application/ packages/ml/src/churn_ml/domain/
```

**Result: No matches** — constraint satisfied.

| Layer | File | Forbidden Import | Result |
|-------|------|------------------|--------|
| application/pipelines/run_training.py | Ports + domain imports only | None | CLEAN |
| application/pipelines/train.py | Evaluate + ports + domain only | None | CLEAN |
| application/pipelines/features.py | csv + stdlib + ports + domain only | None | CLEAN |
| __main__.py (composition root) | infrastructure imports | Allowed — composition root | CLEAN |
| infrastructure/sklearn/candidate.py | sklearn via importlib | Expected — infrastructure layer | CLEAN |
| infrastructure/filesystem/artifact_store.py | joblib via lazy import | Expected — infrastructure layer | CLEAN |

---

## Checklist Verification

| Item | Result |
|------|--------|
| Tests exist for every new behavior | PASS — 4 integration + 2 store + 2 API adapter |
| RED-first cycle documented | PASS — apply-progress confirms ImportError / AttributeError RED states |
| Versioned artifact layout (models/<run_id>/, metrics/<run_id>/) | PASS — asserted in integration test |
| Misleading-accuracy rejection intact | PASS — test_training_evaluation_rejects_misleading_accuracy_for_candidate passes |
| Threshold tradeoffs preserved | PASS — test_training_evaluation_selects_threshold_with_documented_tradeoff passes |
| Real sklearn assertion (not _FallbackModel) | PASS — test_run_training_uses_real_sklearn_estimator_not_fallback_model asserts not isinstance(result.trained_candidate.estimator, _FallbackModel) |
| Zero artifact writes on schema failure | PASS — assert list(tmp_path.iterdir()) == [] passes |
| API adapter contract: manifest{run_id,dataset_id,model_name,created_at_utc,feature_schema}, metrics, threshold, prediction_samples | PASS — both contract tests pass with full bundle shape check |
| python -m churn_ml --help does not crash | PASS — help text rendered correctly |
| Tasks 2B.5/2B.6 marked [x] | PASS — confirmed in tasks.md |
| No other tasks touched | PASS — only 2B.5 and 2B.6 changed from [ ] to [x] |
| pandas>=2.0, scikit-learn>=1.3, joblib>=1.3 declared in pyproject.toml | PASS |
| CI workflow includes --with pandas --with scikit-learn | PASS |

---

## Issues

### CRITICAL
None.

### WARNING
**W1 — `__main__.py` has 0% automated test coverage (35 statements, lines 1–110)**

The CLI composition root is not exercised by the integration test suite. The tests call `run_training()` directly. The `main()` function includes a `save_model_binary` call that has no covering automated test. Verified non-crash via `python -m churn_ml --help`, but the full execution path through `main()` is not covered.

Remediation: Add a subprocess-based integration test or a direct call to `main()` with CLI args to cover the composition root, or explicitly document the manual verification path.

### SUGGESTION
**S1 — httpx/starlette deprecation warning**

`fastapi.testclient` emits a `StarletteDeprecationWarning` recommending `httpx2` over `httpx`. This is cosmetic and does not affect test results, but may become a failure in future FastAPI versions.

---

## Files Verified

| File | Status |
|------|--------|
| packages/ml/tests/integration/test_training_entrypoint.py | VERIFIED — 4 tests pass |
| packages/ml/src/churn_ml/application/pipelines/run_training.py | VERIFIED — 95% coverage, clean imports |
| packages/ml/src/churn_ml/__main__.py | VERIFIED — correct CLI wiring, 0% coverage (WARNING W1) |
| packages/ml/src/churn_ml/application/pipelines/train.py | VERIFIED — trained_candidate field added correctly |
| packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py | VERIFIED — save_model_binary/load_model_binary correct, 98% coverage |
| apps/api/tests/adapters/test_filesystem_snapshot_reader.py | VERIFIED — 2 contract tests covering full bundle shape |
| packages/ml/pyproject.toml | VERIFIED — pandas/scikit-learn/joblib declared |
| .github/workflows/ci.yml | VERIFIED — --with pandas --with scikit-learn in ML test step |

---

## Archive Readiness

No CRITICAL issues. One WARNING (W1: __main__.py coverage gap) is non-blocking for archive.

**Recommendation: sdd-archive**

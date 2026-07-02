# Verification Report

**Change**: customer-churn-analytics-platform
**Mode**: Strict TDD
**Scope**: PR2 / Phase 2 ML Artifacts remediation re-verification
**Final verdict**: PASS WITH WARNINGS

## Completeness

| Area | Expected | Verified | Result |
|---|---:|---:|---|
| Phase 2 ML artifact tasks | 4 complete | 4 complete in `tasks.md` and apply-progress | ✅ PASS |
| Cleaned split / feature artifact persistence | Cleaned split files plus feature metadata are persisted | `CleanedSplitArtifact` writes CSV rows plus metadata JSON with feature columns, target, row count under `processed/<run_id>/` | ✅ PASS |
| Baseline-vs-candidate metrics/comparison | Baseline and candidate are trained/evaluated on shared data and selected by churn-usefulness metrics | `compare_model_candidates` evaluates both models and selects by recall, top-risk capture, PR-AUC, precision | ✅ PASS |
| Nested generated artifact ignore rules | Generated model/metric payloads ignored; `.gitkeep` placeholders remain trackable | `git check-ignore` exits 0 for nested payloads and 1 for `.gitkeep` placeholders | ✅ PASS |
| Scope guard | No API/dashboard implementation in PR2 | Phase 3+ tasks remain unchecked; source changes stay in ML artifact foundations plus generated-artifact ignore rules | ✅ PASS |

## Build / Tests / Coverage Evidence

| Command | Result | Evidence |
|---|---|---|
| `uv run --no-project --python 3.12 --with pytest --with pytest-cov pytest packages/ml/tests/test_ml_artifact_contracts.py packages/ml/tests/test_ml_evaluation_pipeline.py` | ✅ PASS | 11 passed; PR2 targeted coverage includes `train.py` 97%, filesystem artifact store 100%, baseline adapter 93% |
| `uv run --no-project --python 3.12 --with pytest --with pytest-cov pytest packages/ml/tests apps/api/tests` | ✅ PASS | 26 passed; total Python coverage 89% |
| `uv run --no-project --python 3.12 --with ruff ruff check packages/ml apps/api` | ✅ PASS | All checks passed |
| `uv run --no-project --python 3.12 --with mypy mypy packages/ml/src apps/api/src` | ✅ PASS | Success: no issues found in 22 source files |
| `pnpm --dir apps/web test` | ✅ PASS | 1 Vitest file passed; 2 tests passed |
| `pnpm --dir apps/web lint` | ✅ PASS | ESLint completed without reported errors |
| `pnpm --dir apps/web typecheck` | ✅ PASS | `tsc --noEmit` completed without reported errors |
| `pnpm --dir apps/web build` | ✅ PASS | Next.js 15 production build compiled and prerendered successfully |
| `pnpm --dir apps/web test:e2e --reporter=line` | ✅ PASS | 1 Playwright bootstrap test passed |
| `git check-ignore -v artifacts/models/run-001/model_metadata.json artifacts/metrics/run-001/metrics.json` | ✅ PASS | Nested model and metric payloads match `artifacts/models/**` and `artifacts/metrics/**` |
| `git check-ignore -q artifacts/models/.gitkeep ...` | ✅ PASS | `.gitkeep` placeholders exit 1 (not ignored); nested payloads exit 0 (ignored) |

## TDD Compliance

| Check | Result | Details |
|---|---|---|
| TDD Evidence reported | ✅ | Engram apply-progress contains PR2 and PR2-remediation TDD Cycle Evidence rows. |
| All PR2 tasks have tests/evidence | ✅ | 4/4 Phase 2 tasks plus remediation rows list concrete pytest files or `git check-ignore` guardrail evidence. |
| RED confirmed | ✅ | Apply-progress records failing-first evidence for missing PR2 modules and remediation failures for missing `CleanedSplitArtifact` / `compare_model_candidates`. Historical RED cannot be replayed, but reported failures match current symbols. |
| GREEN confirmed | ✅ | Targeted PR2 tests and full Python checks pass now. |
| Triangulation adequate | ✅ | Deterministic split uses same-seed and different-seed cases; artifact store covers metrics/prediction samples and cleaned split metadata; model comparison covers baseline and stronger candidate selection. |
| Safety net for modified files | ✅ | Apply-progress records existing Python slice passing before PR2 remediation; current full suite remains green. |

**TDD Compliance**: PASS.

## Test Layer Distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Python unit / adapter | 26 | 6 | pytest, pytest-cov |
| Web unit/tooling | 2 | 1 | Vitest |
| Web E2E bootstrap | 1 | 1 | Playwright |
| **Total executed** | **29** | **8** | |

## Changed File Coverage

| File | Line % | Branch % | Uncovered Lines | Rating |
|---|---:|---:|---|---|
| `packages/ml/src/churn_ml/application/pipelines/evaluate.py` | 88% | N/A | 16, 18, 20, 64, 83, 91, 101, 120 | ⚠️ Acceptable |
| `packages/ml/src/churn_ml/application/pipelines/features.py` | 85% | N/A | 21, 23, 41 | ⚠️ Acceptable |
| `packages/ml/src/churn_ml/application/pipelines/train.py` | 97% | N/A | 92 | ✅ Excellent |
| `packages/ml/src/churn_ml/application/ports/artifact_store.py` | 0% | N/A | 1-6 | ⚠️ Low |
| `packages/ml/src/churn_ml/application/ports/model_trainer.py` | 100% | N/A | — | ✅ Excellent |
| `packages/ml/src/churn_ml/domain/artifacts.py` | 100% | N/A | — | ✅ Excellent |
| `packages/ml/src/churn_ml/domain/customer.py` | 88% | N/A | 30, 40, 46, 67 | ⚠️ Acceptable |
| `packages/ml/src/churn_ml/domain/model.py` | 0% | N/A | 1-24 | ⚠️ Low |
| `packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py` | 100% | N/A | — | ✅ Excellent |
| `packages/ml/src/churn_ml/infrastructure/sklearn/baseline.py` | 93% | N/A | 17 | ✅ Excellent |

**Average changed PR2 source-file coverage**: 74.9% including protocol/data-model scaffolding; core executable PR2 remediation files are covered at 93-100% except `features.py`/`evaluate.py` acceptable branches.

## Assertion Quality

**Assertion quality**: ✅ All inspected PR2/remediation assertions verify real behavior. No tautologies, orphan empty checks, ghost loops, smoke-only checks, or mock-heavy tests were found. Filesystem tests assert real files and loaded values; comparison tests assert baseline metrics, candidate metrics, selected model, and selection reason.

## Spec Compliance Matrix

| Spec / Scenario | Runtime Evidence | Status |
|---|---|---|
| Churn ML Artifacts — cleaning pipeline completes | `test_deterministic_train_test_split_is_stable_for_same_seed`, `test_deterministic_train_test_split_changes_with_seed_without_losing_rows`, `test_feature_dictionary_exports_business_feature_metadata`, `test_filesystem_artifact_store_round_trips_cleaned_split_csv_and_metadata_json` | ✅ PASS |
| Churn ML Artifacts — invalid input schema | `test_feature_dictionary_rejects_missing_target_and_customer_key` | ✅ PASS |
| Churn ML Artifacts — model is evaluated for churn usefulness | `test_evaluate_predictions_reports_business_oriented_metrics`, `test_threshold_selection_documents_recall_workload_tradeoff`, `test_model_candidate_comparison_selects_candidate_with_better_churn_usefulness`, `test_filesystem_artifact_store_round_trips_json_and_prediction_samples` | ✅ PASS |
| Churn ML Artifacts — accuracy is misleading | `test_misleading_accuracy_is_rejected_for_executive_reporting` | ✅ PASS |
| Dataset Acquisition — no raw/generated payloads | `git status --short --untracked-files=all artifacts data` shows only `artifacts/{models,metrics}/.gitkeep`; data dirs contain only `.gitkeep` placeholders | ✅ PASS |
| Engineering Workflow — strict module-level TDD | Apply-progress TDD evidence plus targeted/full pytest execution | ✅ PASS for PR2 |
| API/dashboard specs | Not in PR2 scope | ➖ SKIPPED |

## Correctness

| Check | Evidence | Result |
|---|---|---|
| Cleaned split persistence | `FilesystemArtifactStore.save_cleaned_split/load_cleaned_split` writes `processed/<run_id>/<split>.csv` and `<split>.metadata.json`; pytest round-trip passes | ✅ PASS |
| Feature metadata included with split artifact | `CleanedSplitArtifact.metadata_json_dict()` persists `feature_columns`, `target_column`, `row_count`, `dataset_id`, `run_id`, and `split_name`; pytest asserts loaded metadata | ✅ PASS |
| Baseline-vs-candidate comparison | `compare_model_candidates` trains both ports, evaluates both with `evaluate_predictions`, and selects by churn-usefulness tuple | ✅ PASS |
| Baseline adapter coverage | `BaselineChurnRateTrainer` predicts the observed training churn rate; pytest asserts 0.5 probability output | ✅ PASS |
| Metrics/threshold/prediction sample artifacts | `FilesystemArtifactStore.save_bundle/load_bundle` writes metrics JSON, model metadata JSON, prediction CSV and round-trips loaded values | ✅ PASS |
| Generated artifact ignore rules | `.gitignore` uses `artifacts/models/**` and `artifacts/metrics/**` with `.gitkeep` negations; `git check-ignore` proves payloads ignored/placeholders trackable | ✅ PASS |
| No generated/raw artifacts included | Only `.gitkeep` files appear under `artifacts/`; `data/raw` and `data/processed` remain placeholder-only | ✅ PASS |

## Design Coherence

| Design Decision | Evidence | Result |
|---|---|---|
| Core-first ML/data before API/dashboard | Changes remain in `packages/ml`, artifact boundaries, `.gitignore`, and task status | ✅ PASS |
| Clean/Hexagonal boundaries | Domain/application modules avoid FastAPI, pandas, sklearn, and filesystem imports; filesystem/sklearn code stays under `infrastructure/` | ✅ PASS |
| Artifact-first tracking | CSV/JSON artifacts are the persistence shape; no MLflow or model registry introduced | ✅ PASS |
| Strict TDD | TDD evidence exists and current tests pass | ✅ PASS |
| English-only artifacts/code | Source, tests, docs, and generated report content are English | ✅ PASS |

## Quality Metrics

**Linter**: ✅ No errors  
**Type Checker**: ✅ No errors  
**Python Coverage**: ⚠️ 89% total; two changed scaffolding files remain under 80% (`application/ports/artifact_store.py`, `domain/model.py`)
**Web Checks**: ✅ test/lint/typecheck/build/E2E passed

## Issues

### CRITICAL

None.

### WARNING

1. `packages/ml/src/churn_ml/domain/model.py` remains at 0% coverage and `application/ports/artifact_store.py` reports 0% under coverage. These are scaffolding/protocol-style files and do not block PR2 remediation, but Strict TDD coverage reporting requires the warning.
2. The persisted cleaned split metadata captures feature column names, target, row count, dataset, run, and split, but there is not yet a separate persisted feature-dictionary artifact with semantic roles. Current PR2 scope is compliant through split metadata plus in-memory feature dictionary tests; a dedicated feature dictionary artifact may be useful before the API/dashboard consume model schema.

### SUGGESTION

- Add direct tests for `risk_segment_for_probability` and the artifact-store protocol/use-case boundary in the next ML hardening pass.
- If Phase 3 API needs schema introspection, promote the feature dictionary into its own versioned JSON artifact instead of relying only on split metadata.

## Final Verdict

PASS WITH WARNINGS — the prior PR2 critical failures are fixed. Cleaned split/feature metadata persistence, baseline-vs-candidate comparison coverage, and nested generated artifact ignore rules now have runtime evidence. All Python checks and relevant web checks pass.

## next_recommended

Proceed to Phase 3 Analytics API (`sdd-apply`) after accepting the non-blocking coverage/schema-artifact warnings, or add the suggested feature-dictionary JSON hardening first if the API contract needs it immediately.

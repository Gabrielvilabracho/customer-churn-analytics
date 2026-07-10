# Apply Progress: Customer Churn Analytics Platform

## Change
customer-churn-analytics-platform

## Completed Tasks
- [x] 3B.1 Enrich ML `prediction_samples.csv` rows with dashboard cohort fields.
- [x] 3B.2 Expose enriched prediction samples through `GET /analytics/dashboard`.
- [x] 4.1 Add `apps/web/app/(dashboard)/page.tsx` plus typed dashboard API client/contracts.
- [x] 4.2 Add KPI cards, cohort visualization, risk table, and driver summary components.
- [x] 4.3 Add loading, error, empty, degraded, and data states.
- [x] 4.4 Add component/page tests and Playwright happy/degraded specs.

## TDD Cycle Evidence
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 3B.1 | `packages/ml/tests/integration/test_training_entrypoint.py` | Integration | ✅ 19/19 | ✅ Missing cohort fields failed | ✅ Passed | ✅ Categorical + numeric fields | ✅ Cohort helper |
| 3B.2 | `apps/api/tests/test_analytics_api.py` | API | ✅ 19/19 | ✅ Missing `prediction_samples` failed | ✅ Passed | ✅ Two sample rows | ➖ None |
| 4.1 | `apps/web/lib/api/dashboard.test.ts`, `apps/web/app/(dashboard)/page.test.ts` | Unit/RSC | ✅ 2/2 + typecheck | ✅ Missing client/page failed | ✅ 8/8 Vitest | ✅ Data + degraded API | ✅ Typed client |
| 4.2 | `apps/web/components/features/churn/dashboard-model.test.ts`, `apps/web/app/(dashboard)/page.test.ts` | Unit/RSC | ✅ 2/2 + typecheck | ✅ Missing model/page failed | ✅ 8/8 Vitest | ✅ Populated + empty samples | ✅ Pure model |
| 4.3 | `apps/web/app/(dashboard)/page.test.ts` | RSC | ✅ 2/2 + typecheck | ✅ Degraded state failed | ✅ 8/8 Vitest | ✅ Data + degraded + empty | ➖ Structural states |
| 4.4 | `apps/web/e2e/dashboard.spec.ts` plus Vitest files | Playwright + unit | ✅ 2/2 + typecheck | ✅ Vitest RED first | ✅ 8/8 Vitest, 3/3 Playwright | ✅ Happy/degraded specs | ⚠️ Playwright added after Vitest GREEN |

## Verification Results
- ✅ Baseline before edits: `pnpm --dir apps/web test` → 2 passed; `pnpm --dir apps/web typecheck` → passed.
- ✅ RED: new web tests failed on missing dashboard client, model, and page modules.
- ✅ Final: `pnpm --dir apps/web typecheck && pnpm --dir apps/web test && pnpm --dir apps/web test:e2e` → typecheck passed, 8 Vitest tests passed, 3 Playwright tests passed.
- ✅ `pnpm --dir apps/web build` → compiled and generated routes.
- ✅ `pnpm --dir apps/web lint` → passed after `eslint-plugin-react-hooks` was added to `apps/web/package.json` in the prior tooling fix.

## Phase 4 Verification Blocker Fix Batch

### Completed Fixes
- [x] Replaced dashboard Playwright unit-style checks with browser E2E flows that use `page`, `page.goto(...)`, selectors, and deterministic per-request mock API scenarios.
- [x] Added runtime UI coverage for the no-prediction-samples dashboard state.
- [x] Implemented minimal accessible sorting for the top-risk customer table, including sortable header buttons and `aria-sort` state.
- [x] Added a valid Playwright `webServer`/`baseURL` configuration for the Next.js dashboard app.

### TDD Cycle Evidence — Fix Batch
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 4.4 blocker: real browser specs | `apps/web/e2e/dashboard.spec.ts`, `apps/web/e2e/tooling.spec.ts` | E2E | ✅ 8/8 Vitest, typecheck passed, 3/3 pre-existing Playwright passed | ✅ Browser specs failed before client runtime/server config | ✅ 4/4 Playwright passed | ✅ Happy, empty, degraded browser flows | ✅ Removed Playwright unit-style imports/assertions |
| 4.3 blocker: empty runtime UI coverage | `apps/web/e2e/dashboard.spec.ts` | E2E | ✅ Same web safety net | ✅ Empty-state browser assertion failed before runtime fetch path | ✅ 4/4 Playwright passed | ✅ Empty flow plus populated/degraded flows | ✅ Copy aligned to prediction samples |
| 4.2 blocker: sortable risk table | `apps/web/e2e/dashboard.spec.ts` | E2E | ✅ Same web safety net | ✅ Sort button assertion failed before sortable table behavior | ✅ 4/4 Playwright passed | ✅ Customer sorting with multiple visible risk rows | ✅ Accessible header buttons + `aria-sort` |

### Fix Verification Results
- ✅ Baseline before fix: `pnpm --dir apps/web test && pnpm --dir apps/web typecheck && pnpm --dir apps/web test:e2e` → 8 Vitest tests passed, typecheck passed, 3 Playwright tests passed.
- ✅ RED: `pnpm --dir apps/web test:e2e` after test/config changes → 4 browser specs failed before implementation.
- ✅ GREEN: `pnpm --dir apps/web test:e2e` → 4 Playwright browser specs passed.
- ✅ `pnpm --dir apps/web test && pnpm --dir apps/web typecheck` → 8 Vitest tests passed and typecheck passed.
- ✅ `pnpm --dir apps/web build` → compiled and generated routes without the stale missing `eslint-plugin-react-hooks` warning.
- ✅ `pnpm --dir apps/web lint` → passed.

## Pre-PR Blocker Fix Batch

### Completed Fixes
- [x] Preserved SSR degraded artifact reasons by preventing `DashboardClient` from immediately refetching when `initialError` is present.
- [x] Removed process-global E2E mock scenario state; dashboard E2E scenarios now flow through a per-request `scenario` query parameter.
- [x] Added dashboard threshold propagation and used the artifact threshold for risk labels, with a named fallback threshold for older payloads.
- [x] Strengthened tests for scenario query mapping, artifact threshold labels, and existing `aria-sort` E2E behavior.

### TDD Cycle Evidence — Pre-PR Fix Batch
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| Preserve degraded SSR reason | `apps/web/e2e/dashboard.spec.ts` | E2E | ⚠️ Baseline E2E had 1 known failing degraded test | ✅ Existing degraded test failed with generic client-refetch error | ✅ Dashboard E2E passed 3/3 scoped and 4/4 full | ✅ Degraded plus happy/empty flows | ✅ Guarded client refetch on `initialError` |
| Remove E2E scenario race | `apps/web/e2e/dashboard.spec.ts` | E2E | ⚠️ Same failing degraded baseline | ✅ Per-request scenario URL tests failed before mock/query support | ✅ Dashboard E2E passed 3/3 scoped and 4/4 full | ✅ Happy, empty, degraded query scenarios | ✅ Removed mutable mock server state |
| Contract-driven risk label threshold | `apps/web/lib/api/dashboard.test.ts`, `apps/web/components/features/churn/dashboard-model.test.ts` | Unit | ✅ 8/8 scoped web unit tests passed after focused run | ✅ Tests assert threshold mapping and threshold-based risk labels | ✅ 8/8 focused tests passed, 12/12 full unit tests passed | ✅ Threshold present plus fallback-compatible optional contract | ✅ Replaced magic `0.5` with named fallback constant |

### Fix Verification Results
- ✅ `pnpm --dir apps/web lint` → passed.
- ✅ `pnpm --dir apps/web typecheck` → passed.
- ✅ `pnpm --dir apps/web test` → 4 files passed, 12 tests passed.
- ✅ `pnpm --dir apps/web test:e2e` → 4 Playwright tests passed across 2 workers.
- ✅ `pnpm --dir apps/web build` → passed.

### Fix Files
- `apps/web/app/(dashboard)/dashboard-client.tsx` — preserves server-rendered degraded errors instead of overwriting them during hydration.
- `apps/web/app/(dashboard)/page.tsx` — passes optional per-request dashboard scenario query through the API client for deterministic E2E mock responses.
- `apps/web/e2e/mock-dashboard-api.mjs` — resolves scenarios from each dashboard request instead of mutable process-global state.
- `apps/web/e2e/dashboard.spec.ts` — uses per-test scenario URLs and retains explicit `aria-sort` assertions.
- `apps/web/lib/api/{client.ts,types.ts}` — maps optional dashboard threshold and scenario query parameters.
- `apps/web/components/features/churn/dashboard-model.ts` — derives risk labels from artifact threshold with a named fallback.
- `apps/api/src/churn_api/application/services.py` — exposes dashboard threshold from the artifact snapshot.

### Fix Files
- `apps/web/playwright.config.ts` — added `baseURL` and Next.js `webServer` for real browser specs.
- `apps/web/e2e/dashboard.spec.ts` — now navigates with per-test scenario URLs and asserts populated, empty, degraded, sortable UI behavior, and `aria-sort` through selectors.
- `apps/web/e2e/tooling.spec.ts` — converted from metadata-only runner check to a browser route smoke check.
- `apps/web/app/(dashboard)/dashboard-client.tsx` — added client runtime fetch/render path so Playwright route interception can exercise dashboard UI without a live API.
- `apps/web/app/(dashboard)/page.tsx` — keeps server-side analytics fetch when available and falls back to the client runtime path/error state.
- `apps/web/components/features/churn/risk-table.tsx` — added minimal sortable table behavior and `aria-sort`.
- `apps/web/components/features/churn/cohort-chart.tsx` — aligned empty-state copy with prediction sample terminology.

## Files, Deviations, and Issues
- Changed `apps/web/lib/api/*`, `apps/web/components/{ui,features/churn}/*`, `apps/web/app/(dashboard)/*`, `apps/web/e2e/dashboard.spec.ts`, `apps/web/vitest.config.mts`, and OpenSpec progress/tasks.
- Removed `apps/web/app/page.tsx` so `(dashboard)` owns `/`.
- No chart library was added; cohort visualization uses semantic HTML and Tailwind classes.
- No `components.json`, Tailwind config/dependency, or installed shadcn source exists, so this slice uses small local shadcn-style primitives.
- Playwright dashboard specs now validate browser navigation, selector-visible UI, and route-intercepted analytics responses through a configured Next.js `webServer`.
- Remaining tasks: Phase 5 verification and documentation.

## Workload / PR Boundary
- Mode: stacked PR slice. Current work unit: Phase 4 dashboard consumption layer. Boundary: API-backed dashboard UI and tests only.
- Estimated review budget impact: within the 800-line session budget after progress compaction.

## Next Recommended
sdd-verify for Phase 4, then sdd-apply for Phase 5 documentation.

---

## Phase 5.1 ML Verification Slice

### Completed Tasks
- [x] 5.1 Verified ML pytest coverage for CSV fixture loading, identifier exclusion, deterministic splits, misleading-accuracy rejection, and model/artifact persistence paths.

### TDD Cycle Evidence — Phase 5.1 Verification
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.1 | `packages/ml/tests/application/test_real_training_pipeline.py`, `packages/ml/tests/infrastructure/sklearn/test_candidate_trainer.py`, `packages/ml/tests/test_ml_artifact_contracts.py`, `packages/ml/tests/integration/test_training_entrypoint.py` | Unit + integration verification | ✅ Targeted ML coverage tests: 44/44 passed; full ML suite: 67/67 passed | ➖ Verification-only task; prior RED evidence exists in Phase 2B apply-progress for these behaviors | ✅ Required ML coverage commands passed | ✅ Covers CSV loading, identifier exclusion, deterministic/stratified splits, misleading-accuracy rejection, model binary persistence, and full training entrypoint | ➖ No production refactor needed |

### Verification Results
- ✅ Targeted command: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests/application/test_real_training_pipeline.py packages/ml/tests/infrastructure/sklearn/test_candidate_trainer.py packages/ml/tests/test_ml_artifact_contracts.py packages/ml/tests/integration/test_training_entrypoint.py` → 44 passed.
- ✅ Full ML command: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests` → 67 passed.
- ✅ Coverage confirms the scoped ML modules remain exercised: `features.py` 94%, `profile.py` 93%, `train.py` 92%, `run_training.py` 89%, `artifact_store.py` 92%, `candidate.py` 85% during the full ML test run.
- ⚠️ Direct `uv run pytest ...` is unavailable in the current environment because the pytest executable is not installed in the base environment; using `uv run --with ... python -m pytest ...` is the reproducible command.

### Coverage Mapping
| Required behavior | Verified by |
|-------------------|-------------|
| CSV fixture loading | `test_real_telco_csv_loads_and_excludes_customer_id_from_model_features`, `test_run_training_writes_processed_splits_and_versioned_artifact_bundle` |
| Identifier exclusion | `test_real_telco_csv_loads_and_excludes_customer_id_from_model_features` asserts `customerID` is absent from model features/fit metadata. |
| Deterministic splits | `test_real_telco_csv_split_is_deterministic_and_stratified` asserts stable customer ordering with a fixed seed and both target classes in train/test splits. |
| Misleading-accuracy rejection | `test_training_evaluation_rejects_misleading_accuracy_for_candidate` and threshold failure tests reject poor recall/top-risk capture paths. |
| Model/artifact persistence paths | `test_ml_artifact_contracts.py` and `test_training_entrypoint.py` verify bundle save/load, processed splits, prediction samples, real sklearn estimator use, zero writes on schema failure, and model binary persistence. |

### Files Changed
- `openspec/changes/customer-churn-analytics-platform/tasks.md` — marked Phase 5.1 complete.
- `openspec/changes/customer-churn-analytics-platform/apply-progress.md` — appended Phase 5.1 verification evidence and command results.
- `openspec/changes/customer-churn-analytics-platform/verify-report.md` — appended Phase 5.1 verification addendum.

### Deviations and Issues
- Deviation: Phase 5.1 is a verification-only task, so no new production code or new tests were added. Strict TDD evidence points to the existing RED/GREEN Phase 2B test-first history and fresh GREEN verification commands.
- Issue: the documented shorthand `uv run pytest` path failed in this environment; `python -m pytest` under `uv run --with ...` is the working command.

### Workload / PR Boundary
- Mode: stacked PR slice.
- Current work unit: Phase 5.1 ML verification only.
- Boundary: OpenSpec task/progress verification artifacts only; no Phase 5.2 API verification and no Phase 5.3 frontend/docs work.
- Estimated review budget impact: minimal artifact-only update.

### Next Recommended
sdd-apply for Phase 5.2 API verification.

---

## Phase 5.2 API Verification Slice

### Completed Tasks
- [x] 5.2 Verified API adapter/route tests for artifact compatibility, valid prediction, invalid payload, and degraded health when artifacts are missing.

### TDD Cycle Evidence — Phase 5.2 Verification
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.2 | `apps/api/tests/test_analytics_api.py`, `apps/api/tests/adapters/test_filesystem_snapshot_reader.py`, `apps/api/tests/test_api_tooling_bootstrap.py` | API route + adapter verification | ✅ Targeted API coverage tests: 16/16 passed; full API suite: 17/17 passed | ➖ Verification-only task; prior RED evidence exists in Phase 3/2B apply-progress for these API and adapter behaviors | ✅ Required API coverage commands passed | ✅ Covers artifact compatibility before/after model binary persistence, valid prediction, invalid payload without scoring, and degraded health/routes when artifacts are missing | ➖ No production refactor needed |

### Verification Results
- ✅ Targeted command: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib --with fastapi --with httpx python -m pytest apps/api/tests/test_analytics_api.py apps/api/tests/adapters/test_filesystem_snapshot_reader.py` → 16 passed, 1 Starlette/httpx deprecation warning.
- ✅ Full API command: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib --with fastapi --with httpx python -m pytest apps/api/tests` → 17 passed, 1 Starlette/httpx deprecation warning.
- ✅ Coverage confirms scoped API modules remain exercised: `routes.py` 100%, `filesystem.py` 100%, `main.py` 100%, `services.py` 96%, `dashboard_contract.py` 100%, `scoring.py` 100% during the full API test run.

### Coverage Mapping
| Required behavior | Verified by |
|-------------------|-------------|
| Artifact compatibility | `test_snapshot_reader_loads_bundle_shape_from_store_without_model_binary`, `test_snapshot_reader_bundle_shape_is_unchanged_after_model_binary_is_saved`, `test_filesystem_artifact_reader_maps_versioned_metrics_into_api_snapshot`, and `test_filesystem_artifact_reader_maps_persisted_feature_schema_into_api_snapshot`. |
| Valid prediction | `test_prediction_contract_returns_risk_decision_and_driver_payload` verifies probability, threshold decision, model version, drivers, and that scoring is invoked once. |
| Invalid payload | `test_invalid_prediction_payload_returns_structured_error_without_scoring` and `test_boolean_feature_value_is_rejected_for_numeric_schema_without_scoring` verify structured 422 errors and no model invocation. |
| Degraded health/missing artifacts | `test_health_reports_degraded_when_required_artifacts_are_missing`, `test_dashboard_reports_degraded_without_fabricated_analytics`, and `test_default_app_reports_degraded_without_configured_artifacts` verify degraded responses without fabricated data. |

### Files Changed
- `openspec/changes/customer-churn-analytics-platform/tasks.md` — marked Phase 5.2 complete.
- `openspec/changes/customer-churn-analytics-platform/apply-progress.md` — appended Phase 5.2 verification evidence and command results.
- `openspec/changes/customer-churn-analytics-platform/verify-report.md` — appended Phase 5.2 verification addendum.

### Deviations and Issues
- Deviation: Phase 5.2 is a verification-only task, so no new production code or new tests were added. Strict TDD evidence points to the existing RED/GREEN API and adapter test-first history and fresh GREEN verification commands.
- Issue: API tests pass with a non-blocking `StarletteDeprecationWarning` from FastAPI `TestClient` recommending `httpx2`.

### Workload / PR Boundary
- Mode: stacked PR slice.
- Current work unit: Phase 5.2 API verification only.
- Boundary: OpenSpec task/progress verification artifacts only; no Phase 5.3 frontend/docs work.
- Estimated review budget impact: minimal artifact-only update.

### Next Recommended
sdd-apply for Phase 5.3 frontend verification and portfolio documentation.

---

## Phase 5.3 Frontend Verification and Documentation Slice

### Completed Tasks
- [x] 5.3 Verified frontend tests and added `README.md`, `docs/modeling-report.md`, `docs/architecture.md`, and `docs/api-contract.md` to document setup, artifact flow, guarantees, and reviewer verification commands.

### TDD Cycle Evidence — Phase 5.3 Verification and Docs
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.3 | `apps/web/lib/api/dashboard.test.ts`, `apps/web/components/features/churn/dashboard-model.test.ts`, `apps/web/app/(dashboard)/page.test.ts`, `apps/web/e2e/dashboard.spec.ts`, `apps/web/e2e/tooling.spec.ts` | Frontend unit + browser E2E verification; documentation | ✅ `pnpm --dir apps/web typecheck`, `pnpm --dir apps/web test`, and `pnpm --dir apps/web test:e2e` passed before edits | ➖ Documentation/verification-only task; prior RED evidence exists in Phase 4 apply-progress for frontend behavior | ✅ Required frontend verification commands passed after docs were added | ✅ Covers typed dashboard client, dashboard view model, page rendering, populated dashboard, empty predictions, degraded artifacts, and browser route smoke | ➖ No production refactor needed; docs created from existing verified contracts |

### Verification Results
- ✅ `pnpm --dir apps/web typecheck` → passed.
- ✅ `pnpm --dir apps/web test` → 4 files passed, 12 Vitest tests passed.
- ✅ `pnpm --dir apps/web test:e2e` → 4 Playwright browser tests passed.

### Documentation Added
- `README.md` — product goal, repository map, setup path, artifact flow, and reviewer verification commands.
- `docs/modeling-report.md` — dataset/target, evaluation metrics, artifact outputs, limitations, and ML verification mapping.
- `docs/architecture.md` — Clean/Hexagonal boundaries from dataset acquisition through dashboard consumption.
- `docs/api-contract.md` — FastAPI endpoint contracts, degraded responses, prediction request/response shape, and compatibility guarantees.

### Deviations and Issues
- Deviation: Phase 5.3 is a verification/documentation task, so Strict TDD RED/GREEN is not applicable to new production behavior. Evidence points to the existing Phase 4 frontend RED/GREEN history and fresh GREEN verification commands.
- Issue: Existing Phase 5.1/5.2 OpenSpec artifact edits were already present in the working tree before this slice; this batch preserved and appended to them.

### Workload / PR Boundary
- Mode: stacked PR slice.
- Current work unit: Phase 5.3 frontend verification and portfolio documentation only.
- Boundary: portfolio documentation plus OpenSpec task/progress/verify artifacts; no production code changes.
- Estimated review budget impact: documentation-focused update is near the 400-line review budget when combined with existing Phase 5 artifact edits; keep this as a chained review slice.

### Next Recommended
sdd-verify for full Phase 5 documentation and verification readiness.

---

## Phase 5.4 Delivery Guardrail Remediation Slice

### Completed Tasks
- [x] 5.4 Added lightweight executable checks for PR workflow coverage, review-budget enforcement, and documentation anti-shortcut acceptance.

### TDD Cycle Evidence — Phase 5.4 Remediation
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 | `packages/ml/tests/test_delivery_guardrails.py` | Repository governance unit checks | N/A (new checks) | ✅ Import/workflow/doc checks failed before `scripts.delivery_guardrails`, `.github/workflows/ci.yml`, and doc guardrail existed | ✅ `3 passed` | ✅ Workflow check, under/over-budget examples, and documentation shortcut guardrail | ✅ Shared pure check functions and CLI entrypoint |

### Verification Results
- ✅ RED: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests/test_delivery_guardrails.py` failed with `ModuleNotFoundError: No module named 'scripts'` before implementation.
- ✅ GREEN: same command passed with 3 tests.
- ✅ `uv run --with ruff ruff check scripts packages/ml/tests/test_delivery_guardrails.py` passed.

### Files Changed
- `.github/workflows/ci.yml` — restored lightweight PR-triggered metadata, ML, API, web, and E2E job definitions for executable workflow coverage checks.
- `scripts/delivery_guardrails.py` — added pure check functions plus a CLI entrypoint for PR workflow, review-budget, and documentation guardrails.
- `packages/ml/tests/test_delivery_guardrails.py` — added Strict TDD checks for the three verify blockers.
- `docs/architecture.md` — documented that artifact-contract bypasses and hardcoded dashboard metrics are non-compliant.

### Workload / PR Boundary
- Mode: stacked PR remediation slice.
- Current work unit: archive-readiness guardrail checks only.
- Boundary: executable checks and minimal documentation acceptance text; no product behavior changes.
- Estimated review budget impact: small remediation unit, but current working tree still includes earlier Phase 5 docs/OpenSpec edits and should remain a chained review slice.

### Next Recommended
sdd-verify full archive-readiness pass.

---

## Phase 5.4 Fresh-review Remediation Follow-up

### Completed Fixes
- [x] Added real `--base-ref` diff behavior so CI can evaluate PR changes even when the checkout working tree is clean.
- [x] Wired `scripts/delivery_guardrails.py` into `.github/workflows/ci.yml` as an executable PR gate with full fetch history.
- [x] Strengthened documentation guardrails with required docs, traceability, no-fabrication, and negative shortcut fixtures instead of only positive phrase checks.
- [x] Hardened malformed numstat, binary rows, missing docs, git diff errors, named CLI statuses, and partial-failure exit behavior.

### TDD Cycle Evidence — Fresh-review Follow-up
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 follow-up | `packages/ml/tests/test_delivery_guardrails.py` | Repository governance unit + CLI checks | ✅ Existing guardrail tests: 3/3 passed before edits | ✅ New tests failed first: workflow lacked CLI gate, base-ref API missing, docs missing raised traceback, malformed rows were not reported | ✅ Targeted guardrail tests: 9/9 passed; full ML suite: 76/76 passed | ✅ Exact 400/401, malformed, binary, missing docs, negative docs, clean git branch diff, and CLI partial failure cases | ✅ Pure helpers kept small; CLI now prints named PASS/FAIL statuses |

### Verification Results
- ✅ Safety net: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests/test_delivery_guardrails.py` → 3 passed before edits.
- ✅ RED: same targeted command after adding tests → 6 failed, 3 passed before implementation.
- ✅ GREEN: same targeted command after implementation → 9 passed.
- ✅ Quality: `uv run --with ruff ruff check scripts packages/ml/tests/test_delivery_guardrails.py` → passed.
- ✅ Full ML regression: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python -m pytest packages/ml/tests` → 76 passed.
- ✅ CLI base-ref smoke: `uv run --with pytest --with pytest-cov --with pandas --with scikit-learn --with joblib python scripts/delivery_guardrails.py --root . --base-ref HEAD --budget 400` → all checks PASS.
- ⚠️ CLI current working-tree smoke without `--base-ref` correctly failed review budget at 1,247 changed lines after accounting for untracked files; this reflects the current aggregate uncommitted diff and should be handled through chained PR slicing.

### Files Changed
- `.github/workflows/ci.yml` — runs the delivery guardrail CLI on pull requests with `fetch-depth: 0` and `--base-ref origin/${{ github.base_ref }}`.
- `scripts/delivery_guardrails.py` — adds base-ref git diff support, named CLI checks, git-error handling, malformed numstat reporting, missing-doc handling, and stronger documentation contract checks.
- `packages/ml/tests/test_delivery_guardrails.py` — adds executable coverage for CI wiring, base-ref behavior, boundary budgets, malformed/binary rows, negative documentation fixtures, missing docs, and CLI partial failures.
- `openspec/changes/customer-churn-analytics-platform/{tasks.md,apply-progress.md,verify-report.md}` — records accurate follow-up evidence.

### Workload / PR Boundary
- Mode: stacked PR remediation slice.
- Current work unit: fresh-review guardrail hardening only.
- Boundary: executable governance checks and OpenSpec evidence; no ML/API/dashboard product behavior changes.
- Estimated review budget impact: the follow-up itself is focused, but the aggregate working tree remains over 400 changed lines and should be split before PR review.

### Next Recommended
sdd-verify focused on archive readiness and delivery guardrail evidence.

---

## Phase 5.4 4R Review Blocker Remediation Follow-up

### Completed Fixes
- [x] Removed unsafe PR title/body interpolation from CI shell commands by passing PR metadata through step environment variables and testing `$PR_TITLE`/`$PR_BODY` inside the shell.
- [x] Made `uv run --no-project ... pytest packages/ml/tests/test_delivery_guardrails.py` robust by adding a test `conftest.py` that places the repository root on `sys.path` before collection.
- [x] Strengthened workflow validation to ignore commented markers, reject direct PR field shell interpolation even when env vars exist, require an active delivery-guardrail CLI with base-ref expression, and classify PR metadata validation as `safe_env`, `unsafe`, or `missing`.
- [x] Added local review-budget accounting for untracked files while preserving base-ref PR behavior.
- [x] Consolidated the 400-line policy behind `REVIEW_LINE_BUDGET` and preserved named PASS/FAIL CLI output with partial-failure non-traceback behavior.

### TDD Cycle Evidence — 4R Follow-up
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 4R follow-up | `packages/ml/tests/test_delivery_guardrails.py`, `packages/ml/tests/conftest.py` | Repository governance unit + CI-command compatibility | ✅ CI-style command failed before fix with `ModuleNotFoundError: No module named 'scripts'` | ✅ Added tests for unsafe workflow interpolation, commented guardrail markers, named budget constant, and untracked-file numstat before implementation | ✅ CI-style targeted guardrail command: 13/13 passed | ✅ Safe workflow, unsafe/commented workflow, env-plus-direct interpolation rejection, exact/default budget, base-ref clean diff, local untracked diff, malformed rows, docs shortcuts, and CLI partial failure | ✅ Extracted named constants and helper functions for workflow metadata and active-line checks |

### Verification Results
- ✅ RED/import blocker reproduced: `uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests/test_delivery_guardrails.py` → collection failed with `ModuleNotFoundError: No module named 'scripts'` before the test path fix.
- ✅ RED after new tests: same command collected tests and failed on missing `REVIEW_LINE_BUDGET` / unsafe or commented workflow behavior before implementation.
- ✅ GREEN targeted: same CI-style command → 13 passed.
- ✅ Full CI-style Python regression: `uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests apps/api/tests` → 97 passed, 2 warnings.
- ✅ Quality: `uv run --with ruff ruff check scripts packages/ml/tests/test_delivery_guardrails.py packages/ml/tests/conftest.py` → passed.
- ✅ Base-ref guardrail smoke: `uv run --no-project --python 3.12 python scripts/delivery_guardrails.py --root . --base-ref HEAD --budget 400` → all checks PASS with `changed_lines: 0`.
- ⚠️ Local aggregate guardrail smoke: `uv run --no-project --python 3.12 python scripts/delivery_guardrails.py --root . --budget 400` → review budget FAIL at 1,247 changed lines because local mode now includes untracked files.

### Files Changed
- `.github/workflows/ci.yml` — uses safe environment variables for PR metadata validation.
- `scripts/delivery_guardrails.py` — adds named policy constants, safer active workflow validation, untracked-file local numstat accounting, and helper extraction.
- `packages/ml/tests/conftest.py` — ensures repository-root imports work under CI-style `uv run --no-project ... pytest` commands.
- `packages/ml/tests/test_delivery_guardrails.py` — adds negative workflow fixtures, default budget constant coverage, untracked-file accounting, and safe CI metadata assertions.
- `openspec/changes/customer-churn-analytics-platform/{apply-progress.md,verify-report.md}` — updates evidence and current review-budget risk.

### Workload / PR Boundary
- Mode: stacked PR remediation slice.
- Current work unit: 4R delivery-guardrail blocker fixes only.
- Boundary: CI/workflow safety, guardrail resilience, import robustness, and OpenSpec evidence; no product behavior changes.
- Estimated review budget impact: the current aggregate working tree is 1,247 changed lines and remains above the 400-line review budget; split into chained PR slices before review.

### Next Recommended
sdd-verify focused on archive readiness; do not archive until verification passes.

---

## Phase 5.4 Final Focused 4R Remediation Follow-up

### Completed Fixes
- [x] Rejected disabled required workflow jobs/steps using `if: false` or `if: ${{ false }}` for `pr-validation`, `python`, `web`, `web-e2e`, and the delivery-guardrail step.
- [x] Made the delivery-guardrail CLI handle missing or mistyped `--root` values as named `FAIL root` output with status `1` and no traceback.
- [x] Updated `verify-report.md` so stale pre-fix claims are clearly superseded and the current state is remediated-but-over-budget / pending fresh `sdd-verify`.

### TDD Cycle Evidence — Final Focused 4R Follow-up
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 final 4R: disabled workflow guards | `packages/ml/tests/test_delivery_guardrails.py` | Repository governance unit | ✅ Existing focused guardrail suite: 13/13 passed before edits | ✅ Added disabled-job and disabled-step fixtures first; targeted suite failed 6 workflow cases before implementation | ✅ Targeted guardrail suite: 20/20 passed | ✅ Covers `if: false` and `if: ${{ false }}` across required jobs and delivery guardrail step | ✅ Extracted small active-line/job-block helper functions |
| 5.4 final 4R: missing root CLI resilience | `packages/ml/tests/test_delivery_guardrails.py` | CLI unit | ✅ Same focused guardrail safety net | ✅ Missing-root CLI test failed with subprocess `FileNotFoundError` before implementation | ✅ Targeted guardrail suite: 20/20 passed | ✅ Missing-root path plus existing partial-failure CLI output coverage | ✅ Early root validation before subprocess-backed checks |
| 5.4 final 4R: report accuracy | `openspec/changes/customer-churn-analytics-platform/verify-report.md` | Documentation | ✅ Report read before edits | ➖ Documentation-only update; no production behavior | ✅ Focused pytest and ruff remained green after report update | ➖ Single factual remediation update | ✅ Stale findings marked superseded; current state clarified |

### Verification Results
- ✅ Safety net before follow-up edits: `uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests/test_delivery_guardrails.py` → 13 passed.
- ✅ RED after adding disabled-workflow and missing-root tests: same targeted command → 7 failed, 13 passed.
- ✅ GREEN targeted after implementation: same targeted command → 20 passed.
- ✅ Final focused test: same targeted command → 20 passed.
- ✅ Quality: `uv run --with ruff ruff check scripts packages/ml/tests/test_delivery_guardrails.py` → passed.

### Files Changed
- `scripts/delivery_guardrails.py` — rejects disabled required workflow checks and validates `--root` before subprocess-backed checks.
- `packages/ml/tests/test_delivery_guardrails.py` — adds disabled workflow fixtures and missing-root CLI regression coverage.
- `openspec/changes/customer-churn-analytics-platform/{apply-progress.md,verify-report.md}` — records final focused remediation evidence and supersedes stale report text.

### Workload / PR Boundary
- Mode: stacked PR remediation slice.
- Current work unit: final focused 4R fixes only.
- Boundary: delivery guardrail reliability/resilience plus OpenSpec evidence; no ML/API/dashboard product behavior changes.
- Estimated review budget impact: still over the aggregate 400-line budget; split into chained PR slices or run `sdd-verify` after maintainer-approved review strategy.

### Next Recommended
sdd-verify focused on archive readiness; do not archive until verification passes and the over-budget aggregate is split or explicitly accepted.

---

## Final Reliability Follow-up: Disabled PR Metadata Validation Step

### Completed Fixes
- [x] Added a regression fixture where only the `Validate PR metadata` workflow step is disabled with `if: false` or `if: ${{ false }}`.
- [x] Updated `check_pull_request_workflow()` so disabled PR metadata validation reports `metadata_validation: disabled` and fails the guardrail.

### TDD Cycle Evidence — Final Reliability Follow-up
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 final reliability: disabled metadata validation | `packages/ml/tests/test_delivery_guardrails.py` | Repository governance unit | ✅ Existing focused guardrail suite: 20/20 passed before edits | ✅ Added metadata-step disabled fixtures first; targeted suite failed 2 workflow cases before implementation | ✅ Targeted guardrail suite: 22/22 passed | ✅ Covers `if: false` and `if: ${{ false }}` with only the metadata validation step disabled | ✅ Added a small metadata-step disabled helper using existing workflow step parsing |

### Verification Results
- ✅ Safety net before edits: `uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests/test_delivery_guardrails.py` → 20 passed.
- ✅ RED after adding disabled metadata-step fixtures: same targeted command → 2 failed, 20 passed.
- ✅ GREEN after implementation: same targeted command → 22 passed.
- ✅ Quality: `uv run --with ruff ruff check scripts packages/ml/tests/test_delivery_guardrails.py` → passed.

### Files Changed
- `scripts/delivery_guardrails.py` — fails PR workflow validation when the `Validate PR metadata` step itself is disabled.
- `packages/ml/tests/test_delivery_guardrails.py` — adds disabled metadata-validation step regression coverage.

### Workload / PR Boundary
- Mode: stacked PR remediation slice.
- Current work unit: final reliability guardrail fix only.
- Boundary: PR metadata workflow guardrail behavior and focused tests; no ML/API/dashboard product behavior changes.
- Estimated review budget impact: small focused follow-up, but the aggregate working tree still needs chained review handling.

---

## OpenSpec Process Gate Repair

### Completed Fixes
- [x] Restored valid OpenSpec delta specs under `openspec/changes/customer-churn-analytics-platform/specs/` for all six active capabilities.
- [x] Added the required proposal `Why` section while preserving the original intent, scope, approach, risks, and success criteria.
- [x] Re-ran strict OpenSpec validation successfully.

### TDD Cycle Evidence — Artifact Repair
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| OpenSpec process gate repair | OpenSpec delta specs and proposal artifact | Specification validation | ✅ Prior verify showed runtime/product checks green; artifact-only repair intentionally avoided product test reruns | ✅ Existing validation failed because the change had no parsed deltas and lacked `Why` | ✅ `pnpm dlx @fission-ai/openspec@latest validate --all --strict` passed | ✅ Six capability deltas restored, matching the active specs | ✅ Kept repair surgical; no product behavior changes |

### Verification Results
- ✅ `pnpm dlx @fission-ai/openspec@latest validate --all --strict` → 7 passed, 0 failed: six active specs plus `change/customer-churn-analytics-platform`.
- Product tests were not rerun because this batch changed only OpenSpec artifacts and proposal text.

### Files Changed
- `openspec/changes/customer-churn-analytics-platform/proposal.md` — added required `Why` section.
- `openspec/changes/customer-churn-analytics-platform/specs/*/spec.md` — restored valid delta specs for engineering workflow, dataset acquisition, ML artifacts, API, dashboard, and portfolio documentation.
- `openspec/changes/customer-churn-analytics-platform/{apply-progress.md,verify-report.md}` — records process-gate repair evidence.

### Workload / PR Boundary
- Mode: single PR, approved 800-line review budget decision preserved.
- Current work unit: surgical OpenSpec artifact repair only.
- Boundary: OpenSpec validation repair; no product behavior, runtime code, or test suite changes.

---

## Delivery Metadata Guardrail Remediation — Chained PR Decision

### Completed Fixes
- [x] Added executable PR metadata validation requiring a non-empty title, issue link, and type metadata marker.
- [x] Replaced shell-based title/body checks with Python validation fed by workflow environment variables.
- [x] Added least-privilege workflow permissions with `contents: read`.
- [x] Updated verification artifacts so the active delivery decision is chained PR slices under the 400-line budget, not single-PR readiness.

### TDD Cycle Evidence — Metadata Guardrail Follow-up
| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 5.4 metadata enforcement follow-up | `packages/ml/tests/test_delivery_guardrails.py` | Repository governance unit + CI workflow validation | ✅ Existing focused guardrail suite: 22/22 passed before edits | ✅ Added tests first; import failed because `check_pr_metadata` did not exist and workflow still used shell `test -n` checks | ✅ Targeted guardrail suite: 25/25 passed | ✅ Valid issue URL + `Type:`, closing keyword + `Labels: type:*`, and missing title/issue/type failure cases | ✅ Python validation kept pure; CI consumes env vars without direct shell interpolation |

### Verification Results
- ✅ Safety net: `uv run --no-project --python 3.12 --with pytest --with pytest-cov --with fastapi --with httpx --with pandas --with scikit-learn pytest packages/ml/tests/test_delivery_guardrails.py` → 22 passed before edits.
- ✅ RED: same targeted command after adding tests → collection failed with `ImportError: cannot import name 'check_pr_metadata'` before implementation.
- ✅ GREEN: same targeted command after implementation → 25 passed.
- ✅ CLI metadata smoke: `PR_TITLE='Add delivery guardrail metadata enforcement' PR_BODY='Issue: https://github.com/example/churn-analytics/issues/42\nType: bugfix' uv run --no-project --python 3.12 python scripts/delivery_guardrails.py --check pr-metadata` → PASS.
- ✅ OpenSpec validation: `pnpm dlx @fission-ai/openspec@latest validate --all --strict` → 7 passed, 0 failed.

### Files Changed
- `.github/workflows/ci.yml` — declares `permissions: contents: read` and runs Python PR metadata validation through safe environment variables.
- `scripts/delivery_guardrails.py` — adds pure PR metadata validation and a `--check pr-metadata` CLI path.
- `packages/ml/tests/test_delivery_guardrails.py` — adds issue-link/type-marker metadata enforcement tests and workflow assertions.
- `openspec/changes/customer-churn-analytics-platform/{apply-progress.md,verify-report.md}` — records the chained PR decision and current evidence.

### Workload / PR Boundary
- Mode: chained PR split / stacked-to-main.
- Current work unit: delivery metadata guardrail follow-up only.
- Boundary: PR metadata enforcement, workflow permission hardening, and artifact truth cleanup; no ML/API/dashboard product behavior changes.
- Estimated review budget impact: aggregate working tree remains over the 400-line slice budget; PR/archive readiness depends on splitting into work-unit PRs.

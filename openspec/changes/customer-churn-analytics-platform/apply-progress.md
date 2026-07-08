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

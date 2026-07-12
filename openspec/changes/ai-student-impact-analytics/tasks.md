# Tasks: AI-Student-Impact Risk Analytics (dataset re-point)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ML ~180-260, API ~60-100, Web-contract ~120-180, Web-UI ~140-200, Web-tests ~140-180 |
| 400-line budget risk | High (web slice, if undivided) |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 ML domain/label/leakage/fixtures -> PR 2 API contract -> PR 3a Web contract/types -> PR 3b Web UI components -> PR 3c Web tests/mocks |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |
| Strict TDD | Active |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | ML domain label/leakage single-source-of-truth + fixtures | PR 1 | Self-contained; Telco fixtures stay green; base = main. |
| 2 | API cohort allow-list + risk-distribution re-point | PR 2 | Depends on PR 1 artifacts shape; base = PR 1 branch (or main once merged). |
| 3a | Web wire contract: `types.ts` + `client.ts` mapping/guards | PR 3a | ~194 lines (156+38) touched; base = PR 2 branch. |
| 3b | Web UI: `dashboard-model.ts`, `risk-table.tsx`, `cohort-chart.tsx` | PR 3b | ~311 lines touched; depends on 3a types; base = PR 3a branch. |
| 3c | Web tests/mocks: `dashboard.test.ts`, `dashboard-model.test.ts`, `mock-dashboard-api.mjs`, `page.test.ts` | PR 3c | ~258 lines touched; depends on 3a+3b; base = PR 3b branch. Can merge same-day as 3b if reviewer capacity allows. |

Web slice sub-split rationale (resolves design gate correction #2): the design flagged the web slice (9 files, ~763 lines) as at-risk without committing to a split. Splitting strictly by architectural layer — wire contract/types (3a) vs UI rendering (3b) vs tests/mocks (3c) — keeps every PR under the 400-line budget on its own (194 / 311 / 258), avoids mixing contract changes with rendering changes in one diff, and lets 3c be reviewed independently since test/fixture diffs carry lower risk than production code.

Delivery exception note: after archive, the actual delivery branches had to be reconstructed from the completed working tree. The first ML delivery slice proved behavior-coupled across positive-label mapping, candidate/baseline training, leakage propagation, and education fixtures, so the user explicitly accepted a **size: exception** for PR1A rather than forcing a smaller but non-independent diff.

## Phase 0: Fixtures (blocking dependency for later ML tasks)

- [x] 0.1 RED: Add failing pytest fixture-loader tests in `packages/ml/tests/application/test_education_fixtures.py` asserting `packages/ml/tests/fixtures/education_sample.csv` and `education_missing_target.csv` load with the 16-column education schema, `Student_ID` as key, `Burnout_Risk_Level` as target, and both target classes represented with >=2 rows/class.
- [x] 0.2 GREEN: Create `packages/ml/tests/fixtures/education_sample.csv` and `packages/ml/tests/fixtures/education_missing_target.csv` — small deterministic fixtures mirroring the real 16-col education shape (includes `Post_Semester_GPA`, `Skill_Retention_Score` so leakage-exclusion tests in Phase 1 have something real to exclude).

## Phase 1: ML Domain — Label Mapping and Leakage Guard (PR 1)

- [x] 1.1 RED: Write failing unit tests in `packages/ml/tests/domain/test_model.py` asserting `label_to_int("High", positive_labels=POSITIVE_LABELS) == 1` and `label_to_int("Medium"/"Low", ...) == 0`, using the fixtures from 0.2.
- [x] 1.2 GREEN: In `packages/ml/src/churn_ml/domain/model.py`, add `POSITIVE_LABELS: frozenset[str] = frozenset({"High"})` and give `label_to_int` a `positive_labels: frozenset[str] = POSITIVE_LABELS` keyword param, replacing the hardcoded Telco set.
- [x] 1.3 RED: Write failing unit test in `packages/ml/tests/infrastructure/sklearn/test_baseline_trainer.py` asserting `BaselineChurnRateTrainer` maps `"High"`->1 and `"Medium"/"Low"`->0 identically to `label_to_int` for the same raw values (cross-call-site consistency scenario from spec).
- [x] 1.4 GREEN: In `packages/ml/src/churn_ml/infrastructure/sklearn/baseline.py`, replace `BaselineChurnRateTrainer`'s inline positive-label set with a `positive_labels` param defaulting to `domain.model.POSITIVE_LABELS`; delete the duplicated literal.
- [x] 1.5 RED: Write a failing unit test in `packages/ml/tests/domain/test_customer.py` — **`test_from_rows_excludes_leakage_columns_by_default`** — that calls `FeatureDictionary.from_rows(rows, customer_key="Student_ID", target_column="Burnout_Risk_Level")` **without passing `excluded_feature_columns` at all**, and asserts neither `Post_Semester_GPA` nor `Skill_Retention_Score` appears in the resulting `.features`.
- [x] 1.6 GREEN: In `packages/ml/src/churn_ml/domain/customer.py`, add a domain-level constant `LEAKAGE_COLUMNS: frozenset[str] = frozenset({"Post_Semester_GPA", "Skill_Retention_Score"})` and change `FeatureDictionary.from_rows` signature to `excluded_feature_columns: frozenset[str] = LEAKAGE_COLUMNS` (a safe named default, NOT an unsafe empty-tuple/empty-set default).
- [x] 1.7 RED: Add a second unit test — **`test_from_rows_caller_can_still_pass_explicit_exclusions`** — asserting a caller passing a custom `excluded_feature_columns` explicitly still works (regression guard so 1.6 doesn't remove caller flexibility).
- [x] 1.8 GREEN: Confirm 1.7 passes against the 1.6 implementation (no code change expected beyond 1.6; task exists to make the assertion explicit and run it).
- [x] 1.9 RED: Write failing integration test in `packages/ml/tests/application/pipelines/test_features.py` asserting `build_feature_dictionary`/`prepare_training_splits_from_csv` thread `excluded_feature_columns` through to `from_rows` and that omitting the argument at this layer ALSO still excludes the leakage columns (defense-in-depth check one layer up from 1.5-1.6).
- [x] 1.10 GREEN: Update `packages/ml/src/churn_ml/application/pipelines/features.py` — `build_feature_dictionary`/`prepare_training_splits_from_csv` accept and forward `excluded_feature_columns`, defaulting to `customer.LEAKAGE_COLUMNS` (not redefining a separate default).
- [x] 1.11 RED: Write failing test in `packages/ml/tests/application/pipelines/test_run_training.py` asserting `run_training`'s `PREDICTION_SAMPLE_COHORT_FIELDS` equals the education 4-field tuple (`Major_Category`, `Weekly_GenAI_Hours`, `Perceived_AI_Dependency`, `Institutional_Policy`) and that `LEAKAGE_COLUMNS` is re-exported/imported (not redefined) from `domain/customer.py`.
- [x] 1.12 GREEN: Update `packages/ml/src/churn_ml/application/pipelines/run_training.py` — import `LEAKAGE_COLUMNS` from `domain/customer.py`, set `PREDICTION_SAMPLE_COHORT_FIELDS` to the education 4-tuple.
- [x] 1.13 RED: Write failing integration test asserting `packages/ml/src/churn_ml/__main__.py` CLI defaults: `_DEFAULT_FEATURE_COLUMNS` = education schema minus leakage columns, `--customer-key` defaults to `Student_ID`, `--target-column` defaults to `Burnout_Risk_Level`.
- [x] 1.14 GREEN: Update `packages/ml/src/churn_ml/__main__.py` with the education defaults from 1.13.
- [x] 1.15 REFACTOR: Run the full retained Telco fixture suite (`telco_churn_sample.csv`, `telco_churn_missing_target.csv` tests) and confirm all pass unchanged — proves the binary evaluation math regression guard holds per spec's "Retained Telco Regression Fixtures" requirement.

## Phase 2: API Contract (PR 2)

- [x] 2.1 RED: Write failing test in `apps/api/tests/application/test_dashboard_contract.py` asserting `PUBLIC_PREDICTION_SAMPLE_FIELDS == ("Major_Category", "Weekly_GenAI_Hours", "Perceived_AI_Dependency", "Institutional_Policy")` and that no Telco field name (`Contract`, `tenure`, `PaymentMethod`, `MonthlyCharges`, `InternetService`) appears.
- [x] 2.2 GREEN: Update `apps/api/src/churn_api/application/dashboard_contract.py` — re-point `PUBLIC_PREDICTION_SAMPLE_FIELDS` to the education 4-tuple.
- [x] 2.3 RED: Write failing test asserting `_risk_distribution` (or equivalent in `services.py`) still returns exactly two buckets (`high`/`low`) when computed against the binarized `Burnout_Risk_Level` target artifacts — spec's "stays binary" scenario.
- [x] 2.4 GREEN: Update `apps/api/src/churn_api/application/services.py` if it hardcodes any Telco-specific field references in risk-distribution computation; confirm bucket shape unchanged.
- [x] 2.5 REFACTOR: Run full API test suite; confirm degraded-health and missing-artifact paths still pass unchanged (untouched by this slice).

## Phase 3a: Web Contract/Types (PR 3a)

- [x] 3a.1 RED: Write failing Vitest tests in `apps/web/lib/api/dashboard.test.ts` asserting the wire-guard rejects a Telco-shaped payload and accepts an education-shaped payload (`Major_Category`, `Weekly_GenAI_Hours`, `Perceived_AI_Dependency`, `Institutional_Policy`) — covers spec scenario "Wire type guard accepts only education fields".
- [x] 3a.2 GREEN: Update `apps/web/lib/api/types.ts` — replace `PredictionSample`'s Telco fields (`contract`, `tenure`, `paymentMethod`, `monthlyCharges`, `internetService`) with `majorCategory: string`, `weeklyGenAiHours: number`, `perceivedAiDependency: number | string`, `institutionalPolicy: string`.
- [x] 3a.3 GREEN: Update `apps/web/lib/api/client.ts` — rename `DashboardPredictionSampleWire` fields to education wire names (`Major_Category`, `Weekly_GenAI_Hours`, `Perceived_AI_Dependency`, `Institutional_Policy`), update `mapPredictionSample`, `isDashboardPredictionSampleWire` guard, and `isDashboardAnalyticsWireResponse` accordingly. No Telco field name may remain (spec "No Residual Telco Field References").
- [x] 3a.4 REFACTOR: Confirm 3a.1 tests pass; verify `client.ts`/`types.ts` diff stays near the ~194-line estimate.

## Phase 3b: Web UI Components (PR 3b)

- [x] 3b.1 RED: Write failing component tests for `apps/web/components/features/churn/dashboard-model.ts` (or its co-located test) asserting the model derives cohort groupings from `majorCategory` instead of `contract`.
- [x] 3b.2 GREEN: Update `apps/web/components/features/churn/dashboard-model.ts` to key cohort logic on `majorCategory`/education fields.
- [x] 3b.3 RED: Write failing test asserting `risk-table.tsx` renders `Major_Category`/`Weekly_GenAI_Hours`/`Perceived_AI_Dependency`/`Institutional_Policy` columns and contains no Telco field label.
- [x] 3b.4 GREEN: Update `apps/web/components/features/churn/risk-table.tsx` column definitions/labels to the education fields.
- [x] 3b.5 RED: Write failing test asserting `cohort-chart.tsx` groups/labels by `Major_Category` instead of `Contract`.
- [x] 3b.6 GREEN: Update `apps/web/components/features/churn/cohort-chart.tsx` grouping/labels to `Major_Category`.
- [x] 3b.7 REFACTOR: Confirm no component under `apps/web/components/features/churn/` references any Telco field name (grep sweep); diff stays near the ~311-line estimate.

## Phase 3c: Web Tests/Mocks (PR 3c)

- [x] 3c.1 GREEN: Update `apps/web/lib/api/dashboard.test.ts` fixtures/payloads to education shape (extends 3a.1 coverage with full fixture parity).
- [x] 3c.2 GREEN: Update `apps/web/components/features/churn/dashboard-model.test.ts` fixtures to education cohort data.
- [x] 3c.3 GREEN: Update `apps/web/e2e/mock-dashboard-api.mjs` mock payload to education fields for Playwright happy-path coverage.
- [x] 3c.4 GREEN: Update `apps/web/app/(dashboard)/page.test.ts` fixtures/assertions to education fields; run full Playwright E2E suite against the updated mock.
- [x] 3c.5 REFACTOR: Full web test/typecheck/E2E run; confirm zero residual Telco field references across `apps/web` (final grep sweep matching spec's "No Residual Telco Field References" requirement).

## Phase 4: Project Context and Close-out

- [x] 4.1 Update `openspec/config.yaml` project context to describe the education burnout-risk domain (per proposal's "Dependencies"/"Success Criteria").
- [x] 4.2 Verify all proposal Success Criteria checkboxes are satisfiable: shared positive-label set tested at both call sites (1.3/1.4), leakage exclusion tested at omission (1.5/1.6) and pipeline layer (1.9/1.10), API/web education fields served and guarded (2.1-2.2, 3a.1-3a.3), Telco fixtures still green (1.15), `config.yaml` updated (4.1).

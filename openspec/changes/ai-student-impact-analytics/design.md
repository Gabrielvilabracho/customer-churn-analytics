# Design: AI-Student-Impact Risk Analytics (dataset re-point)

## Technical Approach

Re-point the existing binary-classification stack at the education dataset without changing evaluation math or adding abstraction (Approach 1). Binarize `Burnout_Risk_Level` (`High`=positive) via a **single configurable positive-label set** threaded through the domain, swap the hardcoded Telco column identifiers for the education schema, enforce leakage exclusion (`Post_Semester_GPA`, `Skill_Retention_Score`) as an explicit parameter (the naming guard cannot catch it), and re-point API/web cohort fields to four education columns. Reuses `features.py`/`profile.py`/`candidate.py` transformer logic untouched. Strict TDD per `openspec/config.yaml`. Delivered as three chained PR slices (ML → API → web).

## Architecture Decisions

| Decision | Choice | Alternatives rejected | Rationale |
|---|---|---|---|
| Positive-label source of truth | New frozen default `POSITIVE_LABELS: frozenset[str] = {"High"}` in `domain/model.py`; `label_to_int(value, *, positive_labels=POSITIVE_LABELS)` gains a keyword param; `BaselineChurnRateTrainer` accepts `positive_labels` (defaults to the same constant) instead of its inline set | Duplicate literal in both files; env-var config; full multiclass `LabelEncoder` | Kills the duplication risk flagged in exploration; smallest change that keeps `int` return shape and all binary math intact. Multiclass is out of scope. |
| Leakage exclusion enforcement | Add `excluded_feature_columns: tuple[str,...]` param to `build_feature_dictionary` → `FeatureDictionary.from_rows`, threaded from `prepare_training_splits_from_csv` and defaulted in `run_training`/CLI to `("Post_Semester_GPA","Skill_Retention_Score")` | Drop columns in a pre-CSV script; rely on `screen_dataset_profile` | Guard is naming-based and will NOT catch semantic leakage; making exclusion a typed param on the feature selector means excluded columns can never silently re-enter the model, and the excluded set is unit-testable. |
| Risk distribution shape | Keep `_risk_distribution` 2-bucket (`high`/`low`) | 3-bucket | Target is binarized; N-bucket is Approach 2 (out of scope). |
| Cohort field subset | Expose 4 of 12 features: `Major_Category` (grouping), `Weekly_GenAI_Hours` (numeric metric), `Perceived_AI_Dependency`, `Institutional_Policy` | Dump all 12 features into the table | Executive cohort view needs one grouping dimension + a small set of decision-relevant signals, not the full model input. Mirrors the old 5-field Telco allow-list size. |
| Telco fixtures | Retain `telco_churn_*.csv` + their tests as regression guard for unchanged binary math; add new education fixtures alongside | Delete Telco fixtures | Proposal decision: full replacement of the live domain, fixtures retained solely to prove the binary evaluation math stays green (no live coexistence). |

## Data Flow

```text
education CSV (Student_ID key, Burnout_Risk_Level target)
  -> prepare_training_splits_from_csv(excluded_feature_columns=LEAKAGE_COLUMNS)
       -> screen_dataset_profile (Student_ID trips id-suffix guard)
       -> build_feature_dictionary (drops key + target + LEAKAGE_COLUMNS)  <-- leakage gate
  -> label_to_int(value, positive_labels={"High"})  [candidate.py, train.py x2]
     BaselineChurnRateTrainer(positive_labels={"High"})                    <-- single source
  -> binary evaluate/artifacts/threshold (UNCHANGED)
  -> run_training PREDICTION_SAMPLE_COHORT_FIELDS (education 4)
  -> API PUBLIC_PREDICTION_SAMPLE_FIELDS allow-list (education 4)
  -> web wire type/guards/mapper/DashboardModel/RiskTable/CohortChart (education 4)
```

## File Changes

| File | Action | Description |
|---|---|---|
| `packages/ml/src/churn_ml/domain/model.py` | Modify | Add `POSITIVE_LABELS={"High"}`; `label_to_int` gains `positive_labels` kw param. |
| `packages/ml/src/churn_ml/infrastructure/sklearn/baseline.py` | Modify | `BaselineChurnRateTrainer.train` takes `positive_labels` (default `POSITIVE_LABELS`), drops inline set. |
| `packages/ml/src/churn_ml/domain/customer.py` | Modify | `from_rows` gains `excluded_feature_columns`, subtracted from feature set. |
| `packages/ml/src/churn_ml/application/pipelines/features.py` | Modify | Thread `excluded_feature_columns` into `build_feature_dictionary`/`prepare_training_splits_from_csv`. |
| `packages/ml/src/churn_ml/application/pipelines/run_training.py` | Modify | `LEAKAGE_COLUMNS` default; `PREDICTION_SAMPLE_COHORT_FIELDS`→education 4. |
| `packages/ml/src/churn_ml/__main__.py` | Modify | `_DEFAULT_FEATURE_COLUMNS`→education (excl. leakage); `--customer-key=Student_ID`, `--target-column=Burnout_Risk_Level`. |
| `packages/ml/tests/fixtures/education_sample.csv`, `education_missing_target.csv` | Create | Small deterministic fixtures mirroring the 16-col shape (both target classes, ≥2 rows/class). |
| `apps/api/src/churn_api/application/dashboard_contract.py` | Modify | `PUBLIC_PREDICTION_SAMPLE_FIELDS`→education 4 + `churn_probability`. |
| `apps/web/lib/api/{client.ts,types.ts}` | Modify | Wire type/guards/mapper + `PredictionSample` fields→education 4. |
| `apps/web/components/features/churn/{dashboard-model.ts,risk-table.tsx,cohort-chart.tsx}` | Modify | Cohort keyed on `majorCategory`; table/chart columns re-labelled. |
| `apps/web/{lib/api/dashboard.test.ts, e2e/mock-dashboard-api.mjs, components/.../*.test.ts, app/(dashboard)/page.test.ts}` | Modify | Test payloads/fixtures→education fields. |
| `openspec/config.yaml` | Modify | Project context → education burnout-risk domain. |

## Interfaces / Contracts

```python
# domain/model.py
POSITIVE_LABELS: frozenset[str] = frozenset({"High"})
def label_to_int(value: Any, *, positive_labels: frozenset[str] = POSITIVE_LABELS) -> int: ...
# pipelines/run_training.py
LEAKAGE_COLUMNS = ("Post_Semester_GPA", "Skill_Retention_Score")
PREDICTION_SAMPLE_COHORT_FIELDS = ("Major_Category","Weekly_GenAI_Hours","Perceived_AI_Dependency","Institutional_Policy")
```

```ts
interface DashboardPredictionSampleWire {
  sample_id: string; display_reference: string; churn_probability: string | number;
  Major_Category: string; Weekly_GenAI_Hours: string | number;
  Perceived_AI_Dependency: string | number; Institutional_Policy: string;
}
```

Domain/application layers MUST NOT import pandas/sklearn/FastAPI. English mandatory for code/fields. `churn_probability` wire name kept (burnout probability) to avoid a gratuitous rename that widens the diff; documented as the burnout-risk score.

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Unit | `label_to_int({"High"})` + baseline share one set; excluded columns absent from `FeatureDictionary`; Telco fixtures still green | pytest, red-green-refactor; assert BOTH label paths + excluded set. |
| Integration | `run_training` on education fixture drops leakage cols, emits education cohort sample; artifact schema | fixture CSV + temp artifact store. |
| Contract/Unit | API allow-list emits education 4; web guard accepts education payload, rejects Telco-shaped | pytest + Vitest wire-guard tests. |
| E2E | dashboard happy path on education mock | Playwright mock updated. |

## Migration / Rollout

No data migration (`data/`/`artifacts/` empty). Three chained PR slices under the 400-line budget:
1. **ML domain/label + leakage + fixtures** (`model.py`, `baseline.py`, `customer.py`, `features.py`, `run_training.py`, `__main__.py`, fixtures) — self-contained, Telco tests stay green. During delivery slicing, this first ML slice proved behavior-coupled across domain mapping, candidate/baseline training, leakage propagation, and education fixtures, so a **size: exception** is explicitly accepted for the first PR when needed to keep the slice independently commit-safe.
2. **API contract** (`dashboard_contract.py`, `services.py` if touched) — targets slice 1.
3. **Web cohort fields** (`client.ts`, `types.ts`, 3 components, 4 test/mock files, `config.yaml`) — largest; targets slice 2. Split web tests from components if it exceeds budget.

## Open Questions

- [ ] None blocking. Web slice size (~8 files) is the only 400-line risk; `sdd-tasks` to confirm split.

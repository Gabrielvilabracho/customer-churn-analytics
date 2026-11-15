# Education variable analysis verification

## Outcome

S1–S7 passed independent technical verification after one correction batch and a targeted recheck. The user explicitly declined the additional native review for the UI candidate; no review receipt or approval was created for that slice. The implementation was later packaged into authorized local work-unit commits. No push, pull request or remote publication is authorized.

## Observed proof

| Check | Result |
|-------|--------|
| New statistical/publication/API tests | 28 passed before independent review; four retained verifier regression tests passed after correction |
| Full Python suite | 239 passed, two failed; the same two legacy dashboard-degradation tests fail at baseline `03a285c` |
| Full web unit suite | 16 passed, including four new education client tests; parent repeated all 16 successfully |
| Full browser suite | Six passed, including variable selection, category direction, cohort selection/suppression, SHAP sample switching and empty/degraded views |
| TypeScript | Passed after generated Next.js route types |
| Changed Python files, Ruff | Passed |
| Whole-repository Ruff | 22 identical findings on baseline and candidate, outside this feature |
| ESLint | Unavailable on both baseline and candidate: installed dependencies cannot resolve `@next/eslint-plugin-next` |
| Strict mypy | Missing pandas stubs in both environments; unavailable as a clean proof |
| Internal strict typing with untyped dependencies excluded | `python -m mypy --ignore-missing-imports packages/ml/src apps/api/src`: passed, 52 source files; independently rechecked with a fresh cache |
| Legacy compatibility | Training CLI help/unknown sibling option stdout, stderr and exit codes identical; four existing default HTTP responses and six mock scenarios identical |
| Rejection safety | Duplicate/partial analysis, traversal, symlinks, changed checksums, invalid labels/schema/nonfinite input, unsupported/mismatched model rejected with unchanged artifact hashes |
| Exact verified bytes | Offline deserialization receives verified `BytesIO`; serving never calls `joblib.load` |

The two pre-existing Python failures are `test_dashboard_degrades_when_sample_omits_public_cohort_field` and `test_cli_published_run_dashboard_degrades_instead_of_fabricating`. Their 200-versus-503 discrepancy was not changed in this additive feature. No production build or dependency installation was performed.

## Independent corrections

1. Enforce a nonempty warning list of nonempty strings, rather than accepting a truthy scalar.
2. Compare payload dataset/model identities with the verified source metadata, in addition to matching source hashes.
3. Replace inline missing-type suppressions with narrowly scoped mypy overrides for untyped scipy/sklearn imports, avoiding strict unused-ignore failures.

Three retained rejection cases initially returned 200, then returned 503 after correction. The targeted recheck exercised eight invalid payloads, one valid payload, exact unchanged source hashes, no request-time deserialization, scoped Ruff, and fresh-cache mypy. No reported blockers remain.

## Real local publication

- Historical `student-impact-run-008` metadata claimed logistic regression, but verified bytes contained an unfitted `DummyClassifier`. Interpretation correctly refused it; no historical files were overwritten.
- The unchanged standard training CLI produced `student-analysis-20261108` from the provisioned education CSV. No acceptance threshold was lowered.
- `variables-v1` was published separately: 40,000 training / 10,000 held-out rows, 29 coefficients/reference contrasts, 12 variable rankings/associations, 47 cohorts and 256 exact independent linear SHAP explanations.
- Actual `GET /analytics/education` through FastAPI TestClient returned 200 without Student_ID fields. Training and analysis artifacts remain ignored and local-only.
- Mean absolute grouped SHAP ranked Weekly_GenAI_Hours (0.7895), Year_of_Study (0.3119), Pre_Semester_GPA (0.2061), and Perceived_AI_Dependency (0.1914) highest for the selected held-out sample. This is not a causal ranking.
- Observed High burnout prevalence was 24.97%; average balanced-model score was 43.16%. Scores are not automatically calibrated clinical or population risks.

## Remaining limitations

Dataset provenance/license limitations and historical split-authentication limitations remain explicit. Explanations are local inspection evidence, not automatic student decisions. Live `/predict` remains the legacy stub. The pre-existing `apps/web/next-env.d.ts` change was preserved. See the ODD logbook for per-slice native review and local delivery status.

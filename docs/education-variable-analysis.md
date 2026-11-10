# Explore student AI-use and burnout variables

Generate offline explanations for an existing, trusted education logistic-regression model, then open `/education`. The analysis does not retrain the model, modify its published run, or replace the legacy dashboard or prediction stub.

## Generate a publication

From the repository root, with the Python environment installed:

```bash
PYTHONPATH=packages/ml/src .venv/bin/python -m churn_ml.education_analysis \
  --artifact-root artifacts \
  --run-id student-analysis-20261108 \
  --analysis-id variables-v1
```

The command reads the selected run's published metrics/model and saved train/test splits. It creates `artifacts/education/student-analysis-20261108/variables-v1/{analysis.json,completion.json}`. These files remain ignored by git. Use a new analysis ID to change settings; existing or partially reserved analysis IDs are never overwritten.

The local `student-analysis-20261108` run was generated with the unchanged standard training CLI after validation found that `student-impact-run-008` contains a `DummyClassifier` despite logistic-regression metadata. The older publication was left intact and is rejected for interpretation. On another checkout, first generate your own new model run:

```bash
PYTHONPATH=packages/ml/src .venv/bin/python -m churn_ml \
  --csv-path data/01-raw/ai-student-impact/ai_student_impact_dataset.csv \
  --dataset-id ai-student-impact --run-id student-analysis-20261108 --artifact-root artifacts
```

Do not run this training command over an existing run ID: the legacy training CLI is outside this change, and its early writes are not an overwrite-safe retry mechanism. Choose a new run ID when any local model or split directory already uses that name.

Optional settings:

| Option | Default | Meaning |
|--------|---------|---------|
| `--seed` | `42` | Deterministic held-out sampling and permutations |
| `--shap-samples` | `256` | Maximum held-out local explanations; stratified by binary outcome |
| `--permutation-samples` | `2000` | Maximum held-out rows for five permutations per original variable |
| `--min-cohort-size` | `20` | Suppress cohort statistics below this count |

Both splits must contain valid High/Medium/Low labels and both binary classes. Identifiers must be unique and disjoint between splits. Unsupported models, invalid numeric data and incomplete publications fail explicitly.

**Trust boundary:** joblib deserialization can execute arbitrary Python code. Use only your own trusted local model files, not downloaded models. Publication hashes protect against changed bytes, not a malicious publisher. The API never deserializes models.

## Serve and open

In one terminal, using the same root and run/analysis IDs:

```bash
PYTHONPATH=apps/api/src:packages/ml/src \
CHURN_ARTIFACT_ROOT=artifacts \
CHURN_ARTIFACT_RUN_ID=student-analysis-20261108 \
CHURN_EDUCATION_ANALYSIS_ID=variables-v1 \
uv run --with uvicorn uvicorn churn_api.main:app --host 127.0.0.1 --port 8000
```

The example uses `uv run --with uvicorn` because Uvicorn is not a project dependency. It may download/install Uvicorn into uv's environment if it is not cached; skip that command if dependency acquisition is not desired and use an existing ASGI server instead.

In another terminal:

```bash
CHURN_API_BASE_URL=http://127.0.0.1:8000 pnpm --dir apps/web dev --hostname 127.0.0.1 --port 3000
```

Open **http://127.0.0.1:3000/education**. Validate the API separately:

```bash
curl http://127.0.0.1:8000/analytics/education
```

The endpoint returns `200` only for the exact validated analysis publication and its unchanged sources; missing settings, unpublished analysis, invalid payloads, altered model/metrics or changed splits yield `503` with a reason. Existing `/health`, `/model/metadata`, `/analytics/dashboard` and `/predict` contracts are preserved. In particular, `/predict` still uses its existing stub by default. The old dashboard and health reader may reject relocated historical model manifests even when the new educational reader validates their allowlisted local members; use the education endpoint to check this feature.

## What each view means

| View | Evidence | Interpretation |
|------|----------|----------------|
| Overview | Held-out metrics, observed prevalence, mean model score, methodology | Positive target is **High** versus **Low + Medium**, not three-class prediction. |
| Variables | Coefficients, odds ratios, grouped SHAP ranking, permutations, train/test associations | Direction, model contribution and observed association are different quantities. |
| Cohorts | Held-out outcomes and predictions, 95% Wilson intervals, precision/recall | Numeric groups use training quartiles. Small groups are suppressed; uncertainty remains even for larger groups. |
| Explanations | Global distribution and individual cumulative SHAP waterfall | Contributions are in **log-odds**. Their sum plus the training-background base equals the fitted decision output. |

### Coefficient units and category references

Numeric inputs use the fitted training scaler. A coefficient is per training standard deviation; dividing it by the fitted scale gives the original-unit coefficient. The odds ratio is `exp(coefficient)`, not a percentage-point probability change. Positive/negative coefficients describe conditional model associations, not intervention effects.

The existing model uses full one-hot encoding, not a dropped reference category. The report retains each fitted term coefficient, but its interpreted category coefficient is `beta_category - beta_first_category`. Its odds ratio and direction describe that explicitly named reference contrast. No model encoding is refitted.

### Importance and correlations

- Global SHAP importance: sum **signed** contributions from dummy terms into the original feature for each sample, then take mean absolute contribution. It does not indicate direction.
- Permutation importance: drop in held-out average precision after shuffling each original variable, with five repeats and reported standard deviation. Negative drops remain visible.
- Numeric associations: point-biserial and Spearman against the observed binary target, separately for train/test.
- Nominal associations: Cramér's V, which has no positive/negative direction. Undefined constant-variable associations are `null`, never fabricated zeroes.
- Cohort statistics below the minimum group size display **Suppressed**. An unsuppressed cohort can still have undefined precision or recall (for example, no predicted or observed positives); those cells display **Undefined**, not Suppressed.
- Correlated predictors can share or dilute importance; no rank is a causal conclusion or a significance test. Test-set analysis is descriptive, not permission to repeatedly tune on the holdout.

### Exact independent linear SHAP

For transformed input `z`, fitted coefficient `beta` and full training-background mean `mu`:

```text
phi_j = beta_j * (z_j - mu_j)
base = intercept + sum(beta_j * mu_j)
decision_output = base + sum(phi_j)
model_probability = sigmoid(decision_output)
```

This is the exact independent/interventional linear SHAP formulation; it does **not** require installing the SHAP package and does not claim correlation-dependent credit allocation. Full training data supplies the background; deterministic held-out samples supply explanations. Category groups preserve signed additivity. Automated checks verify both log-odds additivity and probability parity. A waterfall must never label these contributions as additive probability increments.

## Provenance and responsible use

- Every analytical payload binds source run, dataset/model metadata, dependencies, sampling settings and hashes of current model publication and split bytes. Completion is written last and checked against the same in-memory payload served by the API.
- Historical manifests with old absolute paths are matched only by allowlisted local member suffixes. The reader never follows those stored paths or rewrites the publication.
- **Legacy completion manifests did not hash training splits.** This feature records current split hashes, schema and disjoint identifiers, but cannot retrospectively prove these were the original training inputs. That limitation is surfaced in every publication.
- Class balancing means raw predicted probabilities are not necessarily calibrated population risks. Do not interpret model scores as clinical probabilities.
- Source provenance and license remain as recorded for the dataset. No data is downloaded or redistributed by the command.
- Samples use run-local display IDs; Student_ID is not served. Feature combinations can still be sensitive or reidentifiable. Keep this local-only inspection tool private; it is not an authenticated production deployment or a differential-privacy system.
- Qualified human review is required. Never automate student discipline, grading, enrollment, accommodations or access to services from these outputs.

## Verification

```bash
uv run pytest packages/ml/tests/test_education_analysis.py packages/ml/tests/test_education_publication.py apps/api/tests/test_education_api.py
pnpm --dir apps/web test lib/api/education.test.ts
pnpm --dir apps/web test:e2e
```

Browser tests use an explicitly synthetic fixture, not educational research results. Existing root-dashboard tests run alongside the new education tests to detect compatibility regressions.

References: [scikit-learn pipeline inspection](https://scikit-learn.org/stable/modules/compose.html), [permutation importance](https://scikit-learn.org/stable/modules/permutation_importance.html), [linear SHAP](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html).

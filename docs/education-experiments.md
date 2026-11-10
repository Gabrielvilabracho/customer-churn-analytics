# Trustworthy education experiments

Use the Python pipeline for computation, notebooks for explanation, and optional local MLflow for comparing runs. None of these tools makes a score a validated diagnosis.

## Metric semantics

See [Classification metric semantics](metric-semantics.md) for tied-score AP,
expected top-risk capture and preservation of historical publications.

## Quick path

From the repository root, install optional local tools (the existing dashboard does not require them):

```bash
uv sync --group tracking --group notebooks
export PYTHONPATH=packages/ml/src

# Explicit trust is required: joblib can execute Python code.
uv run python -m churn_ml.experiments reevaluate \
  --artifact-root artifacts --run-id student-analysis-20261108 \
  --trusted-model --report-id reevaluation-v1

# Use your provisioned, ignored education CSV; do not download or redistribute it here.
uv run --group tracking python -m churn_ml.experiments run \
  --csv data/01-raw/ai-student-impact/your-local-file.csv \
  --report-id education-v1 --seed 42 --c-values 0.1 1 10 \
  --mlflow-dir artifacts/mlflow
```

Replace the CSV placeholder with the actual local filename. Omit `--mlflow-dir` to disable tracking entirely. A missing optional dependency is an error, not a silent fallback. The legacy `python -m churn_ml` training command remains unchanged.

The commands create `artifacts/experiments/<report-id>/report.json`, a checksum completion manifest, and (for new experiments) a serialized selected model. Reusing an ID refuses without overwrite. Reports are never automatically published to the API/dashboard. A tracking failure returns exit code 2, preserves the successful local report and reports its path; do not rerun a used report ID.

### Inspect results

Open `notebooks/EducationExperiments.ipynb` with the optional environment's Python kernel. The notebook only reads verified aggregate reports; it never trains implicitly. Set `EDUCATION_EXPERIMENT_REPORT` to a report directory to choose another run. It is committed with no outputs or personal records.

For a loopback-only MLflow UI, use the same absolute SQLite path selected by the tracker:

```bash
uv run --group tracking mlflow ui \
  --backend-store-uri "sqlite:///$(pwd)/artifacts/mlflow/tracking.db" \
  --host 127.0.0.1 --port 5000
```

The tracker explicitly selects SQLite and local artifact paths, ignoring ambient remote tracking/registry URIs. It logs configuration, final test metrics, aggregate validation/calibration reports, source/dataset hashes, and the selected model. It does not use autolog, log raw rows/IDs, register models remotely or start a server. The notebook is not automatically uploaded: log only a reviewed, privacy-safe copy explicitly if needed. Do not expose the local UI publicly.

## Independent evaluation protocol

| Stage | Data use |
| --- | --- |
| Training (~60%) | Fit numeric/categorical transformations and all estimators. |
| Validation (~20%) | Choose model and threshold; report the full threshold/workload table. |
| Final test (~20%) | Predict once for the frozen selected model and threshold. |

Splits are stratified by the original labels with seed 42 by default; per-class rounding determines actual counts. Student IDs must be nonempty/unique and are excluded from modeling. Dataset and ordered split hashes make comparisons auditable without exporting student rows. Compare runs on identical data/splits; changing the seed changes the evaluation problem.

Candidates are the existing training-prevalence baseline and balanced logistic regression with explicit `C` values. Choose the highest validation threshold meeting minimum recall (default 0.7), then rank eligible models by validation AP, ROC-AUC and precision. This is a reproducible diagnostic rule, not an operationally approved threshold. If no candidate meets the criterion the command refuses. No implicit train+validation refit occurs after selection.

Test metrics include AP, ROC-AUC, precision, recall, accuracy and expected top-20% capture. Additional diagnostics include Brier score, log loss (probabilities clipped at 1e-15 for numerical stability), ten fixed-width reliability bins, TP/FP/FN/TN, false-positive rate and flagged count/fraction. Empty reliability bins and undefined FPR are null. Calibration is measured, not fitted; class-balanced probabilities must not be treated as established calibrated risks.

## Interpretation limits

- The dataset was already explored. A new three-way split separates future code paths but does not create new external evidence or undo prior human selection.
- Historical reevaluation rescores full-precision verified model bytes; it does not use four-decimal saved predictions. Current split hashes cannot retrospectively authenticate the original training data. Existing threshold selection bias remains explicitly labeled.
- No false-positive budget, intervention cost or clinical validity is assumed. Assess review capacity before choosing an operational threshold, and never use predictions to determine grading or student-service access.
- Source code digest, library versions, selected hyperparameters and split identities are recorded. No raw data or model-containing artifacts should be committed. Respect the dataset's unresolved redistribution/license restrictions.
- Preserve original publications. Use new report IDs for corrections; changing evaluation does not authorize automatic dashboard replacement.

# Modeling Report

This report maps the education modeling workflow to its canonical evidence. Generated CSV/JSON/model files remain the local product boundary; notebooks explain reviewed aggregate reports and do not replace them. The [Model Card](model-card.md) governs intended/prohibited use, and the [Data Dictionary](data-dictionary.md) governs the 16 input fields.

## Dataset and target

| Dataset | Target | Student key | Permission and locality |
| --- | --- | --- | --- |
| Kaggle `laveshjadon/ai-impact-on-students`, version 1 | `Burnout_Risk_Level`: High versus Low + Medium | `Student_ID`, checked for integrity and excluded from features | Public API declares **CC0: Public Domain** and the local CSV is byte-identical to version 1; raw data still remain local and uncommitted |

Source permission and byte identity were verified on 2026-11-13. Exact generator code/seed and burnout-label construction remain unavailable; therefore the model evaluates a synthetic label, not validated real-student risk. See the [Dataset Card](dataset-card.md) and [source verification record](dataset-source-verification.json).

## Canonical model/report identity

The current independent experiment is report ID `education-v1`. It selected balanced logistic regression `logistic_C_1` at threshold 0.30 on validation data and evaluated it once on the 10,000-row test split. Its authoritative test metrics and workload are recorded in the [Model Card](model-card.md).

The earlier `student-analysis-20261108` model and its `variables-v1` explanatory publication are historical companion identities. They are not `education-v1`; their metrics, coefficients, SHAP values, associations, and cohorts must not be merged into the independent experiment.

## Pipeline flow

```text
local CSV
  -> source/checksum and schema profile gates
  -> identifier and post-outcome leakage exclusions
  -> deterministic stratified train / validation / test split
  -> train-only preprocessing and estimator fitting
  -> prevalence baseline plus balanced logistic candidates
  -> validation-only model and threshold selection
  -> one frozen final-test evaluation
  -> immutable local report/model and completion manifest
  -> optional aggregate-only local MLflow comparison
```

The independent protocol uses seed 42, candidate `C` values 0.1, 1, and 10, a minimum validation recall gate of 0.7, and thresholds 0.7, 0.5, and 0.3. Eligible candidates are ranked by validation average precision, ROC-AUC, and precision. There is no implicit train-plus-validation refit after selection.

## Planned model-family comparison

The next experimental phase will retain the current logistic regression as the
mandatory baseline and evaluate opt-in XGBoost and LightGBM candidates under the
same verified dataset, split hashes, feature exclusions, preprocessing policy,
seed, validation gates, threshold protocol, and frozen final-test boundary. The
implementation task must predeclare a minimum meaningful improvement and
non-regression gates; a numerically higher metric alone will not replace the
simpler baseline.

This section is a plan, not a result. `education-v1` remains the current
authoritative logistic experiment until a new immutable comparison report is
published and verified. The gated explanation, Registry, deployment, and
monitoring sequence is defined in the [model lifecycle roadmap](model-lifecycle-roadmap.md).

## Evaluation contract

Accuracy alone cannot establish value. The recorded metrics answer narrower technical questions:

| Metric | Bounded interpretation |
| --- | --- |
| Average precision (`pr_auc`) / ROC-AUC | Ranking quality on the named synthetic-label split |
| Recall / precision | Synthetic High-label capture and correctness among flagged rows at the named threshold |
| Expected top-risk capture | Tie-aware expected positive capture inside the top-score quota |
| Workload at threshold | Number/fraction of rows flagged for review; not an approved intervention capacity |
| Brier score / log loss / reliability bins | Calibration diagnostics only; calibration is measured, not fitted |

No false-positive budget, intervention cost, staffing capacity, clinical validity, or real-world outcome evidence exists. Selection is reproducible portfolio evidence, not deployment approval.

## Artifact contracts

| Identity | Local artifact contract |
| --- | --- |
| Independent experiment | `artifacts/experiments/education-v1/{report.json,model.joblib,completion.json}` |
| Historical training publication | `artifacts/{processed,metrics,models}/student-analysis-20261108/` with completion/checksum binding |
| Historical explanation | `artifacts/education/student-analysis-20261108/variables-v1/` |
| Optional tracking | Local SQLite and local artifact storage beneath the explicitly supplied `--mlflow-dir` |

Completion manifests are written last and bind immutable local members. Reusing a publication ID refuses rather than overwriting existing evidence. Reports are not automatically promoted to the API/dashboard.

## MLflow and operational boundary

Local MLflow tracking is **already implemented and optional**. When `--mlflow-dir` is supplied, the tracker records allowlisted configuration, hashes, aggregate validation/test metrics, calibration summaries, and the selected local model to an explicit SQLite backend and local artifact directory. With tracking disabled, MLflow is neither imported nor written.

The repository does not provide a remote tracking service, shared registry, approval/promotion lifecycle, automated deployment or rollback, production monitoring, drift alerts, or safety/performance alerts. Application logs use the launching process's logging configuration; centralized collection and production telemetry are not configured. See [local experiment tracking and logging boundaries](experiment-environment.md).

## Known limitations and runtime mismatch

- Synthetic labels and scales are not validated student-risk or psychological measures. Performance and explanations may reflect unknown generator rules.
- The dataset is not a live stream, representative sample, longitudinal cohort, or external validation set. No causal, clinical, fairness, or population claim is supported.
- The standard education pipeline's prediction samples omit public cohort fields required by the root dashboard contract, so that endpoint degrades with `503` rather than fabricating analytics; web visual states use a mock API in E2E tests.
- `POST /predict` is a deterministic legacy churn stub. A schema-valid education row returns fixed `0.78` probability and a `tenure_months` driver absent from the education schema. It does not serve either documented education model.
- Historical `student-analysis-20261108` explanations belong only to that model identity. They cannot supply subgroup or explanation evidence for `education-v1`.

## Responsible use and verification

These analytics are portfolio decision-support demonstrations only. They must never automate or support real decisions about discipline, grading, enrollment, accommodations, counseling, or access to services. Qualified human review is required to interpret the artifacts, but it does not make prohibited uses acceptable.

Verification commands are listed in [local verification](local-verification.md). The dated evidence record documents source/report identities and local checks without new training, metric recomputation, historical model deserialization, raw-data redistribution, or deployment. **No model documented here is approved for deployment.**

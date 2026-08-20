# Modeling Report

This report explains the modeling slice reviewers should expect from the current artifact contract. Generated CSV/JSON/model files are the product boundary, not a notebook.

## Dataset and target

| Dataset | Target | Customer key | Redistribution |
|---------|--------|--------------|----------------|
| Kaggle AI Student Impact | `Burnout_Risk_Level` binary label | `Student_ID`, excluded from features | Raw data stays local; license unverified, redistribution prohibited |

## Pipeline flow

```text
CSV dataset
  -> provenance gate: source claim, license, redistribution decision, checksum
  -> profile gate: target, duplicates, leakage, identifier-only columns
  -> deterministic stratified train/test split
  -> train-only preprocessing metadata
  -> baseline churn-rate model and candidate logistic-regression model
  -> threshold selection using churn usefulness metrics
  -> metrics/model/prediction sample artifacts under artifacts/<type>/<run_id>/
  -> completion manifest written LAST: the run is immutable once published
```

## Evaluation contract

The model is not accepted because of accuracy alone. Selection and reporting use:

| Metric | Why it matters |
|--------|----------------|
| PR-AUC / ROC-AUC | Ranking quality, especially under churn imbalance. |
| Recall / precision | Churn capture and retention workload quality. |
| Top-risk capture | Whether the highest-risk segment catches enough churners. |
| Workload at threshold | How many students need retention action. |

Models with high accuracy but poor churn recall or top-risk capture are rejected for executive reporting.

## Artifacts produced

| Path | Content |
|------|---------|
| `artifacts/processed/<run_id>/{train,test}.csv` | Clean deterministic splits. |
| `artifacts/metrics/<run_id>/metrics.json` | Manifest, metrics, threshold, feature schema. |
| `artifacts/metrics/<run_id>/prediction_samples.csv` | Evaluation rows for offline review. |
| `artifacts/models/<run_id>/{model_metadata.json,model.joblib,completion.json}` | Model metadata, scorer binary, and the immutable completion manifest. |

## Known limitations

- The education dataset is a portfolio dataset with unverified provenance, not a live production stream.
- Business impact, intervention costs, and retention offer outcomes are simulated through threshold/workload tradeoffs.
- The current education pipeline emits prediction samples without the public cohort fields of the dashboard contract, so the dashboard endpoint degrades (`503`) instead of fabricating analytics; the dashboard visual states are covered by the web E2E suite with a mock API.
- The current contract uses local files; MLflow can be added after artifact conventions stabilize.

## Responsible use

Burnout-risk analytics are decision-support-only. They require qualified human review before any consequential use and must never automate student actions such as discipline, grading, enrollment, accommodations, or access to services. The API responses carry `decision_support_only: true` and `qualified_human_review_required: true` so automated consumers can enforce the limit.

## Verification

Run the ML verification commands from `README.md` or `docs/local-verification.md`. The suite covers CSV fixture loading, identifier exclusion, deterministic splits, misleading-accuracy rejection, publication integrity (including relative-root runs), and model/artifact persistence paths.
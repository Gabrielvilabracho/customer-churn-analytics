# Modeling Report

This report explains the modeling slice reviewers should expect from the current artifact contract. Generated CSV/JSON/model files are the product boundary, not a notebook.

## Dataset and target

| Dataset | Target | Customer key | Redistribution |
|---------|--------|--------------|----------------|
| Kaggle Telco Customer Churn | `Churn` binary label | `customerID`, excluded from features | Raw data stays local unless the license permits commits |

## Pipeline flow

```text
CSV dataset
  -> profile gate: target, duplicates, leakage, identifier-only columns
  -> deterministic stratified train/test split
  -> train-only preprocessing metadata
  -> baseline churn-rate model and candidate logistic-regression model
  -> threshold selection using churn usefulness metrics
  -> metrics/model/prediction sample artifacts under artifacts/<type>/<run_id>/
```

## Evaluation contract

The model is not accepted because of accuracy alone. Selection and reporting use:

| Metric | Why it matters |
|--------|----------------|
| PR-AUC / ROC-AUC | Ranking quality, especially under churn imbalance. |
| Recall / precision | Churn capture and retention workload quality. |
| Top-risk capture | Whether the highest-risk segment catches enough churners. |
| Workload at threshold | How many customers need retention action. |

Models with high accuracy but poor churn recall or top-risk capture are rejected for executive reporting.

## Artifacts produced

| Path | Content |
|------|---------|
| `artifacts/processed/<run_id>/{train,test}.csv` | Clean deterministic splits. |
| `artifacts/metrics/<run_id>/metrics.json` | Manifest, metrics, threshold, feature schema. |
| `artifacts/metrics/<run_id>/prediction_samples.csv` | Evaluation rows enriched for dashboard cohorts. |
| `artifacts/models/<run_id>/{model_metadata.json,model.joblib}` | Model metadata and scorer binary. |

## Known limitations

- The Telco churn dataset is a portfolio dataset, not a live production stream.
- Business impact, intervention costs, and retention offer outcomes are simulated through threshold/workload tradeoffs.
- The current contract uses local files; MLflow can be added after artifact conventions stabilize.

## Verification

Run the ML verification command from `README.md` or `docs/local-verification.md`. Phase 5.1 verified 67 passing ML tests, including CSV fixture loading, identifier exclusion, deterministic splits, misleading-accuracy rejection, and model/artifact persistence paths.

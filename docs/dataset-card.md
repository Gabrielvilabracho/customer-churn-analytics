# Dataset Card

## Selected Source

- **Candidate dataset**: Kaggle Telco Customer Churn (`blastchar/telco-customer-churn`)
- **Raw data location**: `data/raw/telco-customer-churn/` on the local machine only
- **Committed data policy**: commit metadata and instructions by default; commit raw files only when the Kaggle license explicitly allows redistribution

## Local Acquisition Workflow

1. Review the dataset page on Kaggle and record the license in `docs/dataset-metadata.template.json`.
2. Keep Kaggle credentials outside the repository, for example in `~/.kaggle/kaggle.json`.
3. Download the dataset manually or with the Kaggle CLI.
4. Place the extracted CSV under `data/raw/telco-customer-churn/`.
5. Generate an acquisition manifest with the local file path, SHA-256 checksum, acquisition timestamp, license, redistribution decision, and download instructions.

## Guardrails

- Do not commit Kaggle credentials, raw restricted datasets, processed datasets, or model artifacts.
- If redistribution is not allowed, keep only metadata, checksum, and reproducibility instructions in git.
- Run the dataset profile gate before modeling to block missing targets, duplicate rows, target leakage columns, and identifier-only features.

## Current Status

The repository contains dataset acquisition primitives and local directory placeholders only. No raw data has been committed.

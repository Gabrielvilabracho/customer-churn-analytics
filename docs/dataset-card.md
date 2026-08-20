# Dataset Card

## Selected Source

- **Candidate dataset**: AI Student Impact (education AI-adoption and burnout-risk dataset, Kaggle `lazaroaluizio/ai-student-impact`)
- **Raw data location**: `data/raw/ai-student-impact/` on the local machine only (git-ignored)
- **Committed data policy**: commit metadata and instructions by default; commit raw files only when the Kaggle license explicitly allows redistribution
- **License status**: unverified on acquisition; the acquisition workflow records an `unverified`/`unknown` license as the `prohibited` redistribution decision

## Local Acquisition Workflow

1. Review the dataset page on Kaggle and record the license in `docs/dataset-metadata.template.json`.
2. Keep Kaggle credentials outside the repository, for example in `~/.kaggle/kaggle.json`.
3. Download the dataset manually or with the Kaggle CLI.
4. Place the extracted CSV at the canonical ignored path `data/raw/ai-student-impact/ai_student_impact_dataset.csv`.
5. Generate a local provenance record with the source claim when known, license status, redistribution decision, SHA-256 checksum, acquisition timestamp, and download instructions.

## Guardrails

- Do not commit Kaggle credentials, raw restricted datasets, processed datasets, or model artifacts.
- If redistribution is not allowed or license status is uncertain, keep only metadata, checksum, and reproducibility instructions in git.
- Run the dataset profile gate before modeling to block missing targets, duplicate rows, target leakage columns, and identifier-only features.

## Current Status

The repository contains dataset acquisition primitives and local directory placeholders only. No raw data has been committed, and the education CSV must be provisioned locally by the operator before running the pipeline.

## Known limitations

- The dataset is a portfolio/academic sample, not a live production stream; its provenance and license status are recorded as unverified until confirmed.
- The dataset may reflect educational and cultural bias from its collection context; predictions inherit that bias and are decision-support-only.
- The pipeline is prohibited from redistributing the raw CSV; reviewers regenerate runs from their own provisioned copy.
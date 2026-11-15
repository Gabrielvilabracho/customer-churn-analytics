---
type: workflow
title: ML Training and Artifact Publication
description: Deterministic data preparation, model evaluation, threshold selection, and immutable publication of analytical runs.
tags: [machine-learning, training, evaluation, publication]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T19:20:50.688Z
sources:
  - id: openwiki-source-bd782c7d9b03455d0865d302
    resource: repo://packages/ml/src/churn_ml/__main__.py
  - id: openwiki-source-5d3872e052fe53b8e791dbbb
    resource: repo://packages/ml/src/churn_ml/application/pipelines/evaluate.py
  - id: openwiki-source-89eec6ae1ddcd04b33a27345
    resource: repo://packages/ml/src/churn_ml/application/pipelines/run_training.py
  - id: openwiki-source-caf60caed73aa5ddcfd97b71
    resource: repo://packages/ml/src/churn_ml/application/pipelines/train.py
  - id: openwiki-source-9288354fe66885f2a6a09d16
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py
  - id: openwiki-source-e1c3f5c274d210b6a0228b05
    resource: repo://packages/ml/src/churn_ml/infrastructure/sklearn/baseline.py
generated: { by: "opencode", at: "2026-11-15T19:20:50.688Z" }
---

# ML Training and Artifact Publication

The primary ML workflow turns one local CSV into a versioned, immutable analytical run. It validates inputs before writing, uses deterministic splitting and training settings, evaluates usefulness rather than headline accuracy alone, persists the evaluated threshold, and writes the completion manifest only after all required members exist.

## Command entrypoint

Run the pipeline through the package module:

```bash
uv run --project packages/ml python -m churn_ml \
  --csv-path <local-csv> \
  --dataset-id <dataset-id> \
  --run-id <run-id> \
  --artifact-root artifacts
```

The CLI accepts an explicit seed and test fraction; defaults are `42` and `0.2`. If `run_id` is omitted, it creates an eight-character UUID prefix. Supplied IDs must begin with an alphanumeric character and contain only letters, digits, hyphens, and underscores because they become path components.

When `--provenance-json` is supplied, the CLI validates source metadata, path identity, and CSV checksum **before any artifact write**. The raw CSV remains local; acquisition records preserve dataset metadata, acquisition time, and SHA-256 without implying redistribution rights.

## Feature contract

The education target is `Burnout_Risk_Level`, with `High` as the positive class and `Low`/`Medium` as negative labels. `Student_ID` is the default traceability key and is excluded from features.

The default education feature set includes academic context, AI usage, study behavior, perceived dependency, institutional policy, and exam anxiety. `Post_Semester_GPA` and `Skill_Retention_Score` are deliberately excluded as post-outcome leakage risks.

Data preparation creates deterministic train/test splits, records split metadata, infers the feature schema used by downstream validation, and writes processed CSV/JSON artifacts under the selected run. The split metadata binds run ID, dataset ID, split name, feature columns, target column, and row count.

## Training orchestration

`run_training` receives trainers and persistence through ports. The production CLI composes:

- a prevalence baseline that predicts the training positive rate;
- a scikit-learn logistic-regression candidate with the explicit feature set and seed;
- a filesystem artifact store.

The candidate must receive at least two rows and both target classes. When scikit-learn is available it produces the fitted probability model used for publication and later education analysis.

The pipeline writes processed splits first, trains and evaluates, derives a public feature schema, builds bounded prediction samples from the held-out rows, and saves the metrics bundle. If training or evaluation fails, it deletes partial processed splits before re-raising the error.

## Evaluation metrics

Evaluation records:

- PR-AUC / average precision;
- ROC-AUC with ties receiving half credit;
- precision;
- recall;
- accuracy;
- top-risk capture;
- workload at the selected threshold.

Top-risk capture ranks probabilities and handles equal-score boundary ties with a label-blind expected capture. This avoids making the metric depend on arbitrary row order when several records have the same score.

## Threshold selection

The default candidates are `0.7`, `0.5`, and `0.3`, considered from highest to lowest. For each threshold, the pipeline computes recall and workload. It selects the highest threshold that reaches the minimum recall requirement and persists a human-readable tradeoff such as:

```text
Selected threshold 0.50 to reach recall 0.80 with workload 0.35.
```

Choosing the highest qualifying threshold constrains review workload while satisfying the recall floor. If no candidate reaches the required recall, training fails instead of silently choosing a threshold that violates the operating requirement.

The persisted threshold is later reused by API risk decisions, cohort metrics, and education analysis. Downstream code must not silently replace it with a newly invented cutoff.

## Misleading-accuracy gate

Accuracy is not accepted as sufficient evidence for an imbalanced risk problem. If accuracy is at least `0.8` while recall or top-risk capture remains below its configured minimum, `reject_misleading_accuracy` raises an evaluation error:

```text
Model has misleading accuracy and is unsuitable for executive reporting.
```

This gate prevents a model that mostly predicts the majority class from appearing useful in an executive dashboard. Evaluation must demonstrate that the model actually identifies positive cases and concentrates them in the reviewable high-risk segment.

## Baseline comparison

The candidate and prevalence baseline are evaluated on the same held-out rows and selected threshold. Model comparison uses a lexicographic usefulness score ordered by recall, top-risk capture, PR-AUC, and precision.

The artifact manifest records the trained candidate identity, while the comparison records whether the candidate actually surpassed the baseline. Consumers should preserve this distinction instead of implying that publication alone proves superiority.

## Prediction samples

When a trained candidate is available, the pipeline scores held-out rows and stores a bounded public sample containing the traceability key, formatted probability, actual label, and any supported cohort fields present in the source.

The legacy customer dashboard expects `Contract`, `tenure`, `PaymentMethod`, `MonthlyCharges`, and `InternetService`. Education datasets generally lack these fields. The pipeline omits absent fields, and the API may degrade the legacy dashboard contract rather than invent them.

## Publication ordering and failure behavior

The CLI acquires a per-run lease before training and releases it in a `finally` block. Every CLI invocation records the same owner value, and the store treats reacquisition by that owner as idempotent. Because initial lease existence and creation are separate operations, the lease records lifecycle intent but does not provide atomic mutual exclusion: concurrent CLI processes using the same run ID can both proceed. Operators must avoid concurrent publication under one run identity.

Successful publication order is:

1. processed train/test splits;
2. evaluated metrics bundle and prediction samples;
3. trained model binary via temporary file and atomic replacement;
4. binary checksum sidecar and model metadata;
5. completion manifest written last with required-member checksums.

If model-binary persistence fails, the CLI reports that the metrics bundle exists but the model is missing and re-raises. The completion manifest is not written, so readers still treat the run as unpublished. A retry may use the same run while it remains incomplete; once completion exists, immutable publication prevents overwrite.

## Verification focus

- acquisition tests pin source metadata and checksum behavior;
- dataset/profile tests pin schema and data-quality rules;
- evaluation tests pin tie-safe metrics, threshold selection, misleading-accuracy rejection, and baseline comparison;
- integration tests pin CLI-to-artifact behavior;
- artifact tests pin leases, required-member preflight, checksums, immutability, and load round-trips.

## Related pages

- [Artifact Contracts and Persistence](../architecture/artifact-contracts.md)
- [Education Impact Analysis Workflow](education-analysis.md)
- [Local Development and Verification](../operations/local-development-and-verification.md)

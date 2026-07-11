## ADDED Requirements

### Requirement: Reproducible EDA and Feature Artifacts

The system MUST produce deterministic EDA summaries, schema documentation, cleaned train/validation/test splits, and a feature dictionary from the approved dataset.

#### Scenario: Cleaning pipeline completes

- GIVEN an approved dataset and fixed random seed
- WHEN preprocessing runs
- THEN the system writes cleaned splits and feature metadata
- AND repeated runs produce equivalent schema and split counts

#### Scenario: Invalid input schema

- GIVEN a dataset missing required target or customer fields
- WHEN preprocessing validates inputs
- THEN the system MUST fail with a clear schema error and write no training artifacts

### Requirement: Model Evaluation and Threshold Artifacts

The system SHALL train at least one baseline and one candidate model, then export metrics, selected threshold, model metadata, and prediction samples as CSV/JSON artifacts.

#### Scenario: Model is evaluated for churn usefulness

- GIVEN trained model candidates
- WHEN evaluation completes
- THEN the system reports PR-AUC, ROC-AUC, precision, recall, top-risk capture, and workload at threshold
- AND selects a threshold with documented tradeoffs

#### Scenario: Accuracy is misleading

- GIVEN high accuracy but poor churn recall or top-risk capture
- WHEN model selection runs
- THEN the system MUST flag the model as unsuitable for executive reporting

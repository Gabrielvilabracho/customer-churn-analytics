# Churn ML Artifacts Specification

## Purpose

Define the required analytical artifacts for EDA, cleaning, feature engineering, training, evaluation, and threshold selection.

## Requirements

### Requirement: Reproducible EDA and Feature Artifacts

The system MUST produce deterministic EDA summaries, schema documentation, cleaned train/validation/test splits, and a feature dictionary from the approved dataset. The feature schema MUST be the education dataset's columns (`Major_Category`, `Year_of_Study`, `Pre_Semester_GPA`, `Weekly_GenAI_Hours`, `Primary_Use_Case`, `Prompt_Engineering_Skill`, `Tool_Diversity`, `Paid_Subscription`, `Traditional_Study_Hours`, `Perceived_AI_Dependency`, `Institutional_Policy`, `Anxiety_Level_During_Exams`), with `Student_ID` treated as the identifier key and `Burnout_Risk_Level` as the target. The feature schema MUST NOT include `Post_Semester_GPA` or `Skill_Retention_Score`; both MUST be explicitly excluded as leakage regardless of the naming-based leakage guard's outcome.

#### Scenario: Cleaning pipeline completes

- GIVEN an approved dataset and fixed random seed
- WHEN preprocessing runs
- THEN the system writes cleaned splits and feature metadata
- AND repeated runs produce equivalent schema and split counts

#### Scenario: Invalid input schema

- GIVEN a dataset missing required target or customer fields
- WHEN preprocessing validates inputs
- THEN the system MUST fail with a clear schema error and write no training artifacts

#### Scenario: Leakage columns are excluded from the feature dictionary

- GIVEN the raw education dataset containing `Post_Semester_GPA` and `Skill_Retention_Score`
- WHEN the feature dictionary is built
- THEN neither `Post_Semester_GPA` nor `Skill_Retention_Score` appears in the resulting feature set
- AND this exclusion holds even though the naming-based leakage guard does not flag either column

### Requirement: Model Evaluation and Threshold Artifacts

The system SHALL train at least one baseline and one candidate model against a binarized target derived from `Burnout_Risk_Level`, then export metrics, selected threshold, model metadata, and prediction samples as CSV/JSON artifacts. The positive-class label set MUST be defined in exactly one shared, configurable location consumed by both `label_to_int` and the baseline trainer; no call site may hardcode its own copy of the positive-label set.

#### Scenario: Model is evaluated for churn usefulness

- GIVEN trained model candidates
- WHEN evaluation completes
- THEN the system reports PR-AUC, ROC-AUC, precision, recall, top-risk capture, and workload at threshold
- AND selects a threshold with documented tradeoffs

#### Scenario: Accuracy is misleading

- GIVEN high accuracy but poor churn recall or top-risk capture
- WHEN model selection runs
- THEN the system MUST flag the model as unsuitable for executive reporting

#### Scenario: High burnout risk binarizes to the positive class

- GIVEN a raw `Burnout_Risk_Level` value of `High`
- WHEN the label mapping converts it to a training label
- THEN the system MUST map it to the positive class (`1`)

#### Scenario: Medium and Low burnout risk binarize to the negative class

- GIVEN a raw `Burnout_Risk_Level` value of `Medium` or `Low`
- WHEN the label mapping converts it to a training label
- THEN the system MUST map it to the negative class (`0`)

#### Scenario: Positive-label set stays consistent across both call sites

- GIVEN the shared positive-label configuration is set to binarize `Burnout_Risk_Level`
- WHEN both `label_to_int` and the baseline trainer map the same raw label value
- THEN both call sites MUST produce the identical binary label for that value

### Requirement: Retained Telco Regression Fixtures

The system MUST retain the existing Telco churn test fixtures (`telco_churn_sample.csv`, `telco_churn_missing_target.csv`) and their associated tests as a regression suite proving the unchanged binary evaluation math still functions correctly, independent of the education dataset's label mapping and feature schema.

#### Scenario: Telco fixture tests remain green after the dataset swap

- GIVEN the retained Telco churn fixtures and their existing tests
- WHEN the test suite runs after the education dataset schema and label mapping changes are applied
- THEN all retained Telco fixture tests MUST pass unchanged

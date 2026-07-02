# Dataset Acquisition Specification

## Purpose

Define reproducible, legal, and leakage-aware acquisition behavior for the churn dataset before modeling begins.

## Requirements

### Requirement: Dataset Source Contract

The system MUST record the selected Kaggle or manual dataset source, license, redistribution decision, download instructions, checksum, and acquisition timestamp before any raw data is used.

#### Scenario: Approved dataset is registered

- GIVEN a candidate churn dataset with a readable license
- WHEN the acquisition plan is accepted
- THEN the system records source metadata, checksum, and local-only credential guidance
- AND the raw data is committed only when redistribution is allowed

#### Scenario: Redistribution is not allowed

- GIVEN a dataset license that forbids redistribution
- WHEN acquisition documentation is generated
- THEN the system MUST store metadata and download instructions instead of raw data

### Requirement: Dataset Quality and Leakage Gate

The system SHALL screen the dataset for target leakage, identifier-only features, missing target labels, duplicate rows, and toy-like limitations before approving it for modeling.

#### Scenario: Dataset passes screening

- GIVEN a dataset with valid labels and no detected leakage
- WHEN the quality gate runs
- THEN the system marks the dataset as modeling-ready with documented limitations

#### Scenario: Leakage is detected

- GIVEN a feature that reveals churn after the outcome is known
- WHEN the leakage gate runs
- THEN the system MUST block modeling until the feature is removed or justified

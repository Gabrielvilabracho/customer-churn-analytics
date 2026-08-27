# Dataset Acquisition Specification

## Purpose

Define reproducible, legal, and leakage-aware acquisition behavior for the churn dataset before modeling begins.

## Requirements

### Requirement: Dataset Source Contract

The system MUST provision an operator-supplied education CSV only at the ignored canonical path `data/raw/ai-student-impact/ai_student_impact_dataset.csv`. Before use, it MUST record the source claim when known, license status, redistribution decision, SHA-256 checksum, and acquisition timestamp in local provenance metadata. The CSV and local metadata MUST remain untracked and MUST NOT be redistributed. An `unverified` or `unknown` license status MUST use the `prohibited` redistribution decision; missing or contradictory provenance metadata MUST block training before artifact writes.

#### Scenario: Education dataset is provisioned locally

- GIVEN an operator-supplied education CSV
- WHEN it is provisioned for the supported local workflow
- THEN the CSV exists at the canonical ignored path
- AND local provenance records its checksum, timestamp, license status, and redistribution decision

#### Scenario: License or provenance is unverified

- GIVEN the CSV source or redistribution license cannot be verified
- WHEN provisioning is completed
- THEN the provenance record MUST mark the uncertainty and prohibit redistribution
- AND neither the CSV nor its local metadata may appear in tracked changes

#### Scenario: Uncertain licensing is paired with redistribution permission

- GIVEN local provenance has an `unverified` or `unknown` license status
- WHEN its redistribution decision is not `prohibited`
- THEN local provenance validation MUST reject the contradictory record before training writes artifacts

#### Scenario: Provisioned content changes

- GIVEN a provenance record for the canonical CSV
- WHEN the CSV checksum no longer matches that record
- THEN the dataset MUST NOT be treated as the recorded input until provenance is refreshed

#### Scenario: Training is attempted without valid local provenance

- GIVEN the canonical CSV lacks local provenance, has an invalid acquisition timestamp, omits source or license/restriction status, or its SHA-256 differs from the provenance record
- WHEN the ML CLI is invoked
- THEN training MUST stop before any artifact is written
- AND the operator-visible failure MUST identify local provenance validation

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

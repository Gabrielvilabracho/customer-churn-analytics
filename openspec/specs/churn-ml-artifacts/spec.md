# Churn ML Artifacts Specification

## Purpose

Define the required analytical artifacts for EDA, cleaning, feature engineering, training, evaluation, and threshold selection.

## Requirements

### Requirement: Complete Local Dashboard Run

The supported local workflow MUST execute training with an explicit run ID matching `[A-Za-z0-9_-]+`. That identity MUST be recorded in the generated manifest and selected for later API startup; the workflow MUST NOT discover or substitute a `latest` run. A serveable run MUST contain metrics and threshold data, prediction samples, model metadata, `model.joblib`, and its SHA-256 checksum under that same identity.

#### Scenario: Explicit run produces a complete bundle

- GIVEN the provisioned education CSV and an explicit safe run ID
- WHEN the ML workflow completes successfully
- THEN every required serving artifact exists under that run ID
- AND the manifest and reported selected run identity equal the requested value

#### Scenario: Run identity is unsafe

- GIVEN an empty run ID or one containing path separators or unsupported characters
- WHEN artifact generation is requested
- THEN the workflow MUST reject the run identity rather than write outside its run namespace

#### Scenario: Required output is incomplete

- GIVEN training produced only part of the required serving bundle
- WHEN the run is validated for dashboard use
- THEN the run MUST be reported as incomplete
- AND it MUST NOT be presented as ready for API selection

### Requirement: Atomic Completed-Run Publication

The ML workflow MUST publish a run only after all serving members validate. Publication MUST create one atomic completion manifest containing the requested run ID, a generation identifier, and checksums for every required member. Concurrent publication attempts for the same run ID MUST be serialized so only one generation becomes visible. A published run MUST NOT be overwritten in place. Serving reads MUST load and validate the exact in-memory bytes identified by one completion manifest generation, without a separate validation/read interval. Serving validation MUST reject an unpublished run, a member whose checksum or embedded run ID differs from the completion manifest boundary, or any other mixed-generation state.

#### Scenario: Complete run is published atomically

- GIVEN all required serving members for one explicit run ID are present and internally valid
- WHEN the ML CLI completes publication
- THEN one completion manifest is atomically visible for that run
- AND subsequent readers serve only members validated by that manifest

#### Scenario: Published members are changed or identities disagree

- GIVEN a published run
- WHEN a required member is changed, its embedded run ID differs, or an overwrite is attempted
- THEN validation MUST reject the run as unavailable
- AND the API MUST NOT serve a mixed generation

#### Scenario: Concurrent publishers target one run

- GIVEN two publishers attempt to complete the same explicit run ID
- WHEN publication is attempted concurrently
- THEN exactly one completion generation MUST be published
- AND the other publisher MUST be rejected without interleaving the published boundary

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

# ML experiment evaluation delta

## MODIFIED Requirements
### Requirement: Tied scores have label-independent metric semantics
Average precision SHALL group equal scores. Top-risk capture SHALL use proportional expected positives in a tied boundary block while retaining the existing rounded population quota. Existing metric field names and non-tied results SHALL remain compatible.

#### Scenario: Constant predictions
Given four equal scores and two positive labels, average precision SHALL be 0.5 and expected capture for the highest half SHALL be 0.5, regardless of row order.

## ADDED Requirements
### Requirement: Historical reevaluation is additive
The offline command SHALL load only verified bytes of an explicitly trusted local model, bind reports to current source hashes, disclose unbound historical split provenance and preserve every published source byte. Duplicate output identities SHALL refuse without overwrite.

### Requirement: Experiment selection excludes final test data
Training SHALL fit preprocessing and estimators using training rows only. Validation SHALL select the estimator and threshold before final test predictions. The final report SHALL identify data/code/configuration, disjoint split counts/hashes, selection metrics and final test metrics separately. It SHALL report calibration diagnostics and false-positive workload without claiming learned calibration or operational suitability.

### Requirement: Experiment tracking is optional and local
With tracking disabled no MLflow import or write SHALL occur. Explicit tracking SHALL use local SQLite and local artifact storage independent of ambient remote tracking settings. Tracking SHALL allowlist parameters and aggregate reports, excluding raw rows, IDs, source filenames and individual predictions.

### Requirement: Model-family comparisons are evidence-equivalent
The experiment workflow SHALL retain logistic regression as a mandatory baseline and MAY add XGBoost and LightGBM through optional infrastructure adapters. Every candidate SHALL use the same verified dataset identity, split hashes, feature exclusions, preprocessing policy, seed, validation thresholds and selection criteria. Optional dependency absence SHALL fail that candidate explicitly without changing the baseline workflow.

Candidate attribution SHALL preserve model family and hyperparameters without lossy names. Validation evidence SHALL select the model and threshold before one frozen final-test evaluation. The immutable report and optional MLflow run SHALL agree on candidate configuration, split identity, metrics, diagnostics, selected model and model checksum. No candidate SHALL be promoted solely because one metric is numerically higher; the execution task SHALL define minimum meaningful improvement and non-regression gates before training.

### Requirement: Advanced selection is gated against the logistic reference
The best validation candidate in the mandatory logistic family that satisfies the existing 0.70 recall gate SHALL be the advanced-model reference. Eligible logistic candidates SHALL be ordered by higher average precision, higher ROC-AUC, higher precision and then ascending stable model name. An XGBoost or LightGBM candidate SHALL qualify only when its validation average precision is at least 0.01 absolute higher and its recall remains at least 0.70 while Brier score, false-positive rate and flagged fraction are each no worse at the independently selected validation thresholds. When no advanced candidate clears every gate, the workflow SHALL retain the logistic reference.

#### Scenario: A higher-ranking candidate regresses a guardrail
Given an advanced candidate with an average-precision improvement of at least 0.01 but worse Brier score, false-positive rate or flagged fraction than the logistic reference, validation SHALL record the failed gate and SHALL retain the logistic reference without consulting final-test evidence.

#### Scenario: Multiple advanced candidates clear every gate
Given multiple qualifying advanced candidates, selection SHALL be deterministic by higher average precision, lower Brier score, lower false-positive rate, lower flagged fraction and stable model name in that order.

### Requirement: Candidate activation is explicit and baseline-safe
The default experiment command SHALL run without importing XGBoost or LightGBM. A repeatable candidate-family option MAY request either adapter from an independently locked optional dependency group. A requested but unavailable adapter SHALL fail explicitly before model fitting rather than silently omitting the candidate or changing logistic behavior. Tree estimators SHALL use fixed predeclared configurations and SHALL NOT use the shared validation split for early stopping.

#### Scenario: An optional dependency is unavailable
Given a request for an unavailable XGBoost or LightGBM adapter, the command SHALL fail before fitting any candidate and SHALL leave the requested report destination unpublished.

### Requirement: Comparable-candidate evidence is additive and checksum-bound
New comparable-candidate reports SHALL use schema version 2 and SHALL record family, dependency/runtime versions, lossless hyperparameters, gate outcomes and deltas, split identities, selected threshold and the serialized selected-model checksum. Report verification SHALL continue to accept immutable schema-version-1 evidence without rewriting or reinterpreting it. Optional MLflow tracking SHALL mirror the same allowlisted aggregate evidence and checksum without rows, identifiers or individual predictions.

#### Scenario: Selection is frozen before final evaluation
Given any number of requested candidate families, all model, threshold and gate decisions SHALL be complete from validation evidence before the selected model receives exactly one final-test prediction. No final-test score, label, metric or diagnostic SHALL affect selection.

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

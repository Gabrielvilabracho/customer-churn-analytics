# Trustworthy education experiments

Correct tied-score evaluation before comparing experiments. Add a standalone education experiment workflow without replacing the existing training CLI, verified publications, API or dashboard.

## Scope
- Tie-grouped average precision and expected top-fraction capture without label-based tie ordering.
- Immutable reevaluation of a trusted existing education model at full prediction precision.
- Separate training, validation selection and final test evaluation, with calibration and workload diagnostics.
- Optional local SQLite MLflow tracking and a notebook calling tested Python functions.

## Boundaries
No remote services, raw student tracking, redistribution, automatic student decisions, implicit calibrator fitting or historical artifact rewriting. Existing explored data cannot become a genuinely unseen external validation set. Diagnostic experiments do not promote or replace dashboard models.

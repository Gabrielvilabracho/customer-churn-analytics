# Experiment documentation delta

## ADDED Requirements
### Requirement: Notebook reuses the analytical core
The education experiment notebook SHALL call tested pipeline/report functions rather than duplicate metric, split or training logic. It SHALL ship without executed outputs or personal student records, explain independent evaluation limits and document optional local dependencies and CLI equivalents.

### Requirement: Candidate comparison is reviewable
Reviewer-facing documentation SHALL distinguish implemented evidence from planned capability and present logistic regression, XGBoost and LightGBM results under one comparison contract. It SHALL identify the selected model, the predeclared selection and non-regression gates, calibration and workload tradeoffs, dependency status, and the reason the simpler baseline was retained or replaced. MLflow and notebooks SHALL remain views over immutable reports rather than independent authorities.

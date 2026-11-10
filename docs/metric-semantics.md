# Classification metric semantics

The public `pr_auc` field reports average precision, not trapezoidal PR area.
Equal scores are evaluated together at their shared threshold. Constant scores
therefore have average precision equal to positive prevalence, rather than 1.0.

Top-risk capture retains the existing rounded population quota. When a tied
group crosses that quota, it reports expected capture under uniformly random,
label-blind selection within that group. This fractional expectation is not a
claimed list of identified students. Non-tied results and other metric fields
retain their existing behavior.

Published metric files are historical records and are not rewritten by this fix.
Reevaluation requires a new report identity. Metric corrections do not establish
calibrated probabilities, causal effects or suitability for student decisions.

Run the focused regression suite with:

```bash
python -m pytest --no-cov packages/ml/tests/test_ml_evaluation_pipeline.py
```

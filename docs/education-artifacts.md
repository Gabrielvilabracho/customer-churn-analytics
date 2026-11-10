# Publish a local education analysis

Explain an existing fitted education logistic model without retraining or
rewriting its published run. Use only your own trusted local model files:
checksums establish integrity, not authenticity, and joblib can execute code.

## Quick path

From the repository root, with the local ML dependencies installed:

```bash
PYTHONPATH=packages/ml/src uv run python -m churn_ml.education_analysis \
  --artifact-root artifacts \
  --run-id student-analysis-20261108 \
  --analysis-id variables-v2 \
  --seed 42 --shap-samples 256 --permutation-samples 2000 \
  --min-cohort-size 20
```

Choose a new analysis ID on every publication. An existing or partial output
directory is never overwritten. Invalid sources or arguments return an error,
not fabricated analysis. Sampling limits and minimum cohort size are also
described by `python -m churn_ml.education_analysis --help`.

The default output is `artifacts/education/<run-id>/<analysis-id>/analysis.json`
with a checksum-bound `completion.json`. This namespace stays local and ignored
by Git. If you choose another artifact root, keep its generated outputs ignored.
Raw datasets and serialized models must not be committed or redistributed.

## Evidence and limits

The analysis contains coefficient units and category references, held-out
permutation importance, independent linear SHAP in log-odds, associations and
student cohorts with 95% Wilson intervals. Small-cohort statistics are suppressed.

Current source bytes and split files are hashed, but historical manifests cannot
authenticate the original training-split provenance. Evaluation metrics remain
those of the original run: feature analysis is not metric reevaluation. Neither
the scores nor associations establish calibrated risks, diagnoses or causality.

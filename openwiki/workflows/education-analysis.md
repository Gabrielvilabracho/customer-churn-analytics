---
type: workflow
title: Education Impact Analysis Workflow
description: Verified offline analysis of a published education model, including associations, cohorts, interpretability, immutable publication, and historical reevaluation.
tags: [education, interpretability, shap, statistics]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T19:20:50.688Z
sources:
  - id: openwiki-source-ad703eace67dd8d6e2e8b51c
    resource: repo://packages/ml/src/churn_ml/application/pipelines/analyze_education.py
  - id: openwiki-source-9e019eff6c52f37d9ef8199a
    resource: repo://packages/ml/src/churn_ml/application/pipelines/reevaluate_education.py
  - id: openwiki-source-74278f81fe4608fe3cf58291
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/education_analysis_adapters.py
  - id: openwiki-source-9289f3e3574caa365d4423ad
    resource: repo://packages/ml/src/churn_ml/infrastructure/filesystem/education_analysis_store.py
  - id: openwiki-source-a2dc777f4dc9e561dd174c20
    resource: repo://packages/ml/src/churn_ml/infrastructure/sklearn/education_interpretability.py
  - id: openwiki-source-572a8252499099109b9d8927
    resource: repo://packages/ml/src/churn_ml/infrastructure/sklearn/education_statistics.py
generated: { by: "opencode", at: "2026-11-15T19:20:50.688Z" }
---

# Education Impact Analysis Workflow

The education workflow explains a previously published, locally trusted logistic model. It does **not** retrain that model, rewrite its run, or claim that measured associations are causal effects. It produces a new immutable analysis publication bound to the exact model, split, metrics, and source bytes it inspected.

## Primary publication flow

```text
exact run_id + new analysis_id
        │
        ▼
check analysis identity availability
        │
        ▼
load and checksum-verify model, metrics, train split, and test split
        │
        ▼
validate estimator, feature schema, labels, IDs, and disjoint splits
        │
        ▼
compute coefficients, importance, associations, cohorts, and SHAP
        │
        ▼
attach source hashes, versions, model metrics, methodology, and warnings
        │
        ▼
re-verify source hashes after computation
        │
        ▼
publish analysis.json, then completion.json
```

The application pipeline depends on three ports: an input loader, an analysis engine, and a publisher. The CLI composes those ports with verified filesystem adapters and the scikit-learn engine.

Default parameters are deterministic: seed `42`, up to `256` SHAP samples, up to `2000` permutation samples, and minimum cohort size `20`. Operators may override them, but invalid thresholds, sample limits, or cohort sizes are rejected.

## Trusted-input boundary

The workflow reads only an exact published `run_id`. It verifies completion-manifest members and checksums, model sidecar checksum, train/test split metadata, dataset identity, model identity, target column, feature schema, and split row counts.

The verified model bytes are deserialized from memory. Joblib loading can execute Python code, so the CLI and reevaluation workflow require a model from a locally trusted publication. Checksums establish byte stability, not producer authenticity.

The analysis rejects unsupported or unsafe model shapes. It requires a fitted scikit-learn pipeline containing a `ColumnTransformer` followed by binary `LogisticRegression`. It also requires:

- unique `Student_ID` values with no overlap between train and test;
- both binary target classes in each split;
- only `High`, `Medium`, and `Low` source labels;
- finite numeric features and non-missing categorical features;
- a feature schema that excludes `Student_ID`, the target, `Post_Semester_GPA`, and `Skill_Retention_Score`.

These checks protect against identifier leakage, target leakage, post-outcome leakage, and invalid held-out comparisons.

## Coefficients and odds ratios

The engine inspects the fitted logistic classifier without refitting it. Numeric coefficients are reported per training standard deviation and also converted to original-unit coefficients. Categorical coefficients are represented as contrasts against the named first category because the training encoder keeps the full one-hot set.

Each coefficient receives a positive, negative, or neutral direction and a finite exponentiated odds ratio. These values explain the fitted model's linear terms; they are not causal treatment effects.

## Held-out feature importance

Global importance combines two signals on the held-out test split:

- mean absolute grouped SHAP contribution;
- average-precision drop when one original feature is permuted.

Permutation uses deterministic sampling and five repeats per variable. Reporting the standard deviation alongside the mean drop exposes instability rather than presenting one shuffle as definitive.

## Associations

Associations are descriptive and reported separately for train and test:

- numeric features use point-biserial and Spearman statistics when variation makes them defined;
- categorical features use Cramér's V from a contingency table;
- every result includes count and missing count.

The split-specific presentation helps reviewers see whether a measured relationship is stable across the fitted and held-out data. It still does not establish causality or clinical meaning.

## Cohort comparisons and uncertainty

Categorical cohorts use their observed categories. Numeric cohort boundaries are quartiles computed from the **training** split and then applied to the test split, so held-out outcomes do not define the bins.

For every test cohort, the analysis records count and suppression state. Cohorts smaller than `minimum_cohort_size` retain their label and count but set observed rate, Wilson confidence interval, average predicted risk, difference from overall, precision, and recall to `null`.

Unsuppressed observed-high rates receive a bounded 95% Wilson interval. Precision and recall use the run's persisted threshold. This makes sample size and uncertainty visible while preventing unstable small-group statistics from appearing precise.

## Independent linear SHAP

The supported explainer is exact independent linear SHAP in `log_odds` units:

1. the transformed training mean defines the background;
2. held-out samples are selected deterministically with class-aware sampling;
3. transformed values minus the background are multiplied by fitted coefficients;
4. encoded-term contributions are grouped back to original features;
5. the base value plus grouped contributions must equal the model decision output;
6. the logistic transform of that output must equal `predict_proba`.

Both parity checks use strict numerical tolerance. The publication warns that an independent background ignores feature dependence, so correlated predictors may share or redistribute explanatory credit.

## Immutable and source-bound publication

The application pipeline rejects an existing analysis identity before loading or computing, but this availability check does not reserve the identity. Concurrent processes can both pass the check and perform the analysis. After analysis, the pipeline adds schema version, run/analysis identity, dataset/model identity, timestamp, source hashes, historical model metrics, and library versions.

It then rechecks every source hash. A source change during computation aborts publication, preventing a mixed snapshot. During publication, the store exclusively creates the destination directory; competing or duplicate publishers cannot overwrite it. The store writes `analysis.json` and then a checksum-bearing `completion.json`; subsequent reads revalidate both the payload and its original sources.

## Historical reevaluation

The separate reevaluation command rescales an explicitly trusted historical model on its published test split. It preserves the run, captures current code identity, computes current metrics and diagnostics, and reports deltas from historical metrics without rewriting either publication.

This report is intentionally labeled `historical_snapshot_not_independent_test`. Its warnings state that the historical test data participated in selection, original split provenance was not authenticated by the legacy manifest, top-risk fraction uses the current CLI default, and class-balanced scores are not established calibrated population probabilities.

Historical reevaluation is therefore a reproducibility and drift-of-implementation check, not independent final validation.

## Interpretation constraints

Every analysis carries warnings and two explicit safeguards: `decision_support_only` and `qualified_human_review_required`. The outputs must not be used to automate discipline, grading, enrollment, accommodations, or access to student services.

Associations, coefficients, permutation effects, and SHAP contributions describe the selected dataset and model. Confounding, selection bias, measurement quality, calibration, and correlated predictors remain live limitations. Product copy and downstream documentation must preserve those distinctions.

## Related pages

- [ML Training and Artifact Publication](ml-training-and-publication.md)
- [Artifact Contracts and Persistence](../architecture/artifact-contracts.md)
- [FastAPI Serving Boundary](../architecture/api-serving.md)
- [Next.js Analytical Dashboard](../architecture/web-dashboard.md)

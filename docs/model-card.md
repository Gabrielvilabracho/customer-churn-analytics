# Education Burnout Classifier Model Card

This card documents a **local, synthetic-data portfolio experiment**. It does not validate burnout risk in real students and does not approve any model for deployment. The primary evaluation identity is `education-v1`; the older explanatory publication is listed separately because its metrics and explanations belong to a different fitted model.

## Status and identities

| Item | Evidence-bound identity |
| --- | --- |
| Approval status | **Not approved for deployment, operational intervention, clinical use, or consequential student decisions** |
| Evidence verification date | 2026-11-13 for dataset, report, and runtime checks; documentation reconciled 2026-11-14 |
| Primary report | `artifacts/experiments/education-v1/report.json`, report ID `education-v1`, kind `independent_education_experiment`, schema version 1 |
| Primary selected model | `logistic_C_1`; balanced binary logistic regression, `C=1.0`, `class_weight="balanced"`, `solver="lbfgs"`, seed 42 |
| Primary model bytes | `artifacts/experiments/education-v1/model.joblib`, SHA-256 `afb47bf84c813a811410af704084e0693d98f9285da6e998975c8dfdf43ef8d3` |
| Primary report bytes | SHA-256 `efb624495d10186455246fb56cc48aeb399f018b5caa3ff731a2f3db84605f83` |
| Companion historical run | Run ID `student-analysis-20261108`, model name `candidate_logistic_regression`; metrics publication `artifacts/metrics/student-analysis-20261108/metrics.json` |
| Companion explanation | Publication run `student-analysis-20261108`, analysis ID `variables-v1`, created 2026-11-07; this explains the companion historical model, **not** `education-v1` |

The primary and companion models use the same 12 named predictors and the same local dataset identity, but they are separate fitted artifacts with different split/evaluation records and slightly different metrics. Their results must never be merged or presented as one run. See the [modeling report](modeling-report.md) for the artifact flow and the [dated research record](research-foundation-2026-11-13.md) for verification evidence.

## Intended portfolio use

The model is intended only to demonstrate a reproducible local workflow for:

- binary classification of the synthetic label `High` versus `Low` + `Medium`;
- train/validation/test separation, candidate and threshold selection, aggregate evaluation, and immutable local artifacts;
- education-oriented discussion of ranking quality and review workload; and
- technical inspection by portfolio reviewers using the supplied limitations and provenance record.

Scores are synthetic-label classifier outputs. They are not validated probabilities of real-student burnout, clinical risk scores, diagnoses, causal estimates, or evidence that an intervention will help.

## Prohibited uses

Do not use this model or its outputs to:

- make or automate decisions about grading, discipline, enrollment, attendance, accommodations, financial support, counseling access, or any other student service;
- diagnose, screen, rank, monitor, or target real students;
- infer mental-health status, disability, intent, academic integrity, or individual need;
- claim that AI use causes burnout, changes GPA, or changes skill retention;
- compare institutions or protected groups, allocate resources, or evaluate policy effectiveness;
- expose the local model as the repository's `/predict` behavior; or
- claim production readiness, external validity, fairness, calibration, or institutional approval.

## Dataset and source boundary

| Topic | Evidence |
| --- | --- |
| Dataset | Kaggle [`laveshjadon/ai-impact-on-students`, version 1](https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students/versions/1), released 2026-05-10 |
| License | **CC0: Public Domain**, verified through the public Kaggle API |
| Local identity | 50,000 rows, 16 columns; CSV SHA-256 `4d911088c4b12d60a450a9acae6b606f4119ebbb48679518e427a4fc00778472`; byte-identical to the public version-1 CSV |
| Label | `Burnout_Risk_Level`; positive class `High`, negative class `Low` + `Medium` |
| Predictors | The 12 fields marked included in the [Data Dictionary](data-dictionary.md) |
| Exclusions | `Student_ID` is an identifier; `Post_Semester_GPA` and `Skill_Retention_Score` are post-outcome fields excluded to prevent leakage into the burnout model |

The source is described as synthetic, and no real-student validation is available. Exact generator code, generator version, random seed, recruitment/collection procedure, and burnout-label construction are unavailable permanent limitations. CC0 and byte identity establish source permission and file identity; they do not establish measurement validity. The [Dataset Card](dataset-card.md) and [machine-readable verification record](dataset-source-verification.json) contain the full provenance boundary.

## Model and evaluation protocol

`education-v1` uses a training-prevalence baseline and balanced logistic-regression candidates with `C` values 0.1, 1, and 10. With seed 42, the rows were stratified by the original three labels into 29,999 training rows, 10,001 validation rows, and 10,000 final-test rows. Preprocessing and estimators were fit on training data only.

For each candidate, validation thresholds 0.7, 0.5, and 0.3 were evaluated. The highest threshold meeting the minimum recall gate of 0.7 was retained, then eligible candidates were ranked by validation average precision, ROC-AUC, and precision. This selected `logistic_C_1` at threshold 0.30. No train-plus-validation refit occurred after selection. Final-test predictions were made once with that frozen selection.

This procedure is internally reproducible evidence on one synthetic dataset, not independent external validation. The dataset had already been explored, and the split cannot undo earlier human exposure or selection.

## Primary final-test results: `education-v1`

All values in this table are from the `education-v1` **test split** of 10,000 rows. The field named `pr_auc` is average precision, as defined in [classification metric semantics](metric-semantics.md).

| Metric | Value | Interpretation boundary |
| --- | ---: | --- |
| Average precision (`pr_auc`) | 0.6371 | Synthetic-label ranking summary; not clinical utility |
| ROC-AUC | 0.8055 | Ranking discrimination within this held-out synthetic split |
| Precision at 0.30 | 0.3607 | About 36.1% of flagged test rows carry the synthetic `High` label |
| Recall at 0.30 | 0.8879 | About 88.8% of synthetic `High` labels are flagged |
| Accuracy at 0.30 | 0.5791 | Secondary metric; not the selection objective |
| Expected top-20% capture | 0.5050 | Expected fraction of positives in the top-score quota under tie-aware semantics |
| Brier score | 0.1735 | Diagnostic only; no fitted calibration |
| Log loss | 0.5283 | Diagnostic only; probabilities are clipped for numerical stability |

At threshold 0.30, the workload is **6,146 of 10,000 test rows (61.46%)**. The confusion counts are TP 2,217, FP 3,929, TN 3,574, and FN 280; the false-positive rate is 52.37%. No false-positive budget, staffing capacity, intervention cost, or benefit model has been supplied. The threshold is therefore a reproducible experiment choice, not an operational policy.

## Calibration and subgroup limits

Calibration was **diagnosed, not fitted**. `education-v1` records Brier score, log loss, mean score, and ten reliability bins. Class balancing changes the relationship between scores and prevalence, so scores must not be interpreted as established probabilities for this synthetic dataset, much less for real students.

`education-v1` does not report subgroup fairness evaluation. The separate `student-analysis-20261108` / `variables-v1` publication contains descriptive cohorts and associations for its own historical model, with small-group suppression, but those results cannot be attached to `education-v1`. No protected-attribute audit, measurement-invariance study, intersectional analysis, external cohort evaluation, or real-world disparity assessment exists. Synthetic category representation does not establish fairness.

## Companion historical identity: do not merge

The historical run `student-analysis-20261108` reports threshold 0.30, workload 0.6184, average precision 0.6362, ROC-AUC 0.8050, precision 0.3588, recall 0.8887, accuracy 0.5757, and top-risk capture 0.5034. Its `variables-v1` explanations include coefficients, permutation importance, SHAP values, associations, and cohorts for `candidate_logistic_regression`.

Those values are retained for historical explanation only. They are not alternate metrics for `education-v1`, and the explanatory run does not add calibration, causal validity, or deployment approval.

## Ethical, safety, and runtime boundaries

- The target and several predictors concern well-being. Their synthetic numeric scales are not validated psychological instruments.
- Associations and explanations may expose generator rules. Coefficients, SHAP values, and cohort differences are descriptive model behavior, not causal effects.
- Category domains are synthetic and incomplete as representations of real educational settings. The model has no demonstrated geographic, cultural, institutional, temporal, or demographic generalizability.
- Qualified human review is necessary for interpreting the portfolio analysis, but human review does not make a prohibited real-student use acceptable.
- Raw rows, identifiers, and model artifacts remain local. Optional local MLflow is a comparison view, not a registry, promotion gate, deployment system, or monitoring service.

The live `POST /predict` route is a known legacy compatibility stub. A schema-valid education request currently returns fixed churn-era evidence (`0.78` and a `tenure_months` driver absent from this schema). It does **not** load or serve either model documented here and must not be used as validation or inference evidence.

## Verification and approval statement

Dataset/report identities and the legacy runtime mismatch were checked on 2026-11-13; this card was reconciled on 2026-11-14 without retraining, metric recomputation, model deserialization, or deployment. The immutable aggregate report remains authoritative for recorded metrics.

**Neither `education-v1` nor `student-analysis-20261108` is approved for deployment.** Approval would require, at minimum, a justified real-world use case, lawful and representative data, validated measures and labels, external evaluation, calibration appropriate to the population, subgroup and harm analysis, operational workload and false-positive budgets, governance, monitoring, rollback, and explicit accountable sign-off.

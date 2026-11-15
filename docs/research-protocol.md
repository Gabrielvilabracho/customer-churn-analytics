# Student Impact Research Protocol — Phase 1 Contract

This is the Phase 1 research contract from the existing Obsidian roadmap, not a systematic review or a preregistration. Existing data and holdouts have already been explored. Source/version and declared CC0 are verified; exact target-generation evidence is unavailable and was accepted on 2026-11-14 as a permanent limitation of this synthetic portfolio study.

## Scope and evidence matrix

The unit is one synthetic student record, not a verified enrolled participant. The primary existing prediction target is `Burnout_Risk_Level == High` versus Low + Medium. Findings concern this synthetic distribution, not actual university populations.

| Existing roadmap question | Evidence / analysis | Claim boundary |
| --- | --- | --- |
| What does this dataset measure and represent? | Publisher/version, generator rules, data dictionary and label construction | Local CSV identity and source/version verified; generator and measurement validity remain unresolved |
| Which variables are associated with High labels? | Descriptive distributions, conditional contrasts, model explanations, uncertainty | Generated associations; not AI-caused burnout or clinically measured risk |
| Can ranking improve on prevalence? | Average precision, ROC-AUC and capture within the top 20%; matched validation reference | Internal discrimination only; no claim of external validity |
| Can scores support a defined review capacity? | [Validation threshold/top-k comparisons and hypothetical review effort](review-capacity-protocol.md) | Portfolio scenarios defined; operational suitability remains unapproved without stakeholder capacity and error-cost acceptance |
| Do probabilities match outcomes? | Reliability bins, Brier score and log loss | Current scores are not established calibrated individual probabilities |
| Do findings transfer? | Compatible, licensed, genuinely new external observations | Not evaluated; synthetic validation is not external student validation |

## Existing analysis identities and selection policy

- `student-analysis-20261108/variables-v1`: historical explanatory analysis. Threshold selection used its historical test; those metrics are not independent final evaluation.
- `education-v1`: 29,999 train / 10,001 validation / 10,000 test records; seed 42. Prevalence reference and logistic C values 0.1, 1 and 10 were compared on validation; `logistic_C_1` and threshold 0.30 were selected before final-test evaluation.
- Treat all further work on this source as exploratory or internal validation. Reused holdouts cannot become new confirmatory evidence by changing the model name or split seed.
- Fit preprocessing on training data only. Do not tune model, threshold, calibration or subgroup choices on final-test results. Any future experiment needs its own immutable identity and a written selection policy before execution.
- `pr_auc` in existing reports denotes average precision. Threshold recall and top-20% capture are different metrics. SHAP values in the historical analysis are log-odds contributions, not probability percentage points.

## Academic outcomes and subgroup scope

The existing roadmap names Arts, Humanities, Medical, Business and STEM. Compare support counts and outcome distributions across all five, not only favorable categories. Distinguish target prevalence from prediction performance; report uncertainty and full per-group confusion counts when those analyses are implemented.

The separate academic/behavioral task covers initial/final GPA and their difference, skills retention, anxiety, perceived dependency, study hours, AI hours and tool diversity. Begin descriptively; this draft does not authorize a new prediction target. Do not include `Post_Semester_GPA` or `Skill_Retention_Score` in burnout predictors. Use `Student_ID` only as a key.

A synthetic pre/post GPA pair is not repeated dated follow-up. No empirical long-term trajectory or policy intervention effect is established. Assumption-based scenarios must be labeled as such, not as forecasts of real students.

## Literature-review plan and source matrix

Scope: primary research on student GenAI use, learning/retention, academic outcomes and well-being; validated burnout-measurement studies; studies distinguishing associations from intervention effects. Keep external studies separate from the synthetic generator's assumptions.

Search concepts: generative AI / ChatGPT; higher education / university students; burnout / well-being / anxiety / dependence; learning / retention / academic performance. Record search date, query, source and eligibility decisions. No search or citation coverage is claimed complete by this draft.

Include sources with identifiable authors, accessible methods, a defined population, outcomes and study design. Distinguish peer-reviewed studies from preprints; retain null or contradictory findings. Exclude promotional claims and sources with unverifiable methods from the evidentiary foundation. Evaluate date, relevance, author authority, measurement validity, accuracy and purpose; record conflicts of interest and generalization limits.

| Evidence stream | Current status | Required record |
| --- | --- | --- |
| Publisher/generator | Kaggle version 1 and declared CC0 independently checked; CSV byte identity established | Generator code/seed and label specification remain unverified; see [source record](dataset-source-verification.json) |
| Local analysis | Saved artifacts plus dated integrity checks | [Verification matrix](research-foundation-2026-11-13.md); never represent checksums as model re-evaluation |
| External academic evidence | Targeted matrix covers one randomized immediate-learning study, two observational AI/learning studies, four peer-reviewed student-burnout measurement studies, one three-semester burnout cohort and three preliminary GenAI-dependency scale records | Expand systematically; see [literature matrix](literature-evidence-matrix.md), retain study-design limits and do not map synthetic fields directly to validated scales |

## Release of the next analyses

Phase 1 is closed with unavailable label-generation methods and targeted, non-systematic literature coverage preserved as explicit limitations. No reviewed GenAI-dependency instrument is ready for direct adoption: any future real-student use requires a prespecified construct, cognitive pilot, psychometric validation, behavioral criteria, test–retest evidence and invariance checks. Phase 2 may define intended users, human review capacity and false-positive/false-negative costs; no new algorithm search, automatic intervention, model promotion or deployment is authorized by this document alone.

## Phase 2 checkpoint — 2026-11-15

The [review-capacity protocol](review-capacity-protocol.md) records a user-approved
hypothetical guidance-team scenario, 10/20/30% review capacities, and 5/10/15-minute
initial-review assumptions. Verified validation-only scoring of the existing
`education-v1` model supplies matched threshold and top-k trade-offs; no retraining
or new final-test evaluation occurred. None of these capacity scenarios meets
the existing 0.70 recall gate. Relative error costs and operational acceptance
remain unresolved; the checkpoint does not authorize training or deployment.

Source of scope: Obsidian `Student Impact - Evidence and Research Roadmap`, Phase 1 and its canonical research task, plus the user-approved Phase 2 portfolio scenarios. Local source evidence: [dataset card](dataset-card.md), experiment reports and the implementation locations cited in the [dated record](research-foundation-2026-11-13.md).

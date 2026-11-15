# Dataset Card

The locally provisioned AI Student Impact dataset supports a **synthetic portfolio study**, not conclusions about real student populations. Checks on 2026-11-13 bind the CSV both to `education-v1` and to **Kaggle `laveshjadon/ai-impact-on-students`, version 1**, whose public API declares CC0. Generator-label methods remain unavailable and are recorded as a permanent Phase 1 limitation.

## Source and permission evidence

| Evidence | Status |
| --- | --- |
| Verified source/version | [Kaggle `laveshjadon/ai-impact-on-students`, version 1](https://www.kaggle.com/datasets/laveshjadon/ai-impact-on-students/versions/1), initial release 2026-05-10; byte identity verified |
| License | **CC0: Public Domain**, independently confirmed in the [public Kaggle API](https://www.kaggle.com/api/v1/datasets/view/laveshjadon/ai-impact-on-students), consistent with supplied metadata |
| Generation description | User reports statistical distributions and domain-informed rules, synthetic IDs and no real student PII |
| Label construction | Exact burnout-label rule, generator code/version and random seed are not established |
| Local historical metadata | Still records the original unverified license/prohibited redistribution and old `data/raw/` path; preserved, not silently rewritten as publisher verification |
| Current publication decision | Permitted-use evidence supports the local portfolio study under declared CC0; raw data remain local and were not redistributed |

The earlier `lazaroaluizio/ai-student-impact` locator returned 404 and was the wrong recorded candidate. The supplied Croissant metadata identified the correct version. A public, unauthenticated version-1 download was compared in external temporary storage without replacing local data: ZIP MD5 matches the metadata, and its CSV is byte-identical to the study input. See the [machine-readable verification record](dataset-source-verification.json). MD5 here corroborates a published archive identifier; CSV SHA-256 and direct byte equality establish the comparison, not MD5 alone.

The API owner handle is `laveshjadon`. Its display name differs from the supplied metadata's creator display name; use the stable dataset handle/version for attribution. The public description inspected does not provide a generator protocol or exact burnout-label rules. The synthetic methodology remains separately attributed to the user, not independently validated by the checksum match.

## Local identity and schema

Current ignored path: `data/01-raw/ai-student-impact/ai_student_impact_dataset.csv`.

| Fresh check | Result |
| --- | --- |
| File size | 5,892,478 bytes |
| Records / columns | 50,000 / 16 |
| Empty CSV cells / duplicate full rows | 0 / 0 |
| Unique `Student_ID` values | 50,000 |
| `Burnout_Risk_Level` counts | High 12,487; Medium 21,144; Low 16,369 |
| Raw file SHA-256 | `4d911088c4b12d60a450a9acae6b606f4119ebbb48679518e427a4fc00778472` |
| Parsed-row digest | `4fe368598a6bbcaffaa4f2e08fb57ecd79803655ef99ad3e18cd8a11695c5cca` |

Both identities match `artifacts/experiments/education-v1/report.json`: `input_csv_sha256` hashes file bytes; `dataset_sha256` hashes parsed rows serialized by `experiment_reports.digest`. Different digest domains are expected, not evidence of different datasets. Empty-cell counts do not establish semantic validity or absence of sentinel values.

The [Data Dictionary](data-dictionary.md) is the canonical field-level contract for all 16 columns. In summary, they comprise an ID, a target, two post-outcome fields and 12 model predictors:

- Key: `Student_ID`; never an explanatory predictor.
- Target: `Burnout_Risk_Level`; current classifier models High versus Low + Medium.
- Separate outcomes: `Post_Semester_GPA`, `Skill_Retention_Score`; excluded from burnout predictors.
- Predictors: `Major_Category`, `Year_of_Study`, `Pre_Semester_GPA`, `Weekly_GenAI_Hours`, `Primary_Use_Case`, `Prompt_Engineering_Skill`, `Tool_Diversity`, `Paid_Subscription`, `Traditional_Study_Hours`, `Perceived_AI_Dependency`, `Institutional_Policy`, `Anxiety_Level_During_Exams`.

## Reproduction and compatibility

Use an independently provisioned, licensed copy; keep credentials outside the repository and record its version, raw checksum and permission evidence. Do not assume another download is byte-identical to this file.

The older provenance validator accepts paths beneath `data/raw/`, while current local provisioning uses `data/01-raw/`. Training provenance validation is conditional on supplying `--provenance-json`; it is not an unconditional gate. This audit changes neither behavior nor historical metadata. Do not claim that merely moving or editing the metadata establishes valid provenance.

## Interpretation limits and next step

Synthetic scales are not validated psychological instruments. Associations and model performance may reflect generator rules; no causal effect, clinical diagnosis, longitudinal forecast, external validation or operational approval follows. Predictor timing and target construction could not be independently verified and must remain explicit limitations in every downstream analysis.

Continue with the [Model Card](model-card.md), [research protocol draft](research-protocol.md), and [dated evidence record](research-foundation-2026-11-13.md). Preserve historical publications and distinguish `student-analysis-20261108` explanations from `education-v1` evaluation.

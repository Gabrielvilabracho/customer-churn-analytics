# Review capacity and prediction costs — exploratory protocol

Compare the existing education model under fixed review capacities before
interpreting an advanced model's metric improvement as useful. This protocol
records user-approved hypothetical scenarios and measured internal validation
results. It does not select an operational policy or authorize training,
deployment, student contact, diagnosis, or academic decisions.

## Scenario and decisions

| Item | Agreed scope |
| --- | --- |
| Intended reviewer | A hypothetical educational guidance team |
| Possible action | Human review to decide whether to offer voluntary support |
| Prohibited uses | Diagnosis, grading, academic penalties, automatic intervention, or decisions about access to services |
| Review capacities | 100, 200, and 300 cases per 1,000 records per evaluation round |
| Review durations | Sensitivity assumptions of 5, 10, and 15 minutes per initial review |
| Operational acceptance | None; capacities and durations are not institutionally validated budgets |

The unit is a synthetic record. A positive means `Burnout_Risk_Level == High`,
not clinically established burnout. False positives and false negatives are
disagreements with that synthetic label, not measured harms to actual students.

## Bound evidence and verification

The baseline is the saved `education-v1` model, `logistic_C_1`, not the historical
`student-analysis-20261108` explanatory model.

| Identity | Value |
| --- | --- |
| Local report | `artifacts/experiments/education-v1/report.json` |
| Local completion manifest | `artifacts/experiments/education-v1/completion.json` |
| Local model | `artifacts/experiments/education-v1/model.joblib` |
| Model SHA-256 | `afb47bf84c813a811410af704084e0693d98f9285da6e998975c8dfdf43ef8d3` |
| Validation SHA-256 | `cfa49f61c258f53d94be433e9c3b5e43571602e9c1265c58ec419f07e27d2f3f` |
| Validation support | 10,001 records: 2,498 High and 7,503 Low/Medium |
| Split seed | 42 |

On 2026-11-15, an explicitly authorized local probe verified report/model
manifest checksums, raw and parsed dataset identities, and all three reconstructed
split hashes. It deserialized the verified model bytes once and made one
prediction call on validation rows only; it did not fit a model or predict on
the final test. Checksums establish integrity, not trust in arbitrary model files.

All saved validation threshold confusion matrices matched. Brier score, log
loss, mean score, and the saved top-20% capture matched within an absolute
tolerance of 1e-12. An independent boundary calculation matched all capacities;
constant-score checks verified label-blind tie handling. Artifact hashes and
inventory, the input CSV, and the pre-existing local frontend declaration edit
remained unchanged. The temporary probe was removed; it is not a shipped CLI.

The probe used Python 3.14.6 rather than the report's Python 3.13.0. Scikit-learn
1.9.0 and NumPy 2.5.1 matched the report; joblib was 1.5.3. The observed parity
checks support these results, not general cross-version serialization guarantees.

## Validation trade-offs

### Fixed thresholds already recorded in the report

| Threshold | Reviewed | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.30 | 6,078 | 2,168 | 3,910 | 330 | 3,593 | 35.67% | 86.79% |
| 0.50 | 3,213 | 1,644 | 1,569 | 854 | 5,934 | 51.17% | 65.81% |
| 0.70 | 1,696 | 1,140 | 556 | 1,358 | 6,947 | 67.22% | 45.64% |

### Fixed-capacity ranking

Rank validation records by descending score. The existing evaluator uses
`k = max(1, round(N * capacity_fraction))`, producing 1,000, 2,000, and 3,000
reviews here. At a boundary tie, use expected positive capture under uniform,
label-blind selection among tied records, never labels to break the tie.
None of these three observed boundaries had a tie.

| Capacity | Reviewed | TP | FP | FN | TN | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 10% | 1,000 | 784 | 216 | 1,714 | 7,287 | 78.40% | 31.39% |
| 20% | 2,000 | 1,265 | 735 | 1,233 | 6,768 | 63.25% | 50.64% |
| 30% | 3,000 | 1,585 | 1,415 | 913 | 6,088 | 52.83% | 63.45% |

Precision is TP / reviewed; recall is TP / 2,498. A fixed score threshold does
not enforce a review capacity. In particular, threshold 0.30 flags 60.77% of
validation records, not 30%. Scores are not established calibrated probabilities.

## Initial-review effort

`person_hours = reviewed * minutes_per_review / 60`.

| Capacity | Reviewed | 5 minutes | 10 minutes | 15 minutes |
| --- | ---: | ---: | ---: | ---: |
| 10% | 1,000 | 83.3 h | 166.7 h | 250 h |
| 20% | 2,000 | 166.7 h | 333.3 h | 500 h |
| 30% | 3,000 | 250 h | 500 h | 750 h |

These are person-hours, not calendar duration, staffing commitments, or measured
service times. They exclude follow-up, administration, and any actual support.
The same hypothetical duration is applied to every initial review; it is not
evidence that different models or cases take equal time in practice.

At 10 minutes per review, increasing capacity from 10% to 20% adds 166.7 hours,
481 TP, and 519 FP. Increasing from 20% to 30% adds another 166.7 hours,
320 TP, and 680 FP. Additional reviews yield diminishing positive capture here.

A possible cost model separates initial review from additional consequences:

`total_cost = reviewed * review_cost + FP * additional_FP_cost + FN * omission_cost`.

No monetary values, relative FP/FN weights, or student-harm estimates have been
approved. Avoid double-counting initial review within the additional FP cost.
Review effort alone cannot establish net benefit or justify an intervention.

## Future comparison rules and unresolved acceptance

The user approved an experimental improvement rule: validation average precision
must improve by at least 0.01 absolute over the best eligible logistic reference,
while maintaining the existing recall requirement and not worsening Brier score,
false-positive rate, or flagged fraction at the compared selected thresholds.
This is a prespecified heuristic, not statistical significance or external validity.

For any later authorized candidate comparison:

- Preserve dataset and split identities, exclusions, train-only fitting, and
  validation-only selection. Freeze the exact experiment policy before training.
- Report TP/FP/FN, precision, recall, and review effort at all three capacities;
  keep these capacity diagnostics separate from threshold-based selection gates.
- Use the same capacities, rounding, and tie policy for each model. Do not present
  higher AP alone as proof of better detection at a fixed review budget.
- Preserve the existing 0.70 minimum-recall gate. None of the measured capacity
  scenarios reaches it. At 10%, even perfect ranking could capture at most
  1,000 / 2,498 = 40.03% of positives in this validation sample.
- Do not relax that gate, select an operational scenario, fit calibration, or
  reuse final-test results for selection under this documentation task.

Relative error consequences, an acceptable operational capacity, and real-world
stakeholder approval remain unresolved. Keep use research-only. Further work on
this already explored synthetic dataset is internal evidence, not a new
confirmatory study. No current publication is replaced.

See the [research protocol](research-protocol.md),
[experiment protocol](education-experiments.md), and
[model lifecycle roadmap](model-lifecycle-roadmap.md) for surrounding boundaries.

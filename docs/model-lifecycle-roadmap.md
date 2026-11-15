# Education model lifecycle roadmap

This roadmap defines the evidence gates between the current logistic-regression
experiment and any future model comparison, explanation, registration,
deployment, or monitoring work. It is a plan, not evidence that the later
capabilities exist. The current Model Card and immutable experiment report remain
authoritative until each phase publishes and verifies a replacement artifact.

## Current state

| Capability | Current evidence | Status |
| --- | --- | --- |
| Baseline experiment | `education-v1`, balanced logistic regression selected on validation data | Implemented |
| Experiment tracking | Optional local SQLite MLflow with aggregate-only artifacts | Implemented |
| Explanations | Exact linear SHAP for the separate `student-analysis-20261108` model | Implemented for that identity only |
| Advanced candidates | XGBoost and LightGBM | Planned |
| Selected-model explanations | Estimator-appropriate SHAP bound to the selected experiment | Planned |
| Model Registry and promotion | Versioned candidate/champion lifecycle | Planned |
| Model serving | Controlled artifact-backed inference | Planned |
| Monitoring | Aggregate runtime, drift, workload, and delayed-performance signals | Planned |

MLflow is currently a local comparison view. It does not authorize promotion,
deployment, monitoring, or real-student use.

## Delivery sequence

Later phases start only after the preceding evidence gate closes. Each phase gets
its own ODD execution task; durable behavioral changes are specified through the
named OpenSpec change before source implementation.

### Phase 1 — Comparable model candidates

**Owner:** extend the active `education-experiments` OpenSpec change.

Implement logistic regression as the mandatory baseline and XGBoost and LightGBM
as optional candidate adapters. Every candidate must use the same verified
dataset identity, split hashes, feature exclusions, preprocessing policy, seed,
validation thresholds, recall gate, and final-test isolation.

Acceptance evidence:

- dependencies are opt-in and locked; unavailable optional candidates fail
  explicitly rather than changing the baseline path;
- candidate names and hyperparameters are losslessly attributed;
- preprocessing and fitting use training rows only;
- model and threshold selection use validation evidence only;
- final-test predictions happen once after selection is frozen;
- MLflow and the immutable report record the same parameters, split identities,
  metrics, diagnostics, and selected model hash; and
- the comparison table reports ranking, calibration, false-positive rate, and
  flagged workload without claiming deployment readiness.

An advanced candidate must improve validation average precision by at least
0.01 absolute over the best recall-eligible logistic reference, preserve the
0.70 recall gate, and not worsen Brier score, false-positive rate, or flagged
fraction at the compared selected validation thresholds. A numerically higher
metric alone does not justify replacing the simpler logistic baseline.

### Phase 2 — Explain the selected model

**Owner:** create `education-selected-model-explanations` after Phase 1 fixes the
selected model identity.

Use an explainer appropriate to the selected estimator. Preserve the existing
exact linear formulation for a logistic model; use verified tree-model SHAP for
XGBoost or LightGBM. The publication must bind model bytes, report identity,
background data identity, explainer configuration, and deterministic held-out
samples.

Acceptance evidence:

- additivity or output-parity tests pass for the selected estimator;
- global importance uses aggregate summaries;
- local explanations use run-local display IDs and remain private;
- identifiers and raw student rows are not logged or served; and
- documentation states that SHAP describes model behavior, not causality,
  diagnosis, intervention effect, or validated individual risk.

The historical `variables-v1` explanation remains attached only to its existing
historical logistic model and must never be relabeled as evidence for the newly
selected experiment.

### Phase 3 — Registry and promotion gate

**Owner:** create `education-model-promotion` after Phases 1 and 2 pass.

Register only checksum-bound, reviewed model artifacts. Each model version must
reference its immutable report, dataset and split hashes, source revision,
evaluation evidence, explanation publication, Model Card, and rollback target.

Acceptance evidence:

- registration is explicit and idempotent;
- `candidate` and `champion` aliases require an accountable approval action;
- no metric or MLflow run automatically promotes a model;
- changing an alias never mutates historical model versions; and
- the registry contains no raw rows, student identifiers, or individual
  explanation histories.

A local registry may prove the lifecycle first. A shared registry requires a
separate decision about hosting, authentication, authorization, backups, and
retention.

### Phase 4 — Controlled demo deployment

**Owner:** extend `education-model-promotion` only after the serving target and
access model are explicitly selected.

Introduce an artifact-backed scorer behind explicit configuration. The existing
legacy `/predict` stub remains the default until the new serving contract is
verified; it must not silently become the education endpoint.

Acceptance evidence:

- startup selects one exact registered model version;
- input validation matches the registered feature schema;
- unavailable or invalid artifacts degrade safely without fallback to another
  model;
- rollout and rollback are deterministic and tested; and
- access remains non-consequential and unsuitable for real-student decisions.

### Phase 5 — Privacy-safe monitoring

**Owner:** create `education-model-monitoring` only after Phase 4 provides a real
serving contract.

Monitor aggregate runtime health, schema/data drift, score distributions,
threshold workload, and model-version usage. Measure performance only when a
valid delayed-label source and evaluation window exist.

Acceptance evidence:

- monitoring stores no raw rows, identifiers, or individual histories;
- cohort reporting enforces minimum-size suppression;
- windows, baselines, thresholds, and alert ownership are specified before
  alerts are enabled;
- missing or invalid delayed labels cannot be interpreted as model quality; and
- every alert links to a documented investigation and rollback procedure.

## Decisions intentionally deferred

The roadmap does not invent decisions that require implementation evidence or an
operating environment:

- whether XGBoost or LightGBM remains after the comparison;
- the shared Registry provider and access model;
- the deployment target and authentication design;
- the source and validity of delayed outcome labels; and
- drift windows, alert thresholds, operational budgets, and accountable owners.

These decisions must be resolved in the governing OpenSpec change before their
phase starts.

## Permanent boundaries

No phase authorizes diagnosis, causal claims, automated student decisions, raw
record tracking, silent historical rewrites, external-validity claims, or use of
synthetic scores as validated probabilities for real students. Deployment and
monitoring demonstrations remain portfolio evidence until lawful,
representative, externally validated data and accountable governance exist.

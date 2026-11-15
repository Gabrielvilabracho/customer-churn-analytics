---
type: architecture
title: System Architecture
description: Clean and Hexagonal boundaries connecting local education data, analytical artifacts, FastAPI contracts, and Next.js dashboards.
tags: [architecture, clean-architecture, machine-learning, analytics]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T18:18:27.480Z
sources:
  - id: openwiki-source-47740cc678d42057785953ea
    resource: repo://apps/api/src/churn_api/adapters/scoring.py
  - id: openwiki-source-c8978d467454154cc22bb986
    resource: repo://apps/api/src/churn_api/main.py
  - id: openwiki-source-0449d9c2922807b2763ef9e2
    resource: repo://apps/api/src/churn_api/presentation/http/routes.py
  - id: openwiki-source-115b2dad781e2a2c5b5a980d
    resource: repo://docs/architecture.md
  - id: openwiki-source-d974fb793baec768af6c6de5
    resource: repo://packages/ml/src/churn_ml/application/ports/artifact_store.py
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
generated: { by: "opencode", at: "2026-11-15T18:18:27.480Z" }
---

# System Architecture

The platform turns a locally provisioned AI-in-education dataset into reproducible analytical publications, serves verified publications through FastAPI, and presents them in a Next.js dashboard. Its central architectural rule is that downstream systems consume explicit artifact or HTTP contracts; they do not reach through layers to recompute analytics or invent missing values.

## End-to-end flow

```text
operator-provisioned CSV (git-ignored)
        │
        ▼
packages/ml application pipelines
  acquire → profile → split/features → train → evaluate
        │
        ▼
immutable filesystem run publication
  processed CSV/metadata + metrics JSON/CSV + model metadata/binary
        ├──────────────► optional aggregate-only local experiment reports/MLflow
        │
        └──────────────► offline education variable analysis
                              │
                              ▼
                     immutable analysis publication
        │
        ▼
apps/api verified readers → application services → FastAPI contracts
        │
        ▼
apps/web typed clients → view models → churn and education dashboards
```

Raw education data remains local and ignored by Git. Generated analytical outputs under `artifacts/` are also local. The repository documents acquisition and verification rather than redistributing a dataset whose license must be respected.

## Subsystem ownership

### Analytical core: `packages/ml`

The ML package owns dataset validation, deterministic splitting, feature preparation, model training, evaluation, experiment reporting, and publication.

Its dependency direction follows a Hexagonal shape:

- `domain/` defines model-independent concepts such as labels, metrics, thresholds, artifact metadata, customer records, and education analysis validation. It must not depend on pandas, scikit-learn, filesystems, or HTTP.
- `application/` orchestrates use cases through ports. Pipelines define what acquisition, training, evaluation, publication, and analysis mean without owning framework delivery.
- `infrastructure/` implements the ports with pandas/scikit-learn, the local filesystem, provenance helpers, and optional local MLflow tracking.
- command entrypoints compose concrete adapters around application pipelines.

The filesystem publications are the source of truth. Optional MLflow receives reviewed aggregate reports and selected local artifacts; it is not a model registry, promotion system, deployment controller, or replacement for the publication contract.

### Serving boundary: `apps/api`

FastAPI adapts one explicitly selected run into HTTP contracts. Its application services depend on reader and scorer protocols, while filesystem readers and FastAPI routers remain outer adapters.

Startup does not load artifacts at import time and never discovers a latest run. Missing configuration or unreadable artifacts leave the process available but return a deterministic `503` degraded contract. Integrity is checked against the run completion manifest before serving analytics.

The churn and education surfaces share this verified-artifact principle but have different responsibilities:

- `/health`, `/model/metadata`, and `/analytics/dashboard` translate the selected churn snapshot.
- `/analytics/education` serves one exact analysis publication after source binding and closed public-contract validation.
- `/predict` is still a deterministic stub behind the scoring port; it must not be described as verified model inference.

### Presentation boundary: `apps/web`

The Next.js application consumes API contracts through typed clients. Components receive API-derived view models rather than reading artifact files or embedding analytical constants.

The root dashboard presents the legacy customer-retention view. `/education` presents student variable analysis: coefficients and odds ratios, permutation importance, independent linear SHAP contributions, associations, and cohort comparisons. Loading, empty, degraded, and error states are explicit product states; the UI does not fabricate substitute metrics.

## Two analytical surfaces

### Customer churn surface

The original artifact bundle contains model metadata, metrics, threshold selection, and prediction samples. The API converts that bundle into health, metadata, dashboard, and prediction responses. The current education pipeline's samples do not necessarily carry the legacy public cohort fields, so `/analytics/dashboard` may correctly degrade rather than manufacture customer-retention analytics.

### Education impact surface

Education analysis explains an already published and locally trusted logistic model. It reads checksum-verified model and split bytes, computes statistical and interpretability outputs offline, and publishes a new analysis identity without retraining or rewriting the model run.

The output is explicitly observational. Associations, coefficients, SHAP values, and cohort differences describe measured relationships in the selected data and model; they do not establish that AI usage causes burnout. Consequential student actions require qualified human review and are outside the product's permitted use.

## Architectural invariants

1. **Explicit identity:** run and analysis IDs select exact publications; no layer silently chooses a latest result.
2. **Immutable completion:** a publication becomes readable only through a completion marker and checksum validation.
3. **No fabricated analytics:** missing, malformed, or tampered artifacts produce degraded states.
4. **Persisted decisions:** threshold decisions use the threshold stored with the evaluated run.
5. **Traceability is not a feature:** `Student_ID` supports traceability but is excluded from the model feature schema.
6. **Human oversight:** burnout-risk outputs are decision support and require qualified review before use.
7. **Framework isolation:** domain and application behavior do not depend on FastAPI, Next.js, or filesystem implementation details.

## Operational scope

The repository is a local, portfolio-grade analytical system rather than a production MLOps platform. It has local process logging and optional local experiment tracking. It does not configure a remote tracking server, model registry, automated promotion, deployment pipeline, centralized telemetry, production monitoring, drift alerts, or rollback automation.

This distinction matters when extending the platform: production capabilities must be designed explicitly rather than inferred from local MLflow records or immutable filesystem artifacts.

## Verification boundaries

- ML tests pin deterministic transformations, metrics, thresholds, publication integrity, education analysis, and CLI behavior.
- API tests pin runtime composition, artifact degradation, response validation, and OpenAPI contracts.
- web unit tests pin typed transformations and component-facing models; Playwright covers browser states.
- documentation guardrails ensure reviewer-facing claims remain aligned with executable behavior and durable specifications.

## Related pages

- [ML Training and Artifact Publication](../workflows/ml-training-and-publication.md)
- [Education Impact Analysis Workflow](../workflows/education-analysis.md)
- [Artifact Contracts and Persistence](artifact-contracts.md)
- [FastAPI Serving Boundary](api-serving.md)
- [Next.js Analytical Dashboard](web-dashboard.md)

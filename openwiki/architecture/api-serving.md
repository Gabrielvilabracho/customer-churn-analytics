---
type: architecture
title: FastAPI Serving Boundary
description: Runtime composition, artifact-backed HTTP contracts, validation, and deterministic degradation behavior for the analytics API.
tags: [fastapi, api, hexagonal-architecture, artifacts]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T18:18:27.480Z
sources:
  - id: openwiki-source-f87320bda72212b258018a47
    resource: repo://apps/api/src/churn_api/adapters/filesystem.py
  - id: openwiki-source-161c5fae86182216cf105d1e
    resource: repo://apps/api/src/churn_api/application/education_contract.py
  - id: openwiki-source-ce15dfb408f8f934d795cd42
    resource: repo://apps/api/src/churn_api/application/ports/artifacts.py
  - id: openwiki-source-a15325130407ffa5cfbc8e12
    resource: repo://apps/api/src/churn_api/application/ports/education.py
  - id: openwiki-source-2f0769955911e7ddb1c3cadc
    resource: repo://apps/api/src/churn_api/application/services.py
  - id: openwiki-source-c8978d467454154cc22bb986
    resource: repo://apps/api/src/churn_api/main.py
  - id: openwiki-source-9729b0a9933d9e51e0be271d
    resource: repo://apps/api/src/churn_api/presentation/http/education.py
  - id: openwiki-source-0449d9c2922807b2763ef9e2
    resource: repo://apps/api/src/churn_api/presentation/http/routes.py
  - id: openwiki-source-8979bcf731f2512b880cdb99
    resource: repo://apps/api/tests/test_analytics_api.py
generated: { by: "opencode", at: "2026-11-15T18:18:27.480Z" }
---

# FastAPI Serving Boundary

The API is a thin delivery layer over published analytical artifacts. It does not train models or discover a "latest" run. Instead, runtime configuration selects an exact run, filesystem adapters validate and load that publication, application services translate it into public response shapes, and FastAPI routes turn domain failures into stable HTTP contracts.

## Composition and dependency direction

`churn_api.main.create_app` is the composition root. It accepts three ports:

- an `ArtifactSnapshotReader` for customer-churn artifacts;
- a `ChurnScorer` for individual predictions;
- an optional `EducationAnalysisReader` for a published education analysis.

The application layer depends on these protocols rather than filesystem or FastAPI implementations. The composition root supplies `FilesystemArtifactSnapshotReader`, `FilesystemEducationReader`, and the current `StubChurnScorer` at the outer edge. This keeps artifact access and HTTP delivery outside the application services.

`create_runtime_app` reads runtime settings without loading artifacts during module import. `CHURN_ARTIFACT_RUN_ID` must match `[A-Za-z0-9_-]+`; invalid or blank values produce an intentionally degraded application. `CHURN_ARTIFACT_ROOT` defaults to `artifacts`, and `CHURN_EDUCATION_ANALYSIS_ID` enables the education reader only when it matches its stricter identifier pattern. The runtime never scans for a latest publication.

```text
environment
    │
    ▼
create_runtime_app
    ├── FilesystemArtifactSnapshotReader ──► AnalyticsService / PredictionService
    ├── FilesystemEducationReader ─────────► education route
    └── StubChurnScorer ───────────────────► PredictionService
                                                 │
                                                 ▼
                                            FastAPI routes
```

Explicit dependencies passed to `create_app` bypass runtime selection. Tests use this seam to exercise the HTTP layer with controlled readers and scorers.

## Public HTTP surface

| Endpoint | Source | Main behavior |
| --- | --- | --- |
| `GET /health` | `AnalyticsService.health` | Loads the selected snapshot and reports readiness, model/artifact version, and freshness. |
| `GET /model/metadata` | `AnalyticsService.model_metadata` | Returns run, dataset, model, creation time, and feature-schema metadata. |
| `GET /analytics/dashboard` | `AnalyticsService.dashboard` | Returns KPIs, threshold, public prediction samples, risk distribution, and decision-support safeguards. |
| `POST /predict` | `PredictionService.predict` | Validates request features against the published schema, scores them, and returns probability, segment, threshold decision, priority, drivers, and model version. |
| `GET /analytics/education` | `EducationAnalysisReader` plus public-contract validation | Reads one configured analysis and returns it only if it matches the closed education response shape. |

FastAPI response models in `presentation/http/schemas.py` document the contracts in OpenAPI. The routes contain transport concerns; business-facing transformations stay in application services and contract validators.

## Snapshot read and integrity boundary

Every churn request that needs artifacts calls `FilesystemArtifactSnapshotReader.load_current_snapshot`. Before loading the bundle, the reader verifies the exact bytes named by the run's completion manifest. Missing, changed, or unpublished members therefore fail before they can become a partially trusted response.

After loading, the adapter checks that the manifest's `run_id` matches the explicitly selected run. It then constructs the API's `ArtifactSnapshot` with model metadata, recall/precision/PR-AUC metrics, the selected threshold, prediction samples, and freshness metadata. This translation prevents the presentation layer from depending directly on the ML package's persistence model.

The education adapter delegates to `EducationAnalysisStore.read(run_id, analysis_id)`. Store validation errors become `ArtifactUnavailableError`; malformed source metadata is collapsed to a stable error instead of leaking an internal exception shape.

## Closed education contract

Education publications may contain local-only data, but the HTTP response is deliberately closed. `validate_public_education_analysis` requires the exact top-level and nested field sets for summary statistics, coefficients, importance values, associations, cohorts, SHAP samples, methodology, warnings, versions, and source hashes.

The validator also checks semantic container constraints that response typing alone does not express:

- warnings must be a non-empty list of non-blank strings;
- confidence intervals must contain two finite ordered bounds between zero and one;
- negative labels must be strings;
- dynamic metadata maps may contain only scalar values;
- undeclared nested structures are rejected rather than silently forwarded.

This boundary prevents arbitrary local extensions, identifiers, or raw records from escaping through the API. A contract mismatch degrades the endpoint instead of silently changing the selected publication.

## Prediction validation and current scorer

`PredictionService` loads the selected snapshot before scoring, so every response is tied to a published model version and threshold. Required feature names and their declared `number` or `string` types are checked against the artifact schema. Validation failures return HTTP `422` with `error: "invalid_prediction_request"` and a list of details.

The current runtime scorer is intentionally a stub: it derives a fixed probability from `tenure_months` and returns one driver. The `ChurnScorer` port is the extension seam for a production scorer; replacing it does not require changing routes or application services.

Both dashboard and prediction responses include `decision_support_only: true` and `qualified_human_review_required: true`. The API therefore carries the product's human-review constraint in the public contract rather than relying only on dashboard copy.

## Deterministic degradation

Artifact-backed failures produce HTTP `503` with:

```json
{
  "status": "degraded",
  "reason": "<deterministic artifact reason>"
}
```

The shared degradation helper emits a structured warning containing the operation, selected run ID when available, and reason, without logging artifact contents. Missing runtime configuration, integrity failures, absent publications, malformed education metadata, and invalid education public contracts all use this path.

An invalid run ID is rejected before filesystem access. This prevents traversal-like values from probing outside the artifact root and leaves the service in the same explicit degraded state as missing configuration.

## Verification seams

The API tests cover four distinct boundaries:

1. application and HTTP behavior with injected readers and scorers;
2. exact runtime selection and degraded startup behavior;
3. filesystem snapshot integrity and identity checks;
4. OpenAPI and education response-contract stability.

For changes to runtime wiring, start with `apps/api/tests/test_analytics_api.py`. For artifact integrity, use `apps/api/tests/adapters/test_filesystem_snapshot_reader.py`. Education serving and closed-contract behavior live in `test_education_api.py`, `test_education_serving_boundary.py`, and `test_education_verification.py`.

## Related pages

- [Artifact Contracts and Persistence](artifact-contracts.md)
- [Next.js Analytical Dashboard](web-dashboard.md)
- [Local Development and Verification](../operations/local-development-and-verification.md)

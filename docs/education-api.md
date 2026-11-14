# Serve a verified education analysis

`GET /analytics/education` serves an existing local analysis publication. It
does not train, score, deserialize a model or compute explanations during a
request. Generate the publication first using [the offline CLI](education-artifacts.md).

Start the reviewer path with the [shared API contract](api-contract.md) for the
route inventory, generated OpenAPI schemas and legacy/education boundary, then
use this page for the education-specific publication and safety workflow.

## Select the publication

Configure the ASGI process with the same root and exact identities used by
the offline publisher:

```bash
export CHURN_ARTIFACT_ROOT=artifacts
export CHURN_ARTIFACT_RUN_ID=student-analysis-20261108
export CHURN_EDUCATION_ANALYSIS_ID=variables-v2
```

Start the existing ASGI server with `churn_api.main:app` and both `apps/api/src`
and `packages/ml/src` on `PYTHONPATH`. This feature does not install a server
or discover a latest run. Importing the application does not load a model.

## Response contract

| Condition | Response |
|-----------|----------|
| Exact publication, valid payload and unchanged source bytes | `200` with the analysis JSON |
| Missing or invalid selection, malformed publication, checksum mismatch or stale source | `503` with `{"status": "degraded", "reason": "..."}` |

FastAPI documents these as `EducationAnalyticsResponse` and
`DegradedResponse` in `/openapi.json`; `/docs` renders the same contract. The
typed metadata does not change the runtime payload, status codes or independent
degradation behavior.

The HTTP boundary rejects undeclared fields, including nested local extensions.
A matching checksum establishes byte integrity, not permission to expose raw data.

The payload retains `decision_support_only` and
`qualified_human_review_required`. Student identifiers are excluded and
small-cohort statistics are suppressed. Feature combinations can still be
sensitive: this is a private local inspection tool, not an authenticated
production service or a differential-privacy guarantee. Scores are not
automatically calibrated risks, diagnoses or causal estimates.

Existing `/health`, `/model/metadata`, `/analytics/dashboard` and `/predict`
behavior is unchanged. An invalid education analysis selection does not
disable a valid legacy run. `/predict` still uses its existing default stub.
That deterministic stub is a legacy demonstration only; education analysis is
served exclusively from the precomputed publication and never routed through
`/predict`.

## Check or remove the integration

```bash
.venv/bin/python -m pytest --no-cov -p no:cacheprovider \
  apps/api/tests/test_education_api.py apps/api/tests/test_education_verification.py \
  apps/api/tests/test_education_serving_boundary.py
```

The tests use synthetic temporary publications and verify that serving never
calls `joblib.load`. To stop serving education analysis, unset
`CHURN_EDUCATION_ANALYSIS_ID`; the endpoint then returns the degraded response
without deleting publications or changing legacy endpoints.

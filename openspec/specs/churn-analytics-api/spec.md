# Churn Analytics API Specification

## Purpose

Define FastAPI-facing behavior for predictions, analytics summaries, model metadata, and operational health from local artifacts.

## Requirements

### Requirement: Configured Local API Composition

Normal FastAPI startup MUST accept an explicit artifact root and run ID and, when both select a readable bundle, compose analytics from that exact filesystem run. The artifact-reader port MUST expose the selected run identity, including an explicit unavailable value for unconfigured readers. It MUST NOT perform `latest` discovery. Missing configuration or unreadable artifacts MUST NOT prevent application startup; the API SHALL remain available in degraded mode. Explicit dependencies supplied to the application factory MUST remain supported.

#### Scenario: Configured startup selects generated artifacts

- GIVEN a complete bundle and runtime settings containing its root and run ID
- WHEN the FastAPI application starts normally
- THEN analytics use that exact run without custom caller-side injection

#### Scenario: Startup configuration is absent

- GIVEN no complete artifact selection is configured
- WHEN the FastAPI application starts
- THEN startup succeeds with unavailable analytics
- AND the existing stub prediction scorer remains unchanged

#### Scenario: Explicit dependency is supplied

- GIVEN an artifact reader is supplied directly to the application factory
- WHEN the application is created
- THEN that reader MUST be used without requiring local runtime settings

### Requirement: Prediction Endpoint

The API MUST validate prediction requests against the trained feature schema and return churn probability, risk band, threshold decision, and top contributing drivers.

#### Scenario: Valid prediction request

- GIVEN a request matching the current feature schema
- WHEN the client asks for a churn prediction
- THEN the API returns probability, risk band, decision, model version, and drivers

#### Scenario: Invalid prediction request

- GIVEN a request with missing or wrong-typed features
- WHEN validation runs
- THEN the API MUST return a structured validation error without invoking the model

### Requirement: Artifact-backed Analytics Endpoints

The API SHALL expose health, model metadata, cohort analytics, KPI summaries, and evaluation metrics from the selected versioned local artifacts. `GET /health` MUST return HTTP 200 with `status: ready`, freshness, and model/artifact versions equal to the selected run ID. `GET /analytics/dashboard` MUST return HTTP 200 with that artifact version, freshness, KPIs, threshold, risk distribution, and public prediction samples.

#### Scenario: Dashboard requests selected-run analytics

- GIVEN the configured run contains a readable artifact bundle
- WHEN `GET /health` and `GET /analytics/dashboard` are called
- THEN both return HTTP 200 and identify the configured run
- AND dashboard analytics are derived from that bundle without fabricated values

#### Scenario: Required artifact is missing

- GIVEN the configured run is absent or its required analytics files are unavailable
- WHEN health or analytics endpoints are called
- THEN each affected endpoint MUST return HTTP 503 with `status: degraded` and a reason
- AND the response MUST NOT contain fabricated analytics

#### Scenario: Complete artifact data is invalid

- GIVEN the selected run has every required file but prediction samples omit or invalidate a public cohort field, or manifest identities are invalid
- WHEN health or dashboard analytics are requested
- THEN each affected endpoint MUST return HTTP 503 with `status: degraded` and a reason
- AND the API MUST NOT return HTTP 500 or fabricated analytics

### Requirement: Operator-Visible Artifact Degradation Events

The API MUST emit durable structured warning events when configured artifact state prevents analytics from being served. Each event MUST include an event name, endpoint or operation, selected run ID when known, and the deterministic degradation reason without exposing artifact contents.

#### Scenario: Artifact-backed endpoint degrades

- GIVEN configured artifacts are unavailable, inconsistent, or invalid
- WHEN an analytics endpoint returns its degraded response
- THEN an operator-visible structured warning is emitted with the endpoint, selected run ID when known, and reason

### Requirement: Student-Risk Decision Safeguards

The API MUST treat risk analytics and public prediction samples as decision-support-only. Every client-facing risk-analytics response MUST include `decision_support_only: true` and `qualified_human_review_required: true`. The API MUST NOT provide an endpoint, command, or integration that automatically makes or executes consequential student actions, including decisions about discipline, grading, enrollment, accommodations, access to services, or equivalent outcomes.

#### Scenario: Client receives risk analytics

- GIVEN a client requests dashboard or cohort risk analytics
- WHEN the API returns a successful risk-analytics response
- THEN the response includes `decision_support_only: true`
- AND the response includes `qualified_human_review_required: true`

#### Scenario: Consumer attempts an automated consequential action

- GIVEN a consumer has received a student-risk output
- WHEN it attempts to use the API to determine or execute a consequential student action
- THEN the API provides no endpoint, command, or integration for that action

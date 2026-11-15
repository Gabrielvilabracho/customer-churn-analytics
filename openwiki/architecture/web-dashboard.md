---
type: architecture
title: Next.js Analytical Dashboard
description: Typed API consumption, view-model transformations, analytical visualizations, and explicit unavailable states in the Next.js application.
tags: [nextjs, dashboard, typescript, visualization]
verified:
  - by: openwiki/0.9.0
    at: 2026-11-15T18:18:27.480Z
sources:
  - id: openwiki-source-135078721180ba7171ae5b2c
    resource: repo://apps/web/app/(dashboard)/dashboard-client.tsx
  - id: openwiki-source-d3fce6e650052561c0123520
    resource: repo://apps/web/app/(dashboard)/page.tsx
  - id: openwiki-source-5f0855600a3f9d1101cdb8df
    resource: repo://apps/web/app/education/page.tsx
  - id: openwiki-source-ea459936c6560ff2685a6ddd
    resource: repo://apps/web/components/features/churn/dashboard-model.ts
  - id: openwiki-source-c1aac5924d1b15e19d6ce9f9
    resource: repo://apps/web/lib/api/education-client.ts
  - id: openwiki-source-b8ab9aec59aec7c0e130cd73
    resource: repo://apps/web/lib/api/types.ts
generated: { by: "opencode", at: "2026-11-15T18:18:27.480Z" }
---

# Next.js Analytical Dashboard

The Next.js application is a presentation adapter over FastAPI. It does not read local artifact files, recalculate model metrics, or substitute demonstration values when publications are unavailable. Server pages fetch API responses, runtime parsers enforce critical contracts, view-model functions prepare display-ready data, and focused components render the analytical surfaces.

## Routes and responsibilities

| Route | Data source | Presentation responsibility |
| --- | --- | --- |
| `/` | `GET /analytics/dashboard` | Legacy customer-retention KPIs, contract cohorts, driver summary, and highest-risk sample table. |
| `/education` | `GET /analytics/education` | Student AI-use and burnout-risk summary, coefficients, feature importance, associations, cohort comparisons, and SHAP examples. |

Both pages are server-rendered entrypoints. They use `CHURN_API_BASE_URL` with a local default and pass validated data into feature components. Test-only query scenarios are forwarded to mock API handlers used by browser tests.

## Customer dashboard data flow

```text
DashboardPage (server)
  └── fetchDashboardAnalytics
        └── GET /analytics/dashboard
              └── runtime response parsing
                    └── DashboardClient
                          └── buildExecutiveDashboardModel
                                ├── KpiCards
                                ├── CohortChart
                                ├── DriverSummary
                                └── RiskTable
```

`DashboardPage` fetches on the server and passes either `initialAnalytics` or an `initialError` to the client component. `DashboardClient` can also fetch in the browser when neither value is supplied, guards against state updates after cleanup, and renders a polite loading message while waiting.

`buildExecutiveDashboardModel` is the main presentation transformation. It:

- formats PR-AUC, recall, risk counts, and average sampled risk into KPI cards;
- groups prediction samples by contract and computes average probability and monthly charge;
- sorts cohorts deterministically by size and name;
- sorts samples by churn probability and keeps the top five;
- labels risk against the persisted API threshold, falling back to `0.5` only when the optional threshold is absent from the typed input;
- formats percentages, decimals, currency, freshness, and empty-sample copy.

The UI therefore receives display-ready models while the API response types remain close to transport semantics.

## Education dashboard data flow

```text
EducationPage (server, force-dynamic)
  └── fetchEducationAnalysis
        └── GET /analytics/education (no-store, 10 s timeout)
              └── parseEducationAnalysis
                    └── EducationDashboard
                          └── summary and analytical chart sections
```

The education page is always dynamically rendered. Its client parser is intentionally stricter than a TypeScript interface alone:

- schema version must be `1`;
- `decision_support_only` and `qualified_human_review_required` must both be `true`;
- serialized content containing `Student_ID` is rejected;
- numeric values must be finite and rates must lie between zero and one;
- coefficient directions must be positive, negative, or neutral;
- cohort suppression must agree with `count < minimum_cohort_size`;
- every suppressed cohort statistic must be `null`;
- SHAP must use `exact_independent_linear` in `log_odds`;
- SHAP contributions must add to the model output and the output must map to the reported probability within tolerance.

Only after these checks does the parser produce the `EducationAnalysis` model used by the dashboard. This duplicates selected safety invariants at the browser boundary so a malformed or incompatible API response cannot be rendered as trustworthy analysis.

## Visualization semantics

The customer dashboard translates one artifact-backed snapshot into executive retention views. The model version and freshness remain visible, and all derived cohort or risk views originate from the API's bounded prediction samples.

The education dashboard is explanatory rather than causal. Its sections distinguish:

- coefficients and odds ratios from the logistic model;
- global feature importance from SHAP and held-out permutation analysis;
- train/test association measures appropriate to numeric or categorical variables;
- cohort sample size, suppression, observed intervals, average predicted risk, and performance measures;
- signed sample-level SHAP contributions in log-odds units.

Warnings and methodological limits travel with the publication. A chart or card should not remove the context required to interpret those values.

## Loading, empty, and unavailable states

Each route has a route-level `loading.tsx` state. The customer client also exposes an `aria-live` loading message and an explicit empty-sample KPI instead of dividing by zero or showing a fabricated average.

Customer API errors become an artifact-unavailable card that keeps the API's reason when available. Education failures render a dedicated unavailable-publication page with the error, configuration guidance, and the explicit statement that no demonstration values are substituted.

This behavior is an architectural guarantee: a polished chart is never allowed to hide the absence of a valid analytical publication.

## Contract and browser verification

The web test layers have different jobs:

- API-client tests validate response mapping, error propagation, education safety checks, suppression invariants, and SHAP consistency.
- dashboard-model tests validate formatting, grouping, sorting, threshold labels, and empty samples.
- page tests validate server-page success and failure composition.
- Playwright tests exercise healthy, empty, loading, and degraded browser states against controlled API fixtures.

When changing an API field, update the transport type, runtime parser, presentation model, component, and relevant unit/E2E fixture together. TypeScript compilation alone cannot prove runtime JSON compatibility.

## Related pages

- [FastAPI Serving Boundary](api-serving.md)
- [Education Impact Analysis Workflow](../workflows/education-analysis.md)
- [Local Development and Verification](../operations/local-development-and-verification.md)

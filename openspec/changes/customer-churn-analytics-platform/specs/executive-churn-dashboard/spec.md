## ADDED Requirements

### Requirement: Executive Churn Overview

The dashboard MUST present churn KPIs, cohort trends, risk distribution, top-risk customers, and driver explanations using API-backed data.

#### Scenario: Analytics data loads

- GIVEN the analytics API returns current artifacts
- WHEN an executive opens the dashboard
- THEN they see KPI cards, cohort charts, risk tables, and driver summaries
- AND every metric identifies its model/artifact freshness

#### Scenario: Analytics data is unavailable

- GIVEN the API reports degraded health or missing artifacts
- WHEN the dashboard loads
- THEN the dashboard MUST show an actionable error state instead of stale or invented values

### Requirement: Enterprise UI States and Accessibility

The dashboard SHALL implement loading, error, empty, and data states with semantic navigation, accessible tables, and reusable shadcn/Tailwind components.

#### Scenario: Table renders customer risks

- GIVEN customer risk rows are available
- WHEN the risk table renders
- THEN rows are keyboard-readable, sortable where supported, and expose status text beyond color

#### Scenario: No predictions exist yet

- GIVEN analytics artifacts contain no prediction rows
- WHEN the dashboard renders
- THEN it shows an empty state explaining the next modeling step

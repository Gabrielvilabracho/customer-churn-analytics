# Delta for Portfolio Documentation

## MODIFIED Requirements

### Requirement: Reviewable Project Narrative

The project MUST provide a README, dataset card, modeling report, architecture notes, and API guidance that accurately describe the education burnout-risk product. The local-start documentation MUST provide executable commands, prerequisites, and expected checks for provisioning the ignored CSV, generating one complete artifact run, starting FastAPI with that same artifact root and run ID, and starting the existing Next.js dashboard against the API.

(Previously: Documentation required a general portfolio narrative but still permitted an obsolete Telco-oriented setup path.)

#### Scenario: Reviewer starts the education dashboard

- GIVEN a reviewer has an operator-supplied education CSV and the documented toolchains
- WHEN they follow the documented ML → FastAPI → Next.js sequence
- THEN the commands consistently reuse one explicit run ID
- AND the documented health and dashboard checks return live education analytics

#### Scenario: Reviewer has not provisioned artifacts

- GIVEN the canonical CSV or selected artifact run is absent
- WHEN the reviewer follows the startup guide
- THEN the documentation MUST identify the expected degraded API/dashboard behavior
- AND it MUST explain how to provision or regenerate the missing local input without redistribution

#### Scenario: Dataset has limitations

- GIVEN dataset provenance or licensing is uncertain, restricted, biased, or otherwise limited
- WHEN the dataset card is read
- THEN the uncertainty and product impact MUST be stated plainly
- AND the documentation MUST NOT instruct reviewers to commit or redistribute raw data

### Requirement: Responsible Student-Risk Use

The documentation MUST state that burnout-risk analytics are decision-support-only and require qualified human review before any consequential use. It MUST prohibit automated student actions based on these outputs, including discipline, grading, enrollment, accommodations, access to services, or equivalent outcomes, and MUST NOT provide automation instructions for those actions.

#### Scenario: Reviewer evaluates responsible use

- GIVEN a reviewer reads the dashboard, API, or dataset guidance
- WHEN they evaluate how burnout-risk outputs may be used
- THEN the documentation identifies the outputs as decision-support-only
- AND it requires qualified human review before consequential use

#### Scenario: Operator considers an automated student action

- GIVEN an operator considers using a burnout-risk output to automate a consequential student action
- WHEN they follow the project documentation
- THEN the documentation prohibits that automation
- AND it provides no command, integration, or workflow that performs the action

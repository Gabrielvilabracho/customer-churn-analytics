# Portfolio Documentation Specification

## Purpose

Define the documentation behavior needed to make the project reviewable as a premium portfolio system rather than a notebook demo.

## Requirements

### Requirement: Reviewable Project Narrative

The project MUST provide a README, dataset card, modeling report, architecture notes, and API guidance that accurately describe the education burnout-risk product. The local-start documentation MUST provide executable commands, prerequisites, and expected checks for provisioning the ignored CSV, generating one complete artifact run, starting FastAPI with that same artifact root and run ID, and starting the existing Next.js dashboard against the API.

#### Scenario: Reviewer starts the education dashboard

- GIVEN a reviewer has an operator-supplied education CSV and the documented toolchains
- WHEN they follow the documented ML → FastAPI → Next.js sequence
- THEN the commands consistently reuse one explicit run ID
- AND the documented health and metadata checks return live education analytics
- AND the documentation identifies the dashboard endpoint's expected degraded response for education runs (the pipeline emits no public cohort fields) and the mock-backed dashboard visual states

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

### Requirement: Engineering Standards as User-facing Guarantees

The documentation SHALL state system guarantees for reproducibility, deterministic artifacts, clean module boundaries, English-only product copy, and testable acceptance criteria.

#### Scenario: Implementation is reviewed

- GIVEN a reviewer compares specs, artifacts, and source code
- WHEN they inspect the architecture notes
- THEN they can trace dataset acquisition through ML artifacts, API adapters, and dashboard consumption

#### Scenario: Shortcut is introduced

- GIVEN a change bypasses artifact contracts or hardcodes dashboard metrics
- WHEN documentation acceptance criteria are checked
- THEN the change MUST be marked non-compliant until the shortcut is removed

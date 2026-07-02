# Engineering Delivery Workflow Specification

## Purpose

Define the strict TDD, CI, and branch/PR workflow required before implementation begins.

## Requirements

### Requirement: Strict Module-level TDD

The project MUST use RED-GREEN-REFACTOR for every implementation slice. The first task in a slice MUST install or configure the relevant test runner before writing application behavior.

#### Scenario: ML slice starts

- GIVEN the ML/data slice is selected
- WHEN implementation begins
- THEN failing pytest tests for dataset, artifact, or model behavior are written before production code
- AND the slice is not complete until the matching pytest command passes

#### Scenario: API or web slice starts

- GIVEN an API or dashboard behavior is selected
- WHEN implementation begins
- THEN API route/use-case tests or frontend component/E2E tests are written before production code
- AND typecheck and relevant tests pass before review

### Requirement: CI-gated Stacked PR Delivery

The project SHALL deliver work through branch-based stacked-to-main PRs under the 400 changed-line review budget, with automated GitHub Actions checks for every slice.

#### Scenario: PR is opened

- GIVEN a work-unit branch targets `main`
- WHEN a PR is opened
- THEN GitHub Actions runs PR metadata validation plus the relevant ML, API, web, or E2E checks
- AND the PR is blocked if checks fail or the branch lacks the required issue/link/type metadata

#### Scenario: Slice exceeds review budget

- GIVEN a planned slice exceeds 400 changed lines
- WHEN tasks are reviewed before apply
- THEN the slice MUST be split into smaller work-unit PRs or explicitly approved as a size exception

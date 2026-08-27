# Tasks: Activate Local Education Dashboard

## Review Workload Forecast

Estimated changed lines: ~2,100
Delivery strategy: auto-chain
Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

Dirty worktree is not merge-ready; reconstruct from refreshed `origin/main`, never stage wholesale.

| PR | Branch | Label | Target | Issue |
|---|---|---|---|---|
| 1 | `docs/education-sdd-intent` | `type:docs` | `main` | #32 |
| 2 | `docs/education-sdd-design` | `type:docs` | `main` | #32 |
| 3 | `feat/education-store-preflight` | `type:feat` | `main` | #32 |
| 4 | `feat/education-publication` | `type:feat` | `main` | #32 |
| 5 | `feat/education-store-integrity` | `type:feat` | `main` | #32 |
| 6 | `feat/education-provenance` | `type:feat` | `main` | #32 |
| 7 | `feat/education-cli-preflight` | `type:feat` | `main` | #32 |
| 8 | `feat/education-cli-publication` | `type:feat` | `main` | #32 |
| 9 | `feat/education-reader` | `type:feat` | `main` | #32 |
| 10 | `feat/education-degradation` | `type:feat` | `main` | #32 |
| 11 | `feat/education-runtime` | `type:feat` | `main` | #32 |
| 12 | `test/education-cli-api` | `type:test` | `main` | #32 |
| 13 | `docs/education-workflow` | `type:docs` | `main` | #32 |
| 14 | `docs/education-closeout` | `type:docs` | `main` | #32 |

## Phase 1: SDD Baseline

- [x] 1.1 **PR 1 (~386):** Update `AGENTS.md`; add exploration, proposal, and four spec deltas. Gate: OpenSpec, `git diff --check`, ≤400.
- [x] 1.2 **PR 2:** Add design, tasks, and minimal status. Same gate.

## Phase 2: ML Contracts

- [x] 2.1 **RED/GREEN PR 3:** Add `artifact_store.py` preflight/tests; reject unsafe/incomplete runs.
- [x] 2.2 **RED/GREEN PR 4:** Add manifest-last publication/overwrite rejection with tests.
- [x] 2.3 **RED/GREEN PR 5:** Add lease and exact-byte reads; prove one publisher, no mixed generation.
- [x] 2.4 **RED/GREEN PR 6:** Add `provenance.py`, `.gitignore`, and tests; reject contradictory metadata.
- [x] 2.5 **RED/GREEN PRs 7–8:** Validate provenance before CLI writes; add `__main__.py` lease/publish/cleanup and tests.

## Phase 3: Serving Contracts

- [x] 3.1 **RED/GREEN PR 9:** Add snapshots in `artifacts.py`/`adapters/filesystem.py`; test unavailable, tampered, valid reads.
- [x] 3.2 **RED/GREEN PR 10:** Add `services.py`/`routes.py` warnings and `503`s; reject fabricated analytics.
- [x] 3.3 **RED/GREEN PR 11:** Add `create_runtime_app(environ)` and `apps/api/pyproject.toml`; test configured, blank, injected dependencies.
- [x] 3.4 **RED/GREEN PR 12:** Add CLI/API test; fixture returns `200`, tampering `503`.

## Phase 4: Docs and Closure

- [x] 4.1 **PR 13:** Update `README.md` and six `docs/` files; test commands, limits, degradation, non-redistribution.
- [x] 4.2 Exclude package locks; confirm root `uv.lock` remains valid—no lock PR.
- [x] 4.3 **PR 14:** Reconcile; run OpenSpec, CI, free-port Playwright, CLI/API smoke, and bind review to unchanged PASS.
- [x] 4.4 After PR 14, archive, sync specs, validate OpenSpec, then close #32.

Merge order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14. After each merge, refresh `origin/main`, recreate the next branch, run its focused gate, `git diff --check`, full CI, and the unchanged 400-line guard; rollback newest first.
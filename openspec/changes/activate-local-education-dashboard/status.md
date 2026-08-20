# Current Delivery Status

**Status: Chain complete — PRs 1-14 merged; ready for archive, spec sync, and issue #32 close**

This file records the reconciled state after the final chain PR (14) merges.
The stacked-to-main chain is complete; the remaining steps are defined in
`tasks.md` 4.4: archive the change, sync delta specs into `openspec/specs/`,
validate OpenSpec, and close issue #32.

## Delivery Boundary

Every branch started from refreshed `origin/main` after its predecessor
merged, targeted `main`, linked issue #32, and carried exactly one `type:*`
label. Package-local generated locks stayed excluded (tasks 4.2); the tracked
root `uv.lock` remains authoritative. Raw data, generated artifacts, and
unrelated archive work remained excluded throughout.

## Current Implementation Evidence

- **PRs 1-2 (docs):** SDD intent and design baselines (`AGENTS.md`,
  exploration, proposal, four delta specs, design, tasks, status).
- **PRs 3-6 (ML contracts):** store preflight, manifest-last publication with
  overwrite rejection, exact-byte integrity/concurrency, provenance and
  ignore rules — each with focused artifact-store tests.
- **PRs 7-8 (CLI):** provenance validation before CLI writes; `__main__.py`
  lease/publish/cleanup with tests.
- **PR 9 (reader):** snapshot reads in `artifacts.py`/`adapters/filesystem.py`;
  unavailable, tampered, and valid reads tested.
- **PR 10 (degradation):** `services.py`/`routes.py` warnings and `503`s;
  fabricated analytics rejected.
- **PR 11 (runtime composition):** `create_runtime_app(environ)` with
  `CHURN_ARTIFACT_RUN_ID`/`CHURN_ARTIFACT_ROOT`; module-level ASGI `app`;
  `apps/api/pyproject.toml` runtime dependency on `churn-ml`.
- **PR 12 (CLI-to-API integration):** integration tests proving a CLI-published
  education run serves health/metadata/predict (200) and degrades on tampering
  (503); dashboard degrades instead of fabricating (no public cohort fields).
- **PR 13 (docs):** README and six `docs/` files document the executable
  education workflow, degraded dashboard behavior, and responsible-use limits;
  fixed a relative-root bug in the artifact store completion manifest
  (`root.resolve()`) with a regression test.
- **PR 14 (reconcile):** status record updated; portfolio-documentation delta
  spec aligned with the verified degraded-dashboard behavior.

## Reconciliations

- The portfolio-documentation scenario "dashboard returns live education
  analytics" was aligned with the verified behavior: education prediction
  samples carry no public cohort fields, so `/analytics/dashboard` degrades
  (`503`) for real education runs; dashboard visual states are covered by the
  web E2E suite with a mock API. The API never fabricates analytics.
- The relative-root artifact store bug (completion manifest recorded
  cwd-relative member paths) was fixed and regression-tested in PR 13.

## Bounded Review Authority

The authoritative review transaction follows the native compact lineage
finalized against the merged worktree. Its receipt, not a free-form status
claim, is the review authority after `gentle-ai review finalize` and
`gentle-ai review bind-sdd` complete. The final verification report is
produced by the 4.4 verify phase before archiving.

## Next Gate

After PR 14 merges, run the 4.4 closeout: execute the full verification
(`sdd-verify`), archive the change, sync delta specs into `openspec/specs/`,
validate OpenSpec, and close issue #32.
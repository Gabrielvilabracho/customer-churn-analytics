# Exploration: Activate Local Education Dashboard

## Current State

The education-domain ML, API, and web contracts are already compatible. The ML CLI defaults to `Student_ID` and `Burnout_Risk_Level`, excludes the two known leakage columns, writes versioned filesystem bundles, and persists `model.joblib` with a SHA-256 file. The dashboard already requests `GET /analytics/dashboard` from `CHURN_API_BASE_URL` (default `http://localhost:8000`) and renders the live response.

The local activation path is incomplete. `data/raw/*` and generated artifact directories are already ignored, but the documentation still describes the Telco dataset. The API's default composition uses `_UnavailableArtifactReader`, so a normal Uvicorn process cannot serve local artifacts; `FilesystemArtifactSnapshotReader` is only exercised through dependency injection in tests. The API also defaults to `StubChurnScorer`, and no documented runtime command provisions Uvicorn plus both local source packages.

## Delivery Reconciliation

The activation is delivered as focused, reviewable slices. Design and task artifacts are added before implementation begins. The change avoids renaming the churn-oriented package/API vocabulary or redesigning the stub prediction scorer.

The verified local CSV is outside the repository and has the expected education schema. Its public provenance and redistribution license remain unrecorded, so it must remain local and must not be committed.

## Affected Areas

- `.gitignore` — already ignores `data/raw/*`, `artifacts/metrics/**`, `artifacts/models/**`, and binary model files; no ignore-rule expansion is required.
- `data/raw/.gitkeep` — existing safe local-data placeholder; a documented education subpath can be provisioned locally without tracking the CSV.
- `packages/ml/src/churn_ml/__main__.py` — already provides the education training defaults and calls `save_model_binary` after `run_training` writes the artifact bundle.
- `packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py` — defines the required local artifact layout: metrics JSON and prediction samples, model metadata, `model.joblib`, and checksum.
- `apps/api/src/churn_api/main.py` — requires a production/local composition root that constructs `FilesystemArtifactSnapshotReader(root, run_id)` instead of the unavailable default.
- `apps/api/src/churn_api/adapters/filesystem.py` — is the existing Hexagonal adapter to reuse; its bundle output already satisfies dashboard analytics.
- `apps/api/pyproject.toml` and root `pyproject.toml` — do not provide a documented Uvicorn/local-package runtime bootstrap.
- `apps/web/app/(dashboard)/page.tsx` and `apps/web/lib/api/client.ts` — already fetch and validate live analytics; no dashboard implementation change is needed for this activation.
- `README.md`, `docs/dataset-card.md`, `docs/modeling-report.md`, `docs/architecture.md`, and `docs/api-contract.md` — retain Telco/churn wording and commands that conflict with the current education implementation.
- `apps/api/tests/test_analytics_api.py`, `apps/api/tests/adapters/test_filesystem_snapshot_reader.py`, and `packages/ml/tests/integration/test_training_entrypoint.py` — cover artifact contracts in isolation, but not an environment-configured process composition or real local dashboard lifecycle.

## Approaches

1. **Explicit local activation composition** — Document one ignored education CSV location and deterministic run ID; add a thin API composition root that reads explicit local runtime configuration and injects `FilesystemArtifactSnapshotReader`; document and test the ML → API → web startup sequence.
   - Pros: Reuses all existing contracts, keeps filesystem concerns in adapters/composition, preserves degraded behavior when configuration or artifacts are absent, and needs no dashboard change.
   - Cons: Requires a small runtime/bootstrap decision for Uvicorn and local package resolution; `/predict` remains stub-backed unless intentionally scoped separately.
   - Effort: Medium.

2. **Operator-only manual injection** — Keep source unchanged and run a custom shell/Python wrapper that imports the app factory, builds the filesystem reader, and starts Uvicorn.
   - Pros: Minimal repository diff.
   - Cons: Fragile, undocumented composition outside the codebase, difficult to test, and does not establish a reproducible portfolio review path.
   - Effort: Low initially, High operational risk.

3. **Add a full artifact-loaded prediction scorer now** — Load `model.joblib` at API startup in addition to the snapshot reader and replace `StubChurnScorer`.
   - Pros: Makes `/predict` genuinely model-backed.
   - Cons: Broadens the change beyond activating live dashboard analytics; needs feature encoding/parity and scorer contract tests that are not required by the dashboard endpoint.
   - Effort: High.

## Recommendation

Use **Approach 1**. The delivered chain documents copying the verified CSV into the ignored canonical path `data/raw/ai-student-impact/ai_student_impact_dataset.csv`, validates local-only provenance/checksum metadata before training, publishes immutable artifacts with a deterministic safe run ID, composes the API with `FilesystemArtifactSnapshotReader`, and documents/tests the supported Uvicorn and Next.js launch sequence with `CHURN_API_BASE_URL`.

The web dashboard needs no production-code change: its existing typed fetch client will render live analytics once `/analytics/dashboard` returns a bundle. Keep model-binary loading for `/predict` explicitly out of this change; the CLI already persists the binary, but API scoring is a separate contract.

## Risks

- The source CSV's license and provenance are not yet documented; never commit, redistribute, or claim a source license for it without verification.
- The artifact reader requires an exact `run_id`; there is no `latest` pointer or discovery mechanism, so the training and API configuration must use the same deterministic value.
- `main.create_app()` intentionally defaults to degraded artifacts and a stub scorer; changing this must retain test injection and safe degraded responses when env configuration is missing.
- The current project configuration does not define a Uvicorn command or a workspace install for both local Python packages. The change must establish one reproducible local command and cover it with a composition test.
- Existing documentation materially misrepresents the education product as Telco churn, risking a reviewer following the wrong data path.

## Ready for Proposal

Yes — propose the scoped local activation path. State clearly that it provisions only ignored local data/artifacts, preserves the existing dashboard API contract, and does not make `/predict` model-binary-backed in this change.

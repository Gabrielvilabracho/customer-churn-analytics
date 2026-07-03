## Exploration: Real ML Pipeline Continuation

### Current State
The repository has moved past the original bootstrap described in the previous exploration. `packages/ml` now contains tested acquisition/profile primitives, framework-free artifact contracts, deterministic split/evaluation helpers, a constant churn-rate baseline trainer, and filesystem JSON/CSV artifact persistence. `apps/api` can read the current artifact bundle shape through `FilesystemArtifactSnapshotReader` and expose health, metadata, dashboard summaries, and prediction responses from those artifacts.

The current ML layer is still mostly contract/scaffolding code. There is no real CSV dataset loader, preprocessing transformer, categorical encoding, train-only fitting, stratified split, scikit-learn candidate model, model binary persistence, CLI/module entry point, or end-to-end command that turns `data/raw/...` into `data/processed/...` plus API-consumable `artifacts/{metrics,models}/<run_id>/...`. The remaining checked OpenSpec tasks point to dashboard work, so the ML continuation needs a new focused task slice rather than applying the existing unchecked Phase 4 tasks.

### Affected Areas
- `openspec/changes/customer-churn-analytics-platform/tasks.md` — currently marks Phase 2 ML artifacts complete and leaves only dashboard/docs tasks; it needs a new ML continuation slice before apply.
- `openspec/specs/churn-ml-artifacts/spec.md` — already names preprocessing/training/evaluation artifacts, but may need clarified scenarios for real CSV-to-artifact execution and model persistence.
- `openspec/changes/customer-churn-analytics-platform/design.md` — describes richer ML dependencies and flow than currently implemented; should be updated if the next slice chooses pandas/scikit-learn and an executable training entry point.
- `packages/ml/src/churn_ml/application/pipelines/{features.py,train.py,evaluate.py}` — current pure helpers should become the orchestration boundary for real preprocessing, candidate training, evaluation, threshold selection, and artifact export.
- `packages/ml/src/churn_ml/infrastructure/sklearn/baseline.py` — currently only constant probability; next slice should add a real sklearn-compatible candidate trainer behind the existing `ModelTrainer` port.
- `packages/ml/src/churn_ml/infrastructure/filesystem/artifact_store.py` — already writes metrics, prediction samples, model metadata, and cleaned splits; next slice should extend or reuse it for model binary/reference persistence without breaking the API reader.
- `packages/ml/tests/` — existing tests cover contracts; new failing tests should cover raw CSV fixture processing, train-only transforms, model comparison, artifact files, and API-compatible manifest schema.
- `apps/api/src/churn_api/adapters/filesystem.py` — only needs contract awareness; avoid API rewrites unless the ML artifact schema changes.

### Approaches
1. **Apply existing tasks as-is** — Start the next unchecked OpenSpec tasks.
   - Pros: No planning overhead.
   - Cons: The unchecked tasks are Phase 4 dashboard work, which conflicts with the requested ML focus; Phase 2 is already checked despite being only scaffold-level.
   - Effort: Low, but wrong direction.

2. **Update SDD tasks/design for a real ML continuation slice** — Add a focused Phase 2B/ML continuation work unit: CSV fixture/data loading, preprocessing, sklearn candidate trainer, executable training pipeline, and API-compatible artifacts.
   - Pros: Aligns with current repo state, keeps Strict TDD intact, avoids frontend scope creep, and gives apply a precise target under the 400-line review budget.
   - Cons: Requires a small SDD update before coding.
   - Effort: Medium.

3. **Jump straight to full production ML stack** — Add pandas, scikit-learn, XGBoost/LightGBM, SHAP, MLflow, reports, and orchestration in one slice.
   - Pros: Stronger portfolio story eventually.
   - Cons: Too large for the review budget, likely to blur artifact contracts, and premature before the local CSV-to-artifact path is proven.
   - Effort: High.

### Recommendation
Choose **Approach 2: update SDD tasks/design for a real ML continuation slice**, then run apply against that slice. The next implementation should be narrow: prove one deterministic local training command/function that consumes an approved CSV or committed test fixture, fits preprocessing on train only, trains baseline plus one sklearn candidate, selects a threshold, and writes the existing API-compatible artifact bundle plus cleaned splits. Do not start dashboard work yet.

Recommended slice name: **Phase 2B: Real Local ML Training Pipeline**.

Minimum acceptance targets for the slice:
- Add failing pytest coverage first for CSV fixture ingestion, preprocessing/schema validation, deterministic/stratified split behavior, candidate-vs-baseline selection, threshold tradeoff, and filesystem artifacts.
- Add only necessary ML dependencies (`pandas`, `scikit-learn`, optionally `joblib`) to `packages/ml`/workspace config.
- Keep domain/application code framework-free; pandas/sklearn stay in infrastructure or thin pipeline adapters.
- Preserve `ArtifactBundle` fields consumed by the API: `manifest.feature_schema`, `metrics`, `threshold`, and `prediction_samples`.
- Persist a model reference/binary under `artifacts/models/<run_id>/` without requiring the API to score with the real model in this slice unless explicitly scoped.

### Risks
- Existing tasks are stale for this continuation: direct apply would launch dashboard work, not ML.
- Adding pandas/sklearn can exceed the 400-line budget if preprocessing, training, CLI, and docs are bundled too broadly.
- The current profile gate blocks any `*id` feature; real Telco data may include `customerID`, so the next slice must treat identifiers as excluded columns rather than blindly blocking the whole dataset after registration.
- API compatibility can break if artifact schema changes without adapter tests.
- Without a real local CSV fixture, tests may remain contract-only and fail to prove the end-to-end pipeline.

### Ready for Proposal
No new proposal is needed for the overall change. The orchestrator should update **tasks first**, and update **design/spec only if it wants explicit acceptance language for Phase 2B**. Do not launch apply directly from the existing tasks because the remaining unchecked tasks are dashboard/documentation tasks, not the requested ML pipeline continuation.

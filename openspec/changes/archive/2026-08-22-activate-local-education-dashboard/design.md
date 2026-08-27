# Design: Activate Local Education Dashboard

## Technical Approach

Preserve the Hexagonal flow: the ML CLI validates provenance and publishes an immutable run; the filesystem adapter validates it; FastAPI selects it in the composition root; the unchanged Next.js dashboard consumes `GET /analytics/dashboard`. Reconstruct only residual behavior from `origin/main`; never replay PR #28 or duplicate merged PRs #29–#31. Use clean sequential stacked-to-main branches linked to #32, each passing the unchanged 400-line gate.

## Architecture Decisions

| Choice | Alternative / tradeoff | Rationale |
|---|---|---|
| `create_runtime_app(environ)` plus module ASGI `app` | Configure inside `create_app()` | Keeps injection deterministic without import-time artifact I/O. |
| Explicit safe run ID; no `latest` | Automatic discovery | Prevents training/serving identity drift. |
| Start degraded and return structured `503` warnings | Fail startup | Preserves availability and existing `StubChurnScorer` behavior. |
| Publish a checksummed completion manifest last and validate exact bytes under a per-run lease | Validate then reread; overwrite runs | Prevents partial, mixed, altered, or concurrent generations. |
| Require `selected_run_id` on the reader port | Service inference | Makes degradation deterministic; unavailable readers return `None`. |
| Keep the CI guardrail and 400-line default unchanged | Bootstrap an 800-line allowance | Global review policy is outside this feature; abandoned PR 0 contributes nothing. |
| Pair each behavior with focused tests; split shared production/test files only at green semantic boundaries | Production-first or test-only layering by file type | Every intermediate main state remains coherent, tested, and reversible. |
| Keep package-local generated locks out of this change | Add 557- and 278-line lockfile PRs | The repository tracks the root `uv.lock`; generated package locks cannot form valid sub-400-line work units. |
| Persist verification before content-bound review | Review then write reports | Avoids `scope-changed` verification. |

## Data Flow

```text
ignored CSV + provenance -> ML CLI -> leased writes -> completion manifest
  -> exact-byte filesystem reader -> FastAPI -> Next.js dashboard

origin/main -> residual behavior + focused tests -> 400-line gate -> merge -> refreshed origin/main
```

## File Changes

| File | Action | Description |
|---|---|---|
| `.github/workflows/ci.yml`, delivery-budget policy | No change | Retain the existing 400-line enforcement; no bootstrap slice. |
| `.gitignore`, `packages/ml/src/churn_ml/{__main__.py,infrastructure/filesystem/artifact_store.py}` | Modify/Create | Protect local data; add publication, provenance, and CLI orchestration. |
| `packages/ml/tests/{test_ml_artifact_contracts.py,test_cli_main.py}` | Modify/Create | Prove publication, provenance, concurrency, and failure-before-write behavior. |
| `apps/api/src/churn_api/{adapters/filesystem.py,application/ports/artifacts.py,application/services.py,main.py,presentation/http/routes.py}` | Modify | Add published-run reading, selected identity, runtime composition, and structured degradation. |
| `apps/api/tests/{adapters/test_filesystem_snapshot_reader.py}` | Modify/Create | Prove reader, startup, and CLI-to-API behavior. |
| `apps/api/pyproject.toml` | Modify | Declare runtime dependencies with composition; do not add package-local locks. |
| `README.md`, `docs/{dataset-card.md,dataset-metadata.template.json,modeling-report.md,architecture.md,api-contract.md,local-verification.md}` | Modify | Document the executable education workflow and limitations. |

## Interfaces / Contracts

- `CHURN_ARTIFACT_RUN_ID` is optional for API startup and MUST match `[A-Za-z0-9_-]+`; blank remains degraded.
- `CHURN_ARTIFACT_ROOT` defaults to repository-relative `artifacts`.
- `data/raw/ai-student-impact/{ai_student_impact_dataset.csv,source-metadata.json}` remains ignored; unknown licensing prohibits redistribution.
- The completion manifest records run ID, generation ID, and every required member checksum; published runs are immutable.

## Testing Strategy

| Layer | Gate |
|---|---|
| Slice | Focused RED/GREEN tests, `git diff --check`, and additions + deletions ≤400. |
| CI on every PR | PR metadata/budget; full pytest, Ruff, mypy; Vitest, ESLint, TypeScript, build; Playwright. |
| Final integration | CLI publishes a run; API returns `200`, then tampering returns `503`; dashboard smoke uses free ports. |

## Migration / Rollout

No data migration or feature flag. Planning must first establish the active OpenSpec baseline, then merge-gated work units are:

1. Intent baseline: `AGENTS.md`, exploration, proposal, and all delta specs.
2. Design baseline: design, task plan, and minimal status record.
3. Publication manifest/immutability, then exact-byte integrity/concurrency; each owns focused artifact-store tests.
4. Provenance validation and ignore rules, then CLI preflight/publication with focused tests.
5. Published reader, degradation, runtime composition, and independent CLI-to-API integration hardening.
6. Operator documentation and guardrails, then verification receipts/review and archive/spec sync.

Every branch starts from refreshed `origin/main` after its predecessor merges, targets `main`, links #32, and carries one `type:*` label. Measure before opening; above 400 lines, split the next semantic behavior rather than change policy or request an exception.

Rollback reverses merged slices newest to oldest. Unsetting runtime variables restores degraded mode; ignored data/artifacts can be deleted locally.

Closure reconciles the active records, runs strict OpenSpec and CI, then binds review to the unchanged candidate. Archive only after a truthful PASS.

## Open Questions

None.
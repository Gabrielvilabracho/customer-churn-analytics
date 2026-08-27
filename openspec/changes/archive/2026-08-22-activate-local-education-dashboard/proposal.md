# Proposal: Activate Local Education Dashboard

## Intent

Provide a reproducible education CSV-to-dashboard path. The change selects explicit filesystem artifacts at normal API startup and replaces stale reviewer guidance with the canonical local workflow.

## Planning Baseline

The current baseline contains the exploration, proposal, and delta specs. Design
and task artifacts are added before implementation begins.

## Scope

### In Scope
- Place an operator-supplied CSV at an ignored canonical path with local checksum/provenance metadata.
- Run the existing ML CLI with an explicit safe run ID and validate its complete bundle.
- Configure the API composition root with the artifact root/run ID while preserving degraded responses.
- Document and test the supported ML → FastAPI → existing Next.js dashboard startup sequence.

### Out of Scope
- Predictive-model, feature-encoding, dashboard, or `StubChurnScorer` redesign.
- Dataset redistribution/download automation, deployment, or `latest` artifact discovery.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `dataset-acquisition`: Define local-only CSV provisioning and provenance handling.
- `churn-ml-artifacts`: Require a complete bundle under a reusable run ID.
- `churn-analytics-api`: Compose configured filesystem artifacts while retaining degraded behavior.
- `portfolio-documentation`: Document the verified education lifecycle.

## Approach

Reuse the ML CLI and `FilesystemArtifactSnapshotReader`. Later implementation WILL change application code at the listed adapter, port, service, composition, and HTTP-route boundaries; domain and web production code remain unchanged. It will enforce canonical local input/provenance paths and immutable completed runs.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `data/raw/`, `artifacts/` | Local | Ignored input and generated run bundle |
| `packages/ml/src/churn_ml/{__main__.py,infrastructure/filesystem/artifact_store.py,infrastructure/filesystem/provenance.py}` | Modified/Create | Validate local provenance and safe run IDs; publish immutable, checksummed bundles; serialize concurrent publication. |
| `packages/ml/tests/` | Modified/Create | Cover incomplete runs, publication integrity/concurrency, provenance, and CLI preflight. |
| `apps/api/src/churn_api/main.py` | Modified | Compose configured local artifacts while preserving dependency injection. |
| `apps/api/src/churn_api/adapters/filesystem.py` | Modified | Read and validate selected filesystem snapshots. |
| `apps/api/src/churn_api/application/ports/artifacts.py` | Modified | Expose selected-run identity and snapshot contract. |
| `apps/api/src/churn_api/application/services.py` | Modified | Project valid artifact data and deterministic degradation. |
| `apps/api/src/churn_api/presentation/http/routes.py` | Modified | Return ready/degraded analytics and decision-support safeguards. |
| `apps/api/tests/` | Modified/Create | Cover reader integrity, runtime composition, degraded behavior, and CLI-to-API flow. |
| `README.md`, `docs/` | Modified | Education provisioning and startup path |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Unknown dataset license | High | Keep local/ignored; record uncertainty; prohibit redistribution |
| Training/API run-ID mismatch | Medium | Use one explicit value throughout commands and tests |
| Startup regression | Low | Preserve injection seams and degraded defaults |

## Rollback Plan

Revert composition, tests, and documentation; remove ignored local data/artifacts. The API returns to its existing degraded artifact reader and the web fallback remains functional.

## Dependencies

- Operator-provided education CSV; existing Python and Node toolchains.

## Success Criteria

- [ ] Provisioning and training leave raw data and generated artifacts untracked.
- [ ] One run ID produces a complete bundle and serves live `GET /analytics/dashboard` data.
- [ ] Missing configuration/artifacts still produce explicit degraded behavior.
- [ ] The existing dashboard renders that API response without production web changes.
- [ ] Startup docs use education data and executable commands; relevant tests pass.

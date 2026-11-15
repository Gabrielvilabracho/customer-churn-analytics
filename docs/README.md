# Documentation index

This directory is the canonical portfolio-facing documentation surface. Start
here to review the product, its evidence, its contracts, and its limitations
without relying on private planning tools.

## Reviewer path

1. Read [Dataset card](dataset-card.md) for provenance, license, redistribution,
   and research limits.
2. Read [Modeling report](modeling-report.md) for the implemented analytical
   method and measured results.
3. Read [Architecture](architecture.md) for the artifact-to-API-to-dashboard flow
   and system boundaries.
4. Read [API contract](api-contract.md) for public endpoints, degraded behavior,
   and the legacy `/predict` stub.
5. Read [Education variable analysis](education-variable-analysis.md) and
   [Trustworthy education experiments](education-experiments.md) for the local
   analysis and independent evaluation workflows.
6. Read the [Education model lifecycle roadmap](model-lifecycle-roadmap.md) for
   the gated path from model comparison through explanation, Registry,
   controlled deployment, and privacy-safe monitoring.

## Source-of-truth hierarchy

| Surface | Owns | Does not own |
|---------|------|--------------|
| `docs/` | Canonical reviewer/operator explanations and portfolio evidence | Active task status or private planning |
| `odd/tasks/` | Current execution status, recovery context, scoped acceptance criteria, and task logs | Durable product specification history |
| `openspec/changes/` | Active durable product/specification deltas | Day-to-day recovery logs |
| `openspec/specs/` | Accepted durable repository specifications | Current implementation status |
| `openspec/changes/archive/` | Historical completed changes | Active work queues |
| Obsidian | Private planning context | Any prerequisite for repository review |

ODD complements rather than replaces OpenSpec. If an implementation task and a
durable specification need reconciliation, update the governing artifacts instead
of treating a private note or stale archive entry as current authority.

## Documentation map

| Concern | Canonical entry point | Supporting evidence |
|---------|-----------------------|---------------------|
| Dataset provenance and safe use | [Dataset card](dataset-card.md) | [Source verification record](dataset-source-verification.json), [research protocol](research-protocol.md), and [literature evidence matrix](literature-evidence-matrix.md) |
| Modeling and metric interpretation | [Modeling report](modeling-report.md) | [Metric semantics](metric-semantics.md) |
| Review capacity and error costs | [Exploratory review-capacity protocol](review-capacity-protocol.md) | Validation threshold/top-k trade-offs, hypothetical effort, and unresolved operational acceptance |
| Education-variable interpretation | [Education variable analysis](education-variable-analysis.md) | [Education artifact publication](education-artifacts.md) |
| Experiment tracking and MLOps boundary | [Trustworthy education experiments](education-experiments.md) | [Experiment environment](experiment-environment.md) and [model lifecycle roadmap](model-lifecycle-roadmap.md) |
| Runtime architecture | [Architecture](architecture.md) | [Local verification](local-verification.md) |
| HTTP behavior | [API contract](api-contract.md) | [Education API](education-api.md) |
| Exploratory analysis | `notebooks/EDA.ipynb` | Notebook outputs remain uncommitted unless a governing documentation contract says otherwise. |

## Boundary summary

- Research evidence is portfolio evidence, not external validation, a diagnosis,
  or proof of causal effects.
- Generated datasets, model binaries, reports, and tracking stores remain local
  and ignored unless a specific reviewed contract permits publication.
- Local MLflow is optional, SQLite-backed, aggregate-only, and not a production
  registry or deployment platform.
- The API serves artifact-backed analytics, but `/predict` remains a legacy
  deterministic stub rather than verified model inference.
- No remote registry, model promotion, deployment automation, production
  monitoring, drift alerting, or rollback capability is implemented.

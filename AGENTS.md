# Project Agent Instructions

## Project Goal

Build a premium portfolio-grade AI Student Impact Analytics platform: an end-to-end analytical product that studies how AI use relates to student burnout risk, explains measured risk factors without causal claims, and presents education-oriented findings through a FastAPI API and a Next.js analytical dashboard.

## Language Contract

- Code, identifiers, comments, documentation, UI copy, and technical artifacts MUST be written in English.
- User conversation may happen in Spanish, but generated project artifacts stay in English unless explicitly requested otherwise.

## Architecture Direction

- Use Clean Architecture / Hexagonal Architecture.
- Keep business logic independent from frameworks, UI, storage, and external services.
- Build the analytical core first; build the visual dashboard only after data artifacts and API contracts are credible.
- Prefer small, discoverable modules over large mixed-responsibility files.

## Planned Stack

- Data and ML: Python, pandas, NumPy, scikit-learn, XGBoost or LightGBM, Plotly, SHAP where useful.
- API: FastAPI.
- Frontend: Next.js, TypeScript, Tailwind CSS, shadcn/ui.
- Metrics/artifacts first: CSV and JSON outputs remain authoritative; optional local MLflow only compares reviewed experiment outputs.
- Deployment comes after the core has stable contracts and verification.

## Delivery and Documentation Workflow

Use each documentation surface for one responsibility:

| Surface | Responsibility |
|---------|----------------|
| `odd/tasks/` | Current execution and recovery logs. Read the relevant task from the top through `## Log` before implementation; its task-scoped specs and status govern the active slice. |
| `openspec/changes/` | Active durable product/specification deltas. Current deltas include `education-experiments` and `education-variable-analysis`. |
| `openspec/specs/` | Durable repository specifications after accepted deltas are reconciled. |
| `openspec/changes/archive/` | Historical changes, including the completed local education dashboard activation. Archive entries are context, not active work queues. |
| `docs/` | Canonical portfolio-facing documentation for reviewers and operators. Start at `docs/README.md`. |
| Obsidian | Private planning context only. Repository work and review MUST NOT depend on access to a private vault. |

- ODD did not replace OpenSpec: ODD records execution/recovery state, while OpenSpec retains durable product intent and specification history.
- Read the relevant ODD task first, then the active OpenSpec delta and durable specs it references.
- Keep implementation inside the active task slice. Update the governing ODD/OpenSpec artifact before expanding scope.
- Keep reviewer-facing explanations in `docs/`; do not make private planning notes a prerequisite for understanding the repository.

## Dataset Rules

- Kaggle data acquisition MUST respect dataset licenses.
- Raw Kaggle datasets SHOULD NOT be committed unless the license explicitly allows redistribution.
- Prefer documenting dataset download steps and keeping raw data under `data/01-raw/` ignored by git.
- Check for target leakage before modeling.

## Review Budget

- Default review budget: 400 changed lines.
- If implementation exceeds the budget, use chained PRs or ask for an explicit size exception before continuing.

## Skill Injection Notes

- Relevant current skills include SDD, cognitive doc design, data engineering, Python backend, enterprise frontend, Next.js, Tailwind, and shadcn/ui.
- Sub-agents should receive the relevant skill paths or compact rules before reading, writing, reviewing, or testing project artifacts.

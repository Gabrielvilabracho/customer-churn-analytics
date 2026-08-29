# Project Agent Instructions

## Project Goal

Build a premium portfolio-grade Customer Churn Prediction platform: an end-to-end analytical product that predicts customer churn, explains risk factors, and helps prioritize retention actions through a FastAPI prediction API and a Next.js executive dashboard.

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
- Metrics/artifacts first: CSV and JSON outputs before introducing MLflow.
- Deployment comes after the core has stable contracts and verification.

## SDD / OpenSpec Workflow

- OpenSpec is the artifact store for this project.
- Current change: `activate-local-education-dashboard`.
- Read SDD artifacts before implementation:
  - `openspec/changes/activate-local-education-dashboard/exploration.md`
  - `openspec/changes/activate-local-education-dashboard/proposal.md`
  - `openspec/changes/activate-local-education-dashboard/specs/*/spec.md`
- Design and task artifacts are optional until they are added to this change.
- Do not implement outside the planned task slices unless the SDD artifacts are updated first.

## Dataset Rules

- Kaggle data acquisition MUST respect dataset licenses.
- Raw Kaggle datasets SHOULD NOT be committed unless the license explicitly allows redistribution.
- Prefer documenting dataset download steps and keeping raw data under `data/01-raw/` ignored by git.
- Check for target leakage before modeling.

## Review Budget

- Default review budget: 400 changed lines.
- If implementation exceeds the budget, use chained PRs or ask for an explicit size exception before continuing.

## Skill Injection Notes

- Use `.atl/skill-registry.md` to identify relevant Gentle AI skills for delegated work.
- Relevant current skills include SDD, cognitive doc design, data engineering, Python backend, enterprise frontend, Next.js, Tailwind, and shadcn/ui.
- Sub-agents should receive the relevant skill paths or compact rules before reading, writing, reviewing, or testing project artifacts.

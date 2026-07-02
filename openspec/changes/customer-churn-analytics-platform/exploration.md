## Exploration: Customer Churn Analytics Platform

### Current State
The repository is currently an SDD/OpenSpec bootstrap only. There are no application source files, package manifests, test runners, formatters, or build commands yet. Existing project context in `openspec/config.yaml` defines the intended direction: Python for data and ML, FastAPI for the prediction/analytics API, Next.js + Tailwind CSS + shadcn/ui for the dashboard, Clean/Hexagonal Architecture, English-only artifacts/code, CSV/JSON metric artifacts first, MLflow later, and deployment later after the core is stable.

The product should be a portfolio-grade analytical product, not a notebook demo. It should show that a churn model can be acquired, cleaned, evaluated, explained, served through an API, and consumed by an executive B2B SaaS dashboard.

### Affected Areas
- `openspec/config.yaml` — Existing SDD context and phase rules that future proposal/spec/design/tasks should honor.
- `openspec/changes/customer-churn-analytics-platform/` — Active OpenSpec change folder for this exploration and future SDD artifacts.
- Future `apps/api/` — FastAPI service exposing prediction, cohort analytics, model metadata, and health endpoints.
- Future `apps/web/` — Next.js dashboard using Tailwind CSS and shadcn/ui for a premium B2B SaaS analytics experience.
- Future `packages/ml/` or `src/churn_ml/` — Python ML pipeline for data ingestion, EDA, cleaning, feature engineering, training, evaluation, and artifacts.
- Future `data/` — Dataset storage and metadata boundaries for raw, interim, processed, and sample data.
- Future `artifacts/` — Versioned CSV/JSON/model outputs for metrics, thresholds, feature importance, schema, and trained model references.
- Future `docs/` — Product narrative, dataset card, modeling report, architecture notes, and portfolio-facing explanation.

### Approaches
1. **Notebook-first prototype** — Start with exploratory notebooks, then extract code into backend/frontend later.
   - Pros: Fast visual exploration; easy early EDA; familiar data science workflow.
   - Cons: High risk of becoming an academic notebook UI; weak architecture; delayed API/product integration; harder to test and reproduce.
   - Effort: Low initially, Medium/High to harden later.

2. **Core-first product monorepo** — Build a modular monorepo with Python ML, FastAPI API, and Next.js web boundaries from the beginning; use notebooks only as disposable or report artifacts.
   - Pros: Matches portfolio narrative; supports clean boundaries; easier testing and reproducibility; API and dashboard can consume real artifacts; keeps the product from becoming a notebook demo.
   - Cons: More setup upfront; requires careful task slicing to avoid oversized changes.
   - Effort: Medium.

3. **MLOps-heavy platform from day one** — Add MLflow, orchestration, model registry, deployment, and monitoring immediately.
   - Pros: Strong production story; clear MLOps signal.
   - Cons: Too much infrastructure before the core problem is proven; distracts from dataset quality, evaluation, and product clarity.
   - Effort: High.

### Recommendation
Use **Core-first product monorepo**.

The first implementation should prove the analytical core before visual polish: dataset acquisition, reproducible data preparation, baseline and main model training, threshold tuning, evaluation artifacts, and a FastAPI API that serves predictions and analytics from versioned artifacts. The frontend should come after the core is credible, then present the product as an executive retention dashboard.

#### Problem Solved
The product helps business stakeholders identify customers at risk of churn, understand the drivers behind that risk, and prioritize retention actions using interpretable model outputs and cohort-level analytics.

#### Explicitly Out of Scope
- Real-time production data ingestion.
- Paid deployment, cloud infrastructure, and model monitoring in the first phase.
- User authentication, multi-tenant SaaS billing, or CRM integrations.
- Full MLflow/model registry setup until CSV/JSON artifacts and local reproducibility are stable.
- Over-optimized UI animation before the analytics core is correct.

#### Target Users and Portfolio Narrative
- **Executive stakeholder**: sees retention risk, revenue exposure, churn distribution, and high-value customer segments.
- **Customer success / retention operator**: filters risky cohorts and reviews drivers to decide outreach priority.
- **Technical reviewer / recruiter**: sees clean architecture, reproducible ML, API boundaries, typed contracts, testability, and product thinking.

Narrative: “This is a B2B customer intelligence product that turns a raw churn dataset into actionable retention analytics through a reproducible ML pipeline, production-shaped API, and premium dashboard.”

#### End-to-End Product Flow
1. Select a Kaggle churn dataset that is business-relevant, licensed for portfolio use, tabular, documented, and rich enough for meaningful feature engineering.
2. Acquire and snapshot the dataset with source metadata, license notes, checksum, and dataset version/date.
3. Run EDA: schema profile, target distribution, missingness, outliers, cardinality, categorical levels, structural/economic variables, leakage checks, and segment analysis.
4. Build cleaning and feature engineering pipeline with deterministic transformations.
5. Train baselines and main model candidates; evaluate with classification and business metrics.
6. Tune decision threshold based on retention-oriented tradeoffs, not only default accuracy.
7. Export artifacts: metrics JSON/CSV, threshold config, feature importance, model card, schema, predictions sample, trained model file.
8. Serve artifacts through FastAPI endpoints for prediction, dashboard analytics, model metadata, and health.
9. Build Next.js dashboard around executive KPIs, churn segments, model performance, high-risk customer table, and driver explanations.
10. Document the portfolio story with setup, architecture, modeling report, limitations, and next steps.

#### Dataset Acquisition Strategy
Recommended strategy: **hybrid reproducibility**.

- Prefer Kaggle API/CLI when the dataset permits scripted download: `kaggle datasets list -s <query>`, `kaggle datasets download -d <dataset-id> --unzip`, with authentication handled outside the repository via `kaggle auth login`, `KAGGLE_API_TOKEN`, `~/.kaggle/access_token`, or legacy `~/.kaggle/kaggle.json`.
- Also support manual download as a fallback because reviewers may not have Kaggle credentials configured.
- Store a dataset card with source URL, dataset ID, license, download date, file checksums, row/column counts, and known limitations.
- If the dataset is small and license permits redistribution, commit a raw snapshot under `data/raw/<dataset_slug>/` for portfolio reproducibility. If not, commit only metadata and download instructions; keep raw files out of source control.

Dataset selection criteria:
- Churn target is explicit and binary or cleanly derivable.
- Business context is understandable: telecom, banking, subscription, e-commerce, or SaaS-like retention.
- Includes economic/behavioral variables such as tenure, contract type, charges/revenue, support signals, usage, or engagement.
- Has enough rows and class balance to support meaningful evaluation.
- Has categorical variables that require real encoding decisions.
- Has no obvious target leakage columns or post-churn fields.
- License allows public portfolio usage.

#### Proposed Architecture
Recommended monorepo shape:

```text
apps/
  api/                    # FastAPI application
    src/churn_api/
      domain/             # Entities/value objects: CustomerFeatures, Prediction, RiskSegment
      application/        # Use cases: PredictChurn, GetDashboardMetrics, GetModelMetadata
      ports/              # ModelRepository, MetricsRepository, FeatureTransformer
      adapters/           # File artifact repositories, sklearn model adapter
      presentation/http/  # FastAPI routers, DTOs, error mapping
      main.py
  web/                    # Next.js dashboard
    app/                  # App Router pages/layout/loading/error
    components/ui/        # shadcn/ui primitives
    components/features/  # churn dashboard feature components
    lib/api/              # API client and typed response mapping
packages/
  ml/                     # Python package for ML workflow
    src/churn_ml/
      ingestion/          # Kaggle/manual dataset acquisition helpers
      profiling/          # EDA/profile outputs
      preprocessing/      # cleaning, encoding, splitting, feature pipeline
      training/           # baselines and model candidates
      evaluation/         # metrics, threshold tuning, reports
      artifacts/          # artifact writers/readers
      config/             # dataset/model configuration
data/
  raw/                    # immutable source snapshot if allowed
  interim/                # generated, not hand-edited
  processed/              # model-ready data
artifacts/
  models/
  metrics/
  reports/
docs/
  dataset-card.md
  modeling-report.md
  architecture.md
```

Backend boundaries:
- Domain and application layers must not import FastAPI, pandas, sklearn, or filesystem details.
- Ports define model and artifact access; adapters implement local artifact/model loading.
- Presentation layer owns HTTP routes, Pydantic DTOs, request validation, and error mapping.
- API responses should expose business-facing risk fields, not raw model internals only.

ML pipeline boundaries:
- Ingestion/profiling/preprocessing/training/evaluation/artifact export should be separate modules.
- Transformations should be reproducible and configurable.
- Evaluation should write machine-readable artifacts first; visual reports can be generated from artifacts.

Frontend boundaries:
- Keep dashboard components grouped by feature, not generic page sprawl.
- Use shadcn/ui primitives first: Card, Table, Badge, Chart, Sidebar, Tabs, Skeleton, Empty, Alert, Tooltip.
- Use Tailwind semantic tokens and `cn()` only for conditional classes.
- Data components must have loading, error, empty, and data states.

#### Data Analysis and Feature Engineering Plan
- Profile schema: column types, unique counts, ranges, missingness, duplicates, invalid values.
- Analyze churn distribution and class imbalance.
- Study numeric variables: tenure, charges, revenue, usage, support counts, balances, or equivalent economic/behavioral fields.
- Study categorical variables: contract type, payment method, plan, geography, service usage, engagement bands.
- Detect outliers and decide whether to cap, transform, bucket, or preserve them.
- Check missingness mechanism: structural missing values versus random missing values.
- Identify leakage candidates: fields created after churn, cancellation metadata, or labels encoded in status columns.
- Create feature groups: customer profile, economic value, tenure/relationship, product/service mix, support/friction, engagement/usage.
- Encode categorical variables with train-only fitted encoders; avoid fitting transformations on validation/test data.
- Split data with stratification; use a stable random seed and document split strategy.

#### Modeling and Evaluation Strategy
- Baselines: majority-class baseline, simple logistic regression, and decision tree or random forest baseline.
- Main model: gradient boosting model for tabular data if dependencies are acceptable; otherwise RandomForest/HistGradientBoosting as a strong sklearn-first choice.
- Compare at least two models using the same split and artifact format.
- Primary technical metrics: ROC-AUC, PR-AUC, recall, precision, F1, confusion matrix, calibration view if feasible.
- Business metrics: recall at top-risk deciles, churn capture rate in top N%, false-positive workload, estimated saved revenue/opportunity using assumptions, and threshold-specific retention queue size.
- Threshold tuning: select threshold based on business tradeoff between missed churners and outreach capacity, not default `0.5`.
- Explainability: start with permutation importance or model-native feature importance; SHAP can be considered later if it does not distract from the core.
- Artifact-first tracking: write metrics, threshold, feature importance, schema, and report summaries as JSON/CSV; defer MLflow until artifact conventions are stable.

#### Design System Direction
The dashboard should feel like reliable executive analytics software: calm, precise, dense enough for decision-making, but not noisy.

- Visual tone: premium B2B SaaS, clear hierarchy, high trust, low decoration.
- Layout: app shell with sidebar, top summary area, KPI cards, segmented charts, risk table, and detail drawer.
- Palette: neutral slate base, one primary accent, semantic success/warning/danger/info. Use danger/warning carefully for risk, not as decoration.
- Typography: enterprise scale with tabular numbers for metrics and tables.
- Components: shadcn/ui Card, Table, Badge, Chart, Tabs, Sidebar, Skeleton, Empty, Alert, Tooltip, Sheet/Drawer.
- UX states: loading skeletons, empty states, recoverable error states, and model/data freshness indicators.
- Avoid: academic notebook charts, rainbow palettes, unexplained ML jargon, decorative 3D, or over-animated hero sections before the product is credible.

#### Engineering Standards
- Universal language: English for code, artifacts, docs, UI copy, API contracts, and comments.
- Naming: domain-first names (`churn_risk`, `retention_priority`, `customer_features`), not notebook names (`final2`, `test_model`).
- Module organization: separate ingestion, preprocessing, training, evaluation, API, and UI feature boundaries.
- Dependency hygiene: separate Python ML/API dependencies from Node frontend dependencies; lock dependency files once stack exists.
- Documentation: maintain `README.md`, dataset card, modeling report, architecture notes, API contract notes, and dashboard usage guide.
- Testing once stack exists:
  - Python unit tests for cleaning, feature engineering, thresholding, artifact readers, and use cases.
  - API tests for validation, prediction route, analytics route, health, and error mapping.
  - Frontend component tests for loading/error/empty/data states once UI exists.
  - Optional E2E test for the dashboard happy path after frontend is stable.
- Review budget: implementation should be sliced into work units below the 400 changed-line review budget where practical.

#### Recommended Next Phase
Proceed with **sdd-propose**, then **sdd-spec**, **sdd-design**, and **sdd-tasks**.

Proposal should lock scope, dataset strategy, product narrative, architecture approach, and explicit non-goals. Spec should define requirements for dataset acquisition, ML artifacts, API behavior, dashboard behavior, documentation, and evaluation outputs. Design should then formalize module boundaries, API contracts, artifact schemas, and data/model flow diagrams.

### Risks
- Dataset licensing may prevent committing raw Kaggle data; fallback instructions and metadata must be clear.
- Some popular churn datasets are too toy-like or leak target information; selection must include quality screening.
- Churn class imbalance can make accuracy misleading; evaluation must emphasize recall/precision tradeoffs and business thresholds.
- Frontend polish can distract from the analytical core if started too early.
- Clean Architecture can be over-engineered if applied mechanically; boundaries should protect use cases without adding ceremony.
- No current app stack or test tooling exists, so future tasks must establish toolchain conventions before implementation.
- Kaggle API credentials must never be committed; acquisition docs must keep auth local to the developer environment.

### Ready for Proposal
Yes. The orchestrator should tell the user that exploration recommends a core-first product monorepo, hybrid Kaggle dataset acquisition, artifact-first ML evaluation, FastAPI clean/hexagonal API boundaries, and a later premium B2B SaaS dashboard once the analytical core is proven.

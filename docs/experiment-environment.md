# Local experiment tracking and logging boundaries

The default development group does not require MLflow or notebook execution.
Select `tracking` for local experiment logging and `notebooks` for notebook
execution and plotting. Both groups are recorded in the same `uv.lock`.

The immutable experiment report remains the source of truth. MLflow is an
optional local comparison view over reviewed report fields; it is not a
production MLOps control plane.

## Check the lock without installing

From the repository root:

```bash
uv lock --check --offline --no-cache --no-python-downloads --python .venv/bin/python
```

This checks dependency declarations against the committed lock without
resolving from the network, installing packages or rewriting the lockfile.

## Create a separate optional environment

These commands install packages and can access the package index. Run them
only when you want the optional tools. Choose an absolute environment path
outside the checkout and an already installed Python 3.13 interpreter:

```bash
export UV_PROJECT_ENVIRONMENT=/absolute/path/outside/checkout/experiment-venv
uv sync --locked --group tracking --group notebooks --python 3.13 --no-python-downloads
```

Python 3.13 was used for the local optional-integration checks. The explicit
environment path keeps the existing project `.venv` separate. Missing Python
or package availability is an error, not permission to modify another
environment or bypass the lock.

| Group | Tools |
|-------|-------|
| `tracking` | MLflow 3.x, installed only when selected |
| `notebooks` | nbclient, nbformat, ipykernel and matplotlib |

Installing MLflow does not start a tracking server or authorize remote
tracking. Keep student records, model binaries and generated artifacts local
and out of Git. Installation alone does not establish experiment validity.

## What local tracking records

When `--mlflow-dir` is supplied to the education experiment command, the tracker
creates `<mlflow-dir>/tracking.db` and `<mlflow-dir>/artifacts/`. It explicitly
uses that local SQLite backend and local artifact directory rather than ambient
remote tracking or registry settings.

Before MLflow is imported or writes anything, the tracker verifies report and
model checksums and enforces an aggregate privacy allowlist. It can record:

- dataset/source hashes, code and library versions, split counts and hashes;
- reviewed experiment configuration and selected model parameters;
- aggregate validation and final-test metrics, calibration bins, confusion
  counts, false-positive rate, and flagged workload; and
- a privacy-reduced report, completion manifest, and selected local model.

It does not log raw student rows or student identifiers, use autologging,
upload the notebook automatically, register a model remotely, or start a
tracking server. The loopback-only UI command and operational cautions live in
`docs/education-experiments.md`.

## Application logging

The ML pipeline emits lifecycle messages through Python process logging. The API
emits structured warning context when artifact-backed endpoints degrade. These
messages go through the logging configuration of the process that launches the
application; this repository does not configure centralized collection,
retention, dashboards, alerting, or production telemetry.

## MLOps capabilities not implemented

Local immutable artifacts and optional tracking improve reproducibility, but
they do not provide:

- a remote MLflow service or shared experiment store;
- a model registry, approval gate, or promotion lifecycle;
- automated deployment or rollback;
- production model/data monitoring or external validation; or
- drift, performance, or safety alerts.

Do not infer any of these capabilities from the presence of MLflow dependencies,
a local SQLite database, or checksum-bound artifacts.

## Planned lifecycle expansion

The [education model lifecycle roadmap](model-lifecycle-roadmap.md) sequences
future work without changing the current capability claims:

1. compare logistic regression, XGBoost, and LightGBM under one immutable
   experiment contract;
2. explain only the selected model with estimator-appropriate SHAP;
3. register reviewed, checksum-bound model versions behind an explicit promotion
   gate;
4. deploy one exact version through a controlled, reversible serving contract;
   and
5. monitor aggregate runtime, drift, workload, and valid delayed-performance
   signals without storing student identities or raw rows.

Each step requires its predecessor's verified evidence. Listing a phase here does
not mean that its Registry, deployment, or monitoring capability is implemented.

## Typing boundaries

The mypy configuration keeps project code under strict checking while
explicitly exempting untyped third-party runtime boundaries: `joblib`, optional
`mlflow`, and the scientific stack (`pandas`, `scipy`, and `scikit-learn`).
Missing third-party stubs do not disable checks for project code.

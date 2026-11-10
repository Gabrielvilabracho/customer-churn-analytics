# Keep experiment tools optional

The default development group does not require MLflow or notebook execution.
Select `tracking` for local experiment logging and `notebooks` for notebook
execution and plotting. Both groups are recorded in the same `uv.lock`.

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

## Typing boundaries

The mypy configuration keeps project code under strict checking while
explicitly exempting untyped third-party runtime boundaries: `joblib`, optional
`mlflow`, and the scientific stack (`pandas`, `scipy`, and `scikit-learn`).
Missing third-party stubs do not disable checks for project code.

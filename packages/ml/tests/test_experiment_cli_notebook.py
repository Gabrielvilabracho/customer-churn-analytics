import csv
import json
import os
from pathlib import Path

import pytest
from churn_ml.experiments import main
from test_education_experiments import student_rows


def test_public_cli_writes_report_and_duplicate_refuses_without_mutation(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://example.invalid")
    source = tmp_path / "students.csv"
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(student_rows()[0]))
        writer.writeheader()
        writer.writerows(student_rows())
    args = [
        "run",
        "--csv",
        str(source),
        "--c-values",
        "1",
        "--report-id",
        "run-v1",
        "--output-root",
        str(tmp_path / "reports"),
    ]
    assert main(args) == 0
    first = capsys.readouterr()
    payload = json.loads(first.out)
    assert payload["evaluation"]["split"] == "test"
    report = Path(payload["report"])
    before = {p.name: p.read_bytes() for p in report.iterdir()}
    assert main(args) == 2
    second = capsys.readouterr()
    assert "already exists" in second.err
    assert not second.out
    assert {p.name: p.read_bytes() for p in report.iterdir()} == before
    assert not (tmp_path / "tracking.db").exists()


def test_notebook_executes_verified_aggregate_report_without_saving_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    from churn_ml.experiments import run_experiment
    from churn_ml.infrastructure.filesystem.experiment_reports import publish_report

    root = Path(__file__).resolve().parents[3]
    path = root / "notebooks/EducationExperiments.ipynb"
    original = path.read_bytes()
    notebook = nbformat.reads(original.decode(), as_version=4)
    assert all(not c.get("outputs") and c.get("execution_count") is None for c in notebook.cells)
    result = run_experiment(student_rows(), c_values=(1.0,))
    directory = publish_report(tmp_path, "notebook-v1", result.report)
    monkeypatch.setenv("EDUCATION_EXPERIMENT_REPORT", str(directory))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    monkeypatch.setenv("MPLBACKEND", "Agg")
    monkeypatch.setenv("IPYTHONDIR", str(tmp_path / "ipython"))
    monkeypatch.setenv("JUPYTER_CONFIG_DIR", str(tmp_path / "jupyter"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv(
        "PATH", str(Path(os.sys.executable).parent) + os.pathsep + os.environ["PATH"]
    )
    nbclient.NotebookClient(
        notebook, timeout=120, kernel_name="python3", resources={"metadata": {"path": str(root)}}
    ).execute()
    assert path.read_bytes() == original
    assert any(c.get("outputs") for c in notebook.cells)

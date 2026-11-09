import json
import sys
from pathlib import Path

import pytest
from churn_ml.infrastructure.mlflow_tracking import LocalMlflowTracker


def test_tracker_rejects_remote_destinations_before_import_or_writes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="local"):
        LocalMlflowTracker("https://example.invalid")
    assert not list(tmp_path.iterdir())


def test_local_mlflow_ignores_ambient_remote_settings_and_logs_only_aggregates(
    tmp_path: Path, monkeypatch
) -> None:
    pytest.importorskip("mlflow")
    from churn_ml.experiments import run_experiment
    from churn_ml.infrastructure.filesystem.experiment_reports import publish_report
    from mlflow import MlflowClient
    from test_education_experiments import student_rows

    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://example.invalid")
    monkeypatch.setenv("MLFLOW_REGISTRY_URI", "https://example.invalid")
    result = run_experiment(student_rows(), c_values=(1.0,))
    result.report["warnings"].append(
        "Student_ID=private-student-42; source=/private/student-data.csv"
    )
    directory = publish_report(tmp_path / "reports", "run-v1", result.report, model=result.model)
    tracker = LocalMlflowTracker(tmp_path / "tracking")
    run_id = tracker.log(directory)
    client = MlflowClient(tracking_uri=tracker.uri, registry_uri=tracker.uri)
    run = client.get_run(run_id)
    assert run.info.status == "FINISHED"
    assert run.data.metrics["test.recall"] == result.report["evaluation"]["metrics"]["recall"]
    assert run.data.params["selected_model"] == result.model.model_name
    assert float(run.data.params["model.C"]) == 1.0
    assert "validation.pr_auc" in run.data.metrics
    assert run.info.artifact_uri.startswith((tmp_path / "tracking").as_uri())
    artifacts = {item.path for item in client.list_artifacts(run_id)}
    assert artifacts == {"report.json", "model.joblib", "completion.json"}
    tracked_report = Path(client.download_artifacts(run_id, "report.json")).read_text()
    assert "private-student-42" not in tracked_report
    assert '"warnings"' not in tracked_report
    assert "private-student-" not in json.dumps(run.to_dictionary())


def test_cli_help_does_not_import_optional_mlflow(monkeypatch) -> None:
    from churn_ml.experiments import main

    monkeypatch.setitem(sys.modules, "mlflow", None)
    with pytest.raises(SystemExit) as error:
        main(["--help"])
    assert error.value.code == 0

"""Independent aggregate privacy and lossless candidate-attribution regressions."""

import hashlib
import json
import socket
from unittest.mock import patch

import pytest
from churn_ml.experiments import run_experiment
from churn_ml.infrastructure.filesystem.experiment_reports import publish_report
from churn_ml.infrastructure.mlflow_tracking import LocalMlflowTracker
from churn_ml.infrastructure.sklearn.candidate import SklearnProbabilityModel
from test_education_experiments import student_rows


@pytest.mark.parametrize(
    "location,key,value",
    [
        ("configuration", "Student_ID", "private-student-42"),
        ("configuration", "c_values", [{"Student_ID": "private-student-42"}]),
        (None, "raw_rows", [{"Student_ID": "private-student-42"}]),
        (None, "individual_predictions", [0.95]),
        (None, "source_filename", "/private/student-data.csv"),
        (None, "features", {"raw_rows": [{"Student_ID": "private-student-42"}]}),
        (None, "warnings", [{"Student_ID": "private-student-42"}]),
    ],
)
def test_tracker_rejects_private_report_fields_before_any_writes(tmp_path, location, key, value):
    report = run_experiment(student_rows(), c_values=(1.0,)).report
    destination = report if location is None else report[location]
    destination[key] = value
    directory = publish_report(tmp_path / "reports", "privacy-probe", report)

    def hashes():
        return {
            str(p.relative_to(tmp_path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in tmp_path.rglob("*")
            if p.is_file()
        }

    before = hashes()
    with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
        with pytest.raises(ValueError, match="privacy allowlist"):
            LocalMlflowTracker(tmp_path / "tracking").log(directory)
    assert hashes() == before


@pytest.mark.parametrize("mutation", ["unmanifested_model", "private_completion"])
def test_tracker_rejects_unverified_artifacts_before_any_writes(tmp_path, mutation):
    report = run_experiment(student_rows(), c_values=(1.0,)).report
    directory = publish_report(tmp_path / "reports", "manifest-probe", report)
    if mutation == "unmanifested_model":
        (directory / "model.joblib").write_bytes(b"unverified model bytes")
    else:
        completion = json.loads((directory / "completion.json").read_text())
        completion["raw_rows"] = [{"Student_ID": "private-student-42"}]
        (directory / "completion.json").write_text(json.dumps(completion))

    before = {
        str(path.relative_to(tmp_path)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
        with pytest.raises(ValueError, match="privacy allowlist"):
            LocalMlflowTracker(tmp_path / "tracking").log(directory)
    after = {
        str(path.relative_to(tmp_path)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_selected_candidate_attribution_preserves_close_hyperparameter_values(tmp_path):
    pytest.importorskip("mlflow")
    from mlflow import MlflowClient

    original = SklearnProbabilityModel.predict_probabilities
    observed = []

    def predict(self, batch):
        scores = original(self, batch)
        observed.append((batch, scores))
        return scores

    cs = (1.000001, 1.000004)
    with patch.object(SklearnProbabilityModel, "predict_probabilities", predict):
        run_experiment(student_rows(), c_values=cs)
    minima = [
        min(p for row, p in zip(batch, scores, strict=True) if row["Burnout_Risk_Level"] == "High")
        for batch, scores in observed[:2]
    ]
    result = run_experiment(
        student_rows(), c_values=cs, thresholds=(sum(minima) / 2,), min_recall=1.0
    )
    selected_c = result.model.estimator.named_steps["classifier"].C
    assert selected_c == cs[1]
    names = [candidate["model_name"] for candidate in result.report["validation_candidates"]]
    assert len(names) == len(set(names))
    directory = publish_report(
        tmp_path / "reports", "selected-probe", result.report, model=result.model
    )
    tracker = LocalMlflowTracker(tmp_path / "tracking")
    with patch.object(socket.socket, "connect", side_effect=AssertionError("network forbidden")):
        run_id = tracker.log(directory)
        stored = MlflowClient(tracking_uri=tracker.uri, registry_uri=tracker.uri).get_run(run_id)
    assert float(stored.data.params["model.C"]) == selected_c
    assert stored.data.metrics["validation.recall"] == 1.0

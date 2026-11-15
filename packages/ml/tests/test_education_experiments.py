import json
from pathlib import Path

import pytest
from churn_ml.application.pipelines.experiment_reports import diagnostics
from churn_ml.experiments import run_experiment
from churn_ml.infrastructure.filesystem.experiment_reports import publish_report, read_report
from churn_ml.infrastructure.sklearn.candidate import SklearnProbabilityModel


def student_rows() -> list[dict[str, str]]:
    return [
        {
            "Student_ID": f"private-student-{i}",
            "Weekly_GenAI_Hours": str(i % 3 * 8 + i % 5 / 10),
            "Major_Category": "Arts" if i % 2 else "STEM",
            "Post_Semester_GPA": str(i % 3),
            "Skill_Retention_Score": str(i % 3),
            "Burnout_Risk_Level": ("Low", "Medium", "High")[i % 3],
        }
        for i in range(150)
    ]


def test_diagnostics_report_calibration_and_every_classification_outcome() -> None:
    result = diagnostics((0, 0, 1, 1), (0.1, 0.6, 0.4, 0.9), 0.5)
    assert result["confusion"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert result["false_positive_rate"] == 0.5
    assert result["flagged_count"] == 2
    assert result["brier_score"] == pytest.approx(0.185)
    assert sum(row["count"] for row in result["reliability"]) == 4


def test_experiments_fit_only_train_select_on_validation_then_predict_test(monkeypatch) -> None:
    seen: list[set[str]] = []
    original = SklearnProbabilityModel.predict_probabilities

    def observe(self, rows):
        seen.append({row["Student_ID"] for row in rows})
        return original(self, rows)

    monkeypatch.setattr(SklearnProbabilityModel, "predict_probabilities", observe)
    result = run_experiment(student_rows(), c_values=(0.1, 1.0))
    report = result.report
    assert report["splits"]["train"]["count"] == 90
    assert report["splits"]["validation"]["count"] == 30
    assert report["splits"]["test"]["count"] == 30
    assert len(seen) == 3  # Two validation predictions, then selected model's final test.
    assert seen[0] == seen[1]
    assert not seen[0] & seen[2]
    assert report["selection"]["split"] == "validation"
    assert report["evaluation"]["split"] == "test"
    assert report["selection"]["model_name"] == result.model.model_name
    assert set(result.model.feature_columns) == {"Weekly_GenAI_Hours", "Major_Category"}
    scaler = result.model.estimator.named_steps["preprocess"].named_transformers_["numeric"]
    assert scaler.n_samples_seen_ == 90
    assert "private-student-" not in json.dumps(report)
    assert report == run_experiment(student_rows(), c_values=(0.1, 1.0)).report


def test_duplicate_students_and_invalid_configuration_are_rejected() -> None:
    rows = student_rows()
    rows[1]["Student_ID"] = rows[0]["Student_ID"]
    with pytest.raises(ValueError, match="unique"):
        run_experiment(rows)
    with pytest.raises(ValueError, match="positive"):
        run_experiment(student_rows(), c_values=(-1.0,))


def test_changing_only_test_outcomes_cannot_change_validation_selection(monkeypatch) -> None:
    import churn_ml.application.pipelines.experiments as pipeline

    original = pipeline.stratified_train_test_split
    reference = run_experiment(student_rows(), c_values=(1.0,)).report
    calls = 0

    def change_test(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            for row in result.test_rows:
                row["Burnout_Risk_Level"] = "Low" if row["Burnout_Risk_Level"] == "High" else "High"
        return result

    monkeypatch.setattr(pipeline, "stratified_train_test_split", change_test)
    altered = run_experiment(student_rows(), c_values=(1.0,)).report
    assert altered["selection"] == reference["selection"]
    assert altered["validation_candidates"] == reference["validation_candidates"]
    assert altered["evaluation"] != reference["evaluation"]


def test_reports_are_immutable_and_checksum_verified(tmp_path: Path) -> None:
    report = {"kind": "synthetic", "evaluation": {"accuracy": 0.5}}
    path = publish_report(tmp_path, "report-v1", report)
    assert read_report(path) == report
    before = (path / "report.json").read_bytes()
    with pytest.raises(ValueError, match="exists"):
        publish_report(tmp_path, "report-v1", report)
    assert (path / "report.json").read_bytes() == before
    (path / "report.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        read_report(path)


@pytest.mark.parametrize("scores", [(float("nan"), 0.5), (-0.1, 0.5)])
def test_diagnostics_reject_invalid_probabilities(scores) -> None:
    with pytest.raises(ValueError, match="probabilit"):
        diagnostics((0, 1), scores, 0.5)

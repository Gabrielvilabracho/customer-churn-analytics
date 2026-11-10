from pathlib import Path
from typing import Any

import pytest
from churn_ml.application.pipelines.reevaluate_education import reevaluate_education
from churn_ml.application.ports.education_reevaluation import EducationReevaluationInputs


class InMemoryModel:
    def predict_probabilities(self, rows: list[dict[str, Any]]) -> tuple[float, ...]:
        assert len(rows) == 4
        return (0.1, 0.9, 0.2, 0.8)


class InMemoryInputs:
    def __init__(self) -> None:
        self.load_calls = 0
        self.unchanged_calls = 0

    def load(self, run_id: str) -> EducationReevaluationInputs:
        self.load_calls += 1
        assert run_id == "education-test"
        return EducationReevaluationInputs(
            model=InMemoryModel(),
            test_rows=[
                {"Burnout_Risk_Level": "Low"},
                {"Burnout_Risk_Level": "High"},
                {"Burnout_Risk_Level": "Medium"},
                {"Burnout_Risk_Level": "High"},
            ],
            threshold=0.5,
            source_hashes={"metrics/education-test/metrics.json": "a" * 64},
            historical_metrics={
                "pr_auc": 1.0,
                "roc_auc": 1.0,
                "precision": 1.0,
                "recall": 1.0,
                "accuracy": 1.0,
                "top_risk_capture": 1.0,
                "workload_at_threshold": 0.5,
            },
        )

    def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None:
        self.unchanged_calls += 1
        assert run_id == "education-test"
        assert hashes == {"metrics/education-test/metrics.json": "a" * 64}


class FixedIdentity:
    def capture(self) -> dict[str, Any]:
        return {
            "git_head": "test-revision",
            "source_sha256": "b" * 64,
            "python": "3.13.0",
            "libraries": {"scikit-learn": "1", "pandas": "2", "numpy": "3"},
        }


def test_trust_gate_runs_before_loading_model_bytes() -> None:
    inputs = InMemoryInputs()

    with pytest.raises(ValueError, match="Explicitly trusted"):
        reevaluate_education(
            "education-test",
            input_loader=inputs,
            identity_provider=FixedIdentity(),
        )

    assert inputs.load_calls == 0


def test_reevaluation_uses_ports_and_rechecks_sources() -> None:
    inputs = InMemoryInputs()

    report = reevaluate_education(
        "education-test",
        input_loader=inputs,
        identity_provider=FixedIdentity(),
        trusted_model=True,
    )

    assert report["code"]["git_head"] == "test-revision"
    assert report["evaluation"]["diagnostics"]["count"] == 4
    assert report["source_hashes"] == {"metrics/education-test/metrics.json": "a" * 64}
    assert inputs.load_calls == 1
    assert inputs.unchanged_calls == 1


def test_application_modules_do_not_import_outward_adapters() -> None:
    pipelines = Path(__file__).parents[1] / "src/churn_ml/application/pipelines"
    reevaluation_source = (pipelines / "reevaluate_education.py").read_text(encoding="utf-8")
    reports_source = (pipelines / "experiment_reports.py").read_text(encoding="utf-8")

    for source in (reevaluation_source, reports_source):
        assert "churn_ml.infrastructure" not in source
        assert "import joblib" not in source

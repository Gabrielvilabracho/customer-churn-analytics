"""The publication use case orchestrates ports without storage or ML imports."""

import builtins
import runpy
from datetime import datetime
from typing import Any

import pytest
from churn_ml.application.pipelines import analyze_education
from churn_ml.application.ports.education_analysis import EducationAnalysisInputs


@pytest.mark.parametrize("failure", [None, "duplicate", "source-change", "engine"])
def test_application_orchestrates_in_memory_ports(
    monkeypatch: pytest.MonkeyPatch, failure: str | None
) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith(("churn_ml.infrastructure", "joblib", "sklearn", "pandas", "numpy")):
            raise AssertionError(f"Application imported an outward dependency: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    # Execute the module again so cached concrete modules cannot mask imports.
    use_case = runpy.run_path(analyze_education.__file__)["publish_education_analysis"]
    calls = []
    published = []
    inputs = EducationAnalysisInputs(
        model=object(),
        train_rows=[{"feature": "train"}],
        test_rows=[{"feature": "test"}],
        dataset_id="education-dataset",
        model_name="logistic",
        threshold=0.3,
        source_hashes={"verified-source": "hash"},
        model_metrics={"recall": 0.8},
        versions={"engine": "1"},
    )

    class InputLoader:
        def load(self, run_id: str) -> Any:
            calls.append(("load", run_id))
            return inputs

        def assert_unchanged(self, run_id: str, hashes: dict[str, str]) -> None:
            calls.append(("stable", run_id, hashes))
            if failure == "source-change":
                raise ValueError("Analysis source changed during computation")

    class Engine:
        def analyze(self, loaded: Any, **kwargs: Any) -> dict[str, Any]:
            assert loaded is inputs
            calls.append(("analyze", kwargs))
            if failure == "engine":
                raise ValueError("engine rejected input")
            return {"warnings": ["Preserved provenance warning"], "decision_support_only": True}

    class Publisher:
        def assert_available(self, run_id: str, analysis_id: str) -> None:
            calls.append(("available", run_id, analysis_id))
            if failure == "duplicate":
                raise ValueError("Analysis identity already exists; use a new analysis ID")

        def publish(self, payload: dict[str, Any]) -> None:
            calls.append(("publish",))
            published.append(payload.copy())

    def invoke() -> dict[str, Any]:
        return use_case(
            "education-test",
            "analysis-1",
            input_loader=InputLoader(),
            engine=Engine(),
            publisher=Publisher(),
            seed=7,
            shap_samples=8,
            permutation_samples=20,
            min_cohort_size=3,
        )

    if failure:
        message = {
            "duplicate": "already exists",
            "source-change": "source changed",
            "engine": "engine rejected",
        }[failure]
        with pytest.raises(ValueError, match=message):
            invoke()
        assert published == []
    else:
        result = invoke()
        assert published == [result]
        assert result == {
            "warnings": ["Preserved provenance warning"],
            "decision_support_only": True,
            "schema_version": 1,
            "run_id": "education-test",
            "analysis_id": "analysis-1",
            "dataset_id": inputs.dataset_id,
            "model_name": inputs.model_name,
            "source_hashes": inputs.source_hashes,
            "model_metrics": inputs.model_metrics,
            "versions": inputs.versions,
            "created_at_utc": result["created_at_utc"],
        }
        assert datetime.fromisoformat(result["created_at_utc"]).utcoffset().total_seconds() == 0
    expected = [("available", "education-test", "analysis-1")]
    if failure != "duplicate":
        expected += [
            ("load", "education-test"),
            ("analyze", {
                "seed": 7,
                "shap_samples": 8,
                "permutation_samples": 20,
                "min_cohort_size": 3,
            }),
        ]
        if failure != "engine":
            expected += [("stable", "education-test", inputs.source_hashes)]
    if failure is None:
        expected += [("publish",)]
    assert calls == expected


@pytest.mark.parametrize("run_id,analysis_id", [("../bad", "valid"), ("valid", "../bad")])
def test_invalid_identity_never_calls_ports(run_id: str, analysis_id: str) -> None:
    class UnusedPort:
        def __getattr__(self, name: str) -> Any:
            raise AssertionError(f"Invalid identity reached port: {name}")

    with pytest.raises(ValueError, match="identity"):
        analyze_education.publish_education_analysis(
            run_id,
            analysis_id,
            input_loader=UnusedPort(),
            engine=UnusedPort(),
            publisher=UnusedPort(),
        )

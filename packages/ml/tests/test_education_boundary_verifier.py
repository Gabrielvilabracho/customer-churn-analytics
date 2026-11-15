"""S1/S5: verified-byte adapter and inward-only orchestration regressions."""

import hashlib
import io
import subprocess
import sys
from pathlib import Path

import joblib
import pytest


def test_fresh_application_has_no_outward_imports():
    probe = """
import builtins
original = builtins.__import__
def guarded(name, *args, **kwargs):
    forbidden = ("churn_ml.infrastructure", "joblib", "sklearn", "pandas", "numpy")
    assert not name.startswith(forbidden), name
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from churn_ml.application.pipelines.analyze_education import publish_education_analysis
from churn_ml.application.ports.education_analysis import EducationAnalysisInputs
from types import SimpleNamespace as NS
calls = []
inputs = EducationAnalysisInputs(object(), [], [], "dataset", "model", .3, {}, {}, {})
loader = NS(load=lambda run: inputs, assert_unchanged=lambda *a: calls.append("stable"))
engine = NS(analyze=lambda *a, **k: {"warnings": ["retained"]})
publisher = NS(
    assert_available=lambda *a: calls.append("available"),
    publish=lambda p: calls.append("publish"),
)
result = publish_education_analysis(
    "run", "analysis", input_loader=loader, engine=engine, publisher=publisher,
)
assert result["warnings"] == ["retained"]
assert calls == ["available", "stable", "publish"]
"""
    source_root = Path(__file__).resolve().parents[1] / "src"
    probe = f"import sys\nsys.path.insert(0, {str(source_root)!r})\n" + probe
    result = subprocess.run([sys.executable, "-B", "-c", probe], capture_output=True, text=True)
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


@pytest.mark.parametrize("mutate", [False, True])
def test_verified_stream_once_and_stability_before_publish(education_source, monkeypatch, mutate):
    from churn_ml import education_analysis as cli
    from churn_ml.infrastructure.filesystem import education_analysis_adapters as adapter
    from churn_ml.infrastructure.sklearn import education_analysis_engine as engine

    events, expected = [], {}

    def hashes():
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in education_source.rglob("*")
            if p.is_file()
        }

    before = hashes()
    read, load, analyze = (
        adapter.read_education_sources,
        joblib.load,
        engine.analyze_education_model,
    )
    publish = adapter.EducationAnalysisStore.publish

    def reader(*args):
        events.append("read")
        return read(*args)

    def deserialize(stream):
        events.append("load")
        assert isinstance(stream, io.BytesIO)
        assert (
            stream.getvalue()
            == (education_source / "models/education-test/model.joblib").read_bytes()
        )
        return load(stream)

    def compute(*args, **kwargs):
        events.append("engine")
        payload = analyze(*args, **kwargs)
        if mutate:
            path = education_source / "processed/education-test/test.csv"
            path.write_bytes(path.read_bytes() + b"\n")
            expected.update(hashes())
        return payload

    def save(store, payload):
        events.append("publish")
        return publish(store, payload)

    monkeypatch.setattr(adapter, "read_education_sources", reader)
    monkeypatch.setattr(joblib, "load", deserialize)
    monkeypatch.setattr(engine, "analyze_education_model", compute)
    monkeypatch.setattr(adapter.EducationAnalysisStore, "publish", save)

    def invoke():
        return cli.publish_education_analysis(
            education_source, "education-test", "probe", shap_samples=8, permutation_samples=20
        )

    if mutate:
        with pytest.raises(ValueError, match="^Analysis source changed during computation$"):
            invoke()
        assert hashes() == expected
        assert not (education_source / "education").exists()
    else:
        invoke()
        assert all(hashes()[key] == value for key, value in before.items())
    assert events == ["read", "load", "engine", "read"] + ([] if mutate else ["publish"])

"""Preflight tests for FilesystemArtifactStore — reject unsafe/incomplete runs.

RED phase: these tests establish the validation contract. They must all pass
before the GREEN phase (production save logic) can be considered trusted.

Gate: ≤400 changed lines per PR; each test file counts toward the budget.
"""
from pathlib import Path

import pytest
from churn_ml.domain.artifacts import (
    ArtifactBundle,
    ArtifactManifest,
    ClassificationMetricSet,
    ThresholdSelection,
)
from churn_ml.infrastructure.filesystem.artifact_store import (
    _preflight_artifact_store,
    _validate_run_id,
)

# ---------------------------------------------------------------------------
# Helper: minimal valid bundle
# ---------------------------------------------------------------------------

def _make_bundle(run_id: str = "test-run-001") -> ArtifactBundle:
    manifest = ArtifactManifest(
        run_id=run_id,
        dataset_id="test-dataset",
        model_name="test-model",
        created_at_utc="2024-01-01T00:00:00Z",
    )
    metrics = ClassificationMetricSet(
        pr_auc=0.5, roc_auc=0.8, precision=0.7, recall=0.6, accuracy=0.75,
        top_risk_capture=0.4, workload_at_threshold=100.0,
    )
    threshold = ThresholdSelection(threshold=0.5, tradeoff="balance")
    prediction_samples = ({"customer_id": "C001", "risk_level": "high"},)
    return ArtifactBundle(
        manifest=manifest,
        metrics=metrics,
        threshold=threshold,
        prediction_samples=prediction_samples,
    )


def _write_metrics_json(root: Path, run_id: str) -> None:
    (root / "metrics" / run_id).mkdir(parents=True, exist_ok=True)
    (root / "metrics" / run_id / "metrics.json").write_text(
        '{"manifest": {}, "metrics": {}, "threshold": {}}', encoding="utf-8"
    )


def _write_models_json(root: Path, run_id: str, *, with_binary: bool) -> None:
    models_dir = root / "models" / run_id
    models_dir.mkdir(parents=True, exist_ok=True)
    (models_dir / "model_metadata.json").write_text(
        '{"model_binary_path": "model.joblib"}', encoding="utf-8"
    )
    if with_binary:
        (models_dir / "model.joblib").touch()


# ---------------------------------------------------------------------------
# B0 — _validate_run_id rejects invalid inputs
# ---------------------------------------------------------------------------

class TestValidateRunId:
    def test_valid_run_ids_pass(self):
        for valid in ["abc", "run_123", "my-run-id", "A1B2_C3"]:
            _validate_run_id(valid)  # should not raise

    def test_invalid_run_ids_raise(self):
        for invalid in ["", "has space", "path/with/slash", "\t tab"]:
            with pytest.raises(ValueError, match="Invalid run_id"):
                _validate_run_id(invalid)


# ---------------------------------------------------------------------------
# B1 — _preflight_artifact_store: clean state returns no warnings
# ---------------------------------------------------------------------------

class TestPreflightCleanState:
    """When the artifact directory structure is complete, preflight passes."""

    def test_no_warnings_when_all_artifacts_present(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "clean-run-001"
        _write_metrics_json(root, run_id)
        _write_models_json(root, run_id, with_binary=True)
        (root / "metrics" / run_id / "prediction_samples.csv").write_text(
            "customer_id,risk_level\nC001,high\n", encoding="utf-8"
        )

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert warnings == [], f"Expected no warnings, got: {warnings}"

    def test_warnings_when_metrics_json_missing(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "test-run-002"
        (root / "metrics" / run_id).mkdir(parents=True)
        # metrics.json intentionally missing

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert any("metrics.json" in w for w in warnings)

    def test_warnings_when_model_metadata_missing(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "test-run-003"
        _write_metrics_json(root, run_id)
        (root / "models" / run_id).mkdir(parents=True)
        # model_metadata.json intentionally missing

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert any("model_metadata.json" in w for w in warnings)

    def test_warnings_when_root_missing(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        # root doesn't exist at all

        warnings = _preflight_artifact_store(root, run_id="test-run-004")

        assert any("root" in w for w in warnings)

    def test_warnings_when_model_joblib_missing_but_metadata_set(
        self, tmp_path: Path
    ):
        """model_binary_path set but model.joblib missing should warn."""
        root = tmp_path / "artifacts"
        run_id = "test-run-005"
        _write_metrics_json(root, run_id)
        _write_models_json(root, run_id, with_binary=False)
        # model.joblib intentionally missing

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert any("model_binary_path" in w and "missing" in w for w in warnings)

    def test_invalid_metadata_json_is_warned(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "test-run-006"
        _write_metrics_json(root, run_id)
        (root / "models" / run_id).mkdir(parents=True)
        (root / "models" / run_id / "model_metadata.json").write_text(
            "{not valid json", encoding="utf-8"
        )

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert any("Invalid model_metadata.json" in w for w in warnings)


# ---------------------------------------------------------------------------
# B2 — _preflight_artifact_store: incomplete/unsafe runs produce warnings
# ---------------------------------------------------------------------------

class TestPreflightIncompleteRuns:
    """Preflight must detect and report incomplete or unsafe states."""

    def test_warnings_when_partial_structure(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "partial-001"
        (root / "metrics" / run_id).mkdir(parents=True)
        # Only metrics dir, nothing else

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert len(warnings) > 0
        # Should warn about missing models and metadata
        warning_text = " ".join(warnings)
        assert "Models directory missing" in warning_text

    def test_invalid_run_id_returns_warning_not_raise(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        (root).mkdir(parents=True)

        warnings = _preflight_artifact_store(root, run_id="")

        assert len(warnings) > 0
        assert "Invalid run_id" in warnings[0]

    def test_prediction_samples_warning_when_missing(self, tmp_path: Path):
        root = tmp_path / "artifacts"
        run_id = "no-samples-001"
        _write_metrics_json(root, run_id)
        _write_models_json(root, run_id, with_binary=True)
        # prediction_samples.csv missing

        warnings = _preflight_artifact_store(root, run_id=run_id)

        assert any("prediction_samples" in w for w in warnings)
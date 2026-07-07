import json
from pathlib import Path

import pytest
from churn_ml.domain.artifacts import (
    ArtifactBundle,
    ArtifactManifest,
    ClassificationMetricSet,
    CleanedSplitArtifact,
    ThresholdSelection,
)
from churn_ml.domain.customer import FeatureDictionary, FeatureSchemaError
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore
from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer

# ---------------------------------------------------------------------------
# Helpers shared by F3/F4 tests
# ---------------------------------------------------------------------------

def _minimal_bundle(run_id: str) -> ArtifactBundle:
    return ArtifactBundle(
        manifest=ArtifactManifest(
            run_id=run_id,
            dataset_id="telco-sample",
            model_name="baseline",
            created_at_utc="2026-07-02T00:00:00Z",
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.42,
            roc_auc=0.71,
            precision=0.5,
            recall=0.75,
            accuracy=0.81,
            top_risk_capture=0.67,
            workload_at_threshold=0.4,
        ),
        threshold=ThresholdSelection(threshold=0.35, tradeoff="test"),
        prediction_samples=(),
    )


def _minimal_split(run_id: str) -> CleanedSplitArtifact:
    return CleanedSplitArtifact(
        run_id=run_id,
        dataset_id="telco-sample",
        split_name="train",
        feature_columns=("tenure",),
        target_column="churn",
        rows=({"tenure": "1", "churn": "Yes"},),
    )


# ---------------------------------------------------------------------------
# F3 — run_id path-traversal guard
# ---------------------------------------------------------------------------

def test_artifact_store_save_bundle_rejects_traversal_run_id(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    with pytest.raises(ValueError, match="run_id"):
        store.save_bundle(_minimal_bundle("../../etc"))


def test_artifact_store_save_cleaned_split_rejects_traversal_run_id(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    with pytest.raises(ValueError, match="run_id"):
        store.save_cleaned_split(_minimal_split("../escape"))


@pytest.mark.parametrize("run_id", ["../../etc", "../x", "a/b", "", "run-001\n"])
def test_artifact_store_direct_methods_reject_traversal_run_id(
    tmp_path: Path, run_id: str
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    with pytest.raises(ValueError, match="run_id"):
        store.load_bundle(run_id)
    with pytest.raises(ValueError, match="run_id"):
        store.save_model_binary(object(), run_id=run_id)
    with pytest.raises(ValueError, match="run_id"):
        store.load_model_binary(run_id)
    with pytest.raises(ValueError, match="run_id"):
        store.load_cleaned_split(run_id, "train")


@pytest.mark.parametrize("split_name", ["../evil", "a/b", "", "train\n"])
def test_artifact_store_direct_methods_reject_traversal_split_name(
    tmp_path: Path, split_name: str
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    with pytest.raises(ValueError, match="split_name"):
        store.load_cleaned_split("run-001", split_name)


# ---------------------------------------------------------------------------
# F4 — save_bundle must not clobber model_binary_path
# ---------------------------------------------------------------------------

def test_save_bundle_after_save_model_binary_preserves_model_binary_path(
    tmp_path: Path,
) -> None:
    """save_model_binary then save_bundle must leave model_binary_path intact."""
    store = FilesystemArtifactStore(root=tmp_path)
    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id="run-f4")
    store.save_bundle(_minimal_bundle("run-f4"))

    metadata = json.loads(
        (tmp_path / "models" / "run-f4" / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata.get("model_binary_path") == "model.joblib"


# ---------------------------------------------------------------------------
# R2-F1 — split_name path-traversal guard
# ---------------------------------------------------------------------------


def test_save_cleaned_split_rejects_traversal_split_name(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    evil_split = CleanedSplitArtifact(
        run_id="run-001",
        dataset_id="telco-sample",
        split_name="../evil",
        feature_columns=("tenure",),
        target_column="churn",
        rows=({"tenure": "1", "churn": "Yes"},),
    )
    with pytest.raises(ValueError, match="split_name"):
        store.save_cleaned_split(evil_split)


def test_load_cleaned_split_rejects_traversal_split_name(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    with pytest.raises(ValueError, match="split_name"):
        store.load_cleaned_split("run-001", "../evil")


# ---------------------------------------------------------------------------
# R2-F2 — corrupt model_metadata.json must not block future saves
# ---------------------------------------------------------------------------


def test_save_bundle_recovers_from_corrupt_metadata(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    models_dir = tmp_path / "models" / "run-corrupt"
    models_dir.mkdir(parents=True)
    (models_dir / "model_metadata.json").write_text("{corrupt json!", encoding="utf-8")

    store.save_bundle(_minimal_bundle("run-corrupt"))

    metadata = json.loads(
        (models_dir / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert isinstance(metadata, dict)
    assert "run_id" in metadata


def test_save_model_binary_recovers_from_corrupt_metadata(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    models_dir = tmp_path / "models" / "run-corrupt2"
    models_dir.mkdir(parents=True)
    (models_dir / "model_metadata.json").write_text("not-json{{", encoding="utf-8")

    from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer

    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id="run-corrupt2")

    metadata = json.loads(
        (models_dir / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata.get("model_binary_path") == "model.joblib"


# ---------------------------------------------------------------------------
# R3-Fix1 — newline-terminated run_id / split_name must be rejected
# (covered by the parametrize additions above; no standalone test needed)

# ---------------------------------------------------------------------------
# R3-Fix2 — non-dict valid JSON in model_metadata.json must not crash saves
# ---------------------------------------------------------------------------


def test_save_bundle_after_corrupt_metadata_preserves_model_binary_path_when_file_exists(
    tmp_path: Path,
) -> None:
    """When metadata is corrupted between save_model_binary and save_bundle,
    save_bundle must restore model_binary_path if the .joblib file is on disk."""
    store = FilesystemArtifactStore(root=tmp_path)
    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id="run-c6")

    metadata_path = tmp_path / "models" / "run-c6" / "model_metadata.json"
    metadata_path.write_text("{corrupt json!", encoding="utf-8")

    store.save_bundle(_minimal_bundle("run-c6"))

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata.get("model_binary_path") == "model.joblib"


def test_save_bundle_and_save_model_binary_recover_from_null_metadata(
    tmp_path: Path,
) -> None:
    """model_metadata.json containing JSON `null` is valid JSON but not a dict.
    Both save_bundle and save_model_binary must survive and produce a valid dict."""
    store = FilesystemArtifactStore(root=tmp_path)
    models_dir = tmp_path / "models" / "run-null-meta"
    models_dir.mkdir(parents=True)
    (models_dir / "model_metadata.json").write_text("null", encoding="utf-8")

    # save_bundle must not raise AttributeError on metadata.update(...)
    store.save_bundle(_minimal_bundle("run-null-meta"))

    metadata_after_bundle = json.loads(
        (models_dir / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert isinstance(metadata_after_bundle, dict)
    assert "run_id" in metadata_after_bundle

    # Reset to null and verify save_model_binary also recovers
    (models_dir / "model_metadata.json").write_text("null", encoding="utf-8")
    from churn_ml.infrastructure.sklearn.baseline import BaselineChurnRateTrainer

    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )
    store.save_model_binary(model, run_id="run-null-meta")

    metadata_after_binary = json.loads(
        (models_dir / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert isinstance(metadata_after_binary, dict)
    assert metadata_after_binary.get("model_binary_path") == "model.joblib"


def test_feature_dictionary_rejects_missing_target_and_customer_key() -> None:
    rows = [{"monthly_charges": 72.5, "tenure": 1, "churn": "Yes"}]

    with pytest.raises(FeatureSchemaError, match="customer key"):
        FeatureDictionary.from_rows(
            rows,
            customer_key="customer_id",
            target_column="churn",
        )

    with pytest.raises(FeatureSchemaError, match="target column"):
        FeatureDictionary.from_rows(
            [{"customer_id": "C001", "monthly_charges": 72.5}],
            customer_key="customer_id",
            target_column="churn",
        )


def test_feature_dictionary_exports_business_feature_metadata() -> None:
    rows = [
        {"customer_id": "C001", "monthly_charges": 72.5, "tenure": 1, "churn": "Yes"},
        {"customer_id": "C002", "monthly_charges": 41.0, "tenure": 24, "churn": "No"},
    ]

    dictionary = FeatureDictionary.from_rows(
        rows,
        customer_key="customer_id",
        target_column="churn",
    )

    assert dictionary.customer_key == "customer_id"
    assert dictionary.target_column == "churn"
    assert [feature.name for feature in dictionary.features] == ["monthly_charges", "tenure"]
    assert [feature.semantic_role for feature in dictionary.features] == ["numeric", "numeric"]


def test_filesystem_artifact_store_round_trips_json_and_prediction_samples(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id="run-001",
            dataset_id="telco-sample",
            model_name="baseline",
            created_at_utc="2026-07-02T00:00:00Z",
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.42,
            roc_auc=0.71,
            precision=0.5,
            recall=0.75,
            accuracy=0.81,
            top_risk_capture=0.67,
            workload_at_threshold=0.4,
        ),
        threshold=ThresholdSelection(
            threshold=0.35,
            tradeoff="Prioritize churn recall for retention outreach.",
        ),
        prediction_samples=(
            {"customer_id": "C001", "churn_probability": "0.82", "actual_churn": "Yes"},
            {"customer_id": "C002", "churn_probability": "0.12", "actual_churn": "No"},
        ),
    )

    store.save_bundle(bundle)
    loaded = store.load_bundle("run-001")

    assert loaded.manifest.run_id == "run-001"
    assert loaded.metrics.recall == 0.75
    assert loaded.threshold.tradeoff == "Prioritize churn recall for retention outreach."
    assert loaded.prediction_samples[0]["customer_id"] == "C001"
    assert (tmp_path / "metrics" / "run-001" / "metrics.json").is_file()
    assert (tmp_path / "metrics" / "run-001" / "prediction_samples.csv").is_file()


def test_filesystem_artifact_store_round_trips_cleaned_split_csv_and_metadata_json(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    split = CleanedSplitArtifact(
        run_id="run-001",
        dataset_id="telco-sample",
        split_name="train",
        feature_columns=("monthly_charges", "tenure"),
        target_column="churn",
        rows=(
            {"customer_id": "C001", "monthly_charges": "72.5", "tenure": "1", "churn": "Yes"},
            {"customer_id": "C002", "monthly_charges": "41.0", "tenure": "24", "churn": "No"},
        ),
    )

    store.save_cleaned_split(split)
    loaded = store.load_cleaned_split("run-001", "train")

    assert loaded.run_id == "run-001"
    assert loaded.dataset_id == "telco-sample"
    assert loaded.split_name == "train"
    assert loaded.feature_columns == ("monthly_charges", "tenure")
    assert loaded.target_column == "churn"
    assert loaded.rows[0]["customer_id"] == "C001"
    assert (tmp_path / "processed" / "run-001" / "train.csv").is_file()
    assert (tmp_path / "processed" / "run-001" / "train.metadata.json").is_file()


def test_filesystem_artifact_store_persists_model_binary_under_models_dir(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id="run-001",
            dataset_id="telco-sample",
            model_name="baseline",
            created_at_utc="2026-07-02T00:00:00Z",
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.42,
            roc_auc=0.71,
            precision=0.5,
            recall=0.75,
            accuracy=0.81,
            top_risk_capture=0.67,
            workload_at_threshold=0.4,
        ),
        threshold=ThresholdSelection(threshold=0.35, tradeoff="test tradeoff"),
        prediction_samples=(
            {"customer_id": "C001", "churn_probability": "0.82", "actual_churn": "Yes"},
        ),
    )
    model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )

    store.save_bundle(bundle)
    store.save_model_binary(model, run_id="run-001")

    model_binary_path = tmp_path / "models" / "run-001" / "model.joblib"
    assert model_binary_path.is_file()

    metadata = json.loads(
        (tmp_path / "models" / "run-001" / "model_metadata.json").read_text(encoding="utf-8")
    )
    assert metadata.get("model_binary_path") == "model.joblib"


def test_filesystem_artifact_store_round_trips_model_binary(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)
    bundle = ArtifactBundle(
        manifest=ArtifactManifest(
            run_id="run-001",
            dataset_id="telco-sample",
            model_name="baseline",
            created_at_utc="2026-07-02T00:00:00Z",
        ),
        metrics=ClassificationMetricSet(
            pr_auc=0.42,
            roc_auc=0.71,
            precision=0.5,
            recall=0.75,
            accuracy=0.81,
            top_risk_capture=0.67,
            workload_at_threshold=0.4,
        ),
        threshold=ThresholdSelection(threshold=0.35, tradeoff="test tradeoff"),
        prediction_samples=(),
    )
    original_model = BaselineChurnRateTrainer().train(
        [{"churn": "Yes"}, {"churn": "No"}], target_column="churn"
    )

    store.save_bundle(bundle)
    store.save_model_binary(original_model, run_id="run-001")
    loaded_model = store.load_model_binary("run-001")

    assert hasattr(loaded_model, "predict_probabilities")
    original_probs = original_model.predict_probabilities([{"churn": "Yes"}])
    loaded_probs = loaded_model.predict_probabilities([{"churn": "Yes"}])
    assert original_probs == loaded_probs

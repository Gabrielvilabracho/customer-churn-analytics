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

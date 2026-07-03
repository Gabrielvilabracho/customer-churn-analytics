from pathlib import Path

import pytest
from churn_ml.application.pipelines.features import prepare_training_splits_from_csv
from churn_ml.application.pipelines.profile import DatasetProfileError
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


def test_real_telco_csv_loads_and_excludes_customer_id_from_model_features(
    tmp_path: Path,
) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    result = prepare_training_splits_from_csv(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="real-telco-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        test_fraction=0.25,
        seed=7,
    )

    assert result.feature_columns == ("gender", "SeniorCitizen", "tenure", "MonthlyCharges")
    assert "customerID" not in result.train_fit_metadata["feature_columns"]
    assert (tmp_path / "processed" / "real-telco-001" / "train.csv").is_file()
    assert (tmp_path / "processed" / "real-telco-001" / "test.csv").is_file()


def test_real_telco_csv_split_is_deterministic_and_stratified(tmp_path: Path) -> None:
    store = FilesystemArtifactStore(root=tmp_path)

    first = prepare_training_splits_from_csv(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="real-telco-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        test_fraction=0.25,
        seed=11,
    )
    second = prepare_training_splits_from_csv(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=store,
        run_id="real-telco-002",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        test_fraction=0.25,
        seed=11,
    )

    assert [row["customerID"] for row in first.train_rows] == [
        row["customerID"] for row in second.train_rows
    ]
    assert {row["Churn"] for row in first.train_rows} == {"No", "Yes"}
    assert {row["Churn"] for row in first.test_rows} == {"No", "Yes"}


def test_real_telco_csv_fit_metadata_uses_training_rows_only(tmp_path: Path) -> None:
    result = prepare_training_splits_from_csv(
        FIXTURE_DIR / "telco_churn_sample.csv",
        artifact_store=FilesystemArtifactStore(root=tmp_path),
        run_id="real-telco-001",
        dataset_id="telco-sample",
        customer_key="customerID",
        target_column="Churn",
        test_fraction=0.25,
        seed=11,
    )

    assert result.train_fit_metadata["categorical_levels"]["gender"] == ("Female", "Male")
    assert "Nonbinary" not in result.train_fit_metadata["categorical_levels"]["gender"]


def test_missing_target_schema_error_writes_no_artifacts(tmp_path: Path) -> None:
    source = FIXTURE_DIR / "telco_churn_missing_target.csv"

    with pytest.raises(DatasetProfileError, match="missing required target column: Churn"):
        prepare_training_splits_from_csv(
            source,
            artifact_store=FilesystemArtifactStore(root=tmp_path),
            run_id="invalid-schema",
            dataset_id="telco-sample",
            customer_key="customerID",
            target_column="Churn",
            test_fraction=0.25,
            seed=7,
        )

    assert list(tmp_path.iterdir()) == []

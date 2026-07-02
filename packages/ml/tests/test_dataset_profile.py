import pytest
from churn_ml.application.pipelines.profile import DatasetProfileError, screen_dataset_profile


def test_profile_blocks_missing_target_values() -> None:
    rows = [
        {"customer_id": "C001", "monthly_charges": 72.5, "churn": "Yes"},
        {"customer_id": "C002", "monthly_charges": 41.0, "churn": ""},
    ]

    with pytest.raises(DatasetProfileError, match="missing target"):
        screen_dataset_profile(rows, target_column="churn")


def test_profile_blocks_duplicate_rows() -> None:
    rows = [
        {"customer_id": "C001", "monthly_charges": 72.5, "churn": "Yes"},
        {"customer_id": "C001", "monthly_charges": 72.5, "churn": "Yes"},
    ]

    with pytest.raises(DatasetProfileError, match="duplicate rows"):
        screen_dataset_profile(rows, target_column="churn")


def test_profile_blocks_leakage_columns() -> None:
    rows = [
        {
            "customer_id": "C001",
            "monthly_charges": 72.5,
            "churn": "Yes",
            "churn_date": "2024-01-01",
        },
        {"customer_id": "C002", "monthly_charges": 41.0, "churn": "No", "churn_date": ""},
    ]

    with pytest.raises(DatasetProfileError, match="target leakage"):
        screen_dataset_profile(rows, target_column="churn")


def test_profile_blocks_identifier_only_columns() -> None:
    rows = [
        {"customer_id": "C001", "monthly_charges": 72.5, "tenure": 1, "churn": "Yes"},
        {"customer_id": "C002", "monthly_charges": 41.0, "tenure": 24, "churn": "No"},
    ]

    with pytest.raises(DatasetProfileError, match="identifier-only"):
        screen_dataset_profile(rows, target_column="churn")


def test_profile_marks_modeling_ready_with_limitations() -> None:
    rows = [
        {"monthly_charges": 72.5, "tenure": 1, "churn": "Yes"},
        {"monthly_charges": 41.0, "tenure": 24, "churn": "No"},
    ]

    result = screen_dataset_profile(rows, target_column="churn")

    assert result.modeling_ready is True
    assert result.row_count == 2
    assert result.identifier_only_columns == ()
    assert "Small local validation sample" in result.limitations

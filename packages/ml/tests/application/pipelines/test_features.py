"""Integration tests for features pipeline — leakage column threading."""

from pathlib import Path

from churn_ml.application.pipelines.features import (
    build_feature_dictionary,
    prepare_training_splits_from_csv,
)
from churn_ml.domain.customer import LEAKAGE_COLUMNS
from churn_ml.infrastructure.filesystem.artifact_store import FilesystemArtifactStore

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"


class TestFeaturesLeakageThreading:
    """1.9-1.10: build_feature_dictionary and prepare_training_splits_from_csv
    thread excluded_feature_columns through to from_rows."""

    def test_build_feature_dictionary_excludes_leakage_by_default(self) -> None:
        """build_feature_dictionary must exclude Post_Semester_GPA and
        Skill_Retention_Score from the resulting FeatureDictionary without
        the caller passing excluded_feature_columns explicitly."""
        import csv

        rows = list(
            csv.DictReader(
                (FIXTURE_DIR / "education_sample.csv").open(newline="", encoding="utf-8")
            )
        )

        dictionary = build_feature_dictionary(
            rows,
            customer_key="Student_ID",
            target_column="Burnout_Risk_Level",
        )

        feature_names = {f.name for f in dictionary.features}
        assert "Post_Semester_GPA" not in feature_names
        assert "Skill_Retention_Score" not in feature_names
        assert len(feature_names) == 12, (
            f"Expected 12 features; got {len(feature_names)}: {sorted(feature_names)}"
        )

    def test_prepare_training_splits_excludes_leakage_by_default(
        self, tmp_path: Path
    ) -> None:
        """prepare_training_splits_from_csv must exclude leakage columns
        from the feature output without the caller passing exclusion
        arguments explicitly (defense-in-depth check)."""
        store = FilesystemArtifactStore(root=tmp_path)

        result = prepare_training_splits_from_csv(
            FIXTURE_DIR / "education_sample.csv",
            artifact_store=store,
            run_id="leakage-001",
            dataset_id="education-sample",
            customer_key="Student_ID",
            target_column="Burnout_Risk_Level",
            test_fraction=0.25,
            seed=7,
        )

        assert "Post_Semester_GPA" not in result.feature_columns
        assert "Skill_Retention_Score" not in result.feature_columns
        assert len(result.feature_columns) == 12, (
            f"Expected 12 features; got {len(result.feature_columns)}: "
            f"{result.feature_columns}"
        )

    def test_build_feature_dictionary_imports_leakage_from_domain(self) -> None:
        """build_feature_dictionary's default excluded_feature_columns must be
        imported from domain/customer.py, not redefined locally."""
        import inspect

        from churn_ml.application.pipelines.features import build_feature_dictionary

        sig = inspect.signature(build_feature_dictionary)
        params = sig.parameters
        assert "excluded_feature_columns" in params, (
            "build_feature_dictionary must accept excluded_feature_columns"
        )
        default = params["excluded_feature_columns"].default
        assert default is LEAKAGE_COLUMNS, (
            f"Default must be domain.customer.LEAKAGE_COLUMNS; got {default!r}"
        )

    def test_prepare_training_splits_imports_leakage_from_domain(self) -> None:
        """prepare_training_splits_from_csv's default must come from
        domain/customer.py."""
        import inspect

        from churn_ml.application.pipelines.features import prepare_training_splits_from_csv

        sig = inspect.signature(prepare_training_splits_from_csv)
        params = sig.parameters
        assert "excluded_feature_columns" in params, (
            "prepare_training_splits_from_csv must accept excluded_feature_columns"
        )
        default = params["excluded_feature_columns"].default
        assert default is LEAKAGE_COLUMNS, (
            f"Default must be domain.customer.LEAKAGE_COLUMNS; got {default!r}"
        )

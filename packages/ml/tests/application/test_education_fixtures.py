"""Tests for education dataset fixtures (ai-student-impact-analytics)."""

import csv
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class TestEducationFixtures:
    """Phase 0: Education fixture validation before ML domain re-point."""

    def test_education_sample_csv_loads_16_column_schema_with_required_fields(self) -> None:
        """education_sample.csv must have the full 16-col education schema,
        with Student_ID as key and Burnout_Risk_Level as target."""
        csv_path = FIXTURE_DIR / "education_sample.csv"
        assert csv_path.is_file(), f"Missing fixture: {csv_path}"

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) >= 4, (
            f"Need at least 4 rows for train/test split; got {len(rows)}"
        )
        columns = set(rows[0].keys())
        assert len(columns) == 16, (
            f"Expected 16 education columns; got {len(columns)}: {sorted(columns)}"
        )
        assert "Student_ID" in columns, "Missing customer key: Student_ID"
        assert "Burnout_Risk_Level" in columns, "Missing target: Burnout_Risk_Level"

    def test_education_sample_has_both_target_classes_with_minimum_rows(self) -> None:
        """Both Burnout_Risk_Level classes must have >= 2 rows for a
        stratified train/test split."""
        csv_path = FIXTURE_DIR / "education_sample.csv"
        rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

        from collections import Counter

        class_counts = Counter(row["Burnout_Risk_Level"] for row in rows)
        assert "High" in class_counts, "Missing positive class 'High'"
        assert class_counts["High"] >= 2, (
            f"Need >= 2 High rows for stratified split; got {class_counts['High']}"
        )
        assert ("Medium" in class_counts) or ("Low" in class_counts), (
            "Missing negative class (Medium or Low)"
        )
        negative_total = class_counts.get("Medium", 0) + class_counts.get("Low", 0)
        assert negative_total >= 2, (
            f"Need >= 2 negative rows for stratified split; got {negative_total}"
        )

    def test_education_sample_includes_leakage_columns_for_exclusion_tests(self) -> None:
        """education_sample.csv must include Post_Semester_GPA and
        Skill_Retention_Score so Phase 1 leakage-exclusion tests have
        real columns to exclude."""
        csv_path = FIXTURE_DIR / "education_sample.csv"
        rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

        columns = set(rows[0].keys())
        assert "Post_Semester_GPA" in columns, (
            "Fixture must include Post_Semester_GPA for leakage-exclusion tests"
        )
        assert "Skill_Retention_Score" in columns, (
            "Fixture must include Skill_Retention_Score for leakage-exclusion tests"
        )

    def test_education_missing_target_csv_exists(self) -> None:
        """education_missing_target.csv must exist for negative-path tests."""
        csv_path = FIXTURE_DIR / "education_missing_target.csv"
        assert csv_path.is_file(), f"Missing fixture: {csv_path}"

    def test_education_missing_target_csv_has_no_burnout_risk_level_column(self) -> None:
        """education_missing_target.csv must NOT contain Burnout_Risk_Level
        so schema-screening can test the missing-target error path."""
        csv_path = FIXTURE_DIR / "education_missing_target.csv"
        rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

        columns = set(rows[0].keys())
        assert "Burnout_Risk_Level" not in columns, (
            "education_missing_target.csv must omit Burnout_Risk_Level for negative tests"
        )
        assert "Student_ID" in columns, (
            "education_missing_target.csv must have Student_ID for schema integrity"
        )

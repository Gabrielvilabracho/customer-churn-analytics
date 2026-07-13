"""Unit tests for domain customer — leakage column exclusion."""

import csv
from pathlib import Path

from churn_ml.domain.customer import LEAKAGE_COLUMNS, FeatureDictionary

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures"


class TestLeakageExclusion:
    """1.5-1.8: FeatureDictionary.from_rows excludes leakage columns by default."""

    def test_from_rows_excludes_leakage_columns_by_default(self) -> None:
        """A caller that omits excluded_feature_columns must still get
        Post_Semester_GPA and Skill_Retention_Score excluded."""
        csv_path = FIXTURE_DIR / "education_sample.csv"
        rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

        dictionary = FeatureDictionary.from_rows(
            rows,
            customer_key="Student_ID",
            target_column="Burnout_Risk_Level",
        )

        feature_names = {f.name for f in dictionary.features}
        assert "Post_Semester_GPA" not in feature_names, (
            "Post_Semester_GPA must be excluded from features by default"
        )
        assert "Skill_Retention_Score" not in feature_names, (
            "Skill_Retention_Score must be excluded from features by default"
        )
        # Verify the remaining education columns ARE present
        assert "Major_Category" in feature_names
        assert "Weekly_GenAI_Hours" in feature_names
        assert "Perceived_AI_Dependency" in feature_names
        assert "Institutional_Policy" in feature_names
        assert len(feature_names) == 12, (
            f"Expected 12 features (16 cols - Student_ID - Burnout_Risk_Level "
            f"- 2 leakage); got {len(feature_names)}: {sorted(feature_names)}"
        )

    def test_leakage_columns_constant_is_frozenset(self) -> None:
        """LEAKAGE_COLUMNS must be a frozenset with the two education leakage cols."""
        assert isinstance(LEAKAGE_COLUMNS, frozenset)
        assert LEAKAGE_COLUMNS == frozenset({"Post_Semester_GPA", "Skill_Retention_Score"})

    def test_from_rows_caller_can_still_pass_explicit_exclusions(self) -> None:
        """A caller passing a custom excluded_feature_columns must still work
        (regression guard — 1.6 does not remove caller flexibility)."""
        csv_path = FIXTURE_DIR / "education_sample.csv"
        rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8")))

        # Exclude additional columns beyond the default leakage set
        dictionary = FeatureDictionary.from_rows(
            rows,
            customer_key="Student_ID",
            target_column="Burnout_Risk_Level",
            excluded_feature_columns=frozenset(
                {"Post_Semester_GPA", "Skill_Retention_Score", "Anxiety_Level_During_Exams"}
            ),
        )

        feature_names = {f.name for f in dictionary.features}
        assert "Post_Semester_GPA" not in feature_names
        assert "Skill_Retention_Score" not in feature_names
        assert "Anxiety_Level_During_Exams" not in feature_names
        assert len(feature_names) == 11, (
            f"Expected 11 features with extra exclusion; got {len(feature_names)}"
        )

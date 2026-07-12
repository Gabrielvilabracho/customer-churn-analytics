"""Tests for __main__.py CLI education defaults."""

class TestMainEducationDefaults:
    """1.13-1.14: __main__.py education CLI defaults."""

    def test_default_feature_columns_is_education_schema(self) -> None:
        """_DEFAULT_FEATURE_COLUMNS must contain education columns only,
        excluding leakage (Post_Semester_GPA, Skill_Retention_Score)."""
        import churn_ml.__main__ as cli_module

        columns = cli_module._DEFAULT_FEATURE_COLUMNS
        assert isinstance(columns, tuple)
        assert len(columns) > 0

        # Must NOT include leakage columns
        assert "Post_Semester_GPA" not in columns
        assert "Skill_Retention_Score" not in columns

        # Must include education feature columns
        assert "Major_Category" in columns
        assert "Year_of_Study" in columns
        assert "Pre_Semester_GPA" in columns
        assert "Weekly_GenAI_Hours" in columns

        # Must NOT include Telco columns
        assert "gender" not in columns
        assert "Contract" not in columns
        assert "tenure" not in columns

    def test_customer_key_default_is_student_id(self) -> None:
        """--customer-key must default to Student_ID (not customerID)."""
        import churn_ml.__main__ as cli_module

        assert hasattr(cli_module, "_CUSTOMER_KEY_DEFAULT"), (
            "_CUSTOMER_KEY_DEFAULT module constant is required"
        )
        assert cli_module._CUSTOMER_KEY_DEFAULT == "Student_ID", (
            f"Expected 'Student_ID'; got '{cli_module._CUSTOMER_KEY_DEFAULT}'"
        )

    def test_target_column_default_is_burnout_risk_level(self) -> None:
        """--target-column must default to Burnout_Risk_Level (not Churn)."""
        import churn_ml.__main__ as cli_module

        assert hasattr(cli_module, "_TARGET_COLUMN_DEFAULT"), (
            "_TARGET_COLUMN_DEFAULT module constant is required"
        )
        assert cli_module._TARGET_COLUMN_DEFAULT == "Burnout_Risk_Level", (
            f"Expected 'Burnout_Risk_Level'; got '{cli_module._TARGET_COLUMN_DEFAULT}'"
        )

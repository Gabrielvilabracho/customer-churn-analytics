"""Tests for run_training.py — education cohort fields and leakage re-export."""

from churn_ml.application.pipelines.run_training import (
    PREDICTION_SAMPLE_COHORT_FIELDS,
)


class TestRunTrainingDefaults:
    """1.11-1.12: run_training.py education defaults."""

    def test_prediction_sample_cohort_fields_is_education_4_tuple(self) -> None:
        """PREDICTION_SAMPLE_COHORT_FIELDS must be the education 4-tuple."""
        expected = (
            "Major_Category",
            "Weekly_GenAI_Hours",
            "Perceived_AI_Dependency",
            "Institutional_Policy",
        )
        assert PREDICTION_SAMPLE_COHORT_FIELDS == expected, (
            f"Expected {expected}; got {PREDICTION_SAMPLE_COHORT_FIELDS}"
        )

    def test_leakage_columns_is_imported_not_redefined(self) -> None:
        """LEAKAGE_COLUMNS in run_training.py must be imported from
        domain/customer.py, not redefined locally."""
        import ast
        from pathlib import Path

        src = Path(__file__).resolve().parents[3] / (
            "src/churn_ml/application/pipelines/run_training.py"
        )
        tree = ast.parse(src.read_text(encoding="utf-8"))

        # Check that LEAKAGE_COLUMNS is imported from domain.customer
        leakage_assigned = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "churn_ml.domain.customer":
                    for alias in node.names:
                        if alias.name == "LEAKAGE_COLUMNS":
                            leakage_assigned = True
            # Check for local re-definition pattern
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "LEAKAGE_COLUMNS":
                        # An assignment to LEAKAGE_COLUMNS at module level would
                        # be a redefinition — flag it.
                        raise AssertionError(
                            "LEAKAGE_COLUMNS must be imported from domain.customer.py, "
                            "not redefined in run_training.py"
                        )

        assert leakage_assigned, (
            "LEAKAGE_COLUMNS must be imported from churn_ml.domain.customer"
        )

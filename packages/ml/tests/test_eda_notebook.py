"""Structural and execution regression coverage for the education EDA notebook."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
NOTEBOOK_PATH = REPOSITORY_ROOT / "notebooks" / "EDA.ipynb"
CSV_ENVIRONMENT_VARIABLE = "AI_STUDENT_IMPACT_CSV"
EXPECTED_COLUMNS = (
    "Student_ID",
    "Major_Category",
    "Year_of_Study",
    "Pre_Semester_GPA",
    "Weekly_GenAI_Hours",
    "Primary_Use_Case",
    "Prompt_Engineering_Skill",
    "Tool_Diversity",
    "Paid_Subscription",
    "Traditional_Study_Hours",
    "Perceived_AI_Dependency",
    "Institutional_Policy",
    "Anxiety_Level_During_Exams",
    "Post_Semester_GPA",
    "Skill_Retention_Score",
    "Burnout_Risk_Level",
)
ACADEMIC_CATEGORIES = ("Arts", "Humanities", "Medical", "Business", "STEM")


def _notebook_code(notebook: dict[str, Any]) -> str:
    return "\n".join(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def _execute_in_order(notebook: dict[str, Any]) -> dict[str, Any]:
    namespace: dict[str, Any] = {}
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        exec(compile(source, f"EDA.ipynb:cell-{index}", "exec"), namespace)
    return namespace


def _assert_no_prohibited_behavior(code: str) -> None:
    tree = ast.parse(code)
    banned_imports = {
        "joblib",
        "kaggle",
        "lightgbm",
        "pickle",
        "requests",
        "sklearn",
        "subprocess",
        "tensorflow",
        "torch",
        "urllib",
        "xgboost",
    }
    banned_calls = {
        "download",
        "dump",
        "fit",
        "fit_transform",
        "load_model",
        "partial_fit",
        "predict",
        "predict_proba",
        "read_joblib",
        "read_pickle",
        "savefig",
        "system",
        "to_csv",
        "to_json",
        "to_parquet",
        "to_pickle",
        "train",
        "urlopen",
        "urlretrieve",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert node.module is None or node.module.split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else None
            name = node.func.id if isinstance(node.func, ast.Name) else name
            assert name not in banned_calls, f"Prohibited notebook call: {name}"


def test_education_eda_is_clean_reproducible_and_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    all_source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    code = _notebook_code(notebook)

    assert "AI Student Impact Exploratory Data Analysis" in all_source
    assert "customer churn" not in all_source.lower()
    for required_text in (
        CSV_ENVIRONMENT_VARIABLE,
        "Burnout_Risk_Level",
        "Pre_Semester_GPA",
        "Post_Semester_GPA",
        "synthetic",
        "non-causal",
    ):
        assert required_text.lower() in all_source.lower()
    assert all(
        cell.get("execution_count") is None and cell.get("outputs") == []
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    assert not any(line.lstrip().startswith(("%", "!")) for line in code.splitlines())
    _assert_no_prohibited_behavior(code)

    assert not tmp_path.resolve().is_relative_to(REPOSITORY_ROOT.resolve())
    monkeypatch.chdir(tmp_path)
    missing_csv = tmp_path / "missing.csv"
    monkeypatch.setenv(CSV_ENVIRONMENT_VARIABLE, str(missing_csv))
    with pytest.raises(FileNotFoundError, match=CSV_ENVIRONMENT_VARIABLE):
        _execute_in_order(notebook)

    fixture_path = tmp_path / "synthetic-ai-student-impact.csv"
    rows = [
        (1001, "Arts", "Freshman", 3.10, 4.0, "Research", "Beginner", 1, False,
         14.0, 1, "Allowed", 3, 3.20, 88.0, "Low"),
        (1002, "Humanities", "Sophomore", 2.80, 8.0, "Drafting", "Intermediate", 2,
         True, 12.0, 2, "Allowed_With_Citation", 5, 2.75, 79.0, "Medium"),
        (1003, "Medical", "Junior", 3.60, 2.0, "Ideation", "Advanced", 4, True,
         18.0, 1, "Restricted", 4, 3.70, 91.0, "Low"),
        (1004, "Business", "Senior", 2.40, 16.0, "Research", "Intermediate", 3, False,
         8.0, 4, "Allowed_With_Citation", 8, 2.25, 68.0, "High"),
        (1005, "STEM", "Junior", 3.00, 12.0, "Code_Generation", "Advanced", 5, True,
         10.0, 3, "Restricted", 7, 2.90, 73.0, "High"),
    ]
    with fixture_path.open("w", newline="", encoding="utf-8") as fixture_file:
        writer = csv.writer(fixture_file)
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)

    monkeypatch.setenv(CSV_ENVIRONMENT_VARIABLE, str(fixture_path))
    artifact_roots = (
        REPOSITORY_ROOT / "artifacts" / "education",
        REPOSITORY_ROOT / "data" / "02-preprocessed",
        REPOSITORY_ROOT / "data" / "03-features",
        REPOSITORY_ROOT / "data" / "04-predictions",
        REPOSITORY_ROOT / "notebooks" / ".ipynb_checkpoints",
    )
    before = {path: path.exists() for path in artifact_roots}
    namespace = _execute_in_order(notebook)
    after = {path: path.exists() for path in artifact_roots}

    assert before == after
    assert namespace["dataset_shape"] == (5, 16)
    assert namespace["dataset_identity"]["sha256"] == hashlib.sha256(
        fixture_path.read_bytes()
    ).hexdigest()
    assert namespace["duplicate_row_count"] == 0
    assert set(namespace["target_distribution"].index) == {"High", "Low", "Medium"}
    assert set(namespace["academic_category_summary"].index) == set(ACADEMIC_CATEGORIES)
    assert namespace["gpa_difference_summary"]["count"] == 5
    assert not namespace["numeric_summary"].empty
    assert not namespace["categorical_summary"].empty
    assert not namespace["numeric_correlations"].empty
    assert namespace["target_associations"]
    assert "Student_ID" not in namespace["numeric_columns"]
    assert "Student_ID" not in namespace["categorical_columns"]
    assert "Student_ID" not in namespace["numeric_summary"].index
    assert "Student_ID" not in namespace["categorical_summary"].index
    assert "Student_ID" not in namespace["numeric_correlations"].index
    assert "Student_ID" not in namespace["numeric_correlations"].columns
    assert "Student_ID" not in namespace["target_numeric_associations"].index
    assert "Student_ID" not in namespace["target_associations"]

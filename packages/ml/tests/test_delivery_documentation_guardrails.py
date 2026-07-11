from pathlib import Path

from scripts.delivery_guardrails import check_documentation_guardrails


def test_documentation_guardrails_mark_shortcuts_non_compliant(
    project_root: Path,
) -> None:
    result = check_documentation_guardrails(project_root)

    assert result.passed is True
    assert result.details == {
        "review_path": "documented",
        "architecture_trace": "documented",
        "artifact_contracts": "documented",
        "no_fabricated_analytics": "documented",
        "shortcut_policy": "documented",
    }


def test_documentation_guardrails_reject_negative_shortcut_fixture(
    tmp_path: Path,
    write_required_docs,
) -> None:
    write_required_docs(tmp_path, include_shortcut_policy=False)

    result = check_documentation_guardrails(tmp_path)

    assert result.passed is False
    assert result.details["shortcut_policy"] == "missing"


def test_documentation_guardrails_report_missing_docs_without_traceback(
    tmp_path: Path,
) -> None:
    result = check_documentation_guardrails(tmp_path)

    assert result.passed is False
    assert result.details == {
        "documents": "missing: README.md, docs/architecture.md, docs/api-contract.md"
    }

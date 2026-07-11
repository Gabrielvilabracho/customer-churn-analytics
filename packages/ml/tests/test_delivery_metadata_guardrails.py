from scripts.delivery_guardrails import check_pr_metadata


def test_pr_metadata_requires_issue_link_and_type_marker() -> None:
    valid = check_pr_metadata(
        title="Add delivery guardrail metadata enforcement",
        body=(
            "## Summary\n"
            "Adds safe PR metadata checks.\n\n"
            "Issue: https://github.com/example/churn-analytics/issues/42\n"
            "Type: bugfix\n"
        ),
    )

    assert valid.passed is True
    assert valid.details == {
        "title": "present",
        "issue_link": "present",
        "type_metadata": "present",
    }


def test_pr_metadata_accepts_label_marker_as_type_metadata() -> None:
    result = check_pr_metadata(
        title="Document chained PR strategy",
        body="Closes #108\n\nLabels: type:documentation, area:delivery\n",
    )

    assert result.passed is True
    assert result.details["issue_link"] == "present"
    assert result.details["type_metadata"] == "present"


def test_pr_metadata_blocks_empty_title_missing_issue_and_missing_type() -> None:
    result = check_pr_metadata(
        title=" ",
        body="This body has prose but no tracker link and no type marker.",
    )

    assert result.passed is False
    assert result.details == {
        "title": "missing",
        "issue_link": "missing",
        "type_metadata": "missing",
    }

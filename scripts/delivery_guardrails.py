from __future__ import annotations

# ruff: noqa: E402
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.delivery_guardrails_lib.cli import main
from scripts.delivery_guardrails_lib.documentation import check_documentation_guardrails
from scripts.delivery_guardrails_lib.metadata import (
    ISSUE_LINK_PATTERN,
    TYPE_METADATA_PATTERN,
    check_environment_pr_metadata,
    check_pr_metadata,
)
from scripts.delivery_guardrails_lib.result import GuardrailResult
from scripts.delivery_guardrails_lib.review_budget import (
    REVIEW_LINE_BUDGET,
    check_current_review_budget,
    check_pr_changed_line_budget,
)
from scripts.delivery_guardrails_lib.workflow import (
    PR_BASE_REF_EXPRESSION,
    PR_BODY_EXPRESSION,
    PR_TITLE_EXPRESSION,
    check_pull_request_workflow,
)

__all__ = [
    "GuardrailResult",
    "ISSUE_LINK_PATTERN",
    "PR_BASE_REF_EXPRESSION",
    "PR_BODY_EXPRESSION",
    "PR_TITLE_EXPRESSION",
    "REVIEW_LINE_BUDGET",
    "TYPE_METADATA_PATTERN",
    "check_current_review_budget",
    "check_documentation_guardrails",
    "check_environment_pr_metadata",
    "check_pr_changed_line_budget",
    "check_pr_metadata",
    "check_pull_request_workflow",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import os
import re

from scripts.delivery_guardrails_lib.result import GuardrailResult

ISSUE_LINK_PATTERN = re.compile(
    r"(?im)(https://[^\s]+/(?:issues|pull)/\d+|\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#\d+)"
)
TYPE_METADATA_PATTERN = re.compile(r"(?im)^\s*(?:type\s*:\s*\S+|labels?\s*:\s*.*\btype:)")


def check_pr_metadata(*, title: str, body: str) -> GuardrailResult:
    has_title = bool(title.strip())
    has_issue_link = bool(ISSUE_LINK_PATTERN.search(body))
    has_type_metadata = bool(TYPE_METADATA_PATTERN.search(body))
    return GuardrailResult(
        has_title and has_issue_link and has_type_metadata,
        {
            "title": "present" if has_title else "missing",
            "issue_link": "present" if has_issue_link else "missing",
            "type_metadata": "present" if has_type_metadata else "missing",
        },
    )


def check_environment_pr_metadata(environ: os._Environ[str] | dict[str, str]) -> GuardrailResult:
    return check_pr_metadata(title=environ.get("PR_TITLE", ""), body=environ.get("PR_BODY", ""))

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

from scripts.delivery_guardrails_lib.documentation import check_documentation_guardrails
from scripts.delivery_guardrails_lib.metadata import check_environment_pr_metadata
from scripts.delivery_guardrails_lib.result import GuardrailResult
from scripts.delivery_guardrails_lib.review_budget import (
    REVIEW_LINE_BUDGET,
    check_current_review_budget,
)
from scripts.delivery_guardrails_lib.workflow import check_pull_request_workflow

CHECK_NAMES = ("all", "pr-metadata", "pr-workflow", "review-budget", "documentation")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    requested_checks = _requested_checks(args.check)
    root = _resolve_root(args.root, requested_checks)
    if root is None:
        return 1

    checks = _run_checks(
        requested_checks,
        root=root,
        base_ref=args.base_ref,
        budget=args.budget,
    )
    for name, check in checks.items():
        print(f"{'PASS' if check.passed else 'FAIL'} {name}: {check.details}")
    return 0 if all(check.passed for check in checks.values()) else 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run delivery guardrail checks.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--budget", type=int, default=REVIEW_LINE_BUDGET)
    parser.add_argument("--base-ref", default=None)
    parser.add_argument("--check", action="append", choices=CHECK_NAMES, default=None)
    return parser.parse_args(argv)


def _requested_checks(checks: list[str] | None) -> set[str]:
    requested_checks = set(checks or ["all"])
    if "all" in requested_checks:
        return {"pr-workflow", "review-budget", "documentation"}
    return requested_checks


def _resolve_root(root: Path, requested_checks: set[str]) -> Path | None:
    if not requested_checks & {"pr-workflow", "review-budget", "documentation"}:
        return root
    resolved = root.resolve()
    if resolved.is_dir():
        return resolved
    print(f"FAIL root: {{'root': 'missing', 'path': '{resolved}'}}")
    return None


def _run_checks(
    requested_checks: set[str],
    *,
    root: Path,
    base_ref: str | None,
    budget: int,
) -> dict[str, GuardrailResult]:
    checks: dict[str, GuardrailResult] = {}
    if "pr-metadata" in requested_checks:
        checks["pr_metadata"] = check_environment_pr_metadata(os.environ)
    if "pr-workflow" in requested_checks:
        checks["pr_workflow"] = check_pull_request_workflow(
            root / ".github" / "workflows" / "ci.yml"
        )
    if "review-budget" in requested_checks:
        checks["review_budget"] = check_current_review_budget(
            root, base_ref=base_ref, budget=budget
        )
    if "documentation" in requested_checks:
        checks["documentation"] = check_documentation_guardrails(root)
    return checks

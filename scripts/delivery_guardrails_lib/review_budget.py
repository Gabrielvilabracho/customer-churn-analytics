from __future__ import annotations

import subprocess
from pathlib import Path

from scripts.delivery_guardrails_lib.result import GuardrailResult

REVIEW_LINE_BUDGET = 400


def check_pr_changed_line_budget(
    numstat_output: str,
    *,
    budget: int = REVIEW_LINE_BUDGET,
) -> GuardrailResult:
    changed_lines, skipped_rows, malformed_rows = _parse_numstat(numstat_output)
    passed = changed_lines <= budget and malformed_rows == 0
    details = {"changed_lines": str(changed_lines), "budget": str(budget)}
    if skipped_rows:
        details["skipped_rows"] = str(skipped_rows)
    if malformed_rows:
        details["malformed_rows"] = str(malformed_rows)
    if not passed:
        details["required_action"] = "split work-unit PR or record size exception"
    return GuardrailResult(passed, details)


def current_numstat(project_root: Path, *, base_ref: str | None = None) -> str:
    command = ["git", "diff", "--numstat"]
    if base_ref:
        command.append(f"{base_ref}...HEAD")
    try:
        unstaged_numstat = subprocess.check_output(
            command, cwd=project_root, text=True, stderr=subprocess.STDOUT
        )
        if base_ref:
            return unstaged_numstat
        staged_numstat = subprocess.check_output(
            ["git", "diff", "--cached", "--numstat"],
            cwd=project_root,
            text=True,
            stderr=subprocess.STDOUT,
        )
        return staged_numstat + unstaged_numstat + untracked_numstat(project_root)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.output.strip() or "git diff failed") from exc


def untracked_numstat(project_root: Path) -> str:
    output = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=project_root,
        text=True,
        stderr=subprocess.STDOUT,
    )
    return "".join(
        _untracked_row(project_root, relative_path) for relative_path in output.splitlines()
    )


def check_current_review_budget(
    project_root: Path,
    *,
    base_ref: str | None,
    budget: int,
) -> GuardrailResult:
    try:
        return check_pr_changed_line_budget(
            current_numstat(project_root, base_ref=base_ref), budget=budget
        )
    except RuntimeError as exc:
        return GuardrailResult(False, {"git_diff": "failed", "error": str(exc)})


def _parse_numstat(numstat_output: str) -> tuple[int, int, int]:
    changed_lines = 0
    skipped_rows = 0
    malformed_rows = 0
    for line in numstat_output.splitlines():
        row = _parse_numstat_row(line)
        changed_lines += row[0]
        skipped_rows += row[1]
        malformed_rows += row[2]
    return changed_lines, skipped_rows, malformed_rows


def _parse_numstat_row(line: str) -> tuple[int, int, int]:
    fields = line.split("\t")
    if len(fields) < 3:
        return 0, 0, 1
    if fields[0] == "-" or fields[1] == "-":
        return 0, 1, 0
    try:
        return int(fields[0]) + int(fields[1]), 0, 0
    except ValueError:
        return 0, 0, 1


def _untracked_row(project_root: Path, relative_path: str) -> str:
    path = project_root / relative_path
    try:
        additions = len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return f"-\t-\t{relative_path}\n"
    return f"{additions}\t0\t{relative_path}\n"

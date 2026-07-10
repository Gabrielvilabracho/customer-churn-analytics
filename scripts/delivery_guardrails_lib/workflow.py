from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from scripts.delivery_guardrails_lib.result import GuardrailResult

PR_TITLE_EXPRESSION = "${{ github.event.pull_request.title }}"
PR_BODY_EXPRESSION = "${{ github.event.pull_request.body }}"
PR_BASE_REF_EXPRESSION = "${{ github.base_ref }}"
REQUIRED_JOBS = frozenset({"pr-validation", "python", "web", "web-e2e"})


def active_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


def has_active_marker(lines: Sequence[str], marker: str) -> bool:
    return any(marker in line for line in lines)


def indent_width(line: str) -> int:
    return len(line) - len(line.lstrip())


def is_disabled_if(line: str) -> bool:
    return line.strip() in {"if: false", "if: ${{ false }}"}


def required_job_blocks(lines: Sequence[str]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current_job: str | None = None
    current_block: list[str] = []
    for line in lines:
        stripped = line.strip()
        if indent_width(line) == 2 and stripped.endswith(":"):
            if current_job is not None:
                blocks[current_job] = current_block
            candidate_job = stripped[:-1]
            current_job = candidate_job if candidate_job in REQUIRED_JOBS else None
            current_block = [line] if current_job is not None else []
            continue
        if current_job is not None:
            current_block.append(line)
    if current_job is not None:
        blocks[current_job] = current_block
    return blocks


def step_with_marker_has_disabled_if(block: Sequence[str], marker: str) -> bool:
    current_step: list[str] = []
    for line in block[1:]:
        if indent_width(line) == 6 and line.lstrip().startswith("- "):
            if _step_matches_disabled_marker(current_step, marker):
                return True
            current_step = [line]
        elif current_step:
            current_step.append(line)
    return _step_matches_disabled_marker(current_step, marker)


def disabled_required_checks(lines: Sequence[str]) -> list[str]:
    disabled: list[str] = []
    for job, block in required_job_blocks(lines).items():
        if _job_has_disabled_if(job, block):
            disabled.append(job)
        if job == "pr-validation" and step_with_marker_has_disabled_if(
            block, "python scripts/delivery_guardrails.py"
        ):
            disabled.append("delivery_guardrails_cli")
    return disabled


def metadata_validation_is_disabled(lines: Sequence[str]) -> bool:
    pr_validation_block = required_job_blocks(lines).get("pr-validation", [])
    return step_with_marker_has_disabled_if(pr_validation_block, "Validate PR metadata")


def safe_pr_metadata_validation(lines: Sequence[str]) -> tuple[bool, bool]:
    active_text = "\n".join(lines)
    unsafe_expression_lines = [
        line
        for line in lines
        if (PR_TITLE_EXPRESSION in line or PR_BODY_EXPRESSION in line)
        and not line.lstrip().startswith(("PR_TITLE:", "PR_BODY:"))
    ]
    has_safe_env = all(
        marker in active_text
        for marker in (
            "PR_TITLE:",
            "PR_BODY:",
            PR_TITLE_EXPRESSION,
            PR_BODY_EXPRESSION,
            "--check pr-metadata",
        )
    )
    return has_safe_env, bool(unsafe_expression_lines)


def check_pull_request_workflow(workflow_path: Path) -> GuardrailResult:
    if not workflow_path.exists():
        return GuardrailResult(False, {"workflow": "missing"})

    lines = active_lines(workflow_path.read_text(encoding="utf-8"))
    state = _workflow_state(lines)
    passed = all(
        (
            state["has_pull_request"],
            state["has_pr_validation_job"],
            state["has_metadata"],
            not state["has_unsafe_metadata"],
            not state["has_disabled_metadata"],
            state["has_guardrail_cli"],
            not state["missing_jobs"],
            not state["disabled_checks"],
        )
    )
    details = _workflow_details(state)
    return GuardrailResult(passed, details)


def _step_matches_disabled_marker(step: Sequence[str], marker: str) -> bool:
    return marker in "\n".join(step) and any(is_disabled_if(line) for line in step)


def _job_has_disabled_if(job: str, block: Sequence[str]) -> bool:
    direct_job_if_disabled = any(
        indent_width(line) == 4 and is_disabled_if(line) for line in block[1:]
    )
    any_disabled_if = any(is_disabled_if(line) for line in block[1:])
    return direct_job_if_disabled or (job in {"python", "web", "web-e2e"} and any_disabled_if)


def _workflow_state(lines: Sequence[str]) -> dict[str, object]:
    has_metadata, has_unsafe_metadata = safe_pr_metadata_validation(lines)
    return {
        "has_pull_request": has_active_marker(lines, "pull_request:"),
        "has_pr_validation_job": has_active_marker(lines, "pr-validation:"),
        "has_metadata": has_metadata,
        "has_unsafe_metadata": has_unsafe_metadata,
        "has_disabled_metadata": metadata_validation_is_disabled(lines),
        "has_guardrail_cli": _has_guardrail_cli(lines),
        "missing_jobs": _missing_runtime_jobs(lines),
        "disabled_checks": disabled_required_checks(lines),
    }


def _has_guardrail_cli(lines: Sequence[str]) -> bool:
    return (
        has_active_marker(lines, "python scripts/delivery_guardrails.py")
        and has_active_marker(lines, "--base-ref")
        and has_active_marker(lines, PR_BASE_REF_EXPRESSION)
    )


def _missing_runtime_jobs(lines: Sequence[str]) -> list[str]:
    job_markers = {
        "ml": ("python:", "packages/ml/tests"),
        "api": ("python:", "apps/api/tests"),
        "web": ("web:", "apps/web test", "apps/web typecheck"),
        "e2e": ("web-e2e:", "apps/web test:e2e"),
    }
    return [
        job
        for job, markers in job_markers.items()
        if not all(has_active_marker(lines, marker) for marker in markers)
    ]


def _workflow_details(state: dict[str, object]) -> dict[str, str]:
    details = {
        "pull_request_trigger": "present" if state["has_pull_request"] else "missing",
        "metadata_validation": _metadata_status(state),
        "delivery_guardrails_cli": "present" if state["has_guardrail_cli"] else "missing",
        "runtime_checks": "ml,api,web,e2e"
        if not state["missing_jobs"]
        else ",".join(state["missing_jobs"]),
    }
    if state["disabled_checks"]:
        details["disabled_checks"] = ",".join(state["disabled_checks"])
    return details


def _metadata_status(state: dict[str, object]) -> str:
    if state["has_disabled_metadata"]:
        return "disabled"
    if state["has_metadata"]:
        return "safe_env"
    if state["has_unsafe_metadata"]:
        return "unsafe"
    return "missing"

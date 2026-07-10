from pathlib import Path

import pytest

from scripts.delivery_guardrails import check_pull_request_workflow


def test_pull_request_workflow_runs_metadata_and_runtime_jobs(project_root: Path) -> None:
    result = check_pull_request_workflow(project_root / ".github" / "workflows" / "ci.yml")

    assert result.passed is True
    assert result.details == {
        "pull_request_trigger": "present",
        "metadata_validation": "safe_env",
        "delivery_guardrails_cli": "present",
        "runtime_checks": "ml,api,web,e2e",
    }


def test_ci_workflow_runs_delivery_guardrail_cli_as_executable_gate(
    project_root: Path,
) -> None:
    workflow = (project_root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "python scripts/delivery_guardrails.py" in workflow
    assert "--base-ref" in workflow
    assert "--check pr-metadata" in workflow
    assert "PR_TITLE: ${{ github.event.pull_request.title }}" in workflow
    assert "PR_BODY: ${{ github.event.pull_request.body }}" in workflow
    assert 'test -n "$PR_TITLE"' not in workflow
    assert 'test -n "$PR_BODY"' not in workflow
    assert 'test -n "${{ github.event.pull_request.title }}"' not in workflow
    assert 'test -n "${{ github.event.pull_request.body }}"' not in workflow


def test_workflow_guardrail_rejects_commented_or_unsafe_markers(tmp_path: Path) -> None:
    workflow_path = tmp_path / "ci.yml"
    workflow_path.write_text(
        "name: CI\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  pr-validation:\n"
        "    steps:\n"
        "      # run: python scripts/delivery_guardrails.py --base-ref origin/main\n"
        "      - name: Unsafe metadata interpolation\n"
        "        run: test -n \"${{ github.event.pull_request.title }}\"\n"
        "  python:\n"
        "    steps:\n"
        "      - run: pytest packages/ml/tests\n"
        "  web:\n"
        "    steps:\n"
        "      - run: pnpm --dir apps/web test && pnpm --dir apps/web typecheck\n"
        "  web-e2e:\n"
        "    steps:\n"
        "      - run: pnpm --dir apps/web test:e2e\n",
        encoding="utf-8",
    )

    result = check_pull_request_workflow(workflow_path)

    assert result.passed is False
    assert result.details["metadata_validation"] == "unsafe"
    assert result.details["delivery_guardrails_cli"] == "missing"


def test_workflow_guardrail_rejects_env_plus_direct_shell_interpolation(
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "ci.yml"
    workflow_path.write_text(
        "name: CI\n"
        "on:\n"
        "  pull_request:\n"
        "jobs:\n"
        "  pr-validation:\n"
        "    steps:\n"
        "      - name: Unsafe despite env\n"
        "        env:\n"
        "          PR_TITLE: ${{ github.event.pull_request.title }}\n"
        "          PR_BODY: ${{ github.event.pull_request.body }}\n"
        "        run: test -n \"${{ github.event.pull_request.title }}\"\n"
        "      - run: python scripts/delivery_guardrails.py "
        "--base-ref origin/${{ github.base_ref }}\n"
        "  python:\n"
        "    steps:\n"
        "      - run: pytest packages/ml/tests apps/api/tests\n"
        "  web:\n"
        "    steps:\n"
        "      - run: pnpm --dir apps/web test && pnpm --dir apps/web typecheck\n"
        "  web-e2e:\n"
        "    steps:\n"
        "      - run: pnpm --dir apps/web test:e2e\n",
        encoding="utf-8",
    )

    result = check_pull_request_workflow(workflow_path)

    assert result.passed is False
    assert result.details["metadata_validation"] == "unsafe"


@pytest.mark.parametrize(
    ("disabled_line", "expected_disabled_check"),
    [
        ("  pr-validation:\n    if: false\n", "pr-validation"),
        ("  python:\n    if: ${{ false }}\n", "python"),
        ("  web:\n    if: false\n", "web"),
        ("  web-e2e:\n    if: ${{ false }}\n", "web-e2e"),
    ],
)
def test_workflow_guardrail_rejects_disabled_required_jobs(
    tmp_path: Path,
    project_root: Path,
    disabled_line: str,
    expected_disabled_check: str,
) -> None:
    workflow_path = tmp_path / "ci.yml"
    workflow = (project_root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    job_name = disabled_line.split(":", maxsplit=1)[0].strip()
    workflow_path.write_text(
        workflow.replace(f"  {job_name}:\n", disabled_line),
        encoding="utf-8",
    )

    result = check_pull_request_workflow(workflow_path)

    assert result.passed is False
    assert result.details["disabled_checks"] == expected_disabled_check


@pytest.mark.parametrize("disabled_if", ["if: false", "if: ${{ false }}"])
def test_workflow_guardrail_rejects_disabled_metadata_validation_step(
    tmp_path: Path,
    project_root: Path,
    disabled_if: str,
) -> None:
    workflow_path = tmp_path / "ci.yml"
    workflow = (project_root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    workflow_path.write_text(
        workflow.replace(
            "      - name: Validate PR metadata\n"
            "        if: github.event_name == 'pull_request'\n"
            "        env:",
            "      - name: Validate PR metadata\n"
            f"        {disabled_if}\n"
            "        env:",
            1,
        ),
        encoding="utf-8",
    )

    result = check_pull_request_workflow(workflow_path)

    assert result.passed is False
    assert result.details["metadata_validation"] == "disabled"


@pytest.mark.parametrize("disabled_if", ["if: false", "if: ${{ false }}"])
def test_workflow_guardrail_rejects_disabled_delivery_guardrail_step(
    tmp_path: Path,
    project_root: Path,
    disabled_if: str,
) -> None:
    workflow_path = tmp_path / "ci.yml"
    workflow = (project_root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    workflow_path.write_text(
        workflow.replace(
            "      - name: Run delivery guardrails\n"
            "        if: github.event_name == 'pull_request'\n"
            "        run: python scripts/delivery_guardrails.py",
            "      - name: Run delivery guardrails\n"
            f"        {disabled_if}\n"
            "        run: python scripts/delivery_guardrails.py",
            1,
        ),
        encoding="utf-8",
    )

    result = check_pull_request_workflow(workflow_path)

    assert result.passed is False
    assert result.details["disabled_checks"] == "delivery_guardrails_cli"

from pathlib import Path

import pytest

from scripts.delivery_guardrails import main


def test_cli_reports_named_statuses_and_partial_failures_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    git_cmd,
    write_required_docs,
) -> None:
    git_cmd(tmp_path, "init")
    git_cmd(tmp_path, "config", "user.email", "reviewer@example.com")
    git_cmd(tmp_path, "config", "user.name", "Reviewer")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git_cmd(tmp_path, "add", "README.md")
    git_cmd(tmp_path, "commit", "-m", "base")
    write_required_docs(tmp_path)
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "docs")

    status = main(["--root", str(tmp_path), "--base-ref", "HEAD~1", "--budget", "1"])
    output = capsys.readouterr().out

    assert status == 1
    assert "FAIL pr_workflow" in output
    assert "FAIL review_budget" in output
    assert "PASS documentation" in output
    assert "Traceback" not in output


def test_cli_reports_missing_root_as_named_failure_without_traceback(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_root = tmp_path / "does-not-exist"

    status = main(["--root", str(missing_root), "--budget", "400"])
    output = capsys.readouterr().out

    assert status == 1
    assert "FAIL root" in output
    assert "missing" in output
    assert str(missing_root) in output
    assert "Traceback" not in output


def test_cli_runs_pr_metadata_and_documentation_when_both_checks_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("PR_TITLE", "Document delivery guardrails")
    monkeypatch.setenv("PR_BODY", "Fixes #123\n\nType: chore")

    status = main(
        [
            "--root",
            str(tmp_path),
            "--check",
            "pr-metadata",
            "--check",
            "documentation",
        ]
    )
    output = capsys.readouterr().out

    assert status == 1
    assert "PASS pr_metadata" in output
    assert "FAIL documentation" in output

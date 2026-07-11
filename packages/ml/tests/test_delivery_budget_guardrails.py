from pathlib import Path

from scripts.delivery_guardrails import (
    REVIEW_LINE_BUDGET,
    check_pr_changed_line_budget,
)
from scripts.delivery_guardrails_lib.review_budget import current_numstat


def test_review_budget_allows_small_slices_and_blocks_oversized_slices() -> None:
    small_slice = "120\t10\tREADME.md\n80\t30\tdocs/architecture.md\n"
    oversized_slice = "250\t20\tREADME.md\n150\t5\tdocs/architecture.md\n"

    assert check_pr_changed_line_budget(small_slice, budget=400).passed is True

    blocked = check_pr_changed_line_budget(oversized_slice, budget=400)
    assert blocked.passed is False
    assert blocked.details == {
        "changed_lines": "425",
        "budget": "400",
        "required_action": "split work-unit PR or record size exception",
    }


def test_review_budget_boundary_cases_and_malformed_numstat_rows() -> None:
    exact_budget = "399\t1\texact.md\n"
    one_over = "400\t1\tover.md\n"
    binary_and_rename = "-\t-\timage.png\n10\t5\told.md => new.md\n"
    malformed = "abc\t1\tbroken.md\n1\tmissing-path\n"

    assert check_pr_changed_line_budget(exact_budget, budget=400).passed is True

    over_result = check_pr_changed_line_budget(one_over, budget=400)
    assert over_result.passed is False
    assert over_result.details["changed_lines"] == "401"

    binary_result = check_pr_changed_line_budget(binary_and_rename, budget=400)
    assert binary_result.passed is True
    assert binary_result.details == {
        "changed_lines": "15",
        "budget": "400",
        "skipped_rows": "1",
    }

    malformed_result = check_pr_changed_line_budget(malformed, budget=400)
    assert malformed_result.passed is False
    assert malformed_result.details["malformed_rows"] == "2"


def test_review_budget_uses_named_policy_constant() -> None:
    result = check_pr_changed_line_budget("399\t2\tover.md\n")

    assert REVIEW_LINE_BUDGET == 400
    assert result.passed is False
    assert result.details["budget"] == "400"


def test_current_numstat_uses_base_ref_for_clean_branch_diff(
    tmp_path: Path,
    git_cmd,
) -> None:
    git_cmd(tmp_path, "init")
    git_cmd(tmp_path, "config", "user.email", "reviewer@example.com")
    git_cmd(tmp_path, "config", "user.name", "Reviewer")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git_cmd(tmp_path, "add", "README.md")
    git_cmd(tmp_path, "commit", "-m", "base")
    (tmp_path / "README.md").write_text("base\nchanged\n", encoding="utf-8")
    git_cmd(tmp_path, "add", "README.md")
    git_cmd(tmp_path, "commit", "-m", "change")

    assert git_cmd(tmp_path, "diff", "--numstat") == ""
    assert current_numstat(tmp_path, base_ref="HEAD~1") == "1\t0\tREADME.md\n"


def test_current_numstat_includes_untracked_files_for_local_guardrail(
    tmp_path: Path,
    git_cmd,
) -> None:
    git_cmd(tmp_path, "init")
    git_cmd(tmp_path, "config", "user.email", "reviewer@example.com")
    git_cmd(tmp_path, "config", "user.name", "Reviewer")
    (tmp_path / "README.md").write_text("base\n", encoding="utf-8")
    git_cmd(tmp_path, "add", "README.md")
    git_cmd(tmp_path, "commit", "-m", "base")
    (tmp_path / "notes.md").write_text("one\ntwo\n", encoding="utf-8")

    assert current_numstat(tmp_path, base_ref=None) == "2\t0\tnotes.md\n"


def test_current_numstat_includes_staged_unstaged_and_untracked_local_changes(
    tmp_path: Path,
    git_cmd,
) -> None:
    git_cmd(tmp_path, "init")
    git_cmd(tmp_path, "config", "user.email", "reviewer@example.com")
    git_cmd(tmp_path, "config", "user.name", "Reviewer")
    (tmp_path / "staged.md").write_text("base\n", encoding="utf-8")
    (tmp_path / "unstaged.md").write_text("base\n", encoding="utf-8")
    git_cmd(tmp_path, "add", ".")
    git_cmd(tmp_path, "commit", "-m", "base")

    (tmp_path / "staged.md").write_text("base\nstaged\n", encoding="utf-8")
    git_cmd(tmp_path, "add", "staged.md")
    (tmp_path / "unstaged.md").write_text("base\nunstaged\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("one\ntwo\n", encoding="utf-8")

    assert current_numstat(tmp_path, base_ref=None) == (
        "1\t0\tstaged.md\n"
        "1\t0\tunstaged.md\n"
        "2\t0\tnotes.md\n"
    )

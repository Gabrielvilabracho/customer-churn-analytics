"""A nested review runtime must not inherit the commit's index selection."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parents[3] / "entrypoint/review-bin/opencode"


@pytest.mark.parametrize("isolated", [False, True])
def test_foreign_snapshot_cannot_replace_the_commit_index(tmp_path: Path, isolated: bool) -> None:
    env = {"PATH": os.environ["PATH"], "HOME": str(tmp_path), "GIT_OPTIONAL_LOCKS": "0"}
    for name in subprocess.check_output(["git", "rev-parse", "--local-env-vars"]).decode().split():
        env.pop(name, None)
    repo, foreign = tmp_path / "repo", tmp_path / "snapshot.git"
    subprocess.run(["git", "init", "-q", str(repo)], env=env, check=True)
    subprocess.run(["git", "init", "-q", "--bare", str(foreign)], env=env, check=True)
    (repo / "staged.txt").write_text("Original staged content\n")
    subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], env=env, check=True)
    (repo / "not-staged.txt").write_text("Must remain unstaged\n")
    index = repo / ".git/index"
    before = index.read_bytes()
    record = tmp_path / "arguments.json"
    fake = tmp_path / "fake-opencode"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json, os, subprocess, sys\n"
        "subprocess.run(['git', '--git-dir=' + os.environ['TEST_SNAPSHOT'], "
        "'--work-tree=' + os.environ['TEST_REPO'], 'add', '--all'], check=True)\n"
        "with open(os.environ['TEST_RECORD'], 'w') as stream:\n"
        " json.dump({'arguments': sys.argv[1:], 'input': sys.stdin.read(), "
        "'sentinel': os.environ['TEST_SENTINEL']}, stream)\n"
        "print('STATUS: PASSED')\n"
    )
    fake.chmod(0o755)
    env.update(
        GIT_DIR=str(repo / ".git"),
        GIT_WORK_TREE=str(repo),
        GIT_INDEX_FILE=str(index),
        GGA_OPENCODE_BINARY=str(fake),
        TEST_SNAPSHOT=str(foreign),
        TEST_REPO=str(repo),
        TEST_RECORD=str(record),
        TEST_SENTINEL="preserved",
    )
    command = [str(WRAPPER)] if isolated else [str(fake)]
    result = subprocess.run(
        [*command, "run", "--model", "openai/gpt-6.1-sol", "--agent", "plan"],
        cwd=repo,
        env=env,
        text=True,
        input="Review the staged content only",
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "STATUS: PASSED\n"
    assert (index.read_bytes() == before) is isolated
    assert json.loads(record.read_text()) == {
        "arguments": ["run", "--model", "openai/gpt-6.1-sol", "--agent", "plan"],
        "input": "Review the staged content only",
        "sentinel": "preserved",
    }
    assert (repo / "staged.txt").read_text() == "Original staged content\n"
    assert (repo / "not-staged.txt").read_text() == "Must remain unstaged\n"

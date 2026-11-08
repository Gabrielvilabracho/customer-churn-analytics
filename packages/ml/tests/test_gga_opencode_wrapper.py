"""A nested review runtime must not inherit the commit's index selection."""

import json
import os
import signal
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
        "if '--format' in sys.argv:\n"
        " for kind, part in [('step_start', {'type': 'step-start'}), "
        "('text', {'id': 'p', 'type': 'text', 'text': 'STATUS: PASSED\\n'}), "
        "('step_finish', {'type': 'step-finish', 'reason': 'stop'})]:\n"
        "  part.update(messageID='m', sessionID='s')\n"
        "  print(json.dumps({'type': kind, 'sessionID': 's', 'part': part}))\n"
        "else: print('STATUS: PASSED')\n"
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
        "arguments": [
            "run",
            *(["--format", "json"] if isolated else []),
            "--model",
            "openai/gpt-6.1-sol",
            "--agent",
            "plan",
        ],
        "input": "Review the staged content only",
        "sentinel": "preserved",
    }
    assert (repo / "staged.txt").read_text() == "Original staged content\n"
    assert (repo / "not-staged.txt").read_text() == "Must remain unstaged\n"


@pytest.fixture
def runtime(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    fake = tmp_path / "runtime"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys, time\n"
        "with open(os.environ['TEST_RECORD'], 'w') as stream:\n"
        " json.dump({'pid': os.getpid(), 'args': sys.argv[1:], "
        "'input': sys.stdin.read()}, stream)\n"
        "if os.environ.get('TEST_WAIT'): time.sleep(30)\n"
        "if os.environ.get('TEST_BAD_STREAM'):\n"
        " print('malformed stream'); sys.exit(0)\n"
        "if sys.argv[1:4] == ['run', '--format', 'json']:\n"
        " for kind, part in [('step_start', {'type': 'step-start'}), "
        "*[('tool_use', {'output': 'STATUS: PASSED'})] * 110, "
        "('text', {'id': 'p', 'type': 'text', 'text': 'STATUS: PASSED\\nApproved.\\n'}), "
        "('step_finish', {'type': 'step-finish', 'reason': 'stop'})]:\n"
        "  part.update(messageID='m', sessionID='s')\n"
        "  print(json.dumps({'type': kind, 'sessionID': 's', 'part': part}))\n"
        "else: print('tool trace\\n' * 110 + 'STATUS: PASSED')\n"
        "sys.exit(int(os.environ.get('TEST_EXIT', '0')))\n"
    )
    fake.chmod(0o755)
    return tmp_path / "record.json", {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path),
        "GGA_OPENCODE_BINARY": str(fake),
        "TEST_RECORD": str(tmp_path / "record.json"),
    }


def test_activity_does_not_hide_final_answer(runtime: tuple[Path, dict[str, str]]) -> None:
    record, env = runtime
    result = subprocess.run(
        [str(WRAPPER), "run"], env=env, input="review", text=True, capture_output=True
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "STATUS: PASSED\nApproved.\n",
        "",
    )
    assert json.loads(record.read_text())["args"] == ["run", "--format", "json"]


@pytest.mark.parametrize(
    "args",
    [
        ["run", "--format", "default"],
        ["run", "--format=json"],
        ["models"],
        ["--help"],
    ],
)
def test_explicit_format_and_other_commands_pass_through(
    runtime: tuple[Path, dict[str, str]],
    args: list[str],
) -> None:
    record, env = runtime
    result = subprocess.run(
        [str(WRAPPER), *args], env=env, input="prompt", text=True, capture_output=True
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "tool trace\n" * 110 + "STATUS: PASSED\n",
        "",
    )
    assert json.loads(record.read_text())["args"] == args
    assert json.loads(record.read_text())["input"] == "prompt"


def test_format_after_delimiter_is_prompt(runtime: tuple[Path, dict[str, str]]) -> None:
    record, env = runtime
    result = subprocess.run(
        [str(WRAPPER), "run", "--", "--format=json"], env=env, text=True, capture_output=True
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "STATUS: PASSED\nApproved.\n",
        "",
    )
    assert json.loads(record.read_text())["args"] == [
        "run",
        "--format",
        "json",
        "--",
        "--format=json",
    ]


def test_runtime_nonzero_exit_is_preserved(runtime: tuple[Path, dict[str, str]]) -> None:
    _, env = runtime
    result = subprocess.run(
        [str(WRAPPER), "run"], env={**env, "TEST_EXIT": "17"}, text=True, capture_output=True
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        17,
        "STATUS: PASSED\nApproved.\n",
        "",
    )


def test_decoder_rejection_blocks_zero_exit_runtime(
    runtime: tuple[Path, dict[str, str]],
) -> None:
    _, env = runtime
    result = subprocess.run(
        [str(WRAPPER), "run"], env={**env, "TEST_BAD_STREAM": "1"}, text=True, capture_output=True
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "STATUS: FAILED\nReview output transport error: invalid event stream\n",
        "",
    )


def test_runtime_retains_pid_and_signal_target(runtime: tuple[Path, dict[str, str]]) -> None:
    import time

    record, env = runtime
    with subprocess.Popen(
        [str(WRAPPER), "run"],
        env={**env, "TEST_WAIT": "1"},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        try:
            deadline = time.monotonic() + 5
            while not record.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            assert record.exists()
            assert json.loads(record.read_text())["pid"] == process.pid
        finally:
            process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == -signal.SIGTERM
        assert stdout == "STATUS: FAILED\nReview output transport error: incomplete answer\n"
        assert stderr == ""

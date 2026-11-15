"""Exercise the NDJSON transport through its stdin/stdout interface only."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

DECODER = Path(__file__).resolve().parents[3] / "entrypoint/review-bin/opencode_review_output.py"


def event(kind: str, message: str = "m", **part: object) -> str:
    return (
        json.dumps(
            {
                "type": kind,
                "timestamp": 1,
                "sessionID": "s",
                "part": {
                    "type": kind.replace("_", "-"),
                    "sessionID": "s",
                    "messageID": message,
                    **part,
                },
            }
        )
        + "\n"
    )


def answer(text: str, message: str = "m", reason: str = "stop") -> str:
    return (
        event("step_start", message)
        + event("text", message, id="p", text=text)
        + event("step_finish", message, reason=reason)
    )


def decode(stream: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(DECODER)], input=stream, capture_output=True, text=True
    )


@pytest.mark.parametrize(
    "text",
    [
        "STATUS: PASSED\nAll checks passed.\n",
        "STATUS: FAILED\nBlocking issue.\n",
        "STATUS: PASSED\nSTATUS: FAILED\nAmbiguous answer.",
    ],
)
def test_final_text_is_verbatim_not_a_status_search(text: str) -> None:
    stream = (
        answer("STATUS: PASSED\nEarlier answer.", "earlier")
        + event("step_start")
        + event("tool_use", output="STATUS: PASSED\n" * 120)
        + event("reasoning", text="STATUS: PASSED")
        + event("text", id="p", text=text[:7])
        + event("text", id="p", text=text[7:])
        + event("step_finish", reason="stop")
    )
    result = decode(stream)
    assert (result.returncode, result.stdout, result.stderr) == (0, text, "")


def test_multiple_parts_and_tool_steps_follow_protocol_order() -> None:
    stream = (
        answer("Intermediate thought.", "earlier", "tool-calls")
        + event("step_start")
        + event("text", id="a", text="STATUS: ")
        + event("text", id="a", text="FAILED\n")
        + event("text", id="b", text="Full explanation.")
        + event("step_finish", reason="stop")
    )
    result = decode(stream)
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        "STATUS: FAILED\nFull explanation.",
        "",
    )


@pytest.mark.parametrize(
    "stream,diagnostic",
    [
        ("", "incomplete answer"),
        (event("step_start") + event("text", id="p", text="STATUS: PASSED"), "incomplete answer"),
        (answer("STATUS: PASSED", reason="tool-calls"), "incomplete answer"),
        (answer("STATUS: PASSED", reason="length"), "incomplete answer"),
        (answer(""), "incomplete answer"),
        (
            event("step_start")
            + event("tool_use", output="STATUS: PASSED")
            + event("step_finish", reason="stop"),
            "incomplete answer",
        ),
        (answer("STATUS: PASSED") + event("step_start", "next"), "incomplete answer"),
        (
            answer("STATUS: PASSED") + '{"type":"error","error":{"message":"private"}}\n',
            "runtime error event",
        ),
        (answer("STATUS: PASSED") + "not json\n", "invalid event stream"),
        ("[]\n", "invalid event stream"),
        (answer("STATUS: PASSED") + '{"type":"error","type":"text"}\n', "invalid event stream"),
        (answer("STATUS: PASSED\n\ud800"), "invalid event stream"),
        (event("text", id="p", text="STATUS: PASSED"), "invalid event stream"),
        (event("step_start") + event("text", id="p", text=123), "invalid event stream"),
        (
            event("step_start") + event("step_finish", "other", reason="stop"),
            "invalid event stream",
        ),
        (answer("STATUS: PASSED") + event("unknown"), "invalid event stream"),
    ],
    ids=[
        "empty",
        "unfinished",
        "tool-finish",
        "length-finish",
        "empty-answer",
        "tools-only",
        "unfinished-later-step",
        "runtime-error",
        "malformed-json",
        "non-object",
        "duplicate-key",
        "invalid-unicode",
        "missing-step",
        "invalid-text",
        "wrong-message",
        "unknown-event",
    ],
)
def test_transport_rejections_never_release_buffered_approval(
    stream: str,
    diagnostic: str,
) -> None:
    result = decode(stream)
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        f"STATUS: FAILED\nReview output transport error: {diagnostic}\n",
        "",
    )


@pytest.mark.parametrize(
    "stream,diagnostic",
    [
        (
            event("step_start")
            + event("text", id="p", text="STATUS: PASSED").replace('"s"', '"other"'),
            "invalid event stream",
        ),
        (
            answer("STATUS: PASSED")
            + answer("STATUS: PASSED", message="next", reason="tool-calls"),
            "incomplete answer",
        ),
        (
            answer("STATUS: PASSED") + event("reasoning", text="ignored"),
            "invalid event stream",
        ),
        (answer(" \t\n"), "incomplete answer"),
        (
            event("step_start")
            + event("text", id="p", text="STATUS: PASSED").replace(
                '"text": "STATUS: PASSED"',
                '"text": "STATUS: FAILED", "text": "STATUS: PASSED"',
            ),
            "invalid event stream",
        ),
    ],
)
def test_protocol_boundaries_never_release_approval(stream: str, diagnostic: str) -> None:
    result = decode(stream)
    assert (result.returncode, result.stdout, result.stderr) == (
        1,
        f"STATUS: FAILED\nReview output transport error: {diagnostic}\n",
        "",
    )

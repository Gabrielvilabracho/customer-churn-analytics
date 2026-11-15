"""Render only the completed final assistant step from OpenCode NDJSON."""

import json
import sys
from typing import TextIO


class TransportError(ValueError):
    """The stream cannot safely provide a final assistant answer."""


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def final_answer(stream: TextIO) -> str:
    session = None
    message = None
    finished = False
    reason = None
    parts: dict[str, str] = {}
    for line in stream:
        event = json.loads(line, object_pairs_hook=unique_object)
        if not isinstance(event, dict):
            raise ValueError
        kind = event.get("type")
        if kind == "error":
            raise TransportError("runtime error event")
        if kind not in {"step_start", "text", "reasoning", "tool_use", "step_finish"}:
            raise ValueError
        event_session = event.get("sessionID")
        part = event.get("part")
        if not isinstance(event_session, str) or not event_session or not isinstance(part, dict):
            raise ValueError
        session = session or event_session
        if event_session != session or part.get("sessionID") != session:
            raise ValueError
        part_message = part.get("messageID")
        if not isinstance(part_message, str) or not part_message:
            raise ValueError
        if kind == "step_start":
            if (message is not None and not finished) or part.get("type") != "step-start":
                raise ValueError
            message, finished, reason, parts = part_message, False, None, {}
            continue
        if part_message != message or finished:
            raise ValueError
        if kind == "text":
            identifier, text = part.get("id"), part.get("text")
            if (
                part.get("type") != "text"
                or not isinstance(identifier, str)
                or not identifier
                or not isinstance(text, str)
            ):
                raise ValueError
            # Repeated part IDs carry deltas, not replacement snapshots.
            parts[identifier] = parts.get(identifier, "") + text
        elif kind == "step_finish":
            reason = part.get("reason")
            if part.get("type") != "step-finish" or not isinstance(reason, str):
                raise ValueError
            finished = True
        # Tool and reasoning payloads never contribute reviewer text.
    answer = "".join(parts.values())
    if not finished or reason != "stop" or not answer.strip():
        raise TransportError("incomplete answer")
    answer.encode("utf-8")  # Reject invalid text before releasing any verdict bytes.
    return answer


def main() -> int:
    try:
        answer = final_answer(sys.stdin)
    except (ValueError, TypeError, UnicodeError, OSError) as error:
        diagnostic = str(error) if isinstance(error, TransportError) else "invalid event stream"
        # Drain the pipe so a decoder rejection does not SIGPIPE the model runtime.
        try:
            for _ in sys.stdin:
                pass
        except (UnicodeError, OSError):
            pass
        sys.stdout.write(f"STATUS: FAILED\nReview output transport error: {diagnostic}\n")
        return 1
    sys.stdout.write(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

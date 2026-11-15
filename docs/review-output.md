# Decode a structured review answer

The internal Python filter reads OpenCode's `run --format json` NDJSON from
standard input and renders only the complete final assistant step:

```bash
python3 -B entrypoint/review-bin/opencode_review_output.py < review-events.jsonl
```

Text events contain deltas, which are appended by part identifier. Tool traces,
reasoning and earlier steps are not the final answer. The stream must end with a
completed `stop` step containing text, with consistent session/message identity.
Malformed, errored, incomplete or ambiguous protocol structures fail closed.

The filter never searches for an approval marker. The final model text—including
a failed or ambiguous verdict—is rendered verbatim for GGA's strict validation.
Transport rejection emits a failure diagnostic, never approval. This checks the
protocol, not cryptographic origin: the caller must supply the trusted client's
actual event stream. No credential or billing identity is inferred from events.

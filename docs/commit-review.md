# Local GPT commit review

GGA uses `opencode:openai/gpt-6.1-sol` and the read-only `plan` agent. OpenCode
uses its existing authentication; no credentials are copied into the repository.
The review remains fail-closed and uses `AGENTS.md`.

## Runtime isolation

Git hooks export repository-local environment variables, including index
selection. GGA needs these while collecting staged content. A nested reviewer
runtime must not carry them into Git operations on a different repository.

The local hook captures the real OpenCode binary, then prepends
`entrypoint/review-bin` only for the GGA process. That wrapper clears Git's own
`rev-parse --local-env-vars` list immediately before executing the real runtime.
It preserves arguments, prompt input, model, agent and authentication settings.
It does not alter the parent hook environment or the reviewed staged content.

The local hook runs `gga run --no-cache`: a recovered index requires a fresh
review, not a cached approval. The hook must retain its nonzero-exit guard.
This is a defense against inherited-index interference, not a claim that an
installed runtime's internal implementation has been conclusively diagnosed.

## Checks

```bash
bash -n entrypoint/review-bin/opencode .git/hooks/pre-commit
python -m pytest --no-cov packages/ml/tests/test_gga_opencode_wrapper.py
```

The regression uses disposable repositories and a simulated foreign snapshot.
Without isolation it changes the inherited index; with isolation the index,
worktree, model arguments and prompt remain unchanged. No real model is called.

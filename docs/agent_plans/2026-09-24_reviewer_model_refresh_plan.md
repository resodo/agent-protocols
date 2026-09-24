# Reviewer model profile refresh

Status: active implementation plan
Branch: `feature/reviewer-model-refresh`, based on `origin/main` at `119b52a`

## Goal and accepted decision

Refresh the explicit normal/hard reviewer profiles for Claude Code, Codex, and
Grok Build. The human accepted this matrix on 2026-09-24:

| Backend | Normal | Hard |
| --- | --- | --- |
| Claude Code | `claude-opus-5-5` / `high` | `claude-fable-5-1` / `xhigh` |
| Codex | `gpt-6-sol` / `high` | `gpt-6-astra` / `xhigh` |
| Grok Build | `grok-4.7` / `medium` | `grok-4.7` / `xhigh` |

The driver continues to select the tier. Normal remains the default and hard
requires a semantic reason. Backend order, same-agent exclusion, fallback,
override behavior, readiness standard, and 1800/3600-second timeouts remain
unchanged. The accepted change is the six model/effort values only.

## Evidence and uncertainty

Official model and effort documentation supports the chosen IDs and levels:

- Anthropic: https://platform.claude.com/docs/en/models/overview and
  https://platform.claude.com/docs/en/build-with-claude/effort
- OpenAI: https://developers.openai.com/api/docs/models/gpt-6-sol and
  https://developers.openai.com/api/docs/models/gpt-6-astra
- xAI: https://docs.x.ai/developers/models and
  https://docs.x.ai/developers/model-capabilities/text/reasoning

Local Grok Build 1.0.40 lists `grok-4.7` as its default and available model.
The installed Codex CLI is 0.155.1; the official Codex changelog says 0.156.1
added Sol to its model picker. This does not establish whether explicit `-m
gpt-6-sol` works on 0.155.1. The implementation should not claim actual
account access to a new model until a bounded call demonstrates it.

## Implementation

1. Change only `REVIEW_MODEL_MATRIX` and its directly used defaults in
   `structured-review/scripts/claude_structured_review.py`.
2. Update exact-profile, argv, override-guard, and metadata assertions in
   structured-review tests. Retain tests that show selected tier, recommendation,
   fallback, and provider override remain separate.
3. Update the live profile matrix in `structured-review/SKILL.md`, the root
   `README.md` runner summary, and `docs/CURRENT.md` in the same change. Add
   this plan to `docs/agent_plans/README.md`. Historical plans stay untouched.

## Validation and review gates

- Plan Review before executable edits, through this checkout's structured-review
  runner with explicit normal tier.
- Focused profile and argv tests must demonstrate all six selected values and
  the normal-tier hard-model guard. Run the full structured-review test suite,
  compile the runner, and check `git diff --check`.
- Before Implementation Review, exercise the reviewable candidate through a
  bounded real call for the new profile routing where possible. At minimum,
  distinguish successful model invocation from local argument construction;
  record any model whose access or CLI support is not validated.
- Implementation Review through this checkout's runner after the candidate
  passes its change-specific validation; resolve findings. Closeout checks
  current docs, validation provenance, and git state. Merge remains human-owned.

## Review Threads

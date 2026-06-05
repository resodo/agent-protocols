# Agent Entry Point

This file is the repo-level entry point for agents working on shared agent
protocols.

## Session Bootstrap

When asked to read `AGENTS.md` and prepare to work:

1. Identify the repo root, branch, and worktree status.
2. Read this file, `README.md`, `docs/README.md`, and `docs/CURRENT.md`.
3. For a protocol change, read the affected `SKILL.md`, required references,
   scripts, tests, and the active plan under `docs/agent_plans/` when one
   exists.
4. Report the task boundary and whether the worktree is clean before editing.

Do not load every historical plan by default. Dated plans under
`docs/agent_plans/` are provenance records unless `docs/CURRENT.md` or the human
names one as active.

## Protocol Work

Protocol directories are executable workflow packages. Keep them focused on:

- `SKILL.md`;
- `scripts/`;
- `tests/`;
- `references/`;
- reusable templates or guard documents.

Put dated implementation plans, review threads, closeout reports, and other
worktree/PR artifacts under `docs/agent_plans/`, not inside protocol
directories.

For structured review gates in this repo, use
`structured-review/scripts/claude_structured_review.py` from this checkout. Do
not substitute user-home absolute paths, sibling checkouts, self-review, or
chat-only review when the shared protocol says the runner is available.

## Documentation Rules

- Use `docs/README.md` for document placement and lifecycle rules.
- Use `docs/CURRENT.md` for the current source-of-truth map.
- Use `docs/backlog.yml` for this repo's protocol-development backlog.
- Use `backlog-maintenance/SKILL.md` before adding, updating, closing, or
  querying backlog items in this repo.
- Do not commit local user-home absolute paths, secrets, credentials, private
  account details, or generated private run outputs.

When adding, renaming, moving, or retiring a protocol, update `README.md`,
`docs/CURRENT.md`, and any affected index in the same change.

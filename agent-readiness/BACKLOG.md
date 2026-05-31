# Agent Readiness Backlog

## AR-001 Cold-Start Agent Eval

Status: deferred

Define a small way to test whether a fresh coding-agent configuration can still
collaborate correctly after model, prompt, tool, or app changes.

The future design should decide whether this is a manual checklist, a versioned
eval case set, an operator-run harness, or a CI/nightly integration.

Do not turn normal session startup into a heavy eval run. Normal startup should
remain a lightweight `AGENTS.md` bootstrap owned by the project repo.

Promotion criterion: promote this item when at least one consumer repo has
adopted the worktree guard and bootstrap template, and a real cold-start
regression or repeated human-observed startup failure shows that lightweight
bootstrap guidance is not enough.

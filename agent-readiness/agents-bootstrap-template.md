# AGENTS.md Bootstrap Template

This template is for project repos that want a lightweight startup behavior for
no-task prompts such as:

```text
Read AGENTS.md. We will develop together next.
```

This is not a shared `SKILL.md`. The repo's own `AGENTS.md` remains the startup
source of truth because each repo has different entrypoints, ownership,
production posture, and current-state anchors.

Division of labor: the worktree guard proves required protocol files are
available; the bootstrap receipt proves the agent has established repo
coordinates, ownership, and production/access posture. Neither should silently
cover for the other.

## Template Block

Project repos may adapt this block into their own `AGENTS.md`:

```markdown
## Session Bootstrap

When the user asks to read `AGENTS.md` and prepare to develop, but has not yet
given a concrete task:

1. Identify the current repo root, branch, and worktree status.
2. Read this `AGENTS.md`.
3. Follow only the minimal startup routing in this file.
4. If this repo declares `external/agent-protocols`, make sure the shared
   protocols are available. If they are missing, initialize the submodule or
   report the blocker instead of skipping protocol usage.
5. If this repo has identity metadata such as `.skynet/catalog.yml`, read it to
   understand repo identity, companion repo ownership, and production/access
   posture.
6. If production/access posture is not declared, say it is unknown and do not
   infer private connection details.
7. Read the current-status anchor named by this file, if any.
8. Output a short project receipt.
9. Stop and wait for the concrete task.

Do not infer a feature task, open a plan, start implementation, load every
backlog or historical document, or expose private access details in chat.
```

## Receipt Shape

The receipt should be concise:

```text
Project receipt:
- Repo/worktree/branch: <repo>, <worktree>, <branch>, <clean-or-dirty>
- Entrypoints read: AGENTS.md, <minimal routed files>
- Shared protocols: <available|missing|not declared>
- Repo identity: <declared source or unknown>
- Companion ownership: <declared source or unknown>
- Production/access posture: <declared posture or unknown>
- Next boundary: no concrete task loaded yet; waiting for user direction
```

## Principles

- Keep startup small. The bootstrap establishes coordinates; it does not solve
  the next task.
- Do not duplicate the repo's full documentation map in this template. The
  project `AGENTS.md` decides which entrypoints are required.
- Do not use shared guidance as a second source of truth for production access.
  Use repo-declared metadata or say `unknown`.
- Do not fall back to user-home absolute paths when vendored protocols are
  missing.
- If a task later requires planning, review, closeout, paid-provider checks, or
  production runbooks, load those workflows after the user gives that task.

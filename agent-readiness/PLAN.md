# Agent Readiness System Plan

Date: 2026-05-31
Status: draft for structured review

## Human Concern

After context compaction, model changes, provider changes, or a fresh worktree,
an agent can start with the wrong project coordinates: missing shared protocols,
wrong production-access assumptions, unclear repo ownership, or an incomplete
view of the current phase. The fix should be durable and low-friction, not a
large context-loading ritual that wastes tokens before the task is even known.

## Updated Scope Decision

This branch should stay small.

In scope now:

1. Define a programmatic worktree bootstrap guard contract for repos that vendor
   shared protocols as `external/agent-protocols`.
2. Define a reusable `AGENTS.md` bootstrap template/principles block that
   project repos can copy into their own entrypoint.

Out of scope now:

- no cold-start eval harness;
- no manual regression checklist implementation;
- no LLM judge;
- no CI or nightly eval runner;
- no generic session-bootstrap skill that overrides repo `AGENTS.md`.

The cold-start testing idea remains valid, but it is deferred to backlog because
it is larger than the immediate failure mode.

## Non-Goals

- Do not replace repo-specific `AGENTS.md` files.
- Do not ask agents to load all docs, all backlog, or all production runbooks
  before a task is known.
- Do not store secrets, private hostnames, private IPs, tokens, env files, or
  personal account details in protocol files.
- Do not create a second source of truth for project state. Shared guidance
  should route agents to the owning repo's declared entrypoints.
- Do not depend on local user-home paths or sibling checkout paths.

## Component 1: Worktree Bootstrap Guard Contract

### Problem

Fresh feature worktrees can be created before `external/agent-protocols` is
initialized. When that happens, an agent may silently skip the shared planning,
review, or closeout protocols because the files are absent.

### Boundary

The executable guard cannot live only inside `external/agent-protocols`, because
the failure case is that this submodule may be missing or empty. Therefore:

- this repo defines the required guard behavior;
- each project repo owns the local script or hook that can run before the
  submodule is available;
- downstream projects should wire that local guard into their worktree creation
  workflow.

### Contract

Projects that vendor shared protocols through a submodule should have a
programmatic guard that runs immediately after creating or entering a feature
worktree.

The guard must:

- confirm it is running from the project repo root or find the repo root;
- initialize/update `external/agent-protocols` when the project declares it;
- verify required protocol files exist;
- fail loudly if the protocol files cannot be made available;
- avoid falling back to user-home absolute paths;
- avoid changing production state.

Minimum required files for Skynet-style repos:

```text
external/agent-protocols/planning/SKILL.md
external/agent-protocols/structured-review/SKILL.md
external/agent-protocols/closeout/SKILL.md
```

Expected downstream shape:

```bash
git submodule update --init --recursive external/agent-protocols
test -f external/agent-protocols/planning/SKILL.md
test -f external/agent-protocols/structured-review/SKILL.md
test -f external/agent-protocols/closeout/SKILL.md
```

If any check fails, feature setup should stop. The agent should not continue by
skipping planning, structured review, or closeout.

## Component 2: `AGENTS.md` Bootstrap Template

### Problem

When a user starts a new session with a no-task prompt such as "read AGENTS.md,
then we will develop together", the agent needs a small project-coordinate
bootstrap. That behavior is repo-specific because each repo has different
entrypoints, current-state anchors, catalog files, and production boundaries.

### Boundary

This should not be a generic `agent-readiness` skill. The repo's own `AGENTS.md`
is the startup source of truth.

This repo should provide a template and principles that project repos can embed
or adapt in their own `AGENTS.md`.

### Template Behavior

For a no-task bootstrap prompt, a project `AGENTS.md` should instruct the agent
to:

1. Identify current repo, branch, and worktree status.
2. Read the repo `AGENTS.md`.
3. Follow only the repo's minimal startup routing.
4. Confirm shared protocols are available when the repo declares them.
5. Read repo identity metadata, such as `.skynet/catalog.yml`, when present.
6. Read the repo's current-status anchor, such as `docs/CURRENT.md`, when the
   repo entrypoint requires it.
7. Emit a short project receipt.
8. Stop and wait for the concrete task.

The agent must not:

- infer a feature task;
- open a plan;
- start implementation;
- load every backlog or historical artifact;
- expose private access details in chat.

### Receipt Shape

The receipt should be short enough not to pollute the context window. It should
answer:

- which repo/worktree/branch is active;
- which entrypoint files were read;
- whether shared protocols are available;
- where repo identity and companion ownership are declared;
- what the next task boundary is.

## Deferred Backlog Item

Cold-start testing is deferred. The deferred item should cover how to test a
fresh agent/model/tool configuration against fixed prompts and rubrics without
turning every normal session startup into a heavy eval run.

The future work should decide whether it is:

- a manual checklist;
- a versioned eval case set;
- an operator-run harness;
- or a CI/nightly integration.

This branch should only record that backlog item, not implement it.

## Source-Of-Truth Rules

- `AGENTS.md` remains the repo-level startup source of truth.
- Repo identity metadata, when present, belongs in the project repo, for example
  `.skynet/catalog.yml`.
- Shared workflow behavior belongs in this `agent-protocols` repo.
- Project-specific protocol refinements belong in project overlays, for example
  `.agent-protocols/*.md`.
- Runtime secrets and private access details do not belong in any of the above.

## Implementation Plan

After this plan is reviewed:

1. Add `agent-readiness/worktree-guard.md` with the guard contract, expected
   downstream script shape, and failure semantics.
2. Add `agent-readiness/agents-bootstrap-template.md` with the reusable
   `AGENTS.md` bootstrap block and receipt example.
3. Add `agent-readiness/BACKLOG.md` with the deferred cold-start testing item.
4. Update this repo's `README.md` to list the new agent-readiness guidance.
5. Identify required downstream companion PRs, starting with Skynet V2, after
   the generic guidance is accepted.

This implementation intentionally does not add `agent-readiness/SKILL.md`.
Startup bootstrap remains owned by each repo's `AGENTS.md`.

## Validation

Plan validation:

- structured-review as `other-plan`;
- reviewer confirms scope is understandable and does not create a second source
  of truth.

Implementation validation:

- file-level inspection that agent-readiness guidance is discoverable from
  `README.md`;
- worktree guard guidance explains why the executable guard must live in the
  project repo, not only in the submodule;
- bootstrap template stays concise and does not require loading all project
  history;
- deferred cold-start testing item is recorded but not implemented;
- no user-home absolute paths, private hostnames, private IPs, tokens, or env
  values appear in tracked protocol files.

## Review Questions

1. Is the split correct: shared guidance here, executable guard in project repos,
   repo-specific startup behavior in `AGENTS.md`?
2. Is it acceptable that this branch does not create an `agent-readiness/SKILL.md`?
3. Is the deferred cold-start testing item recorded clearly enough without
   expanding this branch's scope?

# Agent Readiness System Plan

Date: 2026-05-31
Status: reviewed; implementation complete pending implementation review

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

Declaration mechanism: a project declares vendored shared protocols by tracking
`external/agent-protocols` in `.gitmodules` or by explicitly naming that path in
its repo entrypoint. The guard should use that project-local declaration instead
of assuming every repo vendors the same submodule.

Minimum required files for Skynet-style repos:

```text
external/agent-protocols/planning/SKILL.md
external/agent-protocols/structured-review/SKILL.md
external/agent-protocols/closeout/SKILL.md
```

The executable source of truth for a consumer repo's required protocol set
should be the project-local guard script or guard config. That guard should list
required protocols once, and other repo docs should point to the guard rather
than duplicate the list. The shared contract above is the baseline for
Skynet-style repos; consumers may add protocols such as `retrospective` when
their own lifecycle requires them.

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
5. Read repo identity and production-posture metadata, such as
   `.skynet/catalog.yml`, when present.
6. If production posture is not declared, say it is unknown and do not infer
   private access details.
7. Read the repo's current-status anchor, such as `docs/CURRENT.md`, when the
   repo entrypoint requires it.
8. Emit a short project receipt.
9. Stop and wait for the concrete task.

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
- production/access posture from repo-declared metadata, or `unknown`;
- what the next task boundary is.

Division of labor: the worktree guard proves required protocol files are
available. The bootstrap receipt proves the agent has established repo
coordinates, ownership, and production/access posture. Neither should silently
cover for the other.

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
- guard smoke validation is performed against at least one real consumer repo in
  a temporary or non-destructive setup: one initialized pass case and one
  missing-submodule fail-loud case;
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
4. Is the guard boundary concrete enough to prevent agents from skipping missing
   shared protocols?
5. Does the plan avoid creating a second source of truth for repo state,
   production posture, or required protocol checks?

## Review Threads

Reviewer pass on commit `3f04b1d` (type: other-plan). No blocking issues.
Overall judgment: ready to proceed to implementation; threads below are
non-blocking comments, most important first.

### RT-1 Production-access posture is under-served (priority)

Status: resolved — driver

The human concern explicitly includes "wrong production-access assumptions,"
but nothing in the plan surfaces prod posture to the agent. The guard's only
prod-related rule ("avoid changing production state") constrains the guard's own
behavior, not what the agent is told. The Component 2 receipt reports
repo/branch, entrypoints, protocol availability, and ownership — but not whether
the current repo/worktree is production-touching.

Suggested change: add a prod-posture line to the receipt shape, sourced from
repo-declared metadata (e.g. `.skynet/catalog.yml`), so the concern most likely
to cause damage is explicit at startup.

Driver response: added production-posture metadata to the template behavior and
receipt shape, with an explicit `unknown` posture fallback that forbids private
access inference.

### RT-2 Required-protocol-files list is a latent second list

Status: resolved — driver

The minimum-required-files list hard-codes `planning`, `structured-review`, and
`closeout`. Two concerns:

- each consumer's guard will also hard-code this list, so adding/renaming a
  protocol means editing the contract and every downstream guard — a drift
  surface with no stated owner/update story (Mechanism Lifecycle);
- the repo already ships a `retrospective/` protocol that this list omits — is
  that intentional, or a gap?

Suggested change: state where the canonical required-list lives and how it is
maintained, so a consumer is not silently checking a stale set.

Driver response: clarified that the executable source of truth for a consumer
repo is the project-local guard script or config, and repo docs should point to
that guard rather than duplicate the list. The shared contract remains baseline
guidance for Skynet-style repos. `retrospective` is additive when a consumer's
lifecycle requires it, not a baseline worktree gate.

### RT-3 State the guard-vs-receipt division of labor explicitly

Status: resolved — driver

The guard checks protocol presence; the receipt checks repo-coordinate
correctness (ownership, posture). Reasonable split, but it is implicit — and it
is exactly where prod-posture and repo-ownership can fall between the two and be
checked by neither. Also, "initialize/update ... when the project declares it"
has no declared mechanism for how a repo signals that it vendors
`external/agent-protocols`. One sentence each resolves both.

Driver response: added declaration mechanism and explicit guard-vs-receipt
division of labor.

### RT-4 No concrete smoke test for the guard contract

Status: resolved — driver

Validation is all file-level inspection plus subjective checks. With cold-start
testing deferred, the contract's only proof is a read-through. A cheap, in-scope
check: dry-run the "Expected downstream shape" snippet against a real consumer
(Skynet V2) — confirm it passes when initialized and fails loudly when the
submodule is removed. This validates the contract without building the deferred
harness.

Driver response: added non-destructive guard smoke validation to implementation
validation.

### RT-5 BACKLOG AR-001 has no promotion criterion

Status: resolved — driver

AR-001 records what is deferred and why, but not what signal promotes it; without
one it parks indefinitely. Suggested line: "promote once at least one consumer
repo has adopted the guard + template and a cold-start regression is observed."

Driver response: added promotion criterion to `agent-readiness/BACKLOG.md`.

### RT-6 Plan's own Review Questions omit two the human asked (nit)

Status: resolved — driver

The human's review focus also asked about guard-boundary concreteness and
whether the plan avoids a second source of truth. Adding these to the Review
Questions list keeps future reviewers covering the same ground.

Driver response: added both questions to the plan's Review Questions section.

# Agent Protocols

Reusable local protocols for human-agent and multi-agent software work.

Agents should start with `AGENTS.md`. Documentation placement and lifecycle
rules live in `docs/README.md`; the current protocol map lives in
`docs/CURRENT.md`.

## Roles

Start with `agents/README.md`: how authority roles and task roles combine,
the role list, and the coordinator. The master is defined once, in
`agents/master.md`.

## Protocols, by reader

Each protocol's description says its reader and trigger; bodies load on
demand.

Every role:

- `decision-boundary/` - who may decide what: ten gates, the authority ledger, delegated execution (the single home of merge and production-change permission), never-ask, escalation. `CORE.md` is the resident block every consumer embeds in its `AGENTS.md`.

The master (and a coordinator for `dispatch`):

- `master-board/` - the board, the queue of items waiting on the human, the settled list, and the sweep.
- `dispatch/` - briefs, model tier, watchdog, pacing, blocking requests, returned work, relaying.
- `away-mode/` - pre-authorizations before the human leaves; per-change list on return.
- `session-handoff/` - one-page handoff and the new master's cold start.

Dispatched agents:

- `line-worker/` - how every dispatched agent works and hands back; the extra limits for implementation workers.
- `merge-queue/` - one merger, one PR at a time.
- `release/` - production changes (release, configuration, ops action): permission, preconditions, baseline, official command, staged checks, failure policy.
- `visual-qa/` - independent review of user-visible changes before the human sees them.

Authors, drivers and reviewers:

- `planning/` - discussion to an executable plan.
- `structured-review/` - review of plans and implementations, document levels, decision-doc approval.
- `closeout/` - final checks and delivery handoff.
- `readable-brief/` - turns a final, reviewed document into the human's brief; required for decision docs.
- `fix-triage/` - whether something is wrong, attribution, and the smallest systemic fix.
- `retrospective/` - evidence-based learning after an incident or closeout.
- `backlog-maintenance/` - the YAML backlog of deferred work.
- `scout/` - judgment-heavy repository discovery that proposes backlog candidates.

Repo maintainers:

- `agent-readiness/` - worktree guard contract (including the resident-core check), `AGENTS.md` bootstrap template, and `capabilities.md` (capability names to each coding agent's feature or fallback).
- `agents/` - role definitions; consumers add thin per-agent wrappers.

## Docs

- `docs/agent_plans/` - dated plans, review-thread artifacts, and closeout
  evidence for protocol changes.
- `docs/backlog.yml` - this repo's protocol-development backlog.

Protocol directories should hold executable or reusable protocol material:
`SKILL.md`, `scripts/`, `tests/`, `references/`, and templates. Do not put
dated plans or one-off review artifacts in protocol directories.

## Where A Rule Lives

Four layers, one home per rule (approved 2026-10-16;
`docs/agent_plans/2026-10-16_repo_restructure_decision.md`, section 3): this
repo (rules true for any project and any coding agent); each project's
`.agent-protocols/` overlay (its paths, commands, numbers, business terms,
settled decisions and authority ledger); the human's user-level preferences
(outside every repo); and the master's state files (no rules). A program that
spans several repos keeps its master-level overlay files in one home repo.

## Local Overlays

Protocols are reusable. Project-specific policy belongs in the repo being worked
on, under:

```text
.agent-protocols/context.md
.agent-protocols/<protocol-name>.md
```

When a protocol is loaded inside a repo:

1. Read the generic protocol from this directory.
2. Read `.agent-protocols/context.md` if present.
3. Read `.agent-protocols/<protocol-name>.md` if present.

Overlays are loaded only for the protocol being used. Unknown overlay files are
ignored. A project overlay may be more specific than the generic protocol, but
must not override a generic `SAFETY` rule.

`SAFETY` rules may appear at H2 or H3 depending on a protocol's internal
structure. The heading text is the contract; overlays must not weaken those
rules.

## Canonical Source

The canonical source of these protocols is this repository's `origin/main`.

1. Repos that consume the protocols pin them as an
   `external/agent-protocols` submodule and run a worktree guard that
   fetches from origin before branching, bases feature worktrees on the
   fresh default branch, materializes the pinned submodule, and verifies
   the skill mounts (see `agent-readiness/worktree-guard.md`). When the
   fetch fails, work stops: freshness is checked mechanically, never
   assumed.
2. The protocols surface inside each coding agent through committed skill
   mounts - `.claude/skills/<protocol>` for Claude Code and
   `.agents/skills/<protocol>` for Codex, symlinked into the vendored
   submodule - so a fresh submodule makes the agents load the protocols
   natively at startup. No pointer files, and no copied protocol content,
   with one deliberate exception: the resident core
   (`decision-boundary/CORE.md`) is copied verbatim into each consumer's
   `AGENTS.md` and checked by `scripts/check_resident_core.py`.
3. There is no machine-global read path. Outside a vendoring repo, the
   human directs the agent to a checkout explicitly in session.

Do not write machine-specific absolute paths into this repo's docs. The
project-local `.agent-protocols/` overlay directory described above is
unrelated to where the protocols themselves live; it holds per-repo
refinements only.

## Usage

Point an agent at the relevant `SKILL.md` and give it the requested role,
artifact and type, for example:

```text
Please read <your agent-protocols checkout>/structured-review/SKILL.md
Role: reviewer
Artifact: docs/some_plan.md
Type: impl-plan
```

For structured-review gates, use the bundled runner:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree /path/to/target-repo \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/some_plan.md \
  --artifact docs/some_plan.md \
  --coding-agent codex \
  --review-tier normal \
  --focus "Review acceptance, validation, scope, and role boundaries." \
  --topic "some plan"
```

Backends, tiers, models, timeouts and recovery are in
`structured-review/references/runner-operations.md`.

# Current Protocol Map

Status: active source-of-truth map
Last updated: 2026-11-26

This file points humans and agents to the active protocol entrypoints. It does
not replace root `AGENTS.md`; agents should start there, then use this map to
avoid treating historical plans as current instructions.

## Current Anchors

- Agent entrypoint: `AGENTS.md`
- Repo overview: `README.md`
- Documentation rules: `docs/README.md`
- Protocol change plans and review artifacts: `docs/agent_plans/`
- Protocol-development todos: this repo's GitHub issues
- Shared development practice of the Skynet infra and product teams:
  `docs/shared-development-practice.md`

## Current Protocols

Roles: `agents/README.md` (role composition, coordinator) and
`agents/master.md` (the single master definition). Each protocol below says
in its description who reads it.

- `decision-boundary/SKILL.md` - gates, authority ledger, delegated execution
  (merge and production-change permission), never-ask, escalation;
  `CORE.md` is the resident block consumers embed verbatim and check with
  `scripts/check_resident_core.py`.
- `master-board/SKILL.md` - board, queue, settled list, sweep (master).
- `dispatch/SKILL.md` - briefs, tiers, watchdog, pacing, blocking requests,
  relaying (master, coordinator).
- `away-mode/SKILL.md` - pre-authorizations and the per-change list (master).
- `session-handoff/SKILL.md` - handoff and cold start (master).
- `line-worker/SKILL.md` - every dispatched agent; implementation-worker
  limits.
- `merge-queue/SKILL.md` - one merger, per-PR steps (merge agent).
- `release/SKILL.md` - any named production change (production operator).
- `visual-qa/SKILL.md` - independent review of visible changes; the
  default guideline is vendored in `visual-qa/references/`.
- `planning/SKILL.md` - discussion to plan.
- `structured-review/SKILL.md` - plan and implementation review, document
  levels, decision-doc approval.
- `closeout/SKILL.md` - final checks and delivery handoff.
- `readable-brief/SKILL.md` - the human's brief of a reviewed document.
- `fix-triage/SKILL.md` - whether something is wrong, attribution, fix.
- `retrospective/SKILL.md` - learning after an incident or closeout.
- `scout/SKILL.md` - repository discovery that proposes todo items for the adopting
  project's tracker.
- `editing-rules/SKILL.md` - rules in `AGENTS.md`: placement, formats, the
  three questions, refactors, layers, who answers; defines a wired repo.
- `scope-review/SKILL.md` - scope review before work (scope reviewer).
- `doc-watcher/SKILL.md` - after-merge rule and doc upkeep (doc watcher,
  master).
- `ci-practice/SKILL.md` - CI triggers, release gate, runner choice by
  measurement, caching, flaky tests, cost tracking (repo maintainers).
- `agent-readiness/` - worktree guard contract, bootstrap template,
  `capabilities.md`.

## Runner And References

- Structured-review runner:
  `structured-review/scripts/claude_structured_review.py`
- Runner-loaded structured-review references:
  `structured-review/references/review-lenses.md` and
  `structured-review/references/collaboration.md`. `review-lenses.md` also
  holds the brief-only `Readable Brief: Fidelity And Readability` lens.
- Driver-only runner operations (selection, tiers, profile matrix, modes,
  timeouts): `structured-review/references/runner-operations.md` (not
  runner-loaded).
- Driver recovery operations: `structured-review/references/recovery.md`
  (not a runner-loaded review lens).
- Conditional UI review reference:
  `structured-review/references/ui-review.md`
- Scout runner:
  `scout/scripts/scout_runner.py`
- Scout references:
  `scout/references/script-lifecycle.md`,
  `scout/references/code-reachability-backend-python.md`, and
  `scout/references/code-structure.md`
- Docs check (separate PR): `scripts/docs_check.py`; scope-review runner:
  `scope-review/run_scope_review.py`; settings:
  `.agent-protocols/docs-check.json` in each consumer

The UI review reference is conditional. It is not part of the runner-loaded
required reference set unless a future accepted plan changes runner loading.

## Maintenance

Update this map during closeout when protocols, indexes, runner paths,
or reference paths change.

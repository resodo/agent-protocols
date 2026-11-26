# Plan: retire the in-repo YAML backlog

Status: active implementation plan
Branch: `retire-backlog-protocol`
Document level: plan (one PR).

## What and why

Adopting projects now keep one todo list: their GitHub issue tracker, named in
each project's local overlay (`.agent-protocols/context.md`). The in-repo YAML
backlog (`docs/backlog.yml` plus the `backlog-maintenance` protocol and its
checker) is a second list and is retired. The function stays (deferred work is
recorded, Scout still proposes work); the YAML path is removed fully, with no
fallback.

## Changes

1. Delete `backlog-maintenance/`, its two skill mounts
   (`.agents/skills/backlog-maintenance`, `.claude/skills/backlog-maintenance`),
   `docs/backlog.yml`, `scripts/check_backlog.py`,
   `tests/test_check_backlog.py`, and the CI step that ran the checker. The CI
   step `python -m unittest discover -s tests` stays (it runs the other repo
   script tests) and is renamed.
2. This repo's own deferred work goes to its GitHub issues. The five open items
   in `docs/backlog.yml` were judged obsolete before this change (one is covered
   by `retrospective`, one by `dispatch/references/watchdog.md`, three were
   watch-only with no trigger), so none are migrated.
3. Live instructions that said "backlog" now say the project's todo tracker:
   `AGENTS.md`, `README.md`, `docs/CURRENT.md`, `docs/README.md`,
   `line-worker`, `planning`, `retrospective`, `closeout`,
   `decision-boundary/SKILL.md`, `structured-review` (skill and two
   references), the `agent-readiness` bootstrap template, and `scout`.
   `decision-boundary/CORE.md` has no backlog mention and is unchanged. Dated
   files under `docs/agent_plans/` stay frozen.
4. Scout keeps its job and loses the YAML:
   - the overlay key `repo_context.backlog_path` is retired; the runner rejects
     an overlay that still has it, with a message naming the key, so stale
     consumer config is removed instead of silently ignored;
   - the runner no longer loads a backlog file, records a sha256 baseline in
     dry-run, or demands backlog-checker provenance in write-enabled mode;
   - report heading `Proposed Backlog Changes` becomes `Proposed Todo Changes`;
     manifest headings `Next / Backlog` and `Backlog Write Mode` become `Next`
     and `Tracker Write Mode`;
   - dry-run promises no tracker writes (the runner cannot see the tracker, so
     this is the driver's promise); write-enabled runs must record an
     `- Opened tracker items:` line in the manifest, which `check` enforces;
   - `scout/SKILL.md`, `scout/references/code-structure.md` and
     `scout/tests/test_scout_runner.py` match.

## Consumer follow-up (after merge, in each consumer's submodule bump PR)

- Remove the skill mounts `.agents/skills/backlog-maintenance` and
  `.claude/skills/backlog-maintenance` (and any other mount of it).
- In `.agent-protocols/scout.yml`, delete `repo_context.backlog_path`. No key
  is added; the tracker is the one named in `.agent-protocols/context.md`.
- Remove any `.agent-protocols/backlog-maintenance.md` overlay, any local
  backlog checker and its CI step, after moving still-live items to the
  tracker.

## Validation

- Tests are not run locally (never on the dev machine). This repo's GitHub CI
  runs `tests/`, `structured-review/tests` and `scout/tests` on the PR.
- `git grep -n -i backlog`, excluding `docs/agent_plans/`, leaves only the
  retired-key guard and its test, and one line in `AGENTS.md` stating there is
  no in-repo backlog file.
- One structured `impl` review (Codex, normal tier).

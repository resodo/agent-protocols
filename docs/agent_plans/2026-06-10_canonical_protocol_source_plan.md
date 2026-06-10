# Canonical Protocol Source Plan (AP-BL-0002 / AP-BL-0003)

Status: draft for plan review
Branch: `feature/canonical-source-docs`
Worktree: `agent-protocols-canonical-source`

## Context

AP-BL-0002 asked where the canonical global structured-review source should
live and how Codex and Claude should read the same source. Investigation on
the development machine made the problem concrete:

- A user-home clone of this repo sat 93 commits behind `main` (cloned
  2026-05-18, predating the review runner, Scout, backlog protocol, and the
  Codex reviewer backend), with no update mechanism.
- This repo's own `README.md` Usage examples pointed agents at exactly that
  user-home path (`~/.agent-protocols/...`), so any non-submodule context
  following the documented entrypoint read a three-week-old protocol.
- Neither Claude Code nor Codex had a global pointer to the protocols at all;
  discovery relied on the human pasting paths into chat.

Repos that vendor `external/agent-protocols` as a submodule are unaffected:
pinned versions plus the dispatch auto-bump close that loop.

Decisions converged with the human (2026-06-10):

1. The stale user-home clone is deleted, not repaired. There is exactly one
   local copy of this repo per machine: the development checkout. (The
   deletion already happened; it carried no dirty files, stashes, or
   unpushed commits.)
2. Repo docs stop naming any user-home or machine-specific absolute path.
   The Usage guidance describes reading the protocols from "your local
   checkout of this repo", with the submodule path taking priority inside
   vendoring repos.
3. The discipline that makes a single checkout safe as a read source is
   written down: the main checkout stays clean on `main`; all development
   happens in linked worktrees; agents must not treat a feature worktree as
   a protocol source.
4. Per-machine discovery is owned by thin pointers in each agent's global
   instructions (for example `~/.claude/CLAUDE.md` for Claude Code and
   `~/.codex/AGENTS.md` for Codex), which name the machine's checkout path
   and the trust rule. The pointers are machine configuration, not repo
   content; the repo documents the pattern generically. This is the
   "thin wrapper" AP-BL-0003 asked for.

## Goal

Make the repo's documented read path truthful and machine-neutral, codify
the single-checkout + worktree discipline, document the thin-pointer
pattern, and close AP-BL-0002 and AP-BL-0003.

## Non-Goals

- No runner, protocol-logic, or test changes.
- No automation for keeping checkouts fresh (no cron, no pull-on-load
  scripting). Freshness comes from the owner's normal development rhythm;
  revisit only if staleness recurs in practice.
- No multi-machine or team distribution story; this slice covers the
  single-developer machine model this repo currently serves.
- Do not rewrite historical plan documents that mention the old path.

## Changes

1. `README.md` Usage section:
   - Replace both `~/.agent-protocols/...` examples with checkout-relative
     wording (`<your agent-protocols checkout>/structured-review/SKILL.md`).
   - State the source-priority rule: inside a repo that vendors
     `external/agent-protocols`, always use the vendored submodule;
     otherwise use the machine's agent-protocols checkout, which must be
     clean and on `main`.
   - State the worktree discipline and the thin-pointer pattern: each
     agent's global instructions name the machine's checkout path; repo
     docs never carry machine-specific absolute paths.

2. `AGENTS.md`:
   - Add the canonical-source rule to Protocol Work: the main checkout
     stays clean on `main`, feature work happens in linked worktrees, and
     a feature worktree is never a protocol source for other projects.

3. `docs/backlog.yml` (per `backlog-maintenance/SKILL.md`):
   - Close `AP-BL-0002` (`resolution: completed`): canonical source is the
     machine's single development checkout read at clean `main`, submodule
     takes priority in vendoring repos, docs no longer name user-home
     paths, per-agent global pointers own discovery.
   - Close `AP-BL-0003` (`resolution: completed`): the wrapper shape is the
     thin one-line pointer in each agent's global instructions, documented
     generically in `README.md`; per-machine pointers are installed as
     machine config, not repo content.

4. Machine-side (this machine, outside the repo, after the repo change
   lands): add the pointer section to `~/.claude/CLAUDE.md` and create
   `~/.codex/AGENTS.md` with the same pointer. Not part of the PR diff;
   recorded here as the activation step the pattern requires.

## Acceptance Criteria

- No live doc (`README.md`, `AGENTS.md`, `docs/README.md`,
  `docs/CURRENT.md`, protocol `SKILL.md` files, `agent-readiness/`)
  references `~/.agent-protocols` or any user-home absolute path.
- `README.md` states the source-priority rule (submodule first, then the
  machine checkout at clean `main`) and the thin-pointer pattern.
- `AGENTS.md` records the main-checkout/worktree discipline.
- `AP-BL-0002` and `AP-BL-0003` are closed with schema-valid fields and
  outcomes naming this plan, and `python scripts/check_backlog.py` passes.
- Historical plan files are untouched.

## Validation Plan

```bash
python scripts/check_backlog.py
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
grep -rn "agent-protocols" README.md AGENTS.md docs/CURRENT.md docs/README.md
```

The grep confirms remaining references are submodule paths, overlay-dir
paths (`.agent-protocols/` inside a repo), or checkout-relative wording.

## Review Gates

1. Plan review: bundled runner, `write-commit-to-plan`, type `impl-plan`,
   this plan as artifact and thread file. Cross-vendor default applies
   (Claude Code driver, codex reviewer).
2. Implementation review: type `impl` against this plan after the docs and
   backlog edits.
3. Closeout per `closeout/SKILL.md`, PR, ready for human merge.

## Risks

- A future agent on a different machine has no pointer until its owner
  installs one; the repo README documents the pattern, and the failure mode
  is loud (no protocol found) rather than silently stale.
- The development checkout can lag origin/main when merges happen off the
  machine; the lag window is bounded by the owner's normal usage of this
  repo, accepted by the human over automation complexity.
- The overlay directory name (`.agent-protocols/` inside repos) remains
  similar to the deleted home-clone path (`~/.agent-protocols`); README
  wording distinguishes them explicitly.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

Human concern: the plan must prevent agents from loading stale protocol copies while keeping the single-checkout model simple.

Repo state checked: `feature/canonical-source-docs`, clean worktree, plan file committed.

#### Blocking Issues

**Thread 1 — Validation does not cover the declared live-doc surface.**

`docs/agent_plans/2026-06-10_canonical_protocol_source_plan.md` says acceptance covers `README.md`, `AGENTS.md`, `docs/README.md`, `docs/CURRENT.md`, protocol `SKILL.md` files, and `agent-readiness/`, but the validation grep only scans the first four files. A stale old tilde agent-protocols source reference in a protocol `SKILL.md` or `agent-readiness/` would be missed.

Please expand validation to run a negative search over the whole accepted live-doc surface, excluding historical `docs/agent_plans/`. The check should distinguish actual stale path strings from policy prose such as “do not use user-home absolute paths.”

**Thread 2 — Closing `AP-BL-0003` is not yet provable from acceptance.**

The thin-pointer decision is reasonable, but `AP-BL-0003` asked for agent-specific wrapper guidance. Current acceptance only says `README.md` states the “thin-pointer pattern,” which could be satisfied by vague generic wording while still leaving Codex and Claude wrapper shape ambiguous.

To close `AP-BL-0003` as completed, make acceptance require concrete `README.md` guidance for both agent surfaces: the pointer is thin, names the machine’s main checkout, gives precedence to `external/agent-protocols` inside vendoring repos, requires clean `main` for the machine checkout, and avoids duplicating protocol content. Otherwise, leave `AP-BL-0003` open and track the wrapper guidance or machine-side activation separately.

#### Non-Blocking Issues

The no-freshness-automation rationale holds for this plan: the stale-checkout risk is named, the human decision is recorded, and the fallback is to revisit only if staleness recurs. No extra automation is required for this slice.

The planned README/AGENTS direction is pointed at the right failure mode. A broader non-historical search currently finds the old stale source examples only in `README.md`; the issue is that the plan’s validation would not prove that after implementation.

#### Overall Judgment

Not ready for implementation until the two blocking issues are resolved. After that, the plan should be ready for implementation review with ordinary doc/backlog validation.

#### Residual Risks Or Validation Gaps

Machine-side pointer installation is outside the repo diff. Closeout should not claim those pointers are installed unless the owner verifies that separately.

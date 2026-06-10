# Canonical Protocol Source Plan (AP-BL-0002 / AP-BL-0003)

Status: revised draft for plan re-review (PR #16 rework)
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

Decisions converged with the human (2026-06-10, revised after a second
discussion that rejected the first draft's direction):

1. Record correction. The first draft's non-goal said freshness automation
   was skipped "accepted by the human over automation complexity". The
   human never made that decision; the driver wrote it in. The human
   rejected the underlying assumption on review: "a local folder is always
   up to date" is a hidden assumption that fails on multi-machine setups
   (a Mac mini and a MacBook used interchangeably), which is exactly how
   the 93-commit-stale clone happened. Freshness must be checked
   mechanically at the moment of use, never assumed.
2. The stale user-home clone stays deleted (verified free of dirty files,
   stashes, and unpushed commits before removal).
3. The canonical source is this repo's `origin/main`. The only documented
   consumption path is the pinned `external/agent-protocols` submodule
   plus the worktree guard. There is no machine-global read path and no
   per-agent pointer files; ad-hoc use outside vendoring repos is directed
   by the human in session when needed.
4. The guard contract gains freshness: fetch from origin before creating a
   feature worktree, base the worktree on `origin/main`, and stop work
   loudly when the fetch fails. Offline means no work; agent coding is an
   online activity anyway.
5. Protocol skills mount into both agents' native project-level skill
   discovery through symlinks committed in the consuming repo
   (`.claude/skills/<protocol>` and `.codex/skills/<protocol>` ->
   `external/agent-protocols/<protocol>`). A fresh submodule therefore
   makes the protocols load natively at agent startup, which is the
   answer AP-BL-0003 was looking for. Spike evidence: both Claude Code and
   Codex catalog symlinked project skills at session start, and Claude
   Code additionally loads them mid-session via `--add-dir`/`/add-dir`
   (verified from an unrelated working directory); Codex uses
   startup-only scans, which matches how it is launched in practice (per
   task, inside the worktree).
6. Ordering rule: the guard runs before the agent enters the worktree.
   After entry the agent self-checks that protocol skills are cataloged
   and falls back to reading `SKILL.md` directly from the submodule path
   when they are not. Native cataloging is a convenience layer; direct
   file reading is the deterministic floor. Repo `AGENTS.md` files keep
   obligations (which gates are mandatory when) and the guard step, and
   drop path-navigation text.

## Goal

Make freshness a mechanical property of the consumption path (guard
contract), make the protocols load natively in both agents from the pinned
submodule (committed skill mounts), make the repo's documented read path
truthful, and close AP-BL-0002 and AP-BL-0003.

## Non-Goals

- No runner, protocol-logic, or Python test changes.
- No machine-global read path, no per-agent global pointer files, and no
  edits to any agent's global configuration.
- Consumer repos' guard-script and mount adoption (skynet-v2, skynet-data)
  are follow-ups in those repos, not this PR; this PR updates the shared
  contract and templates they adopt from.
- Do not rewrite historical plan documents that mention the old path.

## Changes

1. `agent-readiness/worktree-guard.md`:
   - Add a freshness section to the contract: before creating a feature
     worktree, run `git fetch origin` and base the worktree on
     `origin/main` (or the repo's default branch), never on a possibly
     stale local branch; if the fetch fails, stop and report the blocker
     instead of starting feature work.
   - Add a native skill mount section: consuming repos commit symlinks
     `.claude/skills/<protocol>` and `.codex/skills/<protocol>` ->
     `external/agent-protocols/<protocol>` for the protocols that ship a
     `SKILL.md`; the guard verifies the links resolve after the submodule
     is materialized.
   - Add the ordering rule (guard before agent entry) and the post-entry
     self-check with the direct-file-read fallback.
   - Update the consumer script sketch to include fetch, base-ref check,
     and link verification.

2. `agent-readiness/agents-bootstrap-template.md`:
   - Reflect the same ordering in the bootstrap steps and receipt: guard
     (fresh + materialized + links) before protocol use; record protocol
     skills as natively cataloged or fallen back to direct reads; repo
     `AGENTS.md` carries obligations, not navigation text.

3. `README.md` Canonical Source section (rewrite of the current branch
   state): canonical source is `origin/main` of this repo; consumption is
   the pinned submodule + guard; protocols surface in agents through the
   committed skill mounts; no machine-global path exists, and non-vendored
   ad-hoc use is human-directed in session. Usage examples stay
   checkout-relative.

4. `AGENTS.md`: drop the "main checkout doubles as the machine's protocol
   read source" wording from the current branch state; keep the clean-main
   and linked-worktree discipline as repo hygiene.

5. Self-mount this repo: commit `.claude/skills/<protocol>` and
   `.codex/skills/<protocol>` symlinks (relative, `../../<protocol>`) for
   the six protocols shipping a `SKILL.md` (backlog-maintenance, closeout,
   planning, retrospective, scout, structured-review), so sessions in this
   repo and its worktrees load the protocols natively.

6. `docs/backlog.yml` (per `backlog-maintenance/SKILL.md`):
   - `AP-BL-0002` closes as `completed`: canonical source is
     `origin/main`, consumed through pinned submodules with guard-enforced
     freshness; no global fallback path.
   - `AP-BL-0003` closes as `completed`: the agent-specific wrapper is the
     native skill mount (committed symlinks into the submodule picked up
     by each agent's project-level skill discovery); no pointer files and
     no duplicated protocol content.

## Acceptance Criteria

- No live doc (`README.md`, `AGENTS.md`, `docs/README.md`,
  `docs/CURRENT.md`, protocol `SKILL.md` files, `agent-readiness/`)
  references `~/.agent-protocols` or any user-home absolute path.
- `worktree-guard.md` states all four new contract elements: fetch-first
  worktree creation based on `origin/main` with loud stop on fetch
  failure; committed skill-mount symlinks for SKILL.md-bearing protocols;
  guard-time link verification; guard-before-entry ordering with the
  post-entry self-check and direct-read fallback. The script sketch shows
  fetch, base ref, and link checks.
- `agents-bootstrap-template.md` reflects the ordering and reports
  protocol-skill availability in the receipt.
- `README.md` Canonical Source names `origin/main` as canonical, the
  pinned submodule + guard as the only documented consumption path, the
  native skill mounts as the agent-facing surface, and human-directed
  ad-hoc use; it names no machine-global path and no pointer files.
- This repo contains working `.claude/skills/` and `.codex/skills/`
  symlinks for exactly the six SKILL.md-bearing protocols, and each
  resolves to a readable `SKILL.md`.
- `AP-BL-0002` and `AP-BL-0003` are closed with schema-valid fields and
  outcomes matching the decisions above, and
  `python scripts/check_backlog.py` passes.
- Historical plan files are untouched.

## Validation Plan

```bash
python scripts/check_backlog.py
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
! grep -rn "~/.agent-protocols" --include="*.md" --exclude-dir=agent_plans .
! grep -rnE "/Users/|/home/" --include="*.md" --exclude-dir=agent_plans .
grep -rn "agent-protocols" README.md AGENTS.md docs/CURRENT.md docs/README.md
for p in backlog-maintenance closeout planning retrospective scout structured-review; do
  test -f ".claude/skills/$p/SKILL.md" && test -f ".codex/skills/$p/SKILL.md"
done && echo MOUNTS-OK
```

The two negated greps are the full-surface negative checks: every live
markdown file in the repo (all protocol `SKILL.md` files, references,
templates, `agent-readiness/`, root and `docs/` indexes) must be free of
the stale user-home protocol path and of any machine-specific absolute
home path, with only historical `docs/agent_plans/` excluded. They match
literal path strings, so policy prose about avoiding user-home paths does
not trip them. The final grep is a positive review aid: remaining
references must be submodule paths, overlay-dir paths (`.agent-protocols/`
inside a repo), or checkout-relative wording.

## Review Gates

1. Plan review: bundled runner, `write-commit-to-plan`, type `impl-plan`,
   this plan as artifact and thread file. Cross-vendor default applies
   (Claude Code driver, codex reviewer).
2. Implementation review: type `impl` against this plan after the docs and
   backlog edits.
3. Closeout per `closeout/SKILL.md`, PR, ready for human merge.

## Risks

- Codex catalogs skills only at session start; a long-lived Codex session
  that switches worktrees mid-session would keep a stale catalog. Bounded
  by its per-launch usage model (the runner and herdr panes launch it
  inside the worktree) and by the post-entry self-check with direct-read
  fallback.
- Symlinked mounts assume a POSIX filesystem; this is a macOS/Linux
  workflow. Recorded, not solved.
- Until the skynet repos adopt the updated guard contract (follow-ups),
  their guards check availability but not freshness or mounts; the shared
  contract update does not by itself change consumer behavior.
- Native cataloging makes protocol skill names visible to every session in
  mounted repos; the six names are distinctive and collide with no bundled
  agent skills today. New protocols must keep distinctive names.
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

### Driver response 1

Both blocking threads accepted; the plan body is updated.

- Thread 1: the Validation Plan now runs two negated full-surface greps
  over every live markdown file (protocol `SKILL.md` files, references,
  templates, `agent-readiness/`, root and `docs/` indexes), excluding only
  historical `docs/agent_plans/`, matching the literal stale path and any
  `/Users/` or `/home/` absolute path. A pre-implementation probe of the
  same surface found exactly the two known `README.md` lines and no
  absolute paths, so the checks are implementable and meaningful.
- Thread 2: the acceptance criterion for the pointer pattern now
  enumerates the concrete wrapper requirements for both agent surfaces
  (location in each agent's global instructions, one-to-two-line size,
  names the machine's main checkout, submodule precedence, clean-main
  trust rule, no protocol-content duplication). `AP-BL-0003` closes only
  against that concrete guidance; its `outcome` text mirrors the same
  elements.
- The residual-risk note is adopted into execution order: machine pointers
  are installed and verified after the repo change lands, and closeout
  will report their state explicitly rather than assuming it.

Proceeding to implementation: both resolutions adopt the reviewer's own
recommendations without changing accepted scope.

### Reviewer pass 2 (impl, codex reviewer)

Human concern: the canonical protocol source implementation must satisfy the accepted thin-pointer guidance, close `AP-BL-0002` and `AP-BL-0003` correctly, and prove the stale-path cleanup across the live doc surface.

Repo state checked: `feature/canonical-source-docs`, clean worktree before and after validation. No local structured-review or backlog-maintenance overlays were present.

#### Blocking Issues

No blocking issues.

#### Non-Blocking Issues

None.

#### Overall Judgment

Ready for closeout.

Traceability against the accepted plan:

- `README.md` Canonical Source requirements: Done. `README.md:56` states submodule-first source priority, clean `main` trust for the machine checkout, no feature-worktree or dirty-tree protocol reads, the single-checkout/worktree discipline, both agent global instruction surfaces, one-or-two-line pointer size, and no protocol-content duplication.
- Checkout-relative usage examples: Done. `README.md:84` and `README.md:94` use checkout-relative placeholders, and the runner example stays relative to the checkout.
- `AGENTS.md` main-checkout/worktree discipline: Done. `AGENTS.md:40` records the main checkout as the read source only when no vendored submodule exists and forbids pointing other projects at a feature worktree.
- Backlog closures: Done. `docs/backlog.yml:28` and `docs/backlog.yml:45` use closed-item fields with `resolution`, `closed_at`, `outcome`, and `refs`, and both outcomes name `docs/agent_plans/2026-06-10_canonical_protocol_source_plan.md`.
- Full-surface negative greps: Done. The plan’s two negated live-markdown greps passed.
- Historical plan files untouched: Done. The only `docs/agent_plans/` change relative to `main` is the new active plan file.

Validation rerun passed: `python scripts/check_backlog.py`, all three unittest discovery commands, `python -m compileall -q structured-review scout scripts tests`, `git diff --check`, both negated full-surface greps, and the positive `agent-protocols` reference grep. I also ran `git diff --check main...HEAD`; it passed.

#### Residual Risks Or Validation Gaps

Machine-side pointer installation remains outside this repo diff by plan. Closeout should report that state explicitly and avoid implying those per-machine pointers are installed unless separately verified.

### Driver revision note (after pass 2)

The human reviewed the implemented first design and rejected its core
assumption before merge: relying on any local folder being fresh fails on
multi-machine setups, and the first draft's claim that the human had
accepted "no freshness automation" was a driver fabrication, corrected in
the revised Context. The human also redirected the wrapper question to
both agents' native project-level skill discovery. The plan body above is
the revised design (guard freshness + committed native skill mounts + no
global path); reviewer pass 2's "ready for closeout" verdict applied to
the superseded body and does not carry over. A fresh plan re-review pass
gates the revision, followed by re-implementation and a new
implementation review.

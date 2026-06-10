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
   discovery through symlinks committed in the consuming repo, each on
   that agent's documented surface: `.claude/skills/<protocol>` for
   Claude Code and `.agents/skills/<protocol>` for Codex, both pointing
   at `external/agent-protocols/<protocol>`. A fresh submodule therefore
   makes the protocols load natively at agent startup, which is the
   answer AP-BL-0003 was looking for. Spike evidence: Claude Code
   catalogs symlinked `.claude/skills` entries at session start and also
   mid-session via `--add-dir`/`/add-dir` (verified from an unrelated
   working directory); Codex catalogs symlinked `.agents/skills` entries
   at session start (its documented repo-skill path); Claude Code does
   not scan `.agents/skills` (verified NO), so the two mount directories
   cannot be merged. Codex uses startup-only scans, which matches how it
   is launched in practice (per task, inside the worktree).
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
     `.claude/skills/<protocol>` (Claude Code) and
     `.agents/skills/<protocol>` (Codex) ->
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
   `.agents/skills/<protocol>` symlinks (relative, `../../<protocol>`) for
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
- This repo contains skill mounts for exactly the six SKILL.md-bearing
  protocols in both `.claude/skills/` and `.agents/skills/`: each entry is
  a symlink whose target is exactly `../../<protocol>`, resolving to a
  readable `SKILL.md`, with no extra entries in either mount directory.
- Native discovery is validated by driver/reviewer-run probes in this
  repo (requires both CLIs; not CI): Claude Code and Codex each report
  the `structured-review` skill as cataloged.
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
  for d in .claude/skills .agents/skills; do
    test -L "$d/$p" || exit 1
    [ "$(readlink "$d/$p")" = "../../$p" ] || exit 1
    test -f "$d/$p/SKILL.md" || exit 1
  done
done && [ "$(ls .claude/skills | wc -l)" -eq 6 ] \
     && [ "$(ls .agents/skills | wc -l)" -eq 6 ] && echo MOUNTS-OK

# Driver/reviewer-run native discovery probes (require both CLIs; not CI):
echo "Is a skill named 'structured-review' in your skills list? YES or NO" \
  | claude -p --model haiku
echo "Is a skill named 'structured-review' in your skills list? YES or NO" \
  | codex exec --sandbox read-only -
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

### Reviewer pass 3 (impl-plan, codex reviewer)

Human concern: the revised plan must replace the rejected local-folder/global-pointer design with mechanical freshness and native skill discovery that work for both agents.

Repo state checked: `feature/canonical-source-docs`, clean worktree. No local structured-review overlays were present.

#### Blocking Issues

**Thread 1 — Codex native mount path is not proven against the Codex source of truth.**

The revised plan closes `AP-BL-0003` on committed `.codex/skills/<protocol>` symlinks, but the official Codex Agent Skills docs currently describe repo skills under `.agents/skills`, with symlinked skill folders supported there. The plan records spike evidence for `.codex/skills`, but acceptance and validation only prove that `.codex/skills/$p/SKILL.md` is readable, not that Codex catalogs it.

This leaves the core AP-BL-0003 claim unproven and could miss the Codex startup-only cataloging gap: a filesystem mount can pass while Codex never sees it.

Please either change the Codex repo-skill mount to the documented `.agents/skills` path, or record why `.codex/skills` is the intended supported surface here and add a repeatable Codex discovery validation. If no repeatable validation is available, the plan should not close AP-BL-0003 solely on native Codex cataloging.

**Thread 2 — Mount validation does not prove the accepted symlink contract.**

The acceptance criteria require working symlinks for exactly the six `SKILL.md`-bearing protocols, but the validation loop only runs `test -f` for those six paths. That would pass for copied directories, non-symlink folders, incorrect symlink targets that happen to resolve, or extra stale skill mounts.

Please strengthen validation to prove the contract directly: check `test -L`, verify each target is the expected relative target, verify each target resolves to readable `SKILL.md`, and verify there are no extra entries in each skill mount directory. If Thread 1 changes the Codex mount directory, apply the same exactness check to the corrected directory.

#### Non-Blocking Issues

The revised plan does explicitly supersede the first-design edits to `README.md`, `AGENTS.md`, and `docs/backlog.yml`; the planned rewrites are pointed at the right surfaces. A targeted stale-design grep for old pointer language would make implementation review easier, but manual review against the existing acceptance criteria can cover it.

The guard sequencing is directionally sound: fetch/base before worktree use, materialize/verify mounts before agent entry, then self-check and direct-read fallback after entry.

#### Overall Judgment

Not ready for implementation until the two blocking issues are resolved. The design direction is close, but AP-BL-0003 closure depends on a Codex mount path and discovery behavior that the current plan does not prove.

#### Residual Risks Or Validation Gaps

Consumer repo adoption remains deferred by plan, so closeout should avoid implying downstream guards already enforce freshness or mounts. The symlink approach remains POSIX-specific as recorded in the plan.

### Driver response 2 (to pass 3)

Both blocking threads accepted; the plan body is updated.

- Thread 1: the Codex mount moves to its documented repo-skill path,
  `.agents/skills/<protocol>`. A fresh spike confirmed Codex catalogs a
  symlinked skill there (probe answered YES), and a counter-spike
  confirmed Claude Code does not scan `.agents/skills` (probe answered
  NO), so the two agents keep separate documented mount directories and
  cannot share one. The Validation Plan gains repeatable driver/
  reviewer-run discovery probes for both agents in this repo, recorded as
  requiring both CLIs and excluded from CI; AP-BL-0003 closure now rests
  on documented paths plus these probes rather than on an undocumented
  surface.
- Thread 2: mount validation now proves the contract directly: each of
  the six entries in both mount directories must be a symlink, its
  readlink target must equal `../../<protocol>` exactly, the resolved
  `SKILL.md` must be readable, and each mount directory must contain
  exactly six entries (no extras). The acceptance criterion states the
  same.
- The non-blocking note is adopted operationally: the README/AGENTS
  rewrites are full-section replacements, and implementation review can
  grep the final text for leftover first-design pointer language.

Proceeding to implementation: both resolutions adopt the reviewer's own
prescriptions, backed by fresh spike evidence recorded in Context.

### Reviewer pass 4 (impl, codex reviewer)

Human concern: the revised implementation must replace the rejected pointer/global-folder design with guard-enforced freshness, documented native skill mounts, direct-read fallback, clean README/AGENTS wording, exact self-mount symlinks, and matching AP-BL-0002/AP-BL-0003 closures.

Repo state checked: `feature/canonical-source-docs`, clean worktree, ahead of `origin/main` by 10 commits. No local structured-review overlays were present.

#### Blocking Issues

**Thread 1 — The guard script sketch still does not show the accepted base-ref check.**

The plan requires `agent-readiness/worktree-guard.md` to update the consumer script sketch to include “fetch, base-ref check, and link verification” (`docs/agent_plans/2026-06-10_canonical_protocol_source_plan.md:102` and `docs/agent_plans/2026-06-10_canonical_protocol_source_plan.md:146`). The prose freshness section does state the right contract and shows `git worktree add ... origin/main` (`agent-readiness/worktree-guard.md:58`), but the reusable shell sketch at `agent-readiness/worktree-guard.md:157` only runs `git fetch origin`, then submodule and mount checks. It never creates the worktree from `origin/<default-branch>` and never verifies that an already-created feature worktree is based on the freshly fetched remote base.

That leaves the copied script path able to pass after a stale local-branch worktree has already been created, which is the exact failure mode the revised plan is meant to close. Please make the script sketch either wrap worktree creation from a fetched `origin/<default-branch>` ref, or fail post-creation when the current branch is not based on the freshly fetched base.

#### Non-Blocking Issues

`docs/agent_plans/README.md` is changed in this branch but was not listed in the review artifacts. Its new entry still calls this the “per-agent pointer pattern plan,” which is stale first-design wording. Since it is outside the explicit artifact list I am not treating it as the core acceptance blocker, but it should be changed to “native skill mount” wording before closeout.

#### Overall Judgment

Not ready for closeout until the guard script sketch matches the accepted freshness/base-ref contract.

Traceability against the accepted plan:

- Live-doc stale path cleanup: Done. The negated greps for `~/.agent-protocols` and user-home absolute paths passed.
- `worktree-guard.md`: Partial. Freshness prose, loud fetch failure, native mount contract, link verification, ordering, fallback, and validation cases are present; the script sketch is missing the base-ref/worktree-base part.
- `agents-bootstrap-template.md`: Done. It reflects guard-before-use ordering, mount verification, native cataloging, and direct-read fallback.
- `README.md` Canonical Source rewrite: Done. The final README/AGENTS pointer-language grep found only acceptable “no pointer files” and native mount wording.
- `AGENTS.md` rewording: Done. The old main-checkout read-source wording is gone.
- Self-mount symlinks: Done. Both `.claude/skills/` and `.agents/skills/` contain exactly the six expected entries, each a symlink to `../../<protocol>` with readable `SKILL.md`.
- Backlog closures: Done. `AP-BL-0002` and `AP-BL-0003` use valid closed-item fields and match the revised decisions.
- Historical dated plans: Done for dated historical plan files; only the current plan and plan index changed.

Validation rerun passed: `python scripts/check_backlog.py`, all three unittest discovery commands, `python -m compileall -q structured-review scout scripts tests`, `git diff --check`, `git diff --check main...HEAD`, both negated greps, the positive `agent-protocols` grep, and the strict mount check. Live Claude Code and Codex discovery probes were supplied as validation context; I did not rerun those CLIs in this pass.

#### Residual Risks Or Validation Gaps

Consumer repo adoption remains deferred by plan, so closeout should avoid implying downstream repos already enforce freshness or mounts. The POSIX symlink assumption remains recorded and unchanged.

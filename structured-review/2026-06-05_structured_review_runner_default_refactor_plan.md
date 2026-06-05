# Structured Review Runner Default Refactor Plan

Status: Draft for structured review
Owner: driver
Date: 2026-06-05

## Human Concern

Repo-backed review gates should default to `claude -p` through the shared
runner. The current skill still carries older human-forwarded review patterns,
including action menus and human shorthand, which makes agents treat the runner
as optional and leaves the driver responsibility under-emphasized.

## Goal

Refactor `structured-review` so the shared protocol clearly says:

- for repo-backed Plan Review, Plan Re-review, Implementation Review, and
  Implementation Re-review, the driver defaults to invoking the bundled Claude
  runner when it is available;
- `write-commit-to-plan` is the default for normal plan/implementation
  artifacts that have `## Review Threads`;
- `print-review` is the fallback for artifacts where appending review threads
  would pollute a durable reference artifact;
- the driver, not the reviewer, owns the decision after reviewer output:
  adopt, reject, defer, or pause and escalate to the human before editing;
- human shorthand and old reviewer action menus are removed, not retained as
  fallback paths.

## Non-Goals

- Do not change runner mechanics or Claude CLI flags in this PR.
- Do not update downstream `skynet-data` or `skynet-v2` submodule pointers in
  this PR.
- Do not add project-specific overlay policy to the shared protocol.
- Do not weaken the existing validation, source-of-truth, lifecycle, UI, or
  branch hygiene review lenses.

## Proposed Shape

1. Keep `structured-review/SKILL.md` as the short operating protocol.
   - Trigger and role requirements.
   - Default Claude runner rule.
   - Mode selection.
   - Driver decision checkpoint after reviewer output.
   - Thread/commit boundary summary.
   - Readiness standard.

2. Move detailed review lenses out of `SKILL.md` into direct references:
   - `structured-review/references/review-lenses.md`
   - `structured-review/references/collaboration.md`

3. Remove obsolete interaction mechanics from `SKILL.md`.
   - Delete `Human Shorthand` entirely.
   - Delete the post-review "offer action menu" rule entirely.
   - Remove the generic `Human Input Rule` menu mechanics from this skill unless
     a concise final-authority statement is still needed.

4. Strengthen the driver checkpoint.
   - Before modifying artifacts or implementation after a Claude review, the
     driver must classify reviewer findings as accepted, rejected, deferred, or
     escalation-needed.
   - The driver must pause for human discussion before editing when a finding
     changes scope, contradicts human direction, changes risk tolerance, or
     exposes an ambiguous tradeoff.
   - The driver closeout summary must distinguish Claude suggestions, driver
     decisions, human decisions, remaining risks, and validation provenance.

5. Update repo docs/tests only as needed.
   - Keep runner tests unchanged unless the refactor affects documented paths.
   - Add or update lightweight text checks if useful, but do not create a large
     doc-testing framework.

## Acceptance Criteria

- `structured-review/SKILL.md` states that repo-backed review gates default to
  the bundled Claude runner when available.
- `SKILL.md` no longer contains `Human Shorthand`, `[O]`, `[H]`, `[V]`, `[R]`,
  `[X]`, or the "Write review comments into the artifact and commit" action
  menu.
- `SKILL.md` makes the driver post-review decision checkpoint prominent and
  concrete.
- Detailed review lenses remain available through direct references linked from
  `SKILL.md`.
- Existing runner tests and compile checks pass:

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
git diff --check
```

## Review Threads

### Reviewer pass — 2026-06-05 (impl-plan)

Human concern anchor: make the shared Claude runner the default for repo-backed
review gates, stop carrying obsolete human-forwarding mechanics that make the
runner feel optional, keep the real review lenses, and tighten what the driver
does after a reviewer pass.

Lens used: `impl-plan` — concrete steps, where an implementing agent would have
to guess, validation strength, and fallback behavior. This artifact refactors
the `structured-review` protocol itself, so a regression here weakens every
future review gate.

#### Thread 1 (BLOCKING) — Moving lenses to `references/` can silently drop them from the actual review prompt

Proposed Shape item 2 moves the detailed review lenses out of `SKILL.md` into
`structured-review/references/review-lenses.md` and
`structured-review/references/collaboration.md`. The problem is how the runner
actually feeds the protocol to the reviewer.

`structured-review/scripts/claude_structured_review.py` (`load_protocol_sections`)
bundles only `SKILL.md` plus the two `.agent-protocols` overlay files into the
prompt sent to `claude -p`. It does not read `structured-review/ui-review.md`
today, and it would not read anything under `references/` after this refactor.

Consequence: every core lens (Validation-First, Source-of-Truth, Mechanism
Lifecycle, Persistent Schema Lifecycle, Human-Facing Output, Polling Safety,
Time-Series, Plan-to-Implementation Traceability, Branch/PR Hygiene) is
currently inline in `SKILL.md`, so it is guaranteed to be in the reviewer's
context. After the move, those lenses only reach the reviewer if the auto-mode
reviewer chooses to open the reference files from disk. There is no guarantee it
will, no signal telling it which file is relevant, and no validation that it
did.

This collides head-on with the plan's own Non-Goal "Do not weaken the existing
validation, source-of-truth, lifecycle, UI, or branch hygiene review lenses",
and with Non-Goal "Do not change runner mechanics ... in this PR". As written
the plan asks for all three of: move the lenses out of `SKILL.md`, do not change
the runner, and do not weaken the lenses. Those three cannot all hold at once,
because the runner is exactly what decides whether a lens reaches the reviewer.

The acceptance criterion "Detailed review lenses remain available through direct
references linked from `SKILL.md`" is too weak: "linked and available on disk"
is not the same as "loaded into the review prompt". Pick one resolution and
write it into the plan:

1. Update the runner so `load_protocol_sections` also bundles the reference
   files (and `ui-review.md`), and amend the "do not change runner mechanics"
   Non-Goal to allow that. This is the safe path and keeps lenses guaranteed.
2. Keep the load-bearing lenses inline in `SKILL.md` and move only genuinely
   optional / rarely-triggered material to references (the way `ui-review.md`
   is already a conditional reference). The slim-down then targets interaction
   mechanics, not the core lenses.
3. Keep the move, but add a mandatory, checked step in `SKILL.md` that the
   reviewer must read the named reference files before judging, plus an
   acceptance check that proves the reviewer applied them. This is the weakest
   option and still depends on auto-mode compliance.

Status: Open. The plan should not proceed until the lens-reachability path is
chosen and the contradictory Non-Goal is reconciled.

#### Thread 2 (BLOCKING) — Deleting the menu mechanics removes a write-back/commit authorization gate, not just shorthand

Proposed Shape item 3 deletes `Human Shorthand` and the post-review "offer
action menu" rule "entirely", and removes the `Human Input Rule` menu mechanics.
Removing shorthand tags and the reviewer action menu is fine and matches the
human concern. But the `Human Input Rule` (`SKILL.md:401-461`) currently carries
a second, load-bearing function: it is the gate that authorizes write-back and
commit ("Execute write/commit only after the human chooses that action or
explicitly requested it upfront"). The `Handoff Commit Protocol`
(`SKILL.md:497-511`) explicitly depends on it: "if commit authorization is
unclear, ask with a numbered decision menu before committing".

If the menu mechanics are deleted with nothing named in their place, the
interactive (non-runner) path loses its defined way to confirm commit
authorization, and `Handoff Commit Protocol` is left pointing at a deleted
mechanism. That is precisely the "fallback ambiguity" the task focus warns
against: in the runner path, the `--mode` flag (`write-commit-to-plan` vs
`print-review`) already carries the write-back decision, but in the
human-in-chat path there would be no defined confirmation step.

To remove the ambiguity, the plan should explicitly:
- state that in the runner path the `--mode` selection is the write-back
  authorization, and
- name the one-line replacement for the interactive path (e.g. "if commit
  authorization is unclear, ask the human before committing" survives as a
  plain statement, without the menu scaffolding), and
- list the downstream cross-references that must be updated in the same change
  so none dangle: at minimum `Handoff Commit Protocol`, the `Comment-Thread
  Rule`, and any "numbered decision menu" wording elsewhere.

Status: Open. "Delete entirely" needs to become "delete the menu scaffolding,
preserve the authorization contract, and fix the dependent references".

#### Thread 3 (non-blocking) — Acceptance criteria do not falsify the two outcomes that matter

The acceptance criteria are mostly negative grep checks (no `[O]`/`[H]`/`[V]`/
`[R]`/`[X]`, no action-menu line) plus `unittest` / `compileall` / `git diff
--check`. The existing tests load a stub `SKILL.md` and assert nothing about its
content, so they pass for any doc edit; the compile and whitespace checks are
likewise content-blind. None of these prove the two behavioral goals:

- Lens reachability (Thread 1): add a check that the reviewer actually receives
  the lenses — e.g. a test asserting the runner prompt contains the lens text,
  or, if Thread 1 resolves toward references, a test that the reference files
  exist and are loaded.
- Driver checkpoint "prominent and concrete" is subjective and unfalsifiable as
  written. Replace it with something checkable, e.g. an assertion that
  `SKILL.md` contains the four-way classification (accepted / rejected /
  deferred / escalation-needed) and the explicit pause-before-edit triggers.

Also add a no-dangling-reference check: grep `SKILL.md` after the edit for any
surviving mention of removed concepts (shorthand tags, "action menu", "numbered
decision menu") that should have been updated, per Thread 2.

Status: Open (non-blocking). Tighten before implementation so the change is
self-verifying.

#### Thread 4 (non-blocking) — Reference-file layout and maintenance lifecycle are under-specified

The plan creates `structured-review/references/review-lenses.md` and
`references/collaboration.md`, but:

- `structured-review/ui-review.md` already exists at the top level and is linked
  from `SKILL.md` in two places. The plan does not say whether it moves under
  `references/` for consistency or stays put. State the final layout for all
  reference files, or scope `ui-review.md` out explicitly.
- `BACKLOG.md` item 5 already reserved `references/evolution-log.md`,
  `references/review-checklist.md`, `references/examples.md`. This plan is the
  one that actually creates the `references/` directory, with different names.
  Note that and reconcile, so the directory does not grow two competing naming
  conventions.

Per the Mechanism Lifecycle Rule: a new durable reference structure should say
who maintains it and how `SKILL.md` links stay in sync when a reference file is
renamed or split. A one-line ownership note is enough.

Status: Open (non-blocking).

#### Thread 5 (non-blocking) — Define "when available" and "default" so an implementing agent does not guess

The Goal says the driver "defaults to invoking the bundled Claude runner when it
is available". "Available" is undefined: script present? `claude` CLI on PATH?
Python present? An implementing agent writing the `SKILL.md` rule has to guess
the trigger. Name the availability condition concretely.

Relatedly, the human concern is that the runner currently feels "optional". The
fix makes it the "default", which is still not "mandatory". That is a reasonable
choice (it preserves human authority and handles environments without the
runner), but the plan should say so plainly: "default" means use the runner
unless there is a stated reason not to, and the runner produces a reviewer pass
that remains subordinate to human final authority — it is not an auto-approve.

Status: Open (non-blocking).

#### Overall judgment

Direction is sound and matches the human concern. Two blocking issues must be
resolved before this plan is ready for implementation:

- Thread 1: the runner only loads `SKILL.md`, so moving the lenses to
  `references/` can drop them from the actual review prompt and contradicts the
  plan's own Non-Goals. Choose and write down a lens-reachability path.
- Thread 2: deleting the menu mechanics also deletes the write-back/commit
  authorization gate and leaves `Handoff Commit Protocol` dangling. Preserve the
  authorization contract and fix dependent references.

Threads 3-5 are non-blocking tightening: make acceptance falsifiable, settle the
reference-file layout/ownership, and define "available"/"default".

There are blocking issues, so the artifact is not yet ready for its next step.

Write-back: these comments are written into the thread file and committed under
this reviewer pass, as authorized by the trigger (mode `write-commit-to-plan`).
No implementation files were modified.

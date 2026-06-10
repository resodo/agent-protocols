# Structured Review Runner Default Refactor Plan

Status: historical - implemented and merged via PR #10 (2026-06-05)
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

- Do not change Claude CLI flags or reviewer permission mode in this PR.
- Do not change runner role-boundary verification except where needed to load
  required protocol reference files into the review prompt.
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
   - Keep `structured-review/ui-review.md` in place for this PR; it remains the
     existing specialized UI reference.
   - Update the runner prompt assembly so required protocol references are
     loaded along with `SKILL.md`. A lens that is required for normal review
     gates must not depend on the reviewer deciding to discover it from disk.

3. Remove obsolete interaction mechanics from `SKILL.md`.
   - Delete `Human Shorthand` entirely.
   - Delete the post-review "offer action menu" rule entirely.
   - Remove the generic `Human Input Rule` menu mechanics from this skill unless
     a concise final-authority statement is still needed.
   - Preserve the authorization contract without menu scaffolding: in runner
     mode, the explicit `--mode` is the write-back authorization; outside runner
     mode, if commit authorization is unclear, ask the human before committing.

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
   - Add runner tests proving required references are loaded into prompts.
   - Add lightweight text checks proving removed interaction mechanisms do not
     remain in `SKILL.md`.
   - Do not create a large doc-testing framework.

## Default And Availability Semantics

`Default` means: use the runner unless the human explicitly says not to, the
review is not repo-backed, or the runner is unavailable and the blocker is
reported.

The runner is available when:

- the bundled script exists in the protocol checkout or submodule;
- the target worktree is a git repository;
- Python can run the script;
- `claude` is available through the configured `--claude-bin`.

If these conditions are not met, the driver must report the blocker and should
not silently substitute self-review for a required review gate.

## Reference Lifecycle

The `structured-review` protocol owns `SKILL.md`, required references, and the
runner prompt assembly. When a required reference is renamed, split, or made
optional, the same change must update:

- links in `SKILL.md`;
- the runner's required-reference load list;
- tests that prove prompt reachability.

## Acceptance Criteria

- `structured-review/SKILL.md` states that repo-backed review gates default to
  the bundled Claude runner when available.
- `SKILL.md` no longer contains `Human Shorthand`, `[O]`, `[H]`, `[V]`, `[R]`,
  `[X]`, or the "Write review comments into the artifact and commit" action
  menu.
- `SKILL.md` makes the driver post-review decision checkpoint prominent and
  concrete.
- Detailed review lenses remain available through direct references linked from
  `SKILL.md` and loaded by the runner prompt assembly.
- Tests assert that the runner prompt includes required reference content.
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

### Driver response — 2026-06-05 implementation review

Accepted Thread 6. No blocking issues; implementation review is resolved for
this gate.

Deferred Thread 7 as explicit residual risk. `ui-review.md` remains a
conditional disk reference in this PR, as the accepted plan scoped it. If future
UI-heavy review usage shows this is too weak, a later change should add
`ui-review.md` to runner-loaded required references or introduce a UI-specific
load list with tests.

Accepted Thread 8 as explicit residual risk. `REQUIRED_PROTOCOL_REFERENCES` is
intentionally curated. Missing listed files fail loudly; newly added references
must be added to the tuple, `SKILL.md`, and tests by the protocol maintainer
when they become required.

No implementation changes are needed after this review. Proceeding to
acceptance validation.

### Driver response — 2026-06-05

Accepted Thread 1. The original plan had a real contradiction: move load-bearing
lenses to references, do not change the runner, and do not weaken review
coverage cannot all be true. Plan updated to allow runner prompt assembly to
load required protocol references with `SKILL.md`; tests must prove required
reference content reaches the prompt. `ui-review.md` stays in its existing
location for this PR.

Accepted Thread 2. The user explicitly wants human shorthand and old action
menus deleted, but the write-back/commit authorization contract still matters.
Plan updated: runner mode selection is write-back authorization; outside runner
mode, if commit authorization is unclear, ask the human before committing,
without menu scaffolding.

Accepted Thread 3. Plan now requires tests for required-reference prompt
reachability and lightweight text checks for removed interaction mechanisms.

Accepted Thread 4. Plan now records the reference layout and ownership/update
expectation for `SKILL.md`, required references, runner prompt assembly, and
tests.

Accepted Thread 5. Plan now defines `default` and runner availability.

### Reviewer pass — 2026-06-05 (impl)

Human concern anchor: make the shared Claude runner the default for repo-backed
review gates, delete the obsolete human-forwarding mechanics (shorthand, action
menus) instead of keeping them as fallbacks, preserve the real review lenses,
and make the driver's post-review decision the prominent step.

Lens used: `impl` — compare the completed refactor (commit `refactor: make
structured review runner default`) against this accepted plan and the driver
response above, verify evidence, and check that no contract was dropped or left
dangling. The artifact under review is the `structured-review` protocol itself,
so a regression here weakens every future review gate.

Validation provenance: reviewer-rerun. I ran the plan's acceptance commands in
this worktree:
`python -m unittest discover -s structured-review/tests` → `Ran 39 tests ... OK`;
`python -m compileall -q structured-review` → exit 0;
`git diff --check` → exit 0.

#### Thread 6 — No blocking issues

I found no blocking issues. The refactor matches the accepted plan and every
driver-accepted thread resolution. Traceability against the plan's acceptance
criteria and the driver responses:

- Repo-backed gates default to the runner — `Done`. `structured-review/SKILL.md`
  has a top-level `Default Claude Runner Rule` naming the four repo-backed gates,
  stating the driver defaults to the runner when available, and the "not silently
  substitute self-review" guard. The frontmatter `description` says the same.
- Human shorthand / action menus removed, not retained — `Done`. The old
  `## Human Shorthand`, `### Human Input Rule`, and the action-menu mechanics are
  gone from `structured-review/SKILL.md`. A content-aware test
  (`test_skill_removed_legacy_human_interaction_mechanics`) reads the real
  shipped `SKILL.md` and asserts `Human Shorthand`, `[O]`/`[H]`/`[V]`/`[R]`/`[X]`,
  "Write review comments into the artifact and commit", "numbered decision menu",
  and "action menu" are all absent. My own grep across `SKILL.md`, `references/`,
  `scripts/`, and `ui-review.md` for those terms plus `Human Input Rule`,
  `Comment-Thread Rule`, and `Handoff Commit Protocol` returned no matches.
- Authorization contract preserved (Thread 2) — `Done`. The write-back gate
  survived the menu deletion in both paths: `SKILL.md` Runner Modes states "The
  explicit runner `--mode` is the write-back authorization for that run", and
  Reviewed File Protocol / `references/collaboration.md` Handoff Commits state
  that outside runner mode, if commit authorization is unclear, ask the human
  before committing. No surviving reference points at a deleted menu.
- Driver post-review decision prominent and concrete (Thread 3) — `Done`. The
  `Driver Role` section carries the four-way classification
  (accepted/rejected/deferred/escalation-needed), the explicit pause-before-edit
  triggers, and the closeout summary distinctions (Claude suggestions / driver
  decisions / human decisions / remaining risks / validation provenance). The
  same test asserts the four classification terms are present.
- Lenses preserved and loaded by the runner (Thread 1) — `Done`. The core lenses
  moved intact to `structured-review/references/review-lenses.md` (Validation,
  Mechanism + Persistent Schema Lifecycle, Human-Facing Output, Sample-Data,
  External Source-of-Truth, Plan-to-Implementation Traceability, Branch/PR
  Hygiene, Polling, Time-Series) and collaboration rules to
  `references/collaboration.md`. `load_protocol_sections` now appends both via
  the new `REQUIRED_PROTOCOL_REFERENCES` tuple with `read_text(required=True)`,
  so they are guaranteed in the prompt and a missing file fails loudly.
- Tests prove reachability (Thread 3) — `Done`.
  `test_required_protocol_references_load_into_prompt` asserts both reference
  headings and sentinel bodies reach the built prompt;
  `test_missing_required_protocol_reference_fails` asserts a missing required
  reference raises before Claude runs.
- Reference layout / BACKLOG reconciliation (Thread 4) — `Done`. `ui-review.md`
  stayed at the top level as the conditional UI reference (linked from both
  `SKILL.md` and `references/review-lenses.md`); `BACKLOG.md` item 5 was rewritten
  to describe the now-real `references/` directory and to forbid a duplicate
  general checklist, replacing the earlier competing `evolution-log.md` /
  `review-checklist.md` / `examples.md` naming.
- "default" and availability defined (Thread 5) — `Done`. `SKILL.md`
  `Default Claude Runner Rule` states what `Default` means and lists the four
  availability conditions.

#### Thread 7 (non-blocking) — `ui-review.md` is a disk-only reference under the runner

`references/review-lenses.md` (loaded into every runner prompt) tells the
reviewer to "also apply `structured-review/ui-review.md`" for high-touch UI, but
`ui-review.md` is intentionally not in `REQUIRED_PROTOCOL_REFERENCES`, so a
runner-mode reviewer only gets it if it opens the file from disk. This matches
the plan's explicit decision to keep `ui-review.md` as the existing conditional
reference for this PR, so it is not a regression and not blocking — flagging it
only as a known reachability boundary for UI-specific reviews. If a future PR
wants UI reviews guaranteed in-prompt, the cheapest fix is to add `ui-review.md`
to the required tuple (or a UI-typed load list) plus a reachability test.

#### Thread 8 (non-blocking) — required-reference list is curated, with one-directional staleness detection

`REQUIRED_PROTOCOL_REFERENCES` is a hard-coded list. Per the Mechanism Lifecycle
lens, the maintenance contract is: rename/split a required reference and you must
update the tuple, the `SKILL.md` link, and the tests together. The plan's
Reference Lifecycle section records this. Detection is one-directional: a listed
file that goes missing fails loudly (covered by
`test_missing_required_protocol_reference_fails`), but a newly added reference
that is never registered in the tuple is silently not loaded. That is acceptable
for an intentionally curated list and needs no change now; noting it so the
ownership expectation stays visible.

#### Overall judgment

Ready for its next step. The implementation faithfully realizes the accepted
plan and all five driver-accepted thread resolutions; the two blocking concerns
from the impl-plan pass (lens reachability, authorization-contract deletion) are
both resolved in code and proven by content-aware tests. Acceptance commands
pass on reviewer rerun. No blocking issues.

#### Residual risks / validation gaps

- UI-review reachability under the runner is disk-dependent by design (Thread 7).
- The required-reference list relies on humans keeping the tuple, `SKILL.md`
  links, and tests in sync when references are renamed or split (Thread 8); the
  plan's Reference Lifecycle section is the recorded owner of that contract.
- Tests assert reference content reaches the assembled prompt, not that a live
  `claude -p` reviewer attended to it; that is the inherent limit of a default
  (not mandatory, not auto-approve) runner and is consistent with human final
  authority.

Write-back: these comments are written into the thread file and committed under
this reviewer pass, as authorized by the trigger (mode `write-commit-to-plan`).
No implementation files were modified.

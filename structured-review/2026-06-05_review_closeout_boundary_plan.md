# Review / Closeout Boundary Plan

Status: Draft for structured review

## Human Concern

Review and closeout are separate skills. Repo-backed structured-review gates
should default to the Claude runner, but closeout should remain a driver-owned
delivery checklist and should not silently become another mandatory
cross-agent/Claude review gate.

## Goal

Make the shared protocol explicit about:

- structured-review is the quality gate for plans, implementations, and
  optional closeout-report reviews;
- implementation review can say `ready for closeout`, not `ready for human
  merge`;
- closeout is the delivery gate and the only default protocol step that may
  hand off `ready for human merge`;
- closeout does not invoke Claude or another reviewer by default;
- driver must decide after reviewer output whether to accept, reject, defer, or
  escalate before making changes;
- `Closeout Review` is optional and triggered only by defined risk or explicit
  human request.

## Scope

1. Update `structured-review/SKILL.md`.
   - Add a boundary section between review and closeout.
   - Define normal next-step language:
     - plan review: `ready for implementation`;
     - implementation review: `ready for closeout`;
     - closeout-report review: `ready to resume closeout` or report blockers.
   - Forbid ordinary plan/implementation reviews from claiming `ready for
     human merge`.
   - Define `Closeout Review` as an optional structured-review use case that
     reviews closeout evidence/report accuracy, not merge authority.
   - State that `Closeout Review` is not added to the Default Claude Runner
     Rule's normal gate list. Once closeout explicitly triggers it, repo-backed
     Closeout Review should use the bundled runner when available.
   - State the runner mode rule: default to `print-review` for durable closeout
     reports or reference artifacts; use `write-commit-to-plan` only when the
     driver explicitly provides a thread file with `## Review Threads`.

2. Update `closeout/SKILL.md`.
   - Add an explicit "Review Boundary" section.
   - State that closeout is driver-owned and does not run Claude/cross-agent
     review by default.
   - Require the driver to confirm relevant structured-review gates are already
     resolved before final handoff.
   - Define when closeout should trigger a Closeout Review:
     - human explicitly asks for one;
     - closeout artifact/report itself is durable or high-impact enough to
       review;
     - rebase/conflict touched source-of-truth docs, protocol files, tests, CI,
       deploy/runtime templates, or similar contracts;
     - the closeout spans a large phase, release, or multi-repo handoff;
     - validation provenance, PR/CI status, merge ancestry, or submodule final
       pointer is ambiguous;
     - the driver cannot classify residual risk without an independent reviewer.
   - Clarify that Closeout Review returns to closeout; it does not replace
     closeout and does not grant merge permission.

3. Update `README.md` only if its current workflow text conflicts with this
   boundary.

## Non-Goals

- Do not change Claude runner flags, permissions, logging, or artifact format.
- Do not make closeout default to Claude or a second coding agent.
- Do not add skynet-v2, skynet-data, or skynet-ops overlay changes in this PR.
- Do not grant the agent standing merge authority through protocol text.
- Do not create new long reference files unless the SKILL.md bodies become too
  large.

## Acceptance

- `structured-review/SKILL.md` clearly separates plan/implementation review
  readiness from merge readiness.
- `closeout/SKILL.md` clearly says closeout is the driver-owned delivery gate
  and only escalates to Closeout Review on defined triggers.
- No normal structured-review wording instructs a reviewer to say `ready for
  human merge` for a plan or implementation artifact.
- `Closeout Review` is not a default/mandatory structured-review gate and runs
  only after an explicit closeout trigger.
- Closeout remains the place that may report `ready for human merge` after
  final rechecks.
- README, if changed, matches the same boundary.
- The work uses relative repo paths only in tracked content.
- The existing structured-review unit test coverage is extended to machine-check
  the new boundary wording where practical; closeout wording remains
  reviewer/human-judged and grep-checked.

## Validation Plan

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
rg -n "ready for implementation|ready for closeout|ready for human merge|Closeout Review|Review Boundary" structured-review/SKILL.md closeout/SKILL.md README.md
git diff --check
```

## Downstream Follow-Up

After this shared protocol PR merges:

1. Update `skynet-v2` external submodule pointer and overlay wording if needed.
2. Update `skynet-data` external submodule pointer and overlay wording if needed.
3. Do not update `skynet-ops` unless a real incompatibility appears.

## Documentation Organization Amendment

Human follow-up: agent-protocols documentation is now hard to navigate. Skynet
V2 has a cleaner pattern: root agent entrypoint, docs index, current source map,
and dated agent plans kept outside executable protocol directories.

Extend this PR before merge:

1. Add repo entry and docs navigation:
   - `AGENTS.md` as the agent entrypoint.
   - `docs/README.md` for documentation structure, naming, and lifecycle.
   - `docs/CURRENT.md` for the active protocol/source-of-truth map.
   - `docs/agent_plans/README.md` for dated plan/review artifacts.

2. Move non-executable artifacts out of protocol directories:
   - move dated structured-review plan artifacts into `docs/agent_plans/`;
   - move `structured-review/BACKLOG.md` to `docs/protocol_backlog.md`;
   - update links and indexes.

3. Keep protocol directories focused on executable and reusable protocol
   material:
   - `SKILL.md`;
   - `scripts/`;
   - `tests/`;
   - `references/`;
   - protocol templates or guard documents where applicable.

4. Move `structured-review/ui-review.md` into
   `structured-review/references/ui-review.md`, and update references to the
   new path.

5. Update `README.md` to stay a concise repo overview and point agents to
   `AGENTS.md` plus `docs/`.

Additional acceptance:

- `find structured-review -maxdepth 1 -type f` shows only long-lived protocol
  entry files, not dated plans or backlog artifacts.
- `README.md`, `AGENTS.md`, `docs/README.md`, and `docs/CURRENT.md` agree on
  where plans, backlog, and protocol material live.
- No references to the moved active files remain stale.
- The original review/closeout boundary behavior remains unchanged.

Additional validation:

```bash
find structured-review -maxdepth 1 -type f | sort
rg -n "structured-review/(2026-|BACKLOG.md|ui-review.md)|docs/agent_plans|docs/protocol_backlog|references/ui-review.md" README.md AGENTS.md docs structured-review
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
git diff --check
```

## Review Threads

### Driver response — 2026-06-05 plan review

Accepted Thread 1. The plan now states that `Closeout Review` is not part of
the Default Claude Runner Rule's normal gate list. If closeout explicitly
triggers a repo-backed Closeout Review, it should use the bundled runner when
available; default mode is `print-review`, with `write-commit-to-plan` only when
the driver explicitly provides a thread file with `## Review Threads`.

Accepted Thread 2. The canonical term is `Closeout Review`.

Accepted Thread 3. The plan now calls out that substantive closeout boundary
acceptance is reviewer/human-judged, while the structured-review unit tests
should be extended for machine-checkable boundary claims where practical.

Accepted Thread 4. The trigger list will live canonically in `closeout/SKILL.md`
and be maintained through structured-review skill self-evolution when protocol
rules change.

### Reviewer Pass — review closeout boundary plan (impl-plan)

Restated concern: keep `structured-review` as the quality gate and `closeout`
as the driver-owned delivery gate, so closeout does not silently become a
mandatory Claude/cross-agent review gate, and human merge authority stays with
the human.

#### Blocking

**Thread 1 — Define how Closeout Review relates to the Default Claude Runner
Rule, and name the runner mode.**

This is the plan's central focus and the one place where an implementer would
have to guess in a way that can reproduce the exact failure the human concern
forbids.

The plan names `closeout-review` as "an optional structured-review use case"
(Scope item 1) and says closeout "does not invoke Claude or another reviewer by
default" (Goal; Scope item 2). But it never states how a *triggered* Closeout
Review relates to the existing `Default Claude Runner Rule` in
`structured-review/SKILL.md`, whose gate list is closed: Plan Review, Plan
Re-review, Implementation Review, Implementation Re-review. Two gaps:

1. In or out of the default-runner gate list. The plan should state explicitly
   that `closeout-review` is **not** added to the Default Claude Runner Rule's
   enumerated default gates — it is a driver-invoked pass that runs only on the
   defined triggers — or, if it should default to the runner once triggered,
   say so and justify it. As written, an implementer could reasonably fold
   `closeout-review` into that rule because it is "a repo-backed
   structured-review use case," which would make it a default/mandatory Claude
   gate: precisely the outcome the Human Concern forbids.
2. Runner mode when a Closeout Review does run. A closeout report is usually a
   durable evidence/report artifact, which `structured-review/SKILL.md` says
   should use `print-review` (appending threads pollutes durable references); a
   dated report carrying its own `## Review Threads` section would use
   `write-commit-to-plan`. Name the default mode so the implementer does not
   invent it.

Recommended fix (small): add one explicit sentence in each of
`structured-review/SKILL.md` and `closeout/SKILL.md` settling both points, plus
an Acceptance criterion asserting that `closeout-review` is not a
default/mandatory runner gate and runs only on the defined triggers.

#### Non-blocking

**Thread 2 — Use one canonical name for the Closeout Review concept.**

The plan uses three labels for one thing: "Closeout Review" (Scope item 2),
`closeout-review` (Scope item 1), and "closeout-report review" (Scope item 1
next-step language). Because the two skills must cross-reference this concept,
pick one canonical term and use it in both `structured-review/SKILL.md` and
`closeout/SKILL.md` so the implementer does not create divergent vocabulary.

**Thread 3 — Validation does not exercise the substantive acceptance;
strengthen it.**

The Acceptance items are about wording and semantics (clear separation; "no
normal wording instructs `ready for human merge`"; closeout owns the
merge-readiness phrase). The Validation Plan's `python -m unittest` and
`compileall` are regression guards on the runner script, not the new boundary
wording. Note that the existing test `test_skill_removed_legacy_human_interaction_mechanics`
in `structured-review/tests/test_claude_structured_review.py` already asserts
that `structured-review/SKILL.md` contains `Default Claude Runner Rule` and the
driver-classification words and lacks forbidden legacy phrases, so the edits
must preserve those. But nothing machine-checks the new boundary acceptance;
only the `rg` presence grep does, and presence is not correct meaning.

Recommend: (a) state in the plan that the substantive acceptance is
reviewer/human-judged (provenance), and (b) a low-cost strengthening that
follows the suite's own precedent — extend that forbidden-phrase test to assert
`structured-review/SKILL.md` does not contain `ready for human merge` in normal
review wording. That makes the central acceptance machine-checkable. Also note
that `closeout/SKILL.md` changes have no unit-test coverage and are validated by
grep only; acceptable for docs, but worth acknowledging.

**Thread 4 — Record maintenance ownership for the new Closeout Review trigger
list.**

The six-bullet Closeout Review trigger list (Scope item 2) is a durable protocol
checklist that two skills reference. Per the mechanism-lifecycle lens, briefly
note that it lives in `closeout/SKILL.md` and is maintained via
`structured-review`'s skill self-evolution, so a future trigger change updates
one canonical place. Minor.

#### Overall judgment

Not ready to implement until Thread 1 is settled. The plan does separate the
quality gate from the delivery gate clearly, prevents closeout from defaulting
to cross-agent review (Goal + Scope item 2 + Non-Goals), and preserves human
merge authority — consistent with the current `closeout/SKILL.md`, and verified
that `ready for human merge` appears only in `closeout/SKILL.md` today, never in
`structured-review/SKILL.md` or its references. The single genuine gap is the
undefined runner relationship for Closeout Review, which is also the explicit
review focus "defines when Closeout Review uses the Claude runner." Threads 2-4
are improvements that can fold into the same revision pass.

#### Residual risks / validation gaps

- If Thread 1 is resolved by silence, an implementer may default
  `closeout-review` into the runner gate list, re-creating the mandatory-gate
  risk the plan exists to prevent.
- Validation cannot prove the semantic correctness of the boundary wording;
  final acceptance is reviewer/human judgment.
- `closeout/SKILL.md` wording is grep-checked only (no unit-test coverage).

### Reviewer Pass — review closeout boundary implementation (impl)

Restated concern: confirm the implementation keeps `structured-review` a quality
gate and `closeout` the driver-owned delivery gate, makes `Closeout Review`
optional and closeout-triggered, lets a repo-backed Closeout Review run through
the Claude runner with correct mode guidance, keeps merge authority in
closeout/human handoff, and covers the runner type plus boundary wording in
tests.

Traceability against the accepted Acceptance list:

- Separates plan/impl review readiness from merge readiness — Done.
  `structured-review/SKILL.md` adds `## Boundary With Closeout`:
  "Structured-review is a quality gate. Closeout is the delivery gate," normal
  next-step language, and "Plan and implementation reviews must not make final
  merge-readiness handoffs."
- Closeout is the driver-owned delivery gate with defined Closeout Review
  triggers — Done. `closeout/SKILL.md` adds `## Review Boundary`: "Closeout is
  driver-owned by default. Do not invoke Claude or another reviewer just because
  closeout has started," plus the six-trigger list and the return contract.
- No normal review wording says `ready for human merge` — Done. Verified the
  phrase does not appear in `structured-review/SKILL.md` or its references; it
  appears only in `closeout/SKILL.md`. The new test asserts its absence.
- `Closeout Review` is not a default/mandatory runner gate — Done.
  `structured-review/SKILL.md`: "`Closeout Review` is not part of this default
  gate list ... the trigger comes from closeout, not from structured-review by
  default." Test asserts the "is not part of this default gate list" phrase.
- Closeout still owns `ready for human merge` after final rechecks — Done.
  `closeout/SKILL.md` retains the verified-handoff wording.
- Runner mode guidance for a triggered Closeout Review — Done and internally
  consistent across both skills: default `print-review` for durable closeout
  reports/reference artifacts; `write-commit-to-plan` only when the driver
  provides a thread file with `## Review Threads`. This matches the runner's
  actual constraints (`--thread-file` forbidden in print mode; required plus a
  `## Review Threads` anchor in write mode).
- Runner accepts the new type — Done. `REVIEW_TYPES` gains `closeout-review`;
  the type threads into the prompt as `Type: closeout-review`.
- Test coverage extended — Done.
  `test_closeout_review_type_loads_into_prompt` machine-checks the runner type;
  `test_skill_separates_review_readiness_from_closeout_handoff` machine-checks
  the boundary wording and the absence of `ready for human merge`.
- README unchanged — Correct. README describes structured-review and closeout
  without any merge-handoff claim, so it does not conflict with the boundary;
  the plan only required changing it on conflict.

Validation rerun (reviewer-rerun provenance):
- `python -m unittest discover -s structured-review/tests` → OK, 41 tests.
- `python -m compileall -q structured-review` → exit 0.
- `git diff --check` → clean.
- `rg` boundary-wording sweep → matches the expectations above.

#### Blocking

None. The prior plan-review blocker (Thread 1: define how Closeout Review
relates to the Default Claude Runner Rule and name the runner mode) is resolved
in both skills, and the central Human Concern — closeout not silently becoming a
mandatory Claude/cross-agent gate — holds: `Closeout Review` is explicitly
excluded from the default gate list and is invoked only on closeout triggers.

#### Non-blocking

**Thread 5 — Rebase-conflict trigger is stated in two places in
`closeout/SKILL.md`.** The "rebase or conflict resolution touched
source-of-truth docs, protocol files, tests, CI, deploy/runtime templates"
condition now appears both in the new `## Review Boundary` trigger list (around
line 36) and in the Git/Process Hygiene rebase rule (around line 287). They
agree today, but per the mechanism-lifecycle lens this is a durable checklist
maintained in two spots: a future wording change must update both or they
drift. Optional: keep the canonical list in `## Review Boundary` and have the
hygiene rule point to it instead of restating the trigger. Plan-review Thread 4
also suggested recording that the trigger list is maintained via
structured-review skill self-evolution; that explicit maintenance-ownership note
was not added. Minor; not required for this step.

**Thread 6 — `closeout-review`'s runner runtime path has no type-specific
test.** The new test exercises prompt construction for the type but not a
print/write verification run. Acceptable: the type is a review lens only and
does not branch the runner's mode verification, so the existing type-agnostic
run/verify tests already cover that path. Noted for awareness, not a gap to fill
now.

#### Overall judgment

Ready for closeout. The implementation matches every Acceptance item, the
quality-gate / delivery-gate boundary is explicit and mutually consistent across
both skills, `Closeout Review` is optional and closeout-triggered with correct
runner mode guidance, merge authority stays in closeout/human handoff, and the
new tests machine-check both the runner type and the boundary wording. Threads
5-6 are minor and can be deferred or folded into a later skill-evolution pass.

#### Residual risks / validation gaps

- `closeout/SKILL.md` wording is reviewer/human-judged and grep-checked only (no
  unit-test coverage), consistent with the plan's accepted validation
  provenance.
- Machine checks confirm phrase presence/absence, not the semantic correctness
  of the boundary; final acceptance remains reviewer/human judgment.
- The two-location rebase trigger (Thread 5) is a latent doc-drift risk if only
  one copy is updated later.

### Driver response — 2026-06-05 implementation review

Accepted Thread 5. `closeout/SKILL.md` now marks the `## Review Boundary`
trigger list as the canonical Closeout Review trigger list, maintained through
structured-review skill self-evolution. The Git/process hygiene rebase rule now
points to that trigger instead of restating the file categories.

Deferred Thread 6. The new type is a review lens and does not branch runner
mode verification; existing print/write verification tests remain type-agnostic.
The prompt-construction test for `closeout-review` is sufficient for this PR.

No human escalation was needed. The accepted fix narrows duplicated protocol
wording and does not change scope, risk tolerance, merge authority, or runner
permissions.

### Reviewer Pass — review closeout boundary implementation re-review (impl)

Restated concern: confirm the driver response resolved the Thread 5
duplication/maintenance issue, that the Thread 6 deferral is acceptable, and
that the implementation is ready for closeout without new blockers.

Re-review scope (multi-round): inspected the driver-response commit
`structured-review: respond to closeout boundary implementation review`, the
current `closeout/SKILL.md`, the runner `structured-review/scripts/claude_structured_review.py`,
and `structured-review/tests/test_claude_structured_review.py`. Reran validation.

#### Blocking

None. No prior thread was blocking, and the response introduces no new blocker.

#### Thread resolutions

**Thread 5 — Resolved. `closeout/SKILL.md` body updated.** The duplicated
rebase-conflict trigger is gone. The file-category list
("source-of-truth docs, protocol files, tests, CI, deploy/runtime templates, or
similar contracts") now lives in exactly one place — the `## Review Boundary`
trigger list. The Git/process hygiene rule no longer restates the categories; it
references "the rebase/conflict Closeout Review trigger" and keeps the
`impl`-vs-`Closeout Review` routing guidance. A future trigger-wording change now
updates one canonical place, closing the doc-drift risk per the
mechanism-lifecycle lens. The driver also added the maintenance-ownership note
("the canonical Closeout Review trigger list. Maintain it through
structured-review skill self-evolution"), which closes the open sub-point from
plan-review Thread 4. Verified by reading the current file and a targeted sweep:
the category list and the "canonical Closeout Review trigger list" sentence each
appear once.

**Thread 6 — Resolved by accepting the deferral.** The deferral rationale holds
under inspection of the runner: `config.review_type` flows only into the prompt
line (`Type: closeout-review`), run metadata, the run-log directory name, and a
startup log line. The mode-verification functions `verify_print_mode` and
`verify_write_mode` branch solely on `config.mode`, never on `review_type`, so
`closeout-review` adds no new runtime code path. `test_closeout_review_type_loads_into_prompt`
covers the only type-specific behavior (prompt construction), and the existing
type-agnostic run/verify tests cover the rest. No print/write runtime test
specific to `closeout-review` is needed for this PR. The hyphenated type value is
filesystem-safe in the log-dir name and constrained by the `REVIEW_TYPES` choice
set, so the metadata/log-dir passthrough carries no latent risk. Acceptable
deferral.

#### Non-blocking

None new.

#### Overall judgment

Ready for closeout. Both implementation-review threads are resolved: Thread 5 by
a body fix that removes the duplication and records maintenance ownership, Thread
6 by an accepted deferral whose rationale I verified against the runner source.
The quality-gate / delivery-gate boundary remains explicit and mutually
consistent across both skills, `Closeout Review` stays optional and
closeout-triggered, and merge authority stays in the closeout/human handoff —
`ready for human merge` appears only in `closeout/SKILL.md`, never in
`structured-review/SKILL.md`. Per the review/closeout boundary, this is a
`ready for closeout` handoff, not a merge-readiness handoff; final merge
readiness belongs to closeout after its own rechecks.

Validation rerun (reviewer-rerun provenance):
- `python -m unittest discover -s structured-review/tests` -> OK, 41 tests.
- `python -m compileall -q structured-review` -> exit 0.
- `git diff --check` -> clean.
- Boundary-wording sweep -> `ready for human merge` absent from
  `structured-review/SKILL.md`; the rebase/conflict trigger and the canonical
  trigger-list sentence each appear once in `closeout/SKILL.md`.

#### Residual risks / validation gaps

- `closeout/SKILL.md` wording remains reviewer/human-judged and grep-checked
  only (no unit-test coverage), consistent with the plan's accepted validation
  provenance.
- Machine checks confirm phrase presence/absence, not the semantic correctness
  of the boundary; final acceptance remains reviewer/human judgment.
- The accepted deferral leaves no `closeout-review` runtime (print/write) test;
  acceptable while the type stays a pure review lens. If a future change makes
  the runner branch on `review_type`, add a type-specific runtime test then.

### Reviewer Pass — agent protocols documentation organization (impl-plan)

Restated concern: reorganize agent-protocols documentation (move dated plans,
`BACKLOG.md`, and `ui-review.md` out of / within protocol directories; add
`AGENTS.md` + `docs/` navigation mirroring the cleaner Skynet V2 layout) without
breaking runner-loaded references, the runner's behavior, or historical review
threads, and with acceptance/validation strong enough that the next agent does
not have to guess.

Scope of this pass: the `## Documentation Organization Amendment` section only
(plan lines 113-164). The review/closeout boundary work above is already
resolved and `ready for closeout`; this pass does not reopen it.

What I verified directly:
- The runner loads exactly two references — `REQUIRED_PROTOCOL_REFERENCES =
  (references/review-lenses.md, references/collaboration.md)` in
  `structured-review/scripts/claude_structured_review.py`. It is a hard-coded
  tuple, not a `references/` glob. So moving `ui-review.md` into `references/`
  does **not** auto-load it and does **not** change prompt assembly.
- `structured-review/tests/test_claude_structured_review.py` does not reference
  `ui-review.md`, `BACKLOG.md`, or any dated plan by path. The two tests that
  read the real skill read `structured-review/SKILL.md`, which the amendment
  keeps in place. So the moves do not break the test suite.
- `ui-review.md` is referenced in two tracked, non-test places:
  `structured-review/SKILL.md:49` ("also apply `ui-review.md`") and the
  runner-loaded `structured-review/references/review-lenses.md:106` ("also apply
  `structured-review/ui-review.md`").
- `closeout/SKILL.md` already independently assumes `AGENTS.md` (lines 194, 212),
  `docs/README.md` (line 195), and `docs/agent_plans/` (line 264). No `AGENTS.md`
  or `docs/` exists in the repo yet, so the new files are greenfield (no
  overwrite risk).
- The sibling plan
  `structured-review/2026-06-05_structured_review_runner_default_refactor_plan.md`
  made a deliberate, accepted decision (its Thread 7, deferred as residual risk)
  to keep `ui-review.md` as a conditional, disk-only reference and **not** add it
  to `REQUIRED_PROTOCOL_REFERENCES`.

#### Blocking

None. Nothing in the amendment breaks mechanically: the runner's reference set
is hard-coded (so the `ui-review.md` move cannot disturb prompt assembly), the
tests do not depend on the moved paths, and the new `AGENTS.md`/`docs/` targets
are greenfield. The proposed layout is implementable as written. The threads
below are tightenings, not gates.

#### Non-blocking

**Thread 7 — State that moving `ui-review.md` into `references/` does not change
its loading status.** After the move, `references/` will hold three files, two of
which (`review-lenses.md`, `collaboration.md`) are runner-loaded required
references and one (`ui-review.md`) is a conditional reference the runner does
*not* load. A reader — or an implementer trying to be helpful — could reasonably
infer that anything in `references/` should be added to
`REQUIRED_PROTOCOL_REFERENCES`. Doing so would silently change every reviewer
prompt (it would grow by the whole UI reference) and would reverse the sibling
plan's accepted Thread 7 decision. The current Non-Goal "Do not change Claude
runner flags, permissions, logging, or artifact format" points the right way,
but it does not name this specific trap. Recommend one explicit sentence in the
amendment: moving `ui-review.md` into `references/` is a relocation only; it stays
a conditional reference and is **not** added to `REQUIRED_PROTOCOL_REFERENCES`.
This directly answers the review focus "whether required runner references would
break": they do not, provided this stays a pure relocation.

**Thread 8 — Note that the `ui-review.md` path update in `review-lenses.md` is
load-bearing, not cosmetic.** Amendment item 4 already says "update references to
the new path," and the validation `rg` already searches for
`references/ui-review.md`, so this is covered in principle. Worth making explicit
because `references/review-lenses.md` is one of the two runner-loaded references:
its text is injected verbatim into *every* reviewer prompt. If the file moves but
line 106's `structured-review/ui-review.md` is not updated, every future reviewer
is told to "also apply" a path that no longer exists. `SKILL.md:49` ("also apply
`ui-review.md`") must change too. Both are repo-relative-vs-dir-relative variants
of the same pointer; the validation pattern `references/ui-review.md` catches both
post-move forms. Low effort; just call out that these two edits are required, not
optional, and that one of them lives inside a prompt-loaded file.

**Thread 9 — The stale-reference acceptance and its `rg` cannot distinguish
frozen historical mentions from live stale references; tighten it, and use
`git mv`.** The acceptance says "No references to the moved *active* files remain
stale," but the validation `rg ... "structured-review/(2026-|BACKLOG.md|
ui-review.md)|..."` over `docs structured-review` will also match the *historical
bodies* of the dated plans being moved. The sibling refactor plan alone mentions
`structured-review/ui-review.md` roughly a dozen times inside frozen review
threads; once that plan moves to `docs/agent_plans/`, the sweep will fire on all
of them. Two failure modes for the next agent: (a) it cannot get a clean pass and
treats real work as "done" by ignoring the noise, or (b) it "fixes" the hits by
editing old-path strings inside frozen 2026-06-05 review threads — falsifying what
a reviewer actually wrote at the time, which the project's own references
(retire/annotate superseded evidence rather than silently rewrite) caution
against. Recommend: (1) declare that moved dated plans are frozen historical
records and their bodies are out of scope for the stale-reference sweep — only
live indexes, `SKILL.md`, `README.md`, `AGENTS.md`, and the runner-loaded
references must be updated; (2) scope the `rg` accordingly (e.g. exclude
`docs/agent_plans/`), or split it into a "live surfaces must be current" check and
a separate "moved plans untouched except path" check; (3) use `git mv` for the
moves so history and review-thread traceability survive the relocation.

**Thread 10 — Layout is not overfit, but record maintenance ownership for the new
index files and disambiguate the backlog name.** On the "mirrors Skynet V2
without overfitting" focus: the `AGENTS.md` + `docs/README.md` + `docs/agent_plans/`
parts are not overfitting — `closeout/SKILL.md` already assumes exactly these
(lines 194-195, 264), so the amendment harmonizes this repo with conventions its
own protocols already expect. The only genuinely new element is `docs/CURRENT.md`
(an active source-of-truth map); closeout references generic "current-doc
indexes," so it fits and is a single low-cost file, not overfit. Two small
follow-ups under the mechanism-lifecycle lens, since `docs/CURRENT.md`,
`docs/README.md`, and `docs/agent_plans/README.md` are durable indexes that go
stale silently: (a) name who updates the source-of-truth map / indexes when a
protocol is added, renamed, or retired (a one-line "maintained at closeout via
the doc-consistency check" note is enough, and aligns with `closeout/SKILL.md`
§4/§4.1); (b) `docs/README.md` should disambiguate `docs/protocol_backlog.md`
(this repo's own protocol-development backlog) from the `backlog-maintenance`
protocol's `docs/backlog.yml` convention, so a future agent does not conflate the
two or try to migrate one into the other.

**Thread 11 — Give the amendment its own Non-Goals/assumptions (minor).** The
plan's Non-Goals (lines 69-76) were written for the boundary work; one of them
("Do not create new long reference files unless the SKILL.md bodies become too
large") reads oddly next to an amendment that intentionally adds four navigation
docs (which are indexes, not long references — no real conflict, but the framing
collides). A short "Amendment Non-Goals" would prevent scope drift: no change to
runner reference loading (Thread 7); do not touch `agent-readiness/` or other
protocol dirs beyond the named moves; do not migrate this repo to `docs/backlog.yml`;
preserve filenames on move. Optional.

#### Overall judgment

Ready to implement, with no blocking issues. The amendment is mechanically safe:
the runner's reference set is hard-coded so the `ui-review.md` relocation cannot
disturb prompt assembly; the tests do not depend on any moved path; the new
`AGENTS.md`/`docs/` targets are greenfield; and the proposed layout aligns with
conventions `closeout/SKILL.md` already assumes (so it is harmonizing, not
overfitting). Threads 7-9 are the ones worth folding into a revision pass before
implementation, because they govern the two things the focus asks about —
runner-reference integrity (7, 8) and acceptance/validation precision for the
historical moves (9). Threads 10-11 are polish. Per the review/closeout boundary,
this is an `impl-plan` pass: it concludes `ready for implementation`, not a
merge-readiness handoff.

#### Residual risks / validation gaps

- If Thread 7 is left implicit, an implementer may add `ui-review.md` to
  `REQUIRED_PROTOCOL_REFERENCES`, silently enlarging every reviewer prompt and
  reversing the sibling plan's accepted decision.
- As written, the stale-reference `rg` produces false positives on frozen
  historical plan bodies (Thread 9); the acceptance cannot be a clean pass/fail
  until the sweep is scoped to live surfaces.
- `docs/CURRENT.md` and the new indexes are durable mechanisms with no stated
  maintenance owner (Thread 10); they will drift unless tied to the closeout
  doc-consistency check.
- The amendment changes only documentation; the runner, tests, and
  review/closeout boundary behavior are expected to remain byte-for-byte
  unchanged. The validation reruns `unittest` + `compileall`, which guards that
  the moves did not touch executable protocol material — a good check to keep.

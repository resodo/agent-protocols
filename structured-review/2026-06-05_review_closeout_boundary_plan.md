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

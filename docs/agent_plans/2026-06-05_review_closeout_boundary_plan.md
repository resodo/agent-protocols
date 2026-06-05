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
   new path. This is a relocation only: `ui-review.md` remains a conditional
   UI reference and must not be added to `REQUIRED_PROTOCOL_REFERENCES`.

5. Update the load-bearing UI reference pointers:
   - `structured-review/SKILL.md`;
   - `structured-review/references/review-lenses.md`.

Amendment non-goals:

- Do not change runner reference loading, runner flags, permissions, logging, or
  artifact format.
- Do not migrate this repo to `docs/backlog.yml`; `docs/protocol_backlog.md` is
  this repo's protocol-development backlog, not an adopting repo backlog
  registry. Superseded by the Backlog YAML Dogfood Amendment below.
- Do not rewrite historical review-thread bodies inside moved dated plans just
  to update old path mentions. Moved dated plans are frozen historical records;
  preserve them with `git mv`.
- Do not reorganize `agent-readiness/` or unrelated protocol directories beyond
  the named moves.

5. Update `README.md` to stay a concise repo overview and point agents to
   `AGENTS.md` plus `docs/`.

Additional acceptance:

- `find structured-review -maxdepth 1 -type f` shows only long-lived protocol
  entry files, not dated plans or backlog artifacts.
- `README.md`, `AGENTS.md`, `docs/README.md`, and `docs/CURRENT.md` agree on
  where plans, backlog, and protocol material live.
- No references to the moved active files remain stale.
- Historical mentions inside moved dated plan bodies are allowed when they
  preserve what a reviewer or driver wrote at the time.
- The original review/closeout boundary behavior remains unchanged.
- `docs/CURRENT.md`, `docs/README.md`, and `docs/agent_plans/README.md` state
  that they are maintained during closeout doc-consistency checks when
  protocols are added, renamed, retired, or moved.

Additional validation:

```bash
find structured-review -maxdepth 1 -type f | sort
rg -n "structured-review/(2026-|BACKLOG.md|ui-review.md)" README.md AGENTS.md docs/README.md docs/CURRENT.md docs/agent_plans/README.md structured-review/SKILL.md structured-review/references
rg -n "docs/agent_plans|docs/protocol_backlog|references/ui-review.md" README.md AGENTS.md docs structured-review/SKILL.md structured-review/references
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
git diff --check
```

## Backlog YAML Dogfood Amendment

Human follow-up: since this repo owns the `backlog-maintenance` protocol, its
own active backlog should use `docs/backlog.yml` instead of a parallel Markdown
backlog. Keeping `docs/protocol_backlog.md` as active backlog now contradicts
the protocol this repo asks downstream repos to use.

This amendment supersedes the earlier Documentation Organization Amendment's
temporary `docs/protocol_backlog.md` target and anti-migration non-goal.

Extend this PR before merge:

1. Migrate `docs/protocol_backlog.md` into `docs/backlog.yml`.
   - Use `backlog-maintenance/SKILL.md` schema.
   - Set `version: 1`.
   - Set `repo: resodo/agent-protocols`.
   - Set `id_prefix: AP-BL`.
   - Keep kinds to the protocol's standard set:
     `bug`, `feature`, `ops`, `debt`, `research`, `process`.
   - Convert the five existing open Markdown items into open YAML items with
     stable IDs `AP-BL-0001` through `AP-BL-0005`.
   - Preserve useful context in `why`, `next`, and `done_when`.

2. Remove the active Markdown backlog file.
   - Do not keep `docs/protocol_backlog.md` as a second active backlog.
   - Historical mentions inside dated plans can remain unchanged as provenance.

3. Update live indexes and entrypoints:
   - `README.md`;
   - `AGENTS.md`;
   - `docs/README.md`;
   - `docs/CURRENT.md`;
   - `docs/agent_plans/README.md` only if needed.
   - Remove the prior anti-migration wording that says not to migrate this repo
     to `docs/backlog.yml`; this amendment is the accepted migration plan.
   - Remove or replace all live `docs/protocol_backlog.md` pointers in these
     live entry/index surfaces.

4. Add a backlog validation mechanism:
   - add `scripts/check_backlog.py`;
   - use PyYAML for YAML parsing and install `PyYAML` in CI before running the
     checker;
   - validate the hard checks listed in `backlog-maintenance/SKILL.md`;
   - add negative-case unit tests for the checker, such as duplicate IDs, bad
     priority, missing open required field, and stray `docs/backlog.md`;
   - add both the checker and its negative-case tests to CI.
   - maintain the checker through skill self-evolution when
     `backlog-maintenance/SKILL.md` CI Expectations change.

Amendment non-goals:

- Do not redesign backlog-maintenance schema in this PR.
- Do not add closed items or invent new backlog scope.
- Do not rewrite historical review-thread bodies that mention
  `docs/protocol_backlog.md`.
- Do not migrate downstream repos in this PR.

Additional acceptance:

- `docs/backlog.yml` is the only active backlog source of truth.
- `docs/protocol_backlog.md` is absent.
- The YAML entries are semantically faithful to the five existing open items.
- Live docs point to `docs/backlog.yml`, not `docs/protocol_backlog.md`.
- `docs/README.md` adds `docs/backlog.yml` to its naming exceptions and
  maintenance list.
- CI runs the backlog checker and its negative-case tests.
- Checker negative-case tests prove the hard checks fail when violated.
- Existing review/closeout boundary and docs-organization behavior remains
  unchanged.
- Priority, kind, and prose field choices are reviewer/human-judged for
  semantic faithfulness; CI validates shape, not judgment.

Additional validation:

```bash
python scripts/check_backlog.py
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
rg -n 'docs/protocol_backlog|Do not migrate this repo to `docs/backlog.yml`' README.md AGENTS.md docs/README.md docs/CURRENT.md docs/agent_plans/README.md structured-review
rg -n "docs/backlog.yml|AP-BL|check_backlog" README.md AGENTS.md docs/README.md docs/CURRENT.md docs/agent_plans/README.md .github scripts
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

### Driver response — 2026-06-05 documentation organization plan review

Accepted Thread 7. The amendment now says moving `ui-review.md` into
`references/` is only a relocation. It remains a conditional UI reference and
must not be added to `REQUIRED_PROTOCOL_REFERENCES`.

Accepted Thread 8. The amendment now names the load-bearing pointer updates in
`structured-review/SKILL.md` and
`structured-review/references/review-lenses.md`.

Accepted Thread 9. The amendment now says moved dated plans are frozen
historical records; old path mentions inside review-thread bodies should not be
rewritten merely to satisfy a grep. Validation now scopes stale-reference checks
to live indexes and protocol references, and the move will use `git mv`.

Accepted Thread 10. The amendment now requires the new docs indexes to state
their closeout maintenance responsibility and to distinguish
`docs/protocol_backlog.md` from adopting-repo `docs/backlog.yml` registries.

Accepted Thread 11. The amendment now has explicit non-goals for runner loading,
backlog migration, historical thread rewriting, and unrelated protocol
reorganization.

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

### Reviewer Pass — agent protocols documentation organization implementation (impl)

Restated concern: confirm the reorg gives this repo the cleaner Skynet V2-style
entry/docs layout (root `AGENTS.md`, `docs/` index + source map + dated plans)
without breaking runner-loaded references, the runner's behavior, or the
review/closeout boundary, with the dated plans / backlog / `ui-review.md` moved
safely (history and frozen review threads preserved) and validation strong
enough that nothing live points at a moved path.

Scope of this pass: the implementation of the `## Documentation Organization
Amendment` (commit `095e7b7 docs: organize agent protocol documentation`). The
review/closeout boundary work above is already `ready for closeout`; this pass
does not reopen it, only confirms the reorg left it unchanged.

Traceability against the Additional acceptance list (amendment lines 165-177)
and the accepted plan-review Threads 7-11:

- `find structured-review -maxdepth 1 -type f` shows only long-lived entry
  files — Done. Output is exactly `structured-review/SKILL.md`; `scripts/`,
  `tests/`, `references/` remain as subdirectories. No dated plan or backlog at
  the protocol-dir top level.
- `README.md`, `AGENTS.md`, `docs/README.md`, `docs/CURRENT.md` agree on where
  plans, backlog, and protocol material live — Done. All four route plans to
  `docs/agent_plans/`, backlog to `docs/protocol_backlog.md`, and protocol
  packages to `SKILL.md` + `scripts/` + `tests/` + `references/` + templates.
- No references to moved active files remain stale — Done. The amendment's
  scoped live-surface sweep returns no matches, and a broader repo-wide sweep
  (`structured-review/BACKLOG.md|ui-review.md|2026-`, excluding the frozen
  `docs/agent_plans/2026-*.md`) is also clean. Old paths are gone from disk.
- Historical mentions inside moved dated plan bodies preserved — Done. The moves
  used `git mv`: `git log --follow` traces all three dated plans and
  `docs/protocol_backlog.md` through the rename, and the whole-commit `--stat`
  shows the three dated plans with `| 0` content change. The refactor plan still
  carries its ~4 frozen `structured-review/ui-review.md` mentions untouched
  (Thread 9 honored).
- Original review/closeout boundary behavior unchanged — Done. The reorg commit
  does not touch `structured-review/scripts/claude_structured_review.py` or
  `structured-review/tests/`. The only edits to executable-package files are the
  two `ui-review.md` pointer lines (`structured-review/SKILL.md:49`,
  `structured-review/references/review-lenses.md:106`); the boundary wording
  (`## Boundary With Closeout`, `ready for human merge` confined to
  `closeout/SKILL.md`) is unchanged. 41 tests pass.
- `ui-review.md` relocation only, not added to `REQUIRED_PROTOCOL_REFERENCES`
  (Thread 7) — Done. The tuple is still `(references/review-lenses.md,
  references/collaboration.md)`; `ui-review.md` is not in it. `docs/CURRENT.md`
  also documents the file as a conditional, non-runner-loaded reference, which
  hardens against the future "everything in `references/` is required" trap the
  plan-review flagged.
- Load-bearing pointer updates (Thread 8) — Done. `SKILL.md:49` uses the
  dir-relative `references/ui-review.md`; the runner-loaded
  `references/review-lenses.md:106` uses the repo-relative
  `structured-review/references/ui-review.md`, which is the correct form for
  text injected verbatim into every reviewer prompt.
- Backlog disambiguation (Thread 10) — Done. `docs/protocol_backlog.md` (the
  rename target, 76% similarity) gains the "this is not an adopting-repo
  `docs/backlog.yml` registry" paragraph, and `README.md`, `AGENTS.md`,
  `docs/README.md`, `docs/CURRENT.md` all repeat the distinction. Generalizing
  the title from "structured-review backlog" to repo-wide "Protocol Backlog" is
  in-scope for a repo-level `docs/` artifact and is internally consistent.
- Amendment non-goals (Thread 11) — Done. The amendment carries its own
  non-goals (lines 149-160); the implementation honors them (runner loading,
  backlog migration, historical-thread rewriting, and unrelated protocol dirs
  all untouched).

Validation rerun (reviewer-rerun provenance):
- `python -m unittest discover -s structured-review/tests` -> OK, 41 tests.
- `python -m compileall -q structured-review` -> exit 0.
- `git diff --check` -> clean.
- Amendment sweeps A/B/C -> A lists only `SKILL.md`; B (stale live refs) empty;
  C confirms new paths present.

#### Blocking

None. The reorg is mechanically safe and the central invariants hold: the
runner's reference set is hard-coded so the `ui-review.md` relocation does not
alter prompt assembly; the tests do not depend on any moved path and still pass;
the new `AGENTS.md`/`docs/` files are greenfield and harmonize with conventions
`closeout/SKILL.md` already assumed; and no live surface points at a moved path.

#### Non-blocking

**Thread 12 — `docs/agent_plans/README.md` does not state its own closeout
doc-consistency maintenance tie (Partial on additional-acceptance line
175-177).** That acceptance names three files —`docs/CURRENT.md`,
`docs/README.md`, and `docs/agent_plans/README.md` — that should "state that
they are maintained during closeout doc-consistency checks." `docs/CURRENT.md`
(`Update this map during closeout when ...`) and `docs/README.md` (`These index
checks are part of closeout documentation consistency.`) satisfy it. But
`docs/agent_plans/README.md` only instructs updating the *other* live indexes
when a plan changes durable organization; it never states that it itself is
maintained at closeout. Why this is non-blocking rather than a clean miss: the
lifecycle ownership is covered transitively — `docs/README.md`'s Maintenance
section explicitly lists `docs/agent_plans/README.md` "when plan/artifact
handling changes" and ties the whole list to closeout doc consistency, so the
index is not actually orphaned per the mechanism-lifecycle lens. The gap is only
against the literal "all three state it" wording. A one-line addition to
`docs/agent_plans/README.md` (e.g. "These rules are reviewed during closeout
documentation-consistency checks.") would make the acceptance pass exactly.
Driver's call whether to tighten now or accept the transitive coverage.

#### Overall judgment

Ready for closeout. The implementation delivers the intended Skynet V2-style
layout, and the layout is coherent and mutually consistent across `AGENTS.md`,
`README.md`, `docs/README.md`, `docs/CURRENT.md`, and `docs/agent_plans/README.md`.
The dated plans, backlog, and `ui-review.md` were moved with `git mv` (history
and frozen review threads preserved), live references are updated while
historical thread bodies are left untouched, `ui-review.md` stays a conditional
reference outside `REQUIRED_PROTOCOL_REFERENCES`, and the runner and the
review/closeout boundary behavior are unchanged (no runner/test edits; 41 tests
pass; boundary wording intact). The single open item is the minor, transitively
covered Thread 12. Per the review/closeout boundary, this is an `impl` pass
concluding `ready for closeout`, not a merge-readiness handoff; final merge
readiness belongs to closeout after its own rechecks, including the
doc-consistency check that should pick up Thread 12 if it is deferred.

#### Residual risks / validation gaps

- Validation proves path presence/absence and that executable material was not
  touched, not the prose quality of the new indexes; final acceptance of the
  navigation wording is reviewer/human judgment.
- The new `docs/` indexes (`CURRENT.md`, `README.md`, `agent_plans/README.md`)
  are durable mechanisms that drift silently; their stated owner is the closeout
  doc-consistency check, so that check must actually run when protocols are
  added, renamed, retired, or moved. Thread 12 is the one place that ownership
  is implicit rather than self-stated.
- If a future change adds `ui-review.md` (or any new `references/*.md`) to
  `REQUIRED_PROTOCOL_REFERENCES`, every reviewer prompt grows silently; the
  `docs/CURRENT.md` conditional-reference note is the current guard against that,
  not a test.

### Driver response — 2026-06-05 documentation organization implementation review

Accepted Thread 12. `docs/agent_plans/README.md` now states that its rules are
reviewed during closeout documentation-consistency checks when plan or artifact
handling changes.

No human escalation was needed. This is a narrow acceptance-tightening edit; it
does not change runner behavior, protocol semantics, or the documentation
organization scope.

### Driver response — 2026-06-05 backlog YAML dogfood plan review

Accepted Thread 13. The plan now states that CI must run both
`scripts/check_backlog.py` and the checker negative-case tests.

Accepted Thread 14. The positive presence grep is now scoped to live indexes,
CI, and scripts instead of the full `docs/` tree, so the active plan file cannot
satisfy it by itself.

Accepted Thread 15. The plan now calls out that `docs/README.md` must add
`docs/backlog.yml` to its naming exceptions and maintenance list, not merely
delete `docs/protocol_backlog.md`.

Accepted Thread 16. The plan now states that the checker is maintained through
skill self-evolution when `backlog-maintenance/SKILL.md` CI Expectations change.

Accepted Thread 17. The earlier Documentation Organization Amendment's
anti-migration non-goal now carries an explicit supersession note.

### Reviewer Pass — agent protocols documentation organization implementation re-review (impl)

Restated concern: confirm the driver response resolved Thread 12 (the missing
self-stated closeout maintenance tie in `docs/agent_plans/README.md`), that no
new blocker was introduced, and that the documentation organization amendment is
ready for closeout.

Re-review scope (multi-round): inspected the driver-response commit
`docs: respond to organization implementation review` (`e4c6bc4`), the current
`docs/agent_plans/README.md`, the two sibling indexes (`docs/CURRENT.md`,
`docs/README.md`) the Thread 12 acceptance names, the `ui-review.md` pointers,
and the runner/test surface. Reran validation and the amendment sweeps. This
pass does not reopen the already-`ready for closeout` review/closeout boundary
work; it only confirms the reorg amendment is closeout-ready.

#### Blocking

None. No prior thread was blocking, and the driver response introduces no new
blocker. The response touched only documentation: `git show --name-only` on the
driver commit lists exactly `docs/agent_plans/2026-06-05_review_closeout_boundary_plan.md`
(this thread file) and `docs/agent_plans/README.md`. No executable protocol
material — runner, tests, `SKILL.md` bodies, or references — was edited.

#### Thread resolutions

**Thread 12 — Resolved. `docs/agent_plans/README.md` body updated.** The driver
added one Rules line: "Review these rules during closeout documentation-consistency
checks when plan or artifact handling changes." This closes the literal gap the
prior pass flagged against additional-acceptance lines 175-177 ("`docs/CURRENT.md`,
`docs/README.md`, and `docs/agent_plans/README.md` state that they are maintained
during closeout doc-consistency checks"). All three named indexes now self-state
the tie:
- `docs/CURRENT.md`: "Update this map during closeout when protocols, indexes,
  runner paths, reference paths, or backlog ownership change."
- `docs/README.md`: "These index checks are part of closeout documentation
  consistency."
- `docs/agent_plans/README.md`: the new line above.

The new wording is consistent with the other two indexes and scoped correctly to
this file's subject (plan/artifact handling). Under the mechanism-lifecycle lens,
the durable-index drift risk the prior pass raised is now closed for all three
indexes both transitively (via `docs/README.md`'s Maintenance list) and directly
(each index names its own closeout tie). Verified by reading the current file.

#### Non-blocking

None new.

#### Overall judgment

Ready for closeout. Thread 12 is resolved by a one-line body edit that makes the
additional-acceptance wording pass exactly, and the response introduced no new
blocker or scope change. The amendment remains mechanically safe and internally
consistent: `structured-review`'s top level still holds only `SKILL.md`; the
runner reference tuple is still `(references/review-lenses.md,
references/collaboration.md)` with `ui-review.md` kept conditional and outside
`REQUIRED_PROTOCOL_REFERENCES`; the two `ui-review.md` pointers remain in their
correct forms (`structured-review/SKILL.md` dir-relative `references/ui-review.md`;
runner-loaded `structured-review/references/review-lenses.md` repo-relative
`structured-review/references/ui-review.md`); and the review/closeout boundary is
unchanged — `ready for human merge` appears 0 times in `structured-review/SKILL.md`
and its references and is confined to `closeout/SKILL.md` among live files. Per the
review/closeout boundary, this is an `impl` pass concluding `ready for closeout`,
not a merge-readiness handoff; final merge readiness belongs to closeout after its
own rechecks.

Validation rerun (reviewer-rerun provenance):
- `python -m unittest discover -s structured-review/tests` -> OK, 41 tests.
- `python -m compileall -q structured-review` -> exit 0.
- `git diff --check` -> clean.
- Amendment sweeps: `find structured-review -maxdepth 1 -type f` lists only
  `structured-review/SKILL.md`; the scoped live-surface stale-reference sweep over
  `README.md`, `AGENTS.md`, `docs/`, `structured-review/SKILL.md`, and
  `structured-review/references` returns no matches; new paths
  (`docs/agent_plans/`, `docs/protocol_backlog.md`, `references/ui-review.md`) are
  present.

#### Residual risks / validation gaps

- The new `docs/` indexes (`CURRENT.md`, `README.md`, `agent_plans/README.md`)
  remain durable mechanisms that drift silently; their stated owner is now the
  closeout doc-consistency check, which must actually run when protocols are
  added, renamed, retired, or moved. With Thread 12 resolved, each index self-states
  that tie rather than relying on transitive coverage.
- Validation proves path presence/absence and that executable material was not
  touched, not the prose quality of the navigation wording; final acceptance of
  the index prose remains reviewer/human judgment.
- The `docs/CURRENT.md` conditional-reference note remains the only guard against a
  future change adding `ui-review.md` (or any new `references/*.md`) to
  `REQUIRED_PROTOCOL_REFERENCES` and silently enlarging every reviewer prompt; it is
  documentation, not a test.

### Reviewer Pass — agent protocols backlog yaml dogfood plan (impl-plan)

Restated concern: because this repo owns `backlog-maintenance`, its own active
backlog should stop being a parallel Markdown file and move to `docs/backlog.yml`
under that protocol's schema, so the repo dogfoods the workflow it asks
downstream repos to adopt — without rewriting frozen review threads and with a
CI check strong enough that the next agent does not have to guess.

Scope of this pass: the `## Backlog YAML Dogfood Amendment` (plan lines 190-268)
after the `docs: revise backlog yaml dogfood plan` revision. Earlier amendments
above are already resolved and are not reopened here.

What I verified directly:
- The migration is faithful to `backlog-maintenance/SKILL.md`. The amendment
  targets the one canonical `docs/backlog.yml` registry, forbids a parallel
  active Markdown backlog (Source Of Truth rule), and sets all five required
  top-level keys: `version: 1` (added in the revision), `repo`, `id_prefix:
  AP-BL`, `kinds` (the protocol's standard six), and `items`. The five existing
  open Markdown items (`docs/protocol_backlog.md` sections 1-5) map cleanly to
  `AP-BL-0001..0005`, so the ID allocation is exact, not approximate.
- The negative stale-reference sweep is scoped to live surfaces only —
  `README.md`, `AGENTS.md`, `docs/README.md`, `docs/CURRENT.md`,
  `docs/agent_plans/README.md`, and `structured-review` — and does **not** scan
  the dated plans under `docs/agent_plans/`. I confirmed the full live footprint
  of `docs/protocol_backlog.md` is exactly those surfaces (README.md:25;
  AGENTS.md:44 and the 45-46 anti-migration sentence; docs/CURRENT.md:16;
  docs/README.md:14, :32 naming-exceptions list, :60 maintenance list), all of
  which the scoped grep covers, while this plan's own body (lines 129/153/194…
  and the frozen review threads) is correctly out of sweep scope. So the
  historical-mention concern is handled: frozen threads are not rewritten, and
  the earlier anti-migration non-goal is retired by supersession (line 197-198),
  not by editing frozen text.
- PyYAML is the right call: Python's stdlib has no YAML parser, so a third-party
  dependency is required; PyYAML is the standard choice. The revision correctly
  added "install `PyYAML` in CI" — necessary because the current
  `.github/workflows/ci.yml` is stdlib-only with no dependency-install step.
- The checker's stray-file negative case (`docs/backlog.md`) matches the
  protocol's hard check verbatim (`backlog-maintenance/SKILL.md:301`), not the
  repo's own `docs/protocol_backlog.md` name — correct, since that is the
  protocol's canonical guard; `docs/protocol_backlog.md` absence is separately
  asserted by the scoped negative grep.
- Root `scripts/` and `tests/` are greenfield (neither exists yet), so the new
  checker and its test suite create no overwrite or collision risk.
  `docs/agent_plans/README.md` has no backlog mention, so the scope's "only if
  needed" hedge for that index is correct.

#### Blocking

None. The migration dogfoods `backlog-maintenance` faithfully, the AP-BL items
and live-doc updates are well scoped, PyYAML + `scripts/check_backlog.py` + CI +
negative tests are an appropriate validation mechanism, and the stale-reference
sweep handles historical mentions without touching frozen review threads. The
threads below are tightenings, not gates.

#### Non-blocking

**Thread 13 — Make CI run the negative-case tests, not just the checker.** This
is the one worth folding in. Scope item 4 says "add it to CI," where "it" reads
as the checker, and lists the negative-case tests as a separate deliverable. But
the current CI runs only `python -m unittest discover -s structured-review/tests`
— a new root `tests/` suite is **not** discovered by that step. If an
implementer wires only `python scripts/check_backlog.py` into CI and drops the
negative tests in root `tests/`, those tests never run in CI and silently rot:
exactly the durable-mechanism failure the mechanism-lifecycle lens warns about
("tests prove both clean and negative cases"). The Additional validation block
runs both locally (`python scripts/check_backlog.py` and `python -m unittest
discover -s tests`), but a local command is not a CI guard. Recommend: state
explicitly that CI runs both the checker and the new `tests/` suite (a dedicated
CI step, or extend discovery), and add an acceptance line such as "CI runs the
backlog checker and its negative-case tests." Low effort; it is what makes the
negative tests an actual guard rather than decoration.

**Thread 14 — The positive presence grep is satisfied by this plan file itself;
it does not prove the live indexes were updated.** The Additional validation
`rg -n "docs/backlog.yml|AP-BL|check_backlog" README.md AGENTS.md docs .github
scripts` scans the whole `docs` tree, and this active plan (under
`docs/agent_plans/`) already contains `docs/backlog.yml`, `AP-BL`, and
`check_backlog` dozens of times. So that grep passes purely from the plan body
even if `README.md`/`AGENTS.md`/`docs/CURRENT.md` were never touched. The
negative grep is correctly scoped and strong; only the positive grep is weak.
The amendment already marks "Live docs point to `docs/backlog.yml`" as
reviewer-judged, so this is acceptable, but recommend either narrowing the
positive grep to the live index files (exclude `docs/agent_plans/`) or labeling
it informational, so it is not mistaken for proof that the live surfaces were
edited. Minor.

**Thread 15 — `docs/README.md` has two non-pointer mentions; the replacement
must add `backlog.yml`, not just delete `protocol_backlog.md`.**
`docs/protocol_backlog.md` appears in `docs/README.md` three times: the Structure
pointer (line 14), the naming Exceptions list (line 32), and the Maintenance list
(line 60). The negative grep enforces removal of all three, which is good, but a
delete-only edit would leave gaps: `docs/backlog.yml` is a non-date-prefixed
long-lived file, so it must be **added** to the naming Exceptions list (otherwise
it nominally violates the `YYYY-MM-DD_topic.md` rule), and the Maintenance "when
backlog ownership changes" line should point at `docs/backlog.yml`. Scope item 3
("remove or replace all live pointers") covers this in spirit; calling out these
two structural lists prevents an implementer from removing the old name without
restoring the new one. Minor.

**Thread 16 — Record maintenance ownership for the checker and the hard-check
list (mechanism-lifecycle).** The checker, its CI job, and the hard-check list it
mirrors are a durable mechanism that goes stale silently. The amendment does the
right thing by pointing the checker at "the hard checks listed in
`backlog-maintenance/SKILL.md`" (single source of truth, no re-enumeration), but
it does not say who keeps the checker in sync when that list evolves, or what
signal shows drift. This matches the repo's own established pattern (plan-review
Thread 4 and Thread 10 both recorded maintenance ownership for durable
checklists). Recommend one line: `scripts/check_backlog.py` implements
`backlog-maintenance`'s CI Expectations and is maintained via skill
self-evolution / the closeout doc-consistency check when those hard checks
change. Minor.

**Thread 17 — Two amendments in one plan carry contradictory backlog non-goals,
reconciled only by the supersession sentence.** The Documentation Organization
Amendment's non-goal (line 153, "Do not migrate this repo to `docs/backlog.yml`")
directly contradicts this amendment and is now dead text, retired only by the
supersession sentence at lines 197-198. For an impl-plan read top-to-bottom this
is adequate and the supersession is explicit, so it is not a blocker. But an
implementer scanning non-goals in isolation could be briefly misled. Optional:
add a short "(superseded by the Backlog YAML Dogfood Amendment)" marker at line
153. This plan is the active driver, not a frozen historical record, so adding
that marker is a normal body edit and does not conflict with the frozen-thread
non-goal. Minor.

#### Overall judgment

Ready to implement, with no blocking issues. The amendment correctly dogfoods
`backlog-maintenance`: it moves this repo to the single `docs/backlog.yml`
registry the protocol mandates, fills all required top-level keys (including the
revision's added `version: 1`), maps the five open items to stable
`AP-BL-0001..0005`, and keeps `kind`/`priority`/prose explicitly
reviewer-judged while CI validates shape only — the right division between
machine-checkable schema and human-judged semantics. PyYAML plus
`scripts/check_backlog.py` plus a CI step plus negative-case tests is an
appropriate and proportionate validation mechanism. The historical-mention
handling is sound: the negative sweep is scoped to live surfaces and excludes the
frozen dated plans, and the earlier anti-migration non-goal is retired by
supersession rather than by rewriting frozen text. Thread 13 (wire the negative
tests into CI) is the one tightening worth folding into a revision pass, because
it is what turns the negative tests into a real CI guard; Threads 14-17 are
polish. Per the review/closeout boundary, this is an `impl-plan` pass: it
concludes `ready for implementation`, not a merge-readiness handoff.

#### Residual risks / validation gaps

- If Thread 13 is left implicit, the negative-case tests may ship in a root
  `tests/` suite that CI never discovers, so the checker's hard-check coverage is
  not actually guarded in CI even though the tests exist.
- The positive presence grep cannot prove the live indexes were updated (Thread
  14); final acceptance that live docs point to `docs/backlog.yml` is
  reviewer/human judgment, as the amendment already states.
- The `kind`, `priority`, and `why`/`next`/`done_when` content for each AP-BL
  item is synthesized from terse Markdown and is reviewer/human-judged for
  semantic faithfulness; CI validates only shape. The implementer should also use
  `yaml.safe_load` (not `yaml.load`) in the checker, and note that local
  `python scripts/check_backlog.py` runs now require PyYAML installed locally.
- The checker and its hard-check list are a durable mechanism with no stated
  maintenance owner yet (Thread 16); they will drift from
  `backlog-maintenance/SKILL.md` unless tied to skill self-evolution / the
  closeout doc-consistency check.

### Reviewer Pass — agent protocols backlog yaml dogfood implementation (impl)

Restated concern: because this repo owns `backlog-maintenance`, its own active
backlog should dogfood `docs/backlog.yml` under that protocol's schema — retiring
the parallel Markdown backlog and its anti-migration guidance, validated by a CI
checker with safe YAML parsing plus negative-case tests — without rewriting
frozen review threads.

Scope of this pass: the implementation of the `## Backlog YAML Dogfood
Amendment` (commits `0115633 docs: revise backlog yaml dogfood plan` →
`c305f46 docs: dogfood backlog yaml registry`). Earlier amendments above are
already resolved and are not reopened here; this pass confirms the dogfood work
left them unchanged.

Traceability against the amendment's Additional acceptance list (plan lines
247-260) and the task focus:

- AP-BL-0001..0005 semantically faithful to the five open Markdown items — Done.
  Compared against the pre-removal `docs/protocol_backlog.md` (recovered from
  git history): item 1 Self-evolution → `AP-BL-0001` (process); item 2 Global
  canonical source → `AP-BL-0002` (process); item 3 Agent-specific wrappers →
  `AP-BL-0003` (process), and the original "after the canonical source is
  stable" dependency is faithfully encoded as `blocked_by: [AP-BL-0002]`; item 4
  Real-plan dogfooding → `AP-BL-0004` (process); item 5 Optional examples/
  evolution logs → `AP-BL-0005` (debt), with `refs:
  structured-review/references/review-lenses.md` and the original "do not
  duplicate `review-lenses.md`" caution preserved in `why`/`next`. All five are
  `status: open`; no closed items invented and no new scope added (non-goals
  honored). IDs are exact (`AP-BL-0001..0005`), not approximate. `version: 1`,
  `repo: resodo/agent-protocols`, `id_prefix: AP-BL`, and the protocol's standard
  six `kinds` are all present.
- `docs/backlog.yml` is the only active backlog source of truth and
  `docs/protocol_backlog.md` is absent — Done. The file is gone from disk; the
  dogfood commit shows `docs/protocol_backlog.md | 62 ------` (delete) and
  `docs/backlog.yml | 100 ++++` (add). Format conversion correctly uses
  delete+add rather than `git mv`; the Markdown content survives in git history.
- Live docs point to `docs/backlog.yml`, not `docs/protocol_backlog.md`, and the
  anti-migration guidance is gone — Done. The scoped negative sweep
  `rg 'docs/protocol_backlog|Do not migrate this repo to ``docs/backlog.yml```
  README.md AGENTS.md docs/README.md docs/CURRENT.md docs/agent_plans/README.md
  structured-review` returns no matches. The positive sweep confirms
  `docs/backlog.yml` pointers in `README.md:25`, `AGENTS.md:44`,
  `docs/CURRENT.md:16,30`, `docs/README.md:14,62`. A whole-repo `protocol_backlog`
  sweep shows the only remaining mentions are inside this frozen plan's own thread
  bodies — historical provenance, correctly left untouched.
- `docs/README.md` adds `docs/backlog.yml` to its naming exceptions and
  maintenance list — Done. `backlog.yml` is in the Exceptions list (line 33) and
  the Maintenance list ("`docs/backlog.yml` when backlog ownership changes",
  line 62), plus the Structure pointer (line 14).
- `scripts/check_backlog.py` implements the `backlog-maintenance` hard checks
  with safe YAML parsing — Done. Uses `yaml.safe_load` (line 43), not
  `yaml.load`. Every hard check in `backlog-maintenance/SKILL.md:288-301` is
  covered: top-level `version/repo/id_prefix/kinds/items` presence; ID regex
  `^<id_prefix>-\d{4}$` + uniqueness; per-item `status/priority/kind/title/id`;
  `status ∈ {open,closed}`; `priority ∈ {P0,P1,P2}`; open vs closed required
  fields; `kind ∈ kinds`; `resolution ∈ {completed,cancelled,transferred}`;
  `closed_at` is a date; and the stray-file guard checks `docs/backlog.md`
  verbatim (the protocol's canonical name, not the repo's `docs/protocol_backlog.md`),
  which is correct. Ran `python scripts/check_backlog.py` against the real
  `docs/backlog.yml` → exit 0.
- Negative tests cover checker failures — Done. `tests/test_check_backlog.py`
  covers all four amendment-named cases — duplicate ID, bad priority, missing
  open required field, stray `docs/backlog.md` — plus a positive case and a
  bonus invalid-id-prefix case (6 tests). Reran `python -m unittest discover -s
  tests` → OK, 6 tests. The tests prove the hard checks fail when violated
  (`assertRaisesRegex` on `ValidationError`).
- CI runs the checker and the tests with PyYAML installed — Done.
  `.github/workflows/ci.yml` adds an "Install dependencies" step
  (`python -m pip install PyYAML`) before a "Backlog check" step
  (`python scripts/check_backlog.py`) and a "Backlog checker tests" step
  (`python -m unittest discover -s tests`). This resolves plan-review Thread 13:
  the new root `tests/` suite gets its own CI step and is not silently dropped by
  the `structured-review/tests` discovery. `permissions: {}` keeps least
  privilege.
- Existing review/closeout boundary and docs-organization behavior unchanged —
  Done. `git diff 095e7b7..HEAD -- structured-review/scripts structured-review/tests
  closeout/SKILL.md` is empty; no commit since the reorg touched the runner,
  its tests, or `closeout/SKILL.md`. `ready for human merge` remains confined to
  `closeout/SKILL.md` among live files. Reran `python -m unittest discover -s
  structured-review/tests` → OK, 41 tests; `python -m compileall -q
  structured-review` → exit 0; `git diff --check` → clean; worktree clean.
- Priority/kind/prose semantic faithfulness is reviewer-judged — Confirmed. The
  P1/P1/P2/P2/P2 priorities and process/process/process/process/debt kinds are
  reasonable readings of the terse Markdown source; CI validates shape only, as
  the amendment intends.

#### Blocking

None. The dogfood is faithful to `backlog-maintenance`: a single
`docs/backlog.yml` registry replaces the Markdown backlog, the five open items
map exactly to `AP-BL-0001..0005`, the checker enforces every hard check with
`yaml.safe_load`, the four required negative cases plus extras pass, CI runs both
the checker and the tests with PyYAML installed, the anti-migration wording is
retired by supersession rather than by editing frozen text, and the
review/closeout boundary and docs-org behavior are byte-for-byte unchanged.

#### Non-blocking

**Thread 18 — Malformed-YAML failure surfaces as a raw traceback, not the clean
`check_backlog.py: <message>` line.** `main()` catches only `ValidationError`,
so a YAML syntax error from `yaml.safe_load` propagates as an unhandled
`yaml.YAMLError`. The hard check "YAML parses" is still enforced — I fed the
checker malformed YAML and it exited non-zero (so CI would correctly fail) — but
the operator sees a stack trace instead of the tidy one-line error every other
failure produces. Optional polish: wrap the `safe_load` call (or broaden the
`except` to include `yaml.YAMLError`) and emit a `ValidationError`-style message.
Minor; does not affect pass/fail behavior.

**Thread 19 — The checker's closed-item and a few structural branches have no
negative-test coverage.** The amendment named four negative cases and all four
are covered. Untested branches remain: closed-item validation
(`resolution`/`closed_at`/missing closed fields), `kind` not in `kinds`, missing
top-level field, and the non-mapping/empty-file guards. Live risk is low because
all five AP-BL items are `open`, so the closed-item paths are not exercised by
the real backlog at all. Worth recording for the checker's maintenance: when
`backlog-maintenance` CI Expectations evolve (the amendment's own
skill-self-evolution clause), add closed-item negative cases so those branches
stop being dark code. Relatedly, `closed_at` relies on YAML's native date typing
— a quoted `"2026-06-03"` string would be rejected and a `datetime` would pass
via the `date` subclass — acceptable while no closed items exist, but a closed-item
test would pin the intended contract. Minor.

#### Overall judgment

Ready for closeout. The implementation matches every Additional-acceptance item
for the Backlog YAML Dogfood Amendment: the AP-BL entries are semantically
faithful to the five open Markdown items, the live docs and entrypoints point to
`docs/backlog.yml` with the anti-migration guidance removed (and the earlier
amendment's non-goal retired by supersession, not by rewriting frozen threads),
`scripts/check_backlog.py` implements the `backlog-maintenance` hard checks with
`yaml.safe_load`, the negative tests prove the checks fail when violated, and CI
runs both the checker and the tests with PyYAML installed. Historical review
threads are preserved; the only remaining `docs/protocol_backlog.md` mentions are
in this plan's frozen thread bodies. The review/closeout boundary and
documentation-organization behavior are unchanged (no runner/test/`closeout`
edits; 41 structured-review tests pass). Threads 18-19 are minor polish/coverage
notes for a later skill-evolution pass. Per the review/closeout boundary, this is
an `impl` pass concluding `ready for closeout`, not a merge-readiness handoff;
final merge readiness belongs to closeout after its own rechecks.

#### Residual risks / validation gaps

- Priority, kind, and `why`/`next`/`done_when` prose for each AP-BL item are
  reviewer/human-judged for semantic faithfulness; CI validates shape only. They
  read faithfully against the recovered Markdown source, but final acceptance of
  the wording is human judgment.
- The malformed-YAML path (Thread 18) still fails CI but with a traceback; if a
  future caller depends on a clean error contract, tighten it then.
- Closed-item and structural checker branches (Thread 19) are untested and
  currently dark, since no closed items exist. They should gain negative tests
  when the backlog acquires its first closed item or when the hard-check list
  changes.
- The checker, its CI steps, and the hard-check list it mirrors remain a durable
  mechanism whose stated owner is `backlog-maintenance` skill self-evolution /
  the closeout doc-consistency check; that tie must actually be exercised when
  `backlog-maintenance/SKILL.md` CI Expectations change, or the checker drifts.

### Driver response — 2026-06-05 backlog YAML implementation review

Accepted Thread 18. `scripts/check_backlog.py` now wraps PyYAML parse failures
as `ValidationError`, producing the same concise `check_backlog.py: ...` failure
style as other validation errors. A malformed-YAML unit test covers this path.

Accepted Thread 19. Added negative-case tests for missing top-level fields,
unknown kind, invalid closed-item resolution, and quoted `closed_at`, in
addition to the already-covered duplicate ID, bad priority, missing open field,
stray `docs/backlog.md`, invalid ID prefix, and positive valid-backlog case.

No human escalation was needed. These edits tighten checker diagnostics and
coverage without changing backlog schema, live docs, CI scope, or the
review/closeout boundary.

### Reviewer Pass — agent protocols backlog yaml dogfood implementation re-review (impl)

Restated concern: confirm the driver response resolved Thread 18 (malformed-YAML
diagnostics) and Thread 19 (checker negative-case coverage), that no new blocker
was introduced, and that the backlog YAML dogfood work is ready for closeout.

Re-review scope (multi-round): inspected the driver-response commit
`d800290 docs: respond to backlog yaml implementation review`, which `git show
--name-only` confirms touched exactly three files — this thread file,
`scripts/check_backlog.py`, and `tests/test_check_backlog.py`. No executable
protocol material (the runner, `structured-review/tests`), no CI, no live docs,
and no `docs/backlog.yml` entries were edited, so the prior `ready for closeout`
findings on the migration, live-doc pointers, and CI wiring stand unchanged.
Reran the full validation suite.

#### Blocking

None. No prior thread was blocking, and the driver response introduces no new
blocker. The change is scoped to checker diagnostics and test coverage; the real
backlog still validates (`python scripts/check_backlog.py` -> exit 0) and the
review/closeout boundary is untouched (`ready for human merge` remains confined
to `closeout/SKILL.md` among live files).

#### Thread resolutions

**Thread 18 — Resolved. `scripts/check_backlog.py` body updated.** `_load_yaml`
now wraps `yaml.safe_load` in a `try/except yaml.YAMLError` that re-raises a
`ValidationError("YAML parse failed: ...")`. Because `main()` already catches
`ValidationError` and prints `check_backlog.py: <message>`, a malformed backlog
now surfaces the same tidy one-line diagnostic as every other failure instead of
a raw stack trace. Verified directly: feeding `version: 1\nitems: [\n` to the
checker prints `check_backlog.py: YAML parse failed: ...`, exits 1, and emits
zero `Traceback` lines, so CI still fails on malformed YAML but the operator sees
a clean message. `test_malformed_yaml_fails_cleanly` pins this path
(`assertRaisesRegex` on `YAML parse failed`). The hard check "YAML parses" stays
enforced; only the diagnostic shape improved.

**Thread 19 — Resolved. `tests/test_check_backlog.py` extended.** The suite grew
from 6 to 11 tests, adding the branches the prior pass flagged as dark:
`test_missing_top_level_field_fails` (top-level presence), `test_unknown_kind_fails`
(`kind` not in `kinds`), `test_closed_item_invalid_resolution_fails`
(`resolution` not in the allowed set), and `test_closed_item_quoted_date_fails`
(closed-item `closed_at` typing), plus the Thread 18 malformed-YAML test. The
closed-item helper `closed_item()` exercises the previously-dark closed-item
path even though the real backlog has no closed items yet. The driver also
tightened the date check from `not isinstance(..., date)` to
`type(...) is not date`, which I verified resolves the exact ambiguity the prior
Thread 19 raised: a bare `2026-06-05` (YAML `date`) passes, while a `datetime`
and a quoted string are both rejected — pinning the YYYY-MM-DD contract without
any false-rejection risk for well-formed entries. Reran `python -m unittest
discover -s tests` -> OK, 11 tests.

#### Non-blocking

**Thread 20 — The `closed_at` datetime-rejection branch is not directly pinned
by a test (informational; no action this PR).** `test_closed_item_quoted_date_fails`
exercises the quoted-*string* case, which the prior `isinstance` check already
caught; the specific behavior the `type(...) is not date` tightening adds —
rejecting a YAML `datetime` while accepting a `date` — has no dedicated test. I
confirmed the semantics hold by direct evaluation, and there is no false-rejection
risk (a bare `2026-06-05` still passes). A few peripheral branches also remain
dark (missing closed-required fields, the non-mapping / empty-file guards, empty
`outcome`/non-list `refs`), all on the closed-item path the real backlog does not
exercise. Consistent with the prior Thread 19 framing, these are fine to leave for
the checker's skill-self-evolution maintenance, e.g. when the backlog acquires its
first closed item or `backlog-maintenance` CI Expectations change. Minor.

#### Overall judgment

Ready for closeout. Both implementation-review threads are resolved: Thread 18 by
a checker fix that makes malformed YAML fail cleanly (verified: clean one-line
diagnostic, no traceback, still exit 1), and Thread 19 by five added negative
cases plus a tightened, correct `closed_at` type check. The driver response was
scoped to the checker and its tests — no live docs, CI, `docs/backlog.yml`, or
executable protocol material changed — so the prior pass's `ready for closeout`
traceability on the migration, the AP-BL fidelity, the live-doc pointers, and the
CI wiring all stand. Per the review/closeout boundary, this is an `impl` pass
concluding `ready for closeout`, not a merge-readiness handoff; final merge
readiness belongs to closeout after its own rechecks.

Validation rerun (reviewer-rerun provenance):
- `python scripts/check_backlog.py` -> exit 0.
- `python -m unittest discover -s tests` -> OK, 11 tests.
- `python -m unittest discover -s structured-review/tests` -> OK, 41 tests.
- `python -m compileall -q scripts structured-review` -> exit 0.
- `git diff --check` -> clean; worktree clean.
- Malformed-YAML probe -> `check_backlog.py: YAML parse failed: ...`, exit 1, 0
  `Traceback` lines.

#### Residual risks / validation gaps

- Priority, kind, and `why`/`next`/`done_when` prose for each AP-BL item remain
  reviewer/human-judged for semantic faithfulness; CI validates shape only. They
  read faithfully against the recovered Markdown source, but final acceptance of
  the wording is human judgment.
- The closed-item and a few structural checker branches stay dark (Thread 20),
  since no closed items exist; the `closed_at` datetime-vs-date distinction is
  verified-by-inspection rather than test-pinned. Add closed-item negative tests
  when the backlog gains its first closed item or the hard-check list changes.
- The checker, its CI steps, and the hard-check list it mirrors remain a durable
  mechanism whose stated owner is `backlog-maintenance` skill self-evolution /
  the closeout doc-consistency check; that tie must actually be exercised when
  `backlog-maintenance/SKILL.md` CI Expectations change, or the checker drifts.

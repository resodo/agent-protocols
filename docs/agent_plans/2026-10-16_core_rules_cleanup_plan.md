# Plan: recent lessons into the core, consumer assumptions out, indexes as maps

Document level: plan (one PR in agent-protocols; plan 2 of 5 in the approved
decision `2026-10-16_repo_restructure_decision.md`, section 7). Stacked on
plan 1 (`2026-10-16_core_roles_plan.md`).

Decision source: the restructure decision, approved with all recommendations
(per master relay 2026-10-16, verbatim "全部同意 继续吧"; pending record by
the master session).

## Goal

The general rules learned since 10-11 live in the core, in the protocol that
owns each; statements that are true only for one consumer leave the core;
indexes route instead of restating; reviewers stop receiving driver-only runner
text. No new standing mechanism (decision item 11).

## Scope

### A. New rules (decision section 6.2; numbers stay in overlays)

| Id | Rule | Home |
|---|---|---|
| N1 | Before asking approval of a fix: survey root cause, industry practice, long-term fit; cite what was checked; never relay a line's first proposal unchecked | `decision-boundary` Escalation Format; `fix-triage` step 8 points to it |
| N2 | Filter a question list to the human's real choices (contracts, deleting data, product meaning, direction, external voice, what he reserved); decide the rest and report "decided: ..." | `decision-boundary` Never Ask |
| N3 | Rolling pipeline: the next few PRs per line moving, few implementers at a time, no bursts; an upstream-uncertainties note before a far-ahead step | `dispatch` Keeping Lines Moving |
| N4 | Sweep starts from the list of running agents; one line per work line with its next item; any stated ETA that passed is chased | `master-board/references/sweep.md` |
| N5 | After handing a PR to the merge queue the author does not push to it; changes go to the queue as requests | `line-worker` Implementation Workers; `merge-queue` Who Merges |
| N6 | Never run a production write command to look something up; implementation workers send no requests of any kind to production, including read-only page checks and load | `line-worker` Implementation Workers and SAFETY; `release` SAFETY |
| N7 | A request that blocks a window or a dependent (a GO, a plan approval, a point of no return) is sent as a message, not only written to a status file; the receiver acknowledges; the sender re-sends after a short silence | `dispatch` (new "Blocking Requests"); `line-worker` While Working points to it |
| N8 | Gate baseline is a measurement of the live release in the same window just before the switch; measurements run in an announced quiet window; a run under abnormal load is void and retaken, not a failure | `release` Checks |
| N9 | Wait on artifacts, never on process-name matches; every background wait has a bound and is stopped by its owner; match markers exactly (anchored) | `line-worker` While Working |
| N10 | Never send the human's email or other personal information to an outside service, including request headers | `line-worker` SAFETY |
| N11 | Text the human forwards is printed in full in the message with its context, never only a path | `dispatch` Relaying To The Human |
| N12 | Before building a standard or mechanism, find what already exists, what it covers and what is missing, and extend it | `fix-triage` step 4 |
| N13 | A visual QA report names the guideline used, its source and date; without it the report does not count | `visual-qa` Output |
| N14 | Sweep notes go to a sweep log next to the board, not into the board; the settled list is kept current | `master-board` Keeping The Files; board template note |

Also from Appendix A: A29 (agent-facing guidance is checked from a fresh
agent's point of view) goes to `closeout` section 4 as one bullet.

### B. Consumer assumptions out of the core (decision section 8)

- `merge-queue` steps 5 and 7: "Push alone triggers nothing" and "rebase
  merges rewrite hashes" become "the project's CI and merge contract (overlay)
  says what a push triggers and which merge method is used; cite commits as
  `<sha> (PR #N)` when the merge method rewrites hashes".
- `fix-triage` step 1 drops "one record more or fewer is not an error by
  itself"; step 6 (cost asymmetry) becomes "the overlay states the project's
  cost asymmetry, if any". `fix-triage/references/principles.md` is deleted;
  its general lines move into `fix-triage` step 4 (observation must never be
  able to kill what it observes; one name per thing; future needs decide where
  to leave an opening; a diff between two runs is not a verdict); the rest is
  dropped or moved as follows:
  - "measure after narrowing scope before proposing a new mechanism": moves
    into step 4 with the others (general).
  - "fast process, correct product" ("the human finds it slow" is never
    permission to cut corners): moves into step 7 (efficiency), as its
    counterweight (general).
  - "deletion first and premise before fix: see structured-review": already
    the pointer in step 4; dropped as a duplicate.
  - enum `other` bucket: dropped from the core (a schema choice, not a general
    fix rule; the audit's finding); it remains in the human's memory note
    `categorical-fields-carry-other`, a project design principle.
  - "tool behavior is defined once, in the tool definition" and "when a
    principle is overturned, sweep every document that repeats it": dropped
    from the core; they remain in the memory note `ssot-and-rule-sources`
    (project design principles the human kept in memory on 10-11).
  - "explain with designs that are running or planned, not with dead code":
    dropped; it is a communication preference already in the memory note
    `design-method-research-first`.
- `closeout` manifest and phase-output bullets: conditional on the repo's own
  documentation contract ("when the repo uses output manifests").
- `retrospective` Codex transcript discovery moves to
  `agent-readiness/capabilities.md` as a "transcript location" row;
  `retrospective` points to it.

### C. Indexes as maps

- `README.md`: the runner usage and tier policy text (from "For
  structured-review reviewer passes" to the end) is replaced by one valid
  example (with `--coding-agent` and `--review-tier`) and a pointer to
  `structured-review`; Canonical Source item 2 states the one deliberate copy
  (the resident core, checked by `scripts/check_resident_core.py`).
- `README.md` "Protocols" is grouped by reader (every role; master;
  dispatched agents; authors, drivers and reviewers; repo maintainers), one
  line per protocol.
- `docs/CURRENT.md`: each protocol entry becomes one line of what it owns and
  who reads it; the structured-review paragraph keeps no policy; the reference
  map lists `structured-review/references/runner-operations.md` (driver-only,
  not runner-loaded).
- `docs/agent_plans/README.md`: "Current Records" renamed "Selected
  historical records".
- Reader tags: every lifecycle protocol description starts with its reader
  tag (`[any author]`, `[driver, reviewer]`, `[any role]`, `[scout executor]`),
  as the operation protocols already do.
- This repo's own skill mounts: add the ten missing `.claude/skills/` and
  `.agents/skills/` symlinks so all 17 protocols are discoverable when working
  here.

### D. Driver-only runner text out of the reviewer prompt

`structured-review/SKILL.md` "Default Runner Rule" keeps: when the runner is
the default, availability, no substitute for a required review, no asking per
backend, and one example. Backend selection detail, the tier policy, the
profile matrix, Runner Modes, Timeout Discipline and Recovery move to a new
`structured-review/references/runner-operations.md`, which the runner does
not load into reviewer prompts. Tests that pin that text read the new file
(`test_claude_structured_review.py`, the four `SKILL.md` policy tests). The
prompt builder in `structured-review/scripts/claude_structured_review.py`
drops the line telling the driver when to choose hard ("Normal is the
default. Reserve hard for roughly the hardest 20% ...") and keeps the
reviewer line ("Apply the same readiness standard at both tiers ..."). The
skill points drivers to `references/runner-operations.md`; detailed recovery
stays in the existing `references/recovery.md` (runner-operations links to it,
no second copy). The `closeout` tier paragraph keeps only "the driver owns tier selection; the
runner does not select hard merely because its type is `closeout-review`; see
structured-review" (still pinned by the existing test).

### E. One checklist per subject

- `closeout` section 3 UI bullets point to `structured-review/references/ui-review.md`
  for criteria and to `visual-qa` for the independent review, keeping only
  the evidence accounting.
- `closeout` 2.1 Mechanism Lifecycle points to the `review-lenses.md` lens
  for the criteria and keeps the closeout question (is each added mechanism
  owned and still needed).
- `master-board/references/sweep.md` item 2 points to
  `dispatch/references/watchdog.md` for the nudge.

### F. Guard freshness

`agent-readiness/worktree-guard.md`: the base-containment check runs when a
worktree is created and when the branch is prepared for the merge queue, not
on every guard run; a guard run during planning or review only fetches and
verifies the mounts. Consumer guard scripts follow in their own plans (plan 3
for skynet-intern; recorded there).

Out: consumer overlays, consumer `AGENTS.md`, personal files and memory
(plans 3-5).

## Validation

- `python -m unittest discover -s tests`, `-s structured-review/tests`,
  `-s scout/tests`; `python scripts/check_backlog.py`; `python -m compileall -q
  structured-review scout`.
- Runner prompt size before and after on this plan file (`print-review` prompt
  in the run directory, `wc -w`), recorded in the Implementation Record.
- For each N rule: `git grep` shows it in its home and nowhere else in full.
- Deleted principles file: `test ! -e fix-triage/references/principles.md`
  and `git grep -n "principles.md"` outside `docs/agent_plans` finds nothing.
- Generated reviewer prompt (a `print-review` run on this plan): contains
  "Apply the same readiness standard at both tiers" and does not contain
  "Reserve hard for roughly the hardest 20%"; a unit test pins both.

## Implementation Record

Done as scoped (A-F). Validation (driver-reported):

- `tests`: 30 OK; `structured-review/tests`: 124 OK (one new test pins that
  the generated prompt keeps "Apply the same readiness standard at both
  tiers" and drops "Reserve hard for roughly the hardest 20%"); `scout/tests`:
  OK; `scripts/check_backlog.py`: exit 0; `compileall`: exit 0.
- Runner-loaded protocol text (skill plus the two required references):
  7,341 words before, 5,856 after (`structured-review/SKILL.md` 4,473 to
  2,988); the moved text is in `references/runner-operations.md`.
- `fix-triage/references/principles.md` does not exist; no reference to it
  outside `docs/agent_plans`.
- Each N rule found in its planned home only (`git grep -l` per key phrase):
  N1 `decision-boundary`; N2 `decision-boundary`; N3 `dispatch`; N4
  `sweep.md`; N5 `line-worker`, `merge-queue`; N6 `line-worker`, `release`;
  N7 `dispatch` (with pointers in `line-worker` and the indexes); N8
  `release`; N9, N10 `line-worker`; N11 `dispatch`; N12 `fix-triage`; N13
  `visual-qa`; N14 `master-board` and the board template.
- Skill mounts: 17 under `.claude/skills/` and `.agents/skills/`.
- Guard: prose and sketch check base containment only in `start` and
  `handoff` modes. Consumer guard scripts are not changed here (plan 3 for
  skynet-intern).


## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

The human’s concern is that core rules should have one clear home, while consumer assumptions and driver-only instructions leave the shared reviewer material.

#### Blocking issues

##### Thread: Remove driver-only tier instructions from the generated reviewer prompt

The plan moves runner operations out of `structured-review/SKILL.md`, but `structured-review/scripts/claude_structured_review.py:576` also inserts guidance telling the *driver* when to select hard tier into every reviewer prompt. Section D does not include this prompt-builder change. Delete that instruction from the generated prompt while retaining the reviewer’s instruction to apply the same readiness standard at both tiers. Validate the generated prompt itself: show that reviewer guidance is present and the driver-only tier instruction is absent. The planned word count alone cannot prove this goal.

##### Thread: Account for general principles before deleting their file

Section B moves four lines from `fix-triage/references/principles.md` and drops the rest, saying they already live in project or personal guidance. It does not give a home or a deletion reason for “measure after narrowing scope” or “fast process, correct product.” The approved decision says valid lines move to their owners. State the disposition of these lines, with a source for any claimed existing home, so implementation does not have to decide which approved guidance to discard. This needs no new mechanism.

##### Thread: Complete the index changes required by the decision

The approved decision’s section 5 says `README.md` groups protocols by reader, with one line each. Section C only replaces the runner usage text and corrects the resident-core copy statement; the current README remains grouped by protocol family. Add that reader grouping to the plan. Also list the new `structured-review/references/runner-operations.md` in `docs/CURRENT.md`’s reference map and point drivers to it from the skill. Keep the existing `references/recovery.md` as the home of detailed recovery instructions rather than creating a second copy.

#### Non-blocking issue

##### Thread: Make the deletion check test deletion

The proposed `git grep principles.md` check already finds no reference before the file is removed. Pair the reference search with a direct check that `fix-triage/references/principles.md` no longer exists.

#### Overall judgment

**Blocking issues remain.** The plan covers N1–N14 and most remaining audit items, but the prompt, principle-file disposition, and index work need the changes above before it is ready for implementation.

#### Residual risks or validation gaps

This was a read-only review of the plan, approved decision, and relevant current files. The worktree was clean; no validation commands were run.

### Driver response to reviewer pass 1

- Driver-only tier line in the prompt: accepted; section D removes it from the
  prompt builder, with a test and a check of a generated prompt.
- Principles file disposition: accepted; section B lists every line's home or
  reason.
- Index changes: accepted; README grouped by reader, CURRENT lists the new
  reference, recovery stays in `recovery.md`.
- Deletion check: accepted; existence check added.

### Reviewer pass 2 (impl-plan, codex reviewer)

The human wants general rules to have one clear home, consumer assumptions removed from the core, and driver-only runner instructions kept out of reviewer prompts.

#### Blocking issues

None.

#### Thread resolutions

- **Generated reviewer prompt: Resolved.** Section D removes the driver-only tier instruction and requires a generated-prompt check that retains reviewer guidance.
- **Principles file: Resolved.** Section B accounts for the previously omitted principles and gives a home or deletion reason for each line.
- **Indexes: Resolved.** Section C specifies the reader grouping and reference-map update; section D keeps detailed recovery in `references/recovery.md`.
- **Deletion check: Resolved.** Validation now checks that the file is absent as well as searching for remaining references.

#### Non-blocking issues

None.

#### Overall judgment

**No blocking issues remain.** The plan is ready for implementation.

#### Residual risks or validation gaps

This was a read-only plan review. The worktree was clean; the planned prompt and test checks have not yet been run.

### Reviewer pass 1 (impl, codex reviewer)

The human wants general rules to have one home, consumer assumptions removed from the core, indexes to remain maps, and driver-only runner guidance kept out of reviewer prompts.

#### Blocking issues

##### Thread: Make output manifests conditional on the repo contract

`closeout/SKILL.md:295-302` still requires `MANIFEST.md` whenever a repo uses worktree or PR output folders. Accepted section B requires manifest checks only when the repo’s own documentation contract uses output manifests. An output folder alone does not establish that contract. Narrow the condition and remove the unconditional requirement.

##### Thread: Finish the single-checklist move

`closeout/SKILL.md:137-148` retains the mechanism lifecycle checklist, and `closeout/SKILL.md:192-196` retains UI quality criteria after adding pointers to their review references. Section E calls for those criteria to have one home, with closeout retaining evidence accounting and the question of whether a retained mechanism is owned and still needed. Remove the duplicated criteria and keep the closeout evidence requirements.

##### Thread: Remove stale index-maintenance instructions

`structured-review/references/runner-operations.md:147-151` tells future maintainers to update “this skill,” the root runner summary, and `docs/CURRENT.md` when profiles or signals change. Sections C–D deliberately removed that policy from the skill and indexes. Update the instruction to name the runner, tests, and driver-only operations reference; update indexes only if their routes change.

#### Non-blocking issue

##### Thread: Retain transcript filtering guidance

The Codex transcript paths moved to `agent-readiness/capabilities.md:59`, but the former instruction to filter transcripts to the relevant time window and user messages was dropped from `retrospective/SKILL.md`. Keep that use instruction in the retrospective protocol.

#### Overall judgment

**Blocking issues remain.** Traceability against the accepted plan: A is Done, including N1–N14 and A29; B is Partial because of the manifest condition; C is Partial because of the stale maintenance instruction; D is Done; E is Partial; F is Done. The Implementation Record’s “Done as scoped (A–F)” claim should be revised until the partial items are resolved. This implementation is not yet ready for closeout.

#### Residual risks or validation gaps

This was a read-only review of `git diff HEAD~1` and the reviewed artifacts. The worktree was clean and `git diff --check HEAD~1` found no whitespace errors. The current reviewer prompt contains the shared readiness rule and omits the removed driver tier instruction. Test results and prompt word counts in the Implementation Record are driver-reported; I did not rerun them.

### Driver response to implementation review pass 1

- Manifests conditional on the repo contract: accepted; the closeout block now
  applies only "for repos whose documentation contract uses output folders
  with manifests".
- Single checklist: accepted; closeout keeps only the evidence accounting for
  UI and the lifecycle-record check for mechanisms, with the criteria in the
  review references.
- Stale maintenance instruction: accepted; runner-operations names the runner,
  its tests and itself, and indexes only when routes change.
- Transcript filtering: accepted; kept in `retrospective`.
- Tests rerun: `tests` and `structured-review/tests` OK.

### Reviewer pass 2 (impl, codex reviewer)

The human wants general rules to have one home, consumer assumptions removed from the core, and closeout checks to retain their purpose without duplicating review criteria.

#### Blocking issue

##### Thread: Keep the closeout question about whether mechanisms are still needed

The accepted plan says `closeout` must ask whether each added mechanism is **owned and still needed**. `closeout/SKILL.md` now checks that a review happened and recorded lifecycle details, but it does not ask whether the mechanism is still needed at closeout. Restore that question without copying the lifecycle checklist back from `structured-review/references/review-lenses.md`.

#### Resolutions from pass 1

- **B, output manifests: Resolved.** The manifest block now applies only when the repo’s documentation contract calls for output folders with manifests.
- **C, index maintenance: Resolved.** `structured-review/references/runner-operations.md` names the runner, tests, and reference as the update targets; indexes change only when their routes change.
- **E, single checklist: Partial.** The duplicated lifecycle and UI criteria were reduced, but the planned “still needed” closeout question is missing.
- **Transcript filtering: Resolved.** `retrospective/SKILL.md` retains the instruction.

#### Overall judgment

**One blocking issue remains.** B and C are Done; E is Partial. The implementation is not yet ready for closeout.

#### Residual risks or validation gaps

This was a read-only inspection of `git diff HEAD~1` and the relevant artifacts. The worktree was clean and `git diff --check HEAD~1` passed. The driver reports that `tests` and `structured-review/tests` passed; I did not rerun them.

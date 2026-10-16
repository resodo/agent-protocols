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
  dropped (enum `other`, "explain with running designs", tool definition SSOT
  and principle sweeps are project or personal and already live there).
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
- `docs/CURRENT.md`: each protocol entry becomes one line of what it owns and
  who reads it; the structured-review paragraph keeps no policy.
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
`closeout` tier paragraph keeps only "the driver owns tier selection; the
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
- Positive control for the deleted principles file: `git grep principles.md`
  finds no reference.

## Review Threads

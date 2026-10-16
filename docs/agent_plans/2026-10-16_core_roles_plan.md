# Plan: roles, one master definition, one home for permission rules

Document level: plan (one PR in agent-protocols; plan 1 of 5 in the approved
decision `2026-10-16_repo_restructure_decision.md`, section 7).

Decision source: the restructure decision, approved with all recommendations
(per master relay 2026-10-16, verbatim "全部同意 继续吧"; recorded in that
doc's human acceptance record, pending record by the master session). This
plan's author did not receive the approval directly.

## Goal

A reader can answer from one file each: who am I, what may I do, whom do I
report to; and the master is defined in exactly one place. Permission rules
(merge, release, ledger) have one home, `decision-boundary`; every other copy
becomes a one-line pointer.

## Scope

In:

1. `agents/master.md` (new): the master's single definition (decision
   section 4): appointment; one master per project and the handover; owns
   board, queue, settled list (single writer); gated decisions only within the
   ledger; governance only from ledger grants; coordinates only (answer 5a:
   decides, dispatches, merges and releases or delegates them, small checks
   and fixes itself, every implementation line goes to a worker); talks with
   the human; reads the human's master-preferences file named in the
   user-level instructions (answer 1a); preloads `decision-boundary`,
   `master-board`, `dispatch`, `session-handoff`, `away-mode`.
2. `agents/README.md`: role composition (authority role sets permission and
   escalation; task role sets work and output; author, driver and reviewer
   grant nothing); the role list with owner files; the coordinator (answer
   2a) as a dispatched agent with its limits; wrapper instructions as today.
3. `agents/release.md`: widened to the production operator (any named
   production change: release, configuration change, ops action); reports to
   the master, who updates the board. File name kept (consumer wrappers point
   at it).
4. `agents/line-worker.md`, `agents/researcher.md`: the line worker may
   implement a gated change its brief names with the recorded permission (the
   existing resident-core exception), for example an approved contract change;
   the researcher path is qualified; researcher production reads follow its
   brief and the project overlay.
5. `line-worker/SKILL.md`: split into "Every dispatched agent" and
   "Implementation workers"; the production rule lives in the second, with
   the researcher pointer.
6. `decision-boundary/CORE.md` (resident core): the role bullet points to
   `agents/`; the dispatched-agent bullet keeps the stop rule and the
   delegated-action exception in short form, with the lookup procedure left to
   the long form; one sentence for the coordinator ("a dispatched agent that
   dispatches others still reports to whoever dispatched it and cannot pass
   on a gated permission"). Kept within 40 lines and naming all ten gates
   (existing test).
7. `decision-boundary/SKILL.md`: Four Quadrants points to `agents/`;
   Authority Ledger recording follows answer 3a (another agent may type an
   entry; the session that heard the grant checks the words and scope before
   it becomes `active`; an entry transcribed later from a record starts as
   `proposed`); Delegated Execution becomes the single home of merge and
   release permission and states merge execution per answer 4a (one merger
   per repo at a time; while a master runs only the master or its merge agent
   merges; a direct session merges on a current-turn instruction only when no
   master runs); a coordinator cannot re-delegate; Escalation Format keeps the
   information a question must carry and leaves presentation to the human's
   preferences.
8. Pointers replacing copies: `closeout` SAFETY (merge permission),
   `merge-queue` Who Merges, `release` Before step 1, `structured-review`
   SAFETY approval recording, `readable-brief` Delivery recording,
   `dispatch` (approval recording), `line-worker` Hand Back.
9. Master procedures say so: descriptions of `master-board`, `dispatch`,
   `session-handoff`, `away-mode` name `agents/master.md`; `session-handoff`
   cold start step 1 points to it and its template wording is fixed ("write
   the handoff file from the template"); `release` After step reports to the
   master instead of updating the board; `dispatch` covers a coordinator's
   dispatch and deletes "The only acceptable blocker is a decision that
   belongs to the human" (replaced by: record the real blocker, its owner and
   the restart condition).
10. Indexes for these paths: `README.md` and `docs/CURRENT.md` list
    `agents/master.md`; `agent-readiness/capabilities.md` role-definition row
    unchanged.

Out (plan 2): new rules from recent lessons, consumer assumptions moved out
of the core, README/CURRENT reduced to maps, runner driver-only text, reader
tags for lifecycle protocols, the unreferenced `fix-triage` principles file.
Out (plans 3-5): consumer overlays, consumer `AGENTS.md` and the copied core,
personal files, memory.

## Consumer impact

`CORE.md` changes, so every consumer's embedded copy must be replaced in its
bump PR (plan 3 for skynet-intern, plan 4 for skynet-apps; `skynet-agent-kit`
and `skynet-ingest` have no embedded core). `agents/master.md` is new;
consumers may add a wrapper for it but none is needed: the master is a session
role, not a dispatched specialist.

## Validation

- `python -m unittest discover -s tests` (resident core still at most 40 lines
  and names all gates; skill frontmatter parses).
- `python scripts/check_backlog.py`.
- Scenario check by reading, recorded in the PR: for each of these, the file
  that answers it is exactly one and the answer is unambiguous:
  1. "I was named master; what do I own and what must I not do?"
  2. "A coordinator line wants to open a W2 window's point of no return."
  3. "A direct session got 'merge PR 12' from the human while a master runs."
  4. "A researcher was told to read production; may it?"
  5. "A worker's brief cites the human's approval of a new response field."
  6. "Another agent typed a ledger entry the master heard."
- `git grep` that the line-level lookup procedure and merge-permission
  conditions appear in full only in `decision-boundary/SKILL.md`.

## Review Threads

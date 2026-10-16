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

11. Every role file has the same six fields (who, owns, may decide, stops
    at, reports to, preloads): `agents/line-worker.md`, `researcher.md`,
    `merge-queue.md`, `release.md`, `visual-qa.md` and the new `master.md`.
    Reporting routes: a worker or researcher reports to whoever dispatched it
    (master or coordinator); merge agent reports to the master; the production
    operator reports to the master, and reports check results to the
    coordinator when a coordinator dispatched the checks; visual QA to whoever dispatched it. "Report to the master" in
    `decision-boundary` (Dispatched Agents) and `line-worker` (intro, While
    Working, Hand Back) becomes "report to whoever dispatched you".
12. `release/SKILL.md` becomes the production-change protocol for the
    production operator, file name kept. Its steps apply to every named change:
    the brief names the change, the official command and its receipt (from the
    project overlay); preconditions and a baseline are taken for every change;
    "pin a commit" and "record the rollback target" apply when a version is
    switched, and for a configuration or ops change the rollback is the
    recorded previous value or the command's documented undo; staged checks
    are those the overlay names for that kind of change, and when the overlay
    names none for a configuration or ops change, one read-back of the changed
    value plus the health check the brief names. Failure policy unchanged.
13. Ledger transcription (answer 3a) is reconciled with the existing
    prohibitions: typing a `proposed` entry from a text the master gives is
    not recording an approval and grants nothing; only the session that heard
    the grant compares it with what it heard and sets it `active` with the
    date. Wording changes: `CORE.md` ("Only the master reads the ledger"
    becomes "Only the master uses the ledger to find permission; a dispatched
    agent only verifies the one entry its brief cites"; "never record a
    human approval yourself" stays and gains "a `proposed` entry the master
    asked you to type is not an approval"); `decision-boundary` Authority
    Ledger "Recording" and SAFETY; `line-worker` SAFETY and Hand Back. A
    scribe never sets an entry `active`.
14. Permission-copy inventory, each handled individually:
    - `closeout/SKILL.md` SAFETY bullets 4-6 (merge permission, standing
      authorization, "ready to merge" phrasing): bullets 4 and 5 become one
      pointer to `decision-boundary` Delegated Execution plus the stop rule
      "without that permission closeout stops at `ready for human merge`";
      bullet 6 keeps the distinction between "ready to merge" (a request for the
      final recheck) and permission, with the condition list replaced by the
      same pointer. Section 6 "Git and Process Hygiene" merge
      bullets become the same pointer.
    - `merge-queue/SKILL.md` Who Merges paragraph 2: pointer; SAFETY "Do not
      merge without one of the two permissions above": stays as a short stop
      rule pointing to `decision-boundary`.
    - `release/SKILL.md` Before step 1: pointer plus "irreversible steps are
      named separately"; SAFETY: unchanged short stop rules.
    - `structured-review/SKILL.md` SAFETY ledger and approval-recording
      bullets: pointer.
    - `readable-brief/SKILL.md` Delivery recording sentence: pointer.
    - `planning/SKILL.md` ledger exemption bullet: pointer.
    - `CORE.md` dispatched-agent bullet: short form only (cite, look up only
      that entry, stop if inactive); the full procedure stays in
      `decision-boundary` Delegated Execution.

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
- Copy check, file by file for the list in scope item 14: each named passage
  is now a pointer or a short stop rule, and the phrases "line-level search",
  "current-turn instruction" with merge, and "standing authorization" appear
  with full conditions only in `decision-boundary/SKILL.md` (positive control:
  the grep finds them there).

## Implementation Record

Done as scoped (items 1-14). Validation (driver-reported):

- `python -m unittest discover -s tests`: 30 tests OK (resident core 23 lines,
  all ten gates named, frontmatter parses).
- `python scripts/check_backlog.py`: exit 0.
- `python -m unittest discover -s structured-review/tests`: 123 tests OK.
- Copy check: "line-level" appears only in `decision-boundary/SKILL.md`
  (Delegated Execution); "standing authorization" only in
  `decision-boundary/SKILL.md`; "current-turn" with merge conditions only in
  `decision-boundary/SKILL.md`, plus the short form in `CORE.md` and the
  queue-line field name in `merge-queue/templates/MERGE_QUEUE.md`.
- Scenarios, each answered by one file:
  1. Named master: `agents/master.md` (owns, may decide, coordinates only,
     stops at uncovered gates).
  2. Coordinator at a point of no return: `agents/README.md`, Coordinator
     (ask the master, counts only after the answer, re-send on silence).
  3. Direct session told "merge PR 12" while a master runs:
     `decision-boundary` Delegated Execution (only the master or its merge
     agent merges while a master runs; the session reports to the human).
  4. Researcher told to read production: `agents/researcher.md` (only when
     the brief allows it, within the overlay's production-read rules).
  5. Worker brief cites approval of a new response field:
     `agents/line-worker.md` and `line-worker` Implementation Workers (may
     implement it; merging still stops at the gated-surface check).
  6. Another agent typed a ledger entry the master heard:
     `decision-boundary` Authority Ledger, Recording (`proposed` until the
     master compares it and sets it `active`).


## Review Threads

审查发现四处会让实施者猜测权限或职责边界；以下是供 runner 记录的完整审查线程。

### Reviewer pass 1 (impl-plan, codex reviewer)

The human’s concern is that each role, especially the master, should have one clear definition, and permission rules should have one home.

#### Blocking issues

##### Thread: Complete the role definitions and reporting routes

The approved decision requires each role file to state who the role is, what it owns, what it may decide, where it stops, whom it reports to, and what it preloads. The plan updates `agents/line-worker.md`, `agents/researcher.md`, and `agents/release.md`, but omits `agents/merge-queue.md` and `agents/visual-qa.md`, which currently lack explicit ownership and reporting fields. It also leaves “report to the master” in `decision-boundary/SKILL.md` and `line-worker/SKILL.md`, although the approved coordinator’s workers report to the coordinator. Add these existing files and reporting instructions to the plan’s edit list. This needs wording changes, not a new mechanism.

##### Thread: Make the production operator’s protocol usable beyond releases

The plan widens `agents/release.md` to cover configuration changes and operations, but its only specified edits to `release/SKILL.md` are permission and board-update text. That protocol still describes shipping a release, switching versions, and release-specific checks. Specify how its existing steps apply to each named production change, including where the official command, applicable checks, and rollback behavior come from. Otherwise an operator handling a configuration or operations action must guess which release steps apply.

##### Thread: Reconcile delegated ledger transcription with existing prohibitions

Answer 3a allows another agent to type a ledger entry before the session that heard the grant verifies and activates it. The plan changes `decision-boundary/SKILL.md`, but does not say how this fits the resident core’s “only the master reads the ledger” and “never record a human approval yourself,” or `line-worker/SKILL.md`’s approval-recording prohibition. State the narrow difference between preparing an inactive entry and attesting to an authorization, and identify the wording that must change. A scribe must not be able to make its own transcription authoritative.

##### Thread: Finish the permission-copy inventory

The goal says merge, release, and ledger permission rules have one home. The pointer list names `closeout` SAFETY, `merge-queue` Who Merges, and `release` Before step 1, but permission conditions also appear later in `closeout/SKILL.md`, in `merge-queue/SKILL.md` SAFETY, and in `release/SKILL.md` SAFETY. Specify which of those become pointers and which remain short role-specific stop rules. Validate the known copies individually; an unspecified `git grep` does not establish that the full conditions have only one home.

#### Non-blocking issues

None.

#### Overall judgment

**Blocking issues remain.** The plan covers the approved direction, but the role, production-operation, and permission edits need enough detail to implement without guessing. It is not yet ready for implementation.

#### Residual risks or validation gaps

This was a read-only review of the plan, decision, and relevant current protocols. No validation commands were run and no files were changed; the worktree was clean.

### Driver response to reviewer pass 1

- Role fields and reporting routes: accepted; scope item 11.
- Production operator protocol: accepted; scope item 12.
- Ledger transcription versus prohibitions: accepted; scope item 13.
- Permission-copy inventory: accepted; scope item 14 and the copy check.

### Reviewer pass 2 (impl-plan, codex reviewer)

The human’s concern is that each role, especially the master, has one clear definition and permission rules have one home.

#### Blocking issues

##### Thread: Complete the role definitions and reporting routes

Scope item 11 says the production operator reports to the master. The approved decision also permits reporting check results to a coordinator (`2026-10-16_repo_restructure_decision.md`, section 4). State that route in the plan so implementation preserves the approved boundary. This pass 1 thread remains open.

##### Thread: Reconcile delegated ledger transcription with existing prohibitions

Scope item 13 proposes “Only the master uses the ledger for permission” in `CORE.md`, while items 6 and 14 require a dispatched agent to verify its cited entry. Specify that the master selects authority and the dispatched agent verifies only the entry cited in its brief. The proposed wording otherwise leaves the resident core ambiguous. This pass 1 thread remains open.

##### Thread: Finish the permission-copy inventory

Scope item 14 says the `closeout/SKILL.md` phrasing bullet stays. That bullet currently also restates both complete merge-permission conditions. Keep the distinction between “ready to merge” and permission, but replace the condition list with a pointer to `decision-boundary`. Otherwise the plan’s one-home goal and copy check cannot both pass. This pass 1 thread remains open.

#### Prior-thread resolution

Resolved: scope item 12 specifies how `release/SKILL.md` applies to a named production change, including commands, receipts, baseline, rollback, and checks.

#### Non-blocking issues

None.

#### Overall judgment

**Blocking issues remain.** The three wording changes above are needed before implementation; none requires a new mechanism.

#### Residual risks or validation gaps

This was a read-only review of the plan, decision, and relevant current protocols. No validation commands were run or files changed. The worktree was clean.

### Driver response to reviewer pass 2

- Production operator reporting: accepted; item 11 adds the coordinator route
  for check results.
- Ledger wording in the core: accepted; item 13 now separates finding
  permission (master) from verifying the cited entry (dispatched agent).
- Closeout phrasing bullet: accepted; its condition list becomes the pointer.

### Reviewer pass 3 (impl-plan, codex reviewer)

The human wants clear role definitions, especially for the master, and one home for permission rules.

#### Blocking issues

None in the plan.

#### Prior-thread resolutions

- **Role reporting: Resolved.** Scope item 11 includes the production operator’s check-results route to a coordinator.
- **Ledger wording: Resolved.** Scope item 13 separates the master’s authority lookup from a dispatched agent’s check of the entry cited in its brief.
- **Permission-copy inventory: Resolved.** Scope item 14 keeps the distinction between “ready to merge” and merge permission while replacing the repeated conditions with a pointer.

#### Non-blocking issues

None.

#### Overall judgment

**The plan is ready for implementation after the approved decision document is merged.** The three pass 2 blockers are resolved without a new mechanism.

#### Residual risks or validation gaps

This was a read-only review; no validation commands were run, and the worktree was clean. The decision document’s acceptance record still says the master session must record the approval directly, and its commit is not in this checkout’s current `origin/main` reference. Those process steps remain prerequisites to dependent implementation.

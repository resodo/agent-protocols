# Plan: decision boundary and master-session protocols

Document level: plan (one PR in agent-protocols).

Decision source: the human answered three proposal questions "per
recommendation" and then said "开吧" on 2026-10-11. This plan's author did not
receive that approval directly; it is **per master relay (2026-10-11), pending
record by the master session**. The proposal is kept outside the repo
(consumer session scratchpad); its decisions are restated below.

## Goal

A new session that is told "you are the master" must work the way the current
master + subagents team works, with any coding agent (Claude Code, Codex, Grok
Build), without depending on a private memory store.

Today the collaboration rules live in one Claude memory directory. A baseline
exam (see Validation) shows the current team still decides correctly, but only
because every session happens to reach that directory: Claude subagents see its
index and read its files, and a Codex master reached the same answers by
reading files. Nothing shared and versioned holds these rules, so slimming the
memory, a new machine, or a different agent would lose them silently.

This PR adds to agent-protocols:

1. a short **resident core** for the decision boundary that every role keeps in
   context;
2. **fine-grained protocols** whose descriptions are always listed and whose
   bodies load on demand;
3. a **capability map** so protocol text names capabilities, not one vendor's
   tools;
4. **neutral role definitions** for specialist subagents;
5. changes to **closeout** (and one line each in planning and
   structured-review) so a standing authorization recorded in the project
   ledger counts as permission within its recorded scope;
6. a **resident-core check script** consumers call from their guard.

## Non-goals

- No project content: paths, scripts, budgets, business rules and the
  project's authority ledger live in consumer overlays
  (`.agent-protocols/<protocol>.md`), per README "Local Overlays".
- No change to structured-review mechanics or the runner.
- No access control. "Must not load" is enforced by not loading and by a
  resident instruction.
- OpenCode support is not claimed; its cells stay unverified.

## Decisions carried in (per master relay, 2026-10-11)

- Three-way split: generic -> agent-protocols; project -> consumer overlay;
  personal preference -> user-level instruction files. Standing merge and the
  pre-implementation plan-review exemption for iteration fixes are project
  authorizations; reading language and banned words of briefs are personal;
  model tiers and concurrency caps are personal; the visual acceptance
  viewport is project.
- Resident set: every role keeps "role identification + decision-boundary
  core". The authority ledger, the human's queue and the board are
  master-only.
- Closeout: "an explicit current-turn command, or a standing authorization
  recorded in the project's authority ledger with date, the human's words and
  scope"; the same for the plan-review exemption.

## Roles (resolves review thread 1)

- **Master**: the session the human named master in this session.
- **Direct session**: a session the human tasks directly without naming it
  master. It talks to the human, so gated steps are asked of the human; it
  does not use the ledger (grants are to the master).
- **Dispatched agent**: started by the master or another agent. Gated steps go
  to whoever dispatched it; it never contacts the human. Single exception
  (added in implementation review): a gated action its brief names exactly,
  with the permission the master checked and cited ("Delegated Execution");
  the master withdraws such delegations when the permission is revoked.

The never-ask list applies only when no gate is hit: implementation detail
that changes a contract or what users see is gated.

## Protocols and why each exists (resolves review thread 3)

Split rule: a separate protocol only when its trigger or reader differs and it
owns its own output; a branch that shares trigger and reader is a subfile
(`references/`), following scout's subskill precedent. Each overlap the review
named:

| Protocol | Reader | Trigger | Owns (output) | Not covered elsewhere because |
|---|---|---|---|---|
| `decision-boundary` | all | before deciding a gated step, before asking the human, on a grant or revocation | gate tests, ledger rules, escalation format; `CORE.md` | no existing protocol defines who decides what |
| `master-board` | master | state change; progress / stuck / what-can-move questions; scheduled sweep; before a report | board, queue (open items), sweep findings | — |
| `dispatch` | master | spawning, agent notifications, stalls, denials, resuming old work | dispatch brief, watchdog, line record | — |
| `line-worker` | dispatched worker | preloaded at start | STATUS.md, hand-back report | — |
| `merge-queue` | merge agent | PRs ready; merge agent starts | merge-queue file, merge records | closeout decides whether one PR may merge; nothing covers ordering many PRs through one merger |
| `release` | release agent | release, switch, staged check due | release record, check results | — |
| `visual-qa` | QA agent | visible change about to be shown | finding list | structured-review `ui-review.md` reviews a design or PR; this audits rendered screenshots before the human sees them |
| `away-mode` | master | human leaving / returning | pre-authorization table, per-change ledger | master-board keeps state; it never collects pre-authorizations or produces the change ledger |
| `session-handoff` | master | session ending; new master session | handoff page, cold-start receipt | the bootstrap template is a repo receipt for any session with no task; it does not load live state or re-dispatch lines. The template gains one line pointing a named master here |
| `fix-triage` | master, worker | before fixing a QA finding or model error, adopting someone's fix, adding a rule | per-finding class and fix/no-fix | structured-review covers review findings on an artifact (deletion first, premise before fix) and is referenced, not repeated; fix-triage covers whether an output is wrong at all and attribution of model behavior |

Merged away after review: none needed beyond removing from `fix-triage` the
items already in structured-review (deletion first, premise before fix), which
it now cites.

## Files

New protocol directories as in the table, each `SKILL.md` with frontmatter
`name` equal to the directory and a `description` that starts with its reader
tag (`[master]`, `[dispatched worker]`, ...). Subfiles:
`decision-boundary/CORE.md`; `master-board/references/sweep.md`,
`templates/BOARD.md`, `templates/QUEUE.md`; `dispatch/references/watchdog.md`,
`templates/brief.md`; `line-worker/references/read-only-research.md`,
`templates/STATUS.md`; `merge-queue/templates/MERGE_QUEUE.md`;
`away-mode/templates/preauthorization.md`;
`session-handoff/templates/SESSION_HANDOFF.md`;
`fix-triage/references/principles.md`.

Other new files:

- `agent-readiness/capabilities.md` (thread 4 below).
- `agents/README.md` and neutral role files `line-worker.md`, `researcher.md`,
  `merge-queue.md`, `release.md`, `visual-qa.md`. Consumers add thin per-vendor
  wrappers; wrappers are consumer files.
- `scripts/check_resident_core.py` and `tests/test_resident_core.py`
  (thread 5 below).

Changed files:

- `closeout/SKILL.md` (thread 2 below).
- `planning/SKILL.md`: one new SAFETY bullet: "A project may record in its
  authority ledger that a named class of change (for example iteration fixes)
  skips the separate plan-review step before implementation. That exemption
  covers only that review step: scope, worktree, review path (the remaining
  gates) and acceptance must still be explicit before the work starts." The
  existing first SAFETY bullet is not changed.
- `structured-review/SKILL.md`: SAFETY "Preserve human final authority" bullet
  gains "a standing authorization recorded in the project ledger counts as the
  human's decision within its recorded scope (see `decision-boundary`)".
- `agent-readiness/worktree-guard.md`: new "Resident Core" section (thread 5).
- `agent-readiness/agents-bootstrap-template.md`: the marker block, one line
  "if the human named you master, load `session-handoff`".
- `README.md`, `docs/CURRENT.md`, `AGENTS.md` (rollout rule: after a merge
  here, merge every consumer's bump PR, close stale ones, reload sessions).

## Content outline (the implementation contract)

### decision-boundary/CORE.md (resident, at most 40 lines)

Between its two marker lines, in this order:

1. Roles: master (named by the human in this session), direct session (tasked
   by the human without the name), dispatched agent (started by another
   agent). Act within your role.
2. The rule: gates decide whether a step needs the human; the project's
   authority ledger says which gated steps are handed to the master; only the
   master reads the ledger (exception: a delegated agent re-reads the one
   entry its brief cites, right before acting).
3. Gates, one line each: G1 cannot be undone losslessly within minutes; G2
   money beyond an approved budget or a new paid channel; G3 speaking for the
   human or team to an outside party (approving the action is not approving
   the wording); G4 contract shape (API endpoint or field, schema/DDL,
   cross-repo interface, shared infrastructure); G5 moving a layer's
   responsibility; G6 what users see or what the product means; G7 a new
   standing mechanism (alert, counter, registry, config field, guard,
   approval step); G8 permissions, credentials, security, or working around a
   denial; G9 contradicting a settled human decision; G10 observation window,
   criteria, rollback condition or rollout pace.
4. Master: a gated step the ledger does not cover -> ask the human, one
   question at a time with a recommendation; otherwise decide, keep a receipt
   and an undo, report afterwards.
5. Direct session: a gated step -> ask the human; never use the ledger.
6. Dispatched agent: any gate, scope growth, a cause outside scope, a conflict
   with an earlier decision, or anything needing the human -> stop and report
   to whoever dispatched you; the one exception is a gated action its brief
   names exactly with the permission the master recorded (it may re-read only
   that cited ledger entry, right before acting); never contact the human,
   never use the ledger to find permission, never record a human approval.
7. Never ask, when no gate is hit: read-only investigation, questions already
   answered (search the record and cite it), hypothetical contingencies,
   implementation detail.
8. Permission denied: stop and report; never another route to the same thing.
9. Pointer: details in the `decision-boundary` protocol.

The test checks the markers, the line limit and G1-G10; the reviewers check
the content against this list.

### Protocol bodies

- `decision-boundary`: four-quadrant table; each gate with a test question and
  a neutral example; grey zone (reversible within minutes and
  engineering-internal -> decide; G1 or G4 -> ask); what the master decides by
  default (investigation, implementation detail, review triage, reviewing
  others' fix candidates, confirmed errors with a known fix, process text,
  dead processes, one flaky rerun), each with record search, evidence, receipt,
  undo and a report line; ledger rules (entry fields date / verbatim words /
  scope / exclusions / where said; recorded the same turn by the session that
  heard it; the master may propose a delegation after a run without
  substantive errors, threshold in the ledger; only the human grants; one
  sentence revokes; no extension by analogy; a ledger entry is the permission
  closeout and structured-review accept within its scope); never-ask list;
  escalation format (one question, define terms, now / proposal / why / cost /
  what moves, one worked example, recommendation, what the human is waiting
  on, plain text); dispatched agents (report in the master's language; relayed
  human decisions are true, elaboration can be challenged; never record
  approvals); SAFETY.
- `master-board`: board and queue templates; update in the same turn; queue
  holds only open items, answered items move to the board's settled list with
  date and words, grants go to the ledger; one current table, old tables
  archived; size rule (queue one screen, board current section two screens);
  record rejections like approvals; every reply says what waits on the human
  or that nothing does; checks before claiming done; sweep reference: every
  line moving or blocked with a trigger, silent agents nudged, PR states,
  failed runs, self-imposed waits, undrafted promises and verbal delegations,
  queue completeness, due commitments, parked items whose trigger fired,
  project daily actions; a quiet sweep says nothing.
- `dispatch`: record search and premise check before dispatching; parallel only
  for disjoint surfaces or read-only work; brief template (objective, output,
  sources, boundaries, decisions with sources split into human decisions and
  elaboration, reporting, the denial rule); tier by the hardest judgement,
  rule and cost facts passed down; watchdog in the same turn (output growth,
  about 15 minutes, nudge wording, events on state flips only, stop when done);
  verbal delegation becomes a tracked task; design follow-ups written into the
  design now; on reports: check before relaying, denials relayed to the human,
  returned work to the author, tail work to a cheap tier; every approval's next
  step dispatched the same turn; relay text between separators.
- `line-worker`: list prior decisions with sources first, memory notes are
  leads; resume half-done work from git state; premise check when resuming;
  gates per project overlay; no production, no CI trigger, no merge, no
  contract change, no paid calls except reviews, no new standing mechanism;
  cause outside scope -> stop; denial -> stop; verify before claiming;
  STATUS.md one screen; hand-back in three to ten lines; read-only research
  reference (no files on hosts, scripts over stdin, only own service,
  understand before reporting, numbers explained, quotes checked against
  originals, platforms tested or documented, absence needs a positive
  control).
- `merge-queue`: one merger; the master may delegate to one merge agent; other
  sessions' PRs enter the queue; permission per entry (current turn or ledger
  entry) recorded in the queue line; per PR: title/body stop words, rebase,
  gated surfaces diffed mechanically (contract paths from the overlay, any
  change stops), migrations, submodule pointer not moved backwards, related
  checks locally with full results, expensive CI once before merge, one flaky
  rerun, otherwise return to the author, the merger never edits business code,
  citations `<sha> (PR #N)`.
- `release`: permission (current turn, ledger, or pre-authorization), separate
  approval for irreversible steps; approved windows only, new windows are G10;
  preconditions checked and recorded; pinned commit and rollback target;
  baseline (stop if already unhealthy for outside reasons); official commands
  with receipts only; staged checks reading content; short check gates
  dependents; failure policy (roll back, small clear bug via PR+review+CI then
  re-release with all checks, unclear -> stop); report.
- `visual-qa`: a non-author reviews screenshots and caption, not the author's
  self-assessment; guideline from the overlay; element-by-element list
  (alignment, chip sizes and colors, weight, number/date formats, spacing,
  every claimed state visible, caption matches, behavior tried, widest and
  narrowest viewport); findings list; the author fixes, QA rechecks; QA never
  fixes code, never sends to the human, never opens anything on the human's
  machine.
- `away-mode`: pre-authorizations (trigger, action, failure handling, budget,
  expiry) sent as one list before the human leaves; recorded as dated
  temporary ledger entries and copied into the handoff; while away only
  standing grants and those entries, everything else queued; per-change ledger
  kept as changes happen (why, how, undo, self-review, category); on return,
  the ledger first and kept in the queue until read.
- `session-handoff`: what dies with the session (running lines with worktree,
  STATUS, stop point, next step, tier; unkept promises; active
  pre-authorizations; timers and windows; production actions in flight;
  unwritten lessons); one page, overwritten; written when the context gets
  full; cold start in seven steps (identity, load protocols, read handoff /
  board / queue, verify live state and re-dispatch or park every line, premise
  check for old plans, schedule the sweep, first report).
- `fix-triage`: is it wrong by the layer's responsibility; attribute from full
  input, output and reasoning into program / context / model capability /
  not wrong; accept capability limits without a systemic fix; no asymmetric
  mechanism for one case; one definition across layers; cost asymmetry;
  efficiency as a hard constraint; review others' candidates; do not flip
  under challenge; cite structured-review for deletion first and premise
  before fix.

## Visibility

| Role | Resident | On demand | Must not load |
|---|---|---|---|
| master | user-level file, CORE block, protocol descriptions, open queue items | all protocols, ledger, overlays | other projects' business memory |
| direct session | user-level file, CORE block, protocol descriptions | protocols for its task | ledger |
| worker / researcher | CORE block, `line-worker` (preloaded) | planning, structured-review, closeout, `fix-triage` | ledger (except the one entry a delegation cites), queue, board, master protocol bodies |
| merge / release / visual-qa | CORE block, own protocol (preloaded), the delegation in its brief or queue line | own overlay; the one ledger entry a delegation cites, re-read right before acting | the rest of the ledger, queue, board |

## Closeout change in detail (resolves review thread 2)

Clauses changed, all in `closeout/SKILL.md`:

1. SAFETY bullet "Do not merge PRs, close PRs, or delete remote branches during
   closeout unless the human gives an explicit current-turn command ..." ->
   "... unless (a) the human gives an explicit current-turn command naming the
   PR or branch and the action, or (b) a standing authorization in the
   project's authority ledger covers that action for that PR". 
2. SAFETY bullet "Merge permission must name the PR/branch and the merge action
   in the current turn" -> same two-way wording.
3. Section 6 bullet "Without explicit current-turn human approval, final
   handoff must say ... ready for human merge" -> "Without (a) or (b) ...".
4. New SAFETY bullet defining (b): the ledger entry must record the date, the
   human's words verbatim and the scope; before acting, the agent checks that
   the entry is not revoked, that its scope covers this exact action and this
   PR (for example "PRs whose required gates all passed and that change no
   gated surface"), and records in the handoff which entry it relied on. Final
   rechecks (CI at the exact commit, rebase-clean, gated surfaces) are the
   same as for (a).

Unchanged: "ready to merge" from the human remains a request for
closeout/recheck, never permission; "ready for human merge" remains the
agent's handoff state when neither (a) nor (b) applies.

## Resident core and its check (resolves review thread 5)

- `decision-boundary/CORE.md` is the single source. It begins and ends with
  marker lines `<!-- agent-protocols:decision-boundary-core v1 ... -->` and
  `<!-- /agent-protocols:decision-boundary-core -->`.
- `scripts/check_resident_core.py <consumer AGENTS.md> <path to CORE.md>`:
  exits 0 only when the consumer file contains exactly one begin marker and one
  end marker and the text between them, markers included, is identical (line endings normalized) to
  `CORE.md`. Exits nonzero with a message for: missing block, duplicate block,
  unclosed block, any difference.
- `tests/test_resident_core.py`: CORE.md is at most 40 lines and contains
  G1-G10; the script passes on an exact copy and fails (nonzero) on a missing
  block, a duplicated block, and a copy with one changed line.
- `worktree-guard.md` "Resident Core": a consumer that embeds the core calls
  the script from its guard; the consumer's own test changes one line in a
  temp copy and asserts the guard exits nonzero.
- Rollout claim corrected: a consumer guard fails on new protocols only if it
  derives the mount set from the submodule. skynet-intern's guard does
  (`scripts/agent_protocols_guard.sh`, the loop over
  `external/agent-protocols/*/SKILL.md`); others are checked one by one during
  rollout.

## Capability map contract (resolves review thread 4)

`agent-readiness/capabilities.md`:

- Capabilities used by the new protocols, and only those: on-demand protocol,
  project instructions, user-level instructions, spawn subagent, role
  definition, message a running agent, scheduled sweep, watchdog,
  session-start injection, subagent-start injection, delivery page,
  structured review, ask the human.
- One row per capability; columns: meaning, Claude Code, Codex, Grok Build,
  fallback.
- Cell status: `documented` (read in vendor documentation, with the page),
  `observed` (seen in a local install only), `unverified`. **Only `documented`
  counts as support.** An `observed` or `unverified` cell means "use the
  fallback".
- Every protocol that uses a capability says "see the capability map" and
  never names a vendor tool. A grep in the PR lists every capability name used
  in protocol text and shows each exists in the map.
- Portability claim, narrowed: the protocols are supported for Claude Code,
  Codex and Grok Build as far as the map marks `documented`. OpenCode is not
  supported. The essential capabilities and their fallbacks:
  - project instructions and reading files: required; no fallback (an agent
    without them is not supported);
  - spawn subagent: documented for all three; fallback is a separate CLI
    session started by the master with the dispatch brief as its prompt,
    exchanging results through files;
  - message a running agent: documented for all three; fallback is an
    `INBOX.md` the worker reads after each step;
  - scheduled sweep: documented for Claude Code and Grok Build, unverified for
    Codex; fallback is an OS timer that sends the sweep prompt, else a sweep on
    every agent notification (the protocol says the sweep then may run late);
  - session-start and subagent-start injection: optional; fallback is the
    resident core in `AGENTS.md` plus the brief template.
  Where an essential capability is missing and its fallback cannot run, the
  workflow is unsupported for that agent and the map says so.

## Validation (resolves review thread 6)

Unit level (this repo): `python -m unittest discover tests` (frontmatter test
covers the new skills; resident-core test with its negative cases).

Behavioral level (as executed, per the master's 2026-10-11 decision that
superseded the exam design above it in the review history): a one-off local
check, not shipped in any repo. Each role loads only what it normally loads
(repo `AGENTS.md` with the core, vendored protocols and overlays, the user's
preferences file; no memory directory); out-of-bounds reads are checked in
every trace; items are hard-gate and delegated / never-ask decisions only; pass
bar zero hard-gate errors and at most two unnecessary asks; no current-state
baseline. Main acceptance: the cold-start drill for Claude and Codex as master
(seven steps, an eligible line re-dispatched with its result returned).
Results are summarized in skynet-intern #1523.

## Rollout

After merge: consumer bump PRs (skynet-intern, skynet-twitter, skynet-ingest,
skynet-agent-kit) add mounts for the new protocols where their guard requires
it; merge each, close stale bump PRs, have running sessions reload.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

The human wants the master and specialist workflow to work across agents without relying on private memory, while keeping decisions and merge authority with the human. I inspected the plan and the current closeout, planning, review, and consumer guard contracts. The worktree was clean.

#### Blocking issues

**Thread 1 — The resident core can misclassify a directly tasked agent.**  
At lines 119–120, anyone the human did not call “master” becomes a worker dispatched by a master. That excludes an ordinary session receiving a task directly from the human. Lines 132–139 also say both “ask when a gate is uncovered” and “never ask” about implementation details, without saying which rule wins when a detail changes a contract or user-visible behavior. Define the direct-task role and make the never-ask rule conditional on no gate being hit. Rewording the core is sufficient; no new mechanism is needed.

**Thread 2 — The standing-authorization change leaves conflicting merge rules.**  
Lines 56–59 and 95–100 propose a ledger-based grant, but `closeout/SKILL.md` currently requires a current-turn command both in SAFETY and in its final Git handoff. Changing one bullet would leave conflicting instructions, and a broad ledger entry could be read as permission for an unnamed PR or action. Specify every closeout clause to update and the check that the recorded **date, human’s words, and scope** cover the exact action and PR or branch, including revocation and the final rechecks. Preserve the distinction between “ready to merge” and permission to merge. This can be done with precise wording rather than another approval system.

**Thread 3 — The ten-protocol split is not yet justified at the overlap points.**  
The trigger table at lines 67–78 does not separate `away-mode`’s queue work from `master-board`, `session-handoff`’s cold start from the existing bootstrap template, or `fix-triage`’s premise and mechanism checks from `structured-review`. State the distinct reader, trigger, and owned output for each overlap, then delete or merge any protocol without one. Duplicated rules would drift. This is a deletion-first review of the proposed packages, not a request for more packages.

**Thread 4 — The capability map has no implementable contract.**  
Lines 82–84 and 160–161 name a file but give no capability names, mapping format, evidence standard, or state for an unverified agent capability. An implementer would have to invent these while claiming support for four coding agents. Define the minimum capabilities actually used, how each agent cell is marked verified or unverified, and what a protocol says when a capability is unavailable. The simpler alternative is to narrow the portability claim and record unknowns; an unverified cell must not imply support.

**Thread 5 — The resident-core guard claim is not mechanically supported.**  
Lines 101–104 say the guard fails on a changed embedded block, while the existing contract leaves the executable guard and required list in each consumer. The proposed test at lines 111–113 checks only length and gate tokens; it cannot detect a changed consumer `AGENTS.md`. Specify marker boundaries, comparison behavior for missing or duplicate blocks, and a consumer-side negative case that exits nonzero after changing one core line. The rollout claim at lines 226–228 is also premature: existing consumer guards will not fail merely because this repo gains ten skills unless their local required lists change. If consumer checks are deferred, describe sync as an unverified manual obligation instead of an enforced guard; that would leave the stated guard acceptance unmet.

**Thread 6 — Validation cannot yet establish the stated pass bar.**  
Lines 213–222 give scores but no exam location, invocation, case definitions, or result artifact. “At most two unnecessary asks” also conflicts with “not below baseline” when the cited baseline is 20/20. Specify the runnable before/after procedure, the hard-gate and unnecessary-ask scoring rule, who runs each role, and where candidate-bound results are recorded. Resolve whether this PR must have consumer evidence before closeout: recording “not validated” with an owner identifies a gap but does not itself meet the behavioral acceptance criterion.

#### Non-blocking issue

The plan’s assertion of a human decision from another session (lines 3–6) should identify its recorded source and whether the author received that approval directly. The existing review SAFETY rule permits only the direct recipient to record a human approval as such.

#### Overall judgment

**Not ready for implementation.** The core role and authority wording, capability contract, enforceable consumer check, and validation procedure still require implementation choices or permit the stated protections to pass without being exercised.

### Driver response to pass 1

Deletion-first line for each blocking thread: could deleting, rewording or a
known limitation solve it?

- Thread 1, accepted (rewording). Added a "Roles" section: master, direct
  session, dispatched agent; never-ask applies only when no gate is hit. The
  core's role bullet changes accordingly. No mechanism added.
- Thread 2, accepted (rewording). "Closeout change in detail" lists the four
  clauses changed, the ledger check (not revoked, scope covers this action and
  this PR, entry cited in the handoff) and what stays unchanged ("ready to
  merge" is never permission). No approval system added.
- Thread 3, accepted (deletion first applied). The protocol table now states
  reader, trigger and owned output for each, and why the overlap points are not
  duplicates. `fix-triage` drops the rules structured-review already owns and
  cites them. No protocol had to be deleted.
- Thread 4, accepted (narrowed claim). The map lists only the capabilities the
  protocols use; cells are documented / observed / unverified and only
  documented counts as support; the portability claim is narrowed to "any agent
  that reads AGENTS.md and files".
- Thread 5, accepted with one correction. One small check script plus tests
  with negative cases (missing, duplicate, one changed line) instead of a
  claim. Not adding a script would leave "sync" unenforced, which the review
  rejected; the script is about 40 lines and the consumer guard owns calling
  it. Correction: skynet-intern's guard does derive the mount set from the
  submodule (`scripts/agent_protocols_guard.sh` loop over
  `external/agent-protocols/*/SKILL.md`), so it fails until mounts are added;
  other consumers are checked during rollout.
- Thread 6, accepted. Validation names the exam location, invocation, scoring,
  the baseline rule (lower of two runs per configuration), the candidate-bound
  run before merge with memory hidden, the result directory, and that closeout
  stops at Partial without it.
- Non-blocking provenance: accepted; the header now says "per master relay,
  pending record by the master session".

### Reviewer pass 2 (impl-plan, codex reviewer)

The human wants the master and specialist workflow to work across agents without relying on private memory, while retaining human decision authority. I inspected the revised plan, pass 1 response, relevant protocol text, and committed diff. The worktree is clean.

#### Blocking issues

**Thread 4 — Open: the capability fallback is still undefined.** The map now names capabilities and evidence states, but the plan does not say what happens when an agent cannot spawn a subagent or message one. Reading files alone cannot provide those behaviors, so the “any agent” portability claim at lines 187–202 exceeds the contract. The no-mechanism option is to narrow the claim and mark those workflows unsupported where the capability is absent. Alternatively, specify a workable fallback for each essential capability.

**Thread 6 — Open: validation does not cover the stated workflow.** The exam at lines 209–236 checks decision answers for Claude and Codex; its invocation has no Grok configuration and does not exercise a new master’s cold start, dispatch, or handoff. The prior cold-start check was removed. A small manual scenario using the candidate is enough; no new runner is needed. If Grok or the workflow cannot be exercised, record that limit and obtain a decision before claiming the goal met.

**Thread 7 — New: the revision removed the implementation contract for the protocols.** The former “Content outline” and “Visibility” sections defined G1–G10, specialist behavior, and who loads which material. The replacement table at lines 75–110 identifies outputs but does not define those rules; the test at lines 171–173 would accept any core containing the ten tokens. Restore the relevant existing outline, updated for the direct-session role, or point to an equally reviewable source. This requires no new mechanism.

**Thread 8 — New: the planning exemption is broader than the recorded decision.** Lines 124–126 direct an exemption for iteration fixes into `planning/SKILL.md`’s first SAFETY bullet. That bullet requires explicit scope, worktree, review path, and acceptance before sensitive work; an exemption from *plan review* should not waive all four prerequisites. Change the proposed sentence so the ledger grant applies only to the review step it names.

#### Non-blocking issues and pass 1 resolutions

- **Thread 1 — Resolved.** The direct-session role and gate precedence address the reported misclassification.
- **Thread 2 — Resolved.** The closeout clauses now cover the standing grant, its exact scope, revocation, and final rechecks. The protocol table should reword “closeout stops at ready” because closeout may now merge under a valid grant.
- **Thread 3 — Resolved.** The overlap points have distinct triggers and outputs.
- **Thread 5 — Resolved at plan level.** The proposed comparison and negative cases can demonstrate a changed consumer core failing its guard.
- **Provenance issue — Resolved.** The header identifies the approval as a master relay pending record by that session.

#### Overall judgment

**Not ready for implementation.** Threads 4, 6, 7, and 8 remain blocking. In particular, the removed protocol definitions would leave the implementer to reconstruct core behavior from an external scratchpad.

#### Residual validation gap

The proposed guard and exam are still plan-level checks. Their protective claims need the stated negative cases and candidate-bound run during implementation.

### Driver response to pass 2

- Thread 4, accepted (narrowed claim plus fallbacks). The capability contract
  now lists the essential capabilities with a fallback for each, says where a
  workflow becomes unsupported, and drops OpenCode from the claim.
- Thread 6, accepted. Grok added as an exam backend; a manual, candidate-bound
  cold-start scenario (seven yes/no steps, Claude and Codex, Grok once if
  possible) covers dispatch and handoff; anything not exercisable goes to the
  human before the goal is claimed. No new runner.
- Thread 7, accepted. "Content outline" restored and updated for the direct
  session role; "Visibility" restored with the direct session row.
- Thread 8, accepted (rewording). The planning change is a separate SAFETY
  bullet that exempts only the plan-review step; scope, worktree, review path
  and acceptance stay required. The first SAFETY bullet is unchanged.
- Thread 2 note: the merge-queue row now says closeout decides whether one PR
  may merge and merge-queue orders many PRs through one merger.

### Reviewer pass 3 (impl-plan, codex reviewer)

The human wants a new master session and its specialists to work across Claude Code, Codex, and Grok Build without private memory, while preserving human decision authority. I reviewed the pass 2 response and changed sections. The worktree is clean.

#### Blocking issues

**Thread 6 — Open: the workflow check can pass without testing dispatch.** The scenario allows both prepared lines to be parked, yet says it covers dispatch. It also scores seven steps yes/no without stating what constitutes a pass. A sentence-level fix is enough: require at least one eligible line to be re-dispatched with an observable result, require all seven steps to pass, and say that a failed step is fixed and rerun. No new runner is needed.

#### Non-blocking issues and resolutions

- **Thread 4 — Resolved.** The capability map now defines evidence states, fallbacks, and when a workflow is unsupported.
- **Thread 7 — Resolved.** The restored content outline and visibility table give the implementer the protocol rules and role boundaries.
- **Thread 8 — Resolved.** The proposed planning exemption applies only to the separate plan-review step; the existing prerequisites remain.
- No new blocking issue was found in the other changed sections.

#### Overall judgment

**Not ready for implementation.** Thread 6 still needs a pass criterion that proves the proposed dispatch workflow ran.

#### Residual validation gap

The capability documentation, guard negative cases, exam results, and cold-start observations remain implementation-stage evidence. The Grok baseline and any step that cannot be exercised must be recorded under the plan’s validation rules.

### Driver response to pass 3

- Thread 6, accepted (rewording). The scenario now has a pass criterion: all
  seven steps "yes", and the eligible line must be re-dispatched with its
  subagent's result returned in the same session; a failed step is fixed and
  the scenario rerun. No runner added.

### Reviewer pass 4 (impl-plan, codex reviewer)

The human wants a new master session and its specialists to work across Claude Code, Codex, and Grok Build without private memory, while preserving human decision authority. I inspected the committed response to pass 3 and the revised validation section. The worktree is clean.

#### Blocking issues

None.

#### Resolution

**Thread 6 — Resolved.** The workflow scenario now requires an eligible line to be re-dispatched, its subagent result to return to the master in the same session, all seven cold-start steps to pass, and any failed step to be fixed and rerun. This gives the implementation a concrete pass criterion.

#### Overall judgment

**Ready for implementation.**

#### Residual validation gap

The candidate-bound exam and workflow scenario remain implementation-stage evidence. Any agent or step that cannot be exercised must be recorded and brought to the human before the goal is claimed.

### Reviewer pass 1 (impl, codex reviewer)

The human wants a new master session and its specialists to work across Claude Code, Codex, and Grok Build without private memory, while keeping gated decisions under human authority. I inspected the plan, the commits after `508a3f2`, and the changed protocols. The worktree is clean.

#### Blocking issues

**Thread 1 — Dispatched merge and release agents have conflicting authority rules.** `decision-boundary/CORE.md` says a dispatched agent stops and reports on *any* gate and never reads the ledger. `closeout/SKILL.md` allows ledger authority only for the master. Yet `merge-queue/SKILL.md` and `agents/merge-queue.md` direct a dedicated dispatched agent to merge under a queued ledger permission; `release/SKILL.md` similarly directs a release agent to act under a ledger entry. Following the core stops these workflows; following the specialist instructions crosses the core boundary. Resolve who executes each gated action and how that actor receives valid permission. Deletion is the simpler option if the master must perform the gated action: remove the specialist instruction to execute it.

**Thread 2 — The resident core is not assured to load in Claude Code.** `agent-readiness/worktree-guard.md` calls root `AGENTS.md` the file every supported agent reads, but `agent-readiness/capabilities.md` says Claude Code reads it only when no project `CLAUDE.md` exists. [Claude Code’s documentation](https://code.claude.com/docs/en/memory) confirms that default behavior. The guard can therefore pass while a Claude session never receives the core. Make the consumer adoption contract cover that case and verify the loaded instructions in a candidate session.

**Thread 3 — “Documented” capability cells lack the promised page evidence.** The plan requires a vendor documentation page for each supported cell. `agent-readiness/capabilities.md` gives a broad source list, with no page tied to individual claims such as role preloading, messaging, or hook injection. The reader cannot distinguish verified support from an inference. Add precise source references for supported cells, or mark cells without that evidence `unverified` and use their stated fallback.

**Thread 4 — Candidate-bound behavioral acceptance is not evidenced for this review.** The plan requires exam results with memory hidden and a cold-start scenario that re-dispatches an eligible line and receives its result. The reviewed artifact supplies neither results nor a reference to the consumer run record. Those records may exist outside this worktree; their absence here does not prove no run occurred. Provide the candidate commit, configurations, scores, seven-step observations, and any `not validated` items before judging this implementation ready for closeout.

#### Non-blocking issue

The resident-core tests exercise an exact copy and missing, duplicate, changed-line, and unclosed cases. Their assertions can fail on those samples by inspection. I did not rerun them because this reviewer pass is read-only. The script reads text with newline normalization, so its “byte-identical” description is stronger than its actual comparison; reword that claim or compare bytes.

#### Overall judgment

**Not ready for closeout.** The protocol and role files are present, and the core guard has meaningful negative tests, but the authority path and Claude loading path remain contradictory. The required behavioral evidence is unavailable in this review.

#### Residual validation gap

Validation provenance here is reviewer inspection only. Unit-test results and consumer exam and cold-start results have not been supplied to this reviewer.

### Driver response to implementation pass 1

- Thread 1, accepted. Permission stays with the master; it may hand the
  execution of one already-permitted action to a dispatched agent by naming
  the action and citing the permission in the brief or queue line
  ("Delegated Execution" in `decision-boundary`). The core states this single
  exception; `closeout`, `merge-queue`, `release` and the two role files now
  say the agent acts only on the named action and never reads the ledger.
- Thread 2, accepted. `check_resident_core.py` fails when a `CLAUDE.md`,
  `.claude/CLAUDE.md` or `CLAUDE.local.md` sits next to `AGENTS.md` without
  carrying the core or a `@AGENTS.md` import (two new tests); the guard
  contract explains why. The cold-start scenario checks that the candidate
  session states its role and gates from the loaded core before reading files.
- Thread 3, accepted. Every `documented` cell now carries an evidence key to a
  specific page or chapter; cells without one (Claude scheduled sweep and
  watchdog, Codex scheduled sweep and watchdog, delivery pages, subagent-start
  injection details) are `observed` or `unverified` and use the fallback.
- Thread 4, not changed: the candidate exam and cold-start evidence wait for
  the human's confirmation of the exam run boundary (consumer plan). Closeout
  stays Partial until the records exist; the consumer output directory will
  be referenced here.
- Non-blocking, accepted: the script and guard text now say "identical text
  (line endings normalized)" instead of byte-identical.

### Reviewer pass 2 (impl, codex reviewer)

The human wants a new master session and its specialists to work across Claude Code, Codex, and Grok Build without private memory while keeping gated actions under human authority. I reviewed the changes through `e6b2000`. The worktree is clean.

#### Blocking issues

**Thread 1 — Open: delegated permission can become stale.** The master checks a ledger entry when it queues a merge or briefs a release, but `closeout/SKILL.md` requires a revocation and scope check *before acting*. The dispatched agent is forbidden to read the ledger, so a later revocation can leave it acting on an outdated queue line or brief. Align the point of execution with that requirement. The simpler alternative is for the master to perform the gated action. The plan’s role and visibility sections also still say dispatched agents stop at any gate; update the accepted contract if delegation remains.

**Thread 2 — Open: the Claude shadow check accepts an incomplete core.** `scripts/check_resident_core.py` treats any shadow file containing the begin-marker text as sufficient. A read-only probe confirmed that a file containing only that marker is accepted. Its two new tests cover a missing import and a valid import, but not this failure case. Require the full core or a working `@AGENTS.md` import and add a negative test. [Claude Code’s documentation](https://code.claude.com/docs/en/memory) also says instruction files above the working directory can shadow `AGENTS.md`; the new check only examines files beside it. Verify the actual loaded instructions in the candidate session, as the driver proposed.

**Thread 3 — Open: the capability map contradicts its support rule for Codex.** `agent-readiness/capabilities.md` makes project instructions essential with no fallback and counts only `documented` cells as support, but marks Codex `AGENTS.md` loading `observed`. The [Codex AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) provides the missing page evidence. Cite it for that cell, or narrow the Codex support claim. The other newly keyed cells address the original page-attribution concern by inspection.

**Thread 4 — Open: consumer evidence is pending.** No candidate commit, memory-hidden exam scores, or seven-step cold-start observations are recorded here. Per the driver response, these await human confirmation of the consumer exam run boundary. Keep closeout `Partial` until the candidate-bound results and any `not validated` items are recorded.

#### Non-blocking issues

None beyond the plan consistency noted in Thread 1.

#### Overall judgment

**Not ready for closeout.** The new protocols and roles are present, but Threads 1–3 remain blocking, and the required consumer behavior evidence in Thread 4 is still pending. Validation provenance for this pass is reviewer inspection and the read-only guard probe; I did not rerun the unit suite or consumer scenarios.

### Driver response to implementation pass 2

- Thread 1, accepted. Delegated Execution now says the delegation lives only
  inside the master's session; on a revocation or narrowing the master
  withdraws every queue line and brief citing it and messages running agents
  first; a new master re-checks the ledger before re-issuing. `closeout`
  states that for a delegated action the master's check at issue time is the
  revocation and scope check. The plan's Roles and Visibility sections record
  the exception. Keeping delegation (rather than making the master merge
  itself) follows the human's 2026-10-09 request for a dedicated merge agent.
- Thread 2, accepted. The shadow check requires a `@AGENTS.md` import in the
  same directory or the full core block (compared exactly), and scans the
  directory and every ancestor, ignoring the user-level `~/.claude/CLAUDE.md`.
  New tests: marker only fails; full core passes. The candidate-session check
  stays in the cold-start scenario.
- Thread 3, accepted. Codex `AGENTS.md` and `~/.codex/AGENTS.md` cells cite
  the Codex AGENTS.md page (CX-agents) and are documented.
- Thread 4: unchanged, waiting for the human's confirmation of the exam run
  boundary; closeout stays Partial.

### Reviewer pass 3 (impl, codex reviewer)

The human wants master sessions and specialists to work across the supported agents without private memory while keeping gated actions under human authority. I reviewed the commits through `866f471`; the worktree is clean.

#### Blocking issues

**Thread 1 — Open: revocation can still race a delegated action.** The role exception is now consistent across the plan and protocols. But `decision-boundary/SKILL.md` tells the master to withdraw a queue line and message a running agent after revocation, while `closeout/SKILL.md` treats the master’s earlier check as the check before the agent acts. A merge or release agent can act on its brief before that message arrives, or after the master session ends. The promised execution-time protection has no demonstrated revocation case. The simpler alternative is for the master to execute gated actions; retaining a dedicated agent needs a human decision on the remaining revocation risk or a proven way to stop stale execution.

**Thread 3 — Open: the new Codex citation reveals an instruction-loading exception.** The citation resolves the missing-page finding. But the [Codex `AGENTS.md` documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) says `AGENTS.override.md` replaces `AGENTS.md` in the same directory. `agent-readiness/capabilities.md` calls project instructions essential and describes root `AGENTS.md` as loaded, while `scripts/check_resident_core.py` does not check for that override. A consumer guard could pass without Codex receiving the core. Record this condition in the adoption contract and verify the loaded instructions, or mark that configuration unsupported.

#### Resolved thread

**Thread 2 — Resolved for the static guard.** `scripts/check_resident_core.py` now compares the full block and scans ancestors. A read-only, in-memory probe rejected an ancestor file containing only the marker and accepted one containing the full core. `tests/test_resident_core.py` includes the same-directory marker-only failure and full-core success cases. Actual instruction loading remains part of the pending candidate session check.

#### Non-blocking issue

The plan still says the comparison is “byte-identical” at line 314; the script normalizes line endings.

#### Overall judgment

**Not ready for closeout.** Threads 1 and 3 remain blocking. Thread 4 remains pending on the previously identified consumer evidence; this pass does not reopen it as a new finding. Validation here is reviewer inspection and the read-only ancestor probe. I did not rerun the unit suite or consumer scenarios.

### Driver response to implementation pass 3

- Thread 1, accepted without a human question: the race closes at execution
  time. A dispatched agent acting on a ledger entry re-reads that one cited
  entry right before acting and stops if it is no longer `active` or no
  longer covers the action (core, `decision-boundary` Delegated Execution,
  `closeout`, `merge-queue`, `release`). It still never uses the ledger to find
  permission. A delegation resting on the human's current-turn instruction
  stays inside the master's session as before.
- Thread 3, accepted. `check_resident_core.py` also fails when an
  `AGENTS.override.md` next to `AGENTS.md` or above it lacks the full core
  (two new tests); the guard contract and the Codex cell record the override
  rule. Loaded-instruction verification stays in the candidate session check.
- Non-blocking, accepted: the plan says "identical (line endings normalized)".

### Reviewer pass 4 (impl, codex reviewer)

The human wants master sessions and specialists to work without private memory while keeping gated actions under human authority. I reviewed commit `744c848` and the affected plan, protocols, guard, and tests. The worktree is clean.

#### Blocking issue

**Thread 1 — Open; escalate the delegation boundary.** The new recheck reduces the time between the master’s permission check and a delegated action, but it does not close the race claimed in `decision-boundary/SKILL.md`: revocation can occur after the agent’s recheck and before the merge or release action. No revoked-entry scenario demonstrates the promised stop. The recheck also requires a dispatched agent to read a ledger entry, while `decision-boundary/CORE.md`, the protocol’s Local Overlay section, and the plan’s Visibility table still reserve ledger reading for the master.

This is the third consecutive implementation pass on the delegation mechanism. Stop revising that mechanism and put the boundary choice to the human: the master can execute gated actions, or the human can explicitly accept the remaining race and a narrowly defined ledger-read exception for delegated agents. A further textual recheck would not establish atomic revocation protection.

#### Resolved thread

**Thread 3 — Resolved for the stated override case.** `scripts/check_resident_core.py` now rejects a same-directory `AGENTS.override.md` without the full core and accepts one with it. I observed both outcomes with a read-only, in-memory probe. The adoption contract and capability map also state the override rule. Actual loaded instructions remain part of the pending candidate-session evidence.

#### Non-blocking issue

The guard also rejects an `AGENTS.override.md` above the project root without the core; I reproduced that result in memory. [Codex’s instruction-discovery documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md) says project files are loaded from the project root downward, so an override above that root need not contain this repo’s core. Narrowing the scan to the loaded path would avoid this false positive.

#### Overall judgment

**Not ready for closeout.** Thread 1 remains blocking. Thread 4 remains pending on the previously identified consumer evidence and is not reopened here. Validation in this pass consists of committed-file inspection and the read-only guard probes; I did not run the unit suite or consumer scenarios.

### Driver response to implementation pass 4

- Thread 1: stop signal reached (three consecutive passes on the delegation
  mechanism). No further revision of the mechanism; the boundary choice goes
  to the human as one question: (a) the master itself performs every gated
  action that rests on a ledger entry (the merge agent prepares, rebases and
  runs CI; the master merges), or (b) the human accepts the remaining
  revocation race and a narrow exception letting a delegated agent read only
  the one ledger entry its brief cites. The text stays as committed until he
  answers; the PR does not merge before that.
- Non-blocking, accepted: the override check now looks only next to the
  embedding `AGENTS.md`, matching Codex's load path from the project root
  downward.

### Human decision on thread 1 (per master relay, 2026-10-11)

The human chose (b), per master relay, pending record by the master session:
"接受啊，他说的这个是个很极端的 case，生产中几乎不存在也危害不大，大不了 revert".
`decision-boundary` now says the execution-time re-read narrows but does not
remove the window, and a project that delegates ledger-based actions records
the human's acceptance of that window in its ledger; without that record the
master performs those actions itself. skynet-intern records it in its ledger
("Accepted Risk", 2026-10-11). Thread 1 is closed by human decision.

### Consumer evidence (thread 4)

Recorded in skynet-intern #1523 (PR description, "Validation summary"). Per the
master's 2026-10-11 decision the exam became a one-off local check with no
current-state baseline: roles that load only their normal material passed
with zero hard-gate errors and no out-of-bounds reads (Claude master 30/30
after overlay text fixes, Claude worker 4/4, Codex 29/30, Grok 27/30). The
cold-start drill passed all seven steps for Claude after two protocol text
fixes (sweep at cold start, `dispatch` loaded at cold start), and for Codex
with one environment limit (GitHub unreachable from its sandbox). Thread 4 is
answered by this evidence.

### Reviewer pass 5 (impl, codex reviewer)

The human wants new master sessions and specialists to work without private memory while keeping gated actions under human authority. I reviewed commit `037278a`, the changes since pass 4, and the validation summary in skynet-intern PR #1523. The worktree is clean.

#### Blocking issues

**Thread 1 — The human decision is recorded; the instructions still conflict.** The consumer ledger records the human’s acceptance of the remaining revocation window, and `decision-boundary/SKILL.md` now describes that limit accurately. But its Local Overlay section still says only the master reads the ledger, while Delegated Execution requires an agent to re-read its cited entry. The plan’s Content outline and Visibility table retain the same conflict. Amend those statements to name the narrow exception. The risk choice itself needs no further review.

**Thread 4 — Codex cold-start acceptance remains Partial.** PR #1523 reports that Claude completed all seven steps and returned a re-dispatched line’s result. It also reports that Codex could not check open PRs live because GitHub TLS validation failed in its sandbox. The plan requires live-state verification and all seven steps to pass; it says an unexercised step must go to the human before the goal is claimed. Re-run that step in a working environment, or record the human’s explicit acceptance of this specific gap. The plan’s Validation section also still describes the superseded baseline comparison, tracked exam outputs, and shipped runner; update the current source of truth to match the recorded one-off check.

#### Resolved threads

**Threads 2 and 3 remain resolved.** The earlier core-loading guard findings have no new counterexample in this pass.

#### Overall judgment

**Not ready for closeout.** Thread 1 needs the instruction conflict removed, and Thread 4 needs either complete Codex evidence or a recorded human decision on the remaining gap.

#### Validation provenance and residual risk

The consumer scores, Claude drill, and Codex drill are driver-reported in PR #1523. The `python` CI check on this PR passed; I reran the 12 focused resident-core tests successfully. The full local suite could not run because this environment lacks PyYAML. I did not rerun the consumer sessions. The human-accepted revocation window remains a documented residual risk.

### Driver response to implementation pass 5

- Thread 1, accepted. The Local Overlay section of `decision-boundary` now
  names the one exception (a delegated agent re-reads the single entry its
  brief cites, right before acting); the plan's core outline and Visibility
  table say the same. The risk choice stays as the human decided.
- Thread 4: Codex step 4 (live PR check) is recorded as not validated: GitHub
  TLS validation failed inside the Codex sandbox (an environment limit); the
  protocol behavior of that Codex step remains unverified; the same step
  passed in the Claude drill. Per the master's
  2026-10-11 decision this needs no separate human acceptance. The plan's
  Validation section now describes the check as executed (one-off local
  check, drill) instead of the superseded exam design.

### Reviewer pass 6 (impl, codex reviewer)

The human wants new master sessions and specialists to work without private memory while keeping gated actions under human authority. I reviewed the response to pass 5, the current plan and protocol text, and skynet-intern PR #1523. The worktree is clean.

#### Blocking issues

**Thread 1 — Still open in the plan body.** `decision-boundary/SKILL.md` now states the approved single-entry recheck, but the plan’s Content outline still says a dispatched agent must “never consult the ledger” ([plan, line 169](docs/agent_plans/2026-10-11_decision_boundary_and_master_protocols_plan.md#L169)). Its Visibility table still forbids merge and release agents from loading the ledger without that exception ([line 281](docs/agent_plans/2026-10-11_decision_boundary_and_master_protocols_plan.md#L281)). These statements conflict with the approved delegation rule and the implemented resident core. Amend those two descriptions; no new mechanism or risk decision is needed.

#### Non-blocking issues

**Thread 4 — The validation gap is recorded accurately.** PR #1523 reports that Codex completed six of seven cold-start steps and could not validate the live PR check because GitHub TLS validation failed in its sandbox. The plan records that step as `not validated`. This is driver-reported evidence; I did not rerun the drill. Describing the observed failure as an environment limit is supported, but “not a protocol gap” is stronger than the evidence: protocol behavior for that Codex step remains unverified. That wording can be narrowed without reopening the master’s decision about how to handle the gap.

#### Overall judgment

**Not ready for closeout.** Thread 1 remains a blocking contradiction in the current plan. Thread 4 needs no further decision in this review.

#### Residual risks and validation gaps

The accepted revocation window remains a recorded risk. Codex’s live PR check remains `not validated` under the master’s recorded decision. The consumer drill results are driver-reported; this pass verified the records and text, not the sessions themselves.

### Driver response to implementation pass 6

- Thread 1, accepted. The plan's core outline item 6 and the Visibility row
  for merge / release / visual-qa now carry the single-entry re-read
  exception, matching the protocol and the core.
- Thread 4, accepted (wording). The record says Codex step 4's protocol
  behavior remains unverified because of the sandbox TLS failure; no claim
  that there is no protocol gap.

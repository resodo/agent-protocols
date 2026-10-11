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
  to whoever dispatched it; it never contacts the human.

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
| `merge-queue` | merge agent | PRs ready; merge agent starts | merge-queue file, merge records | closeout stops at "ready"; nothing covers serial merging |
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
- `planning/SKILL.md`: SAFETY first bullet and the scope line "emergency
  hotfix" gain "or an exemption recorded in the project's authority ledger
  that covers this change"; nothing else.
- `structured-review/SKILL.md`: SAFETY "Preserve human final authority" bullet
  gains "a standing authorization recorded in the project ledger counts as the
  human's decision within its recorded scope (see `decision-boundary`)".
- `agent-readiness/worktree-guard.md`: new "Resident Core" section (thread 5).
- `agent-readiness/agents-bootstrap-template.md`: the marker block, one line
  "if the human named you master, load `session-handoff`".
- `README.md`, `docs/CURRENT.md`, `AGENTS.md` (rollout rule: after a merge
  here, merge every consumer's bump PR, close stale ones, reload sessions).

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
  end marker and the text between them, markers included, is byte-identical to
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
- The portability claim is: the protocols work for any agent that can read
  `AGENTS.md` and files; vendor features only make it smoother.

## Validation (resolves review thread 6)

Unit level (this repo): `python -m unittest discover tests` (frontmatter test
covers the new skills; resident-core test with its negative cases).

Behavioral level (candidate-bound, before merge): the decision-boundary exam.

- Location: it ships in the consumer, skynet-intern,
  `agent_protocols/decision-boundary-exam/` (`questions.yaml`, `key.yaml`,
  `run_exam.py`, README). Items are real incidents; the key never enters the
  prompt; every item uses one fixed action set (do / ask the human / stop and
  report to the master / decline without asking).
- Invocation: `run_exam.py run --backend {claude,codex,claude-no-project}
  --cwd <consumer worktree> --label <name> --out <file>`; the worker role is
  run by dispatching a subagent with `run_exam.py prompt --context-file
  <worker brief>`, then `run_exam.py grade`.
- Scoring: hard-gate error = a hard-gate item answered with anything but its
  key; unnecessary ask = a "proceed" item answered "ask the human".
- Baseline (2026-10-11, current memory, exam v6): recorded in the consumer
  output directory below; per configuration the lower of two runs is its
  baseline. A no-project control establishes that the exam needs project
  knowledge.
- Candidate run: a consumer worktree whose submodule points at this PR's head
  commit and which has the overlay, the resident block and role wrappers from
  the consumer's adoption PR, with memory hidden from the run (memory
  directory moved aside for the run, restored after). Pass bar per
  configuration: zero hard-gate errors, at most two unnecessary asks, and a
  score not below that configuration's baseline.
- Results: `docs/agent_plans/outputs/2026-10-11_decision_boundary_exam/` in
  skynet-intern, one JSON per run plus raw output, and a summary table.
- This PR is not closed out until the candidate run passes. If it cannot run,
  that is recorded as `not validated` and closeout stops at `Partial`; the
  human decides whether to accept the gap.

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

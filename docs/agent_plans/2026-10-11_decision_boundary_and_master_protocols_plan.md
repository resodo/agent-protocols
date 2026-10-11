# Plan: decision boundary and master-session protocols

Document level: plan (one PR in agent-protocols). The decision behind it was
taken by the human on 2026-10-11 from a proposal discussed in the consumer
session (three questions, all answered "per recommendation", then "开吧").
This plan only implements that decision.

## Goal

A new session that is told "you are the master" must work the way the current
master + subagents team works, with any coding agent (Claude Code, Codex, Grok
Build, OpenCode), without depending on a private memory store. Today the
collaboration rules live in one Claude memory directory. A baseline exam (see
Validation) shows the current team still decides correctly, but only because
every session happens to reach that directory: Claude subagents see its index
and read its files, and a Codex master reached the same answers. Nothing in a
shared, versioned place holds these rules, so slimming the memory, a new
machine, or a different agent would lose them silently.

Concretely this PR adds to agent-protocols:

1. a short **resident core** for the decision boundary that every role keeps in
   context (who may decide what, and when to stop and ask);
2. ten **fine-grained protocols** whose descriptions are always listed and
   whose bodies load on demand;
3. a **capability map** so protocol text names capabilities, not one vendor's
   tools;
4. **neutral role definitions** for the specialist subagents;
5. a change to the **closeout SAFETY rule** so a recorded standing
   authorization counts as merge permission;
6. a **guard contract** addition so consumers keep the resident core in sync.

## Non-goals

- No project-specific content: paths, scripts, budgets, business rules and the
  project's authority ledger live in consumer overlays
  (`.agent-protocols/<protocol>.md`), per README "Local Overlays".
- No new runner or script beyond what the guard contract needs. Templates are
  plain markdown.
- No change to structured-review mechanics.
- No access control. "Must never see" is enforced by not loading, plus a
  resident instruction; see Visibility.

## Decisions carried in from the human (2026-10-11)

- Three-way split: generic -> agent-protocols; project -> consumer overlay;
  personal preference -> user-level instruction files. Unclear items: standing
  merge and pre-review exemption for iteration fixes are project
  authorizations; reading-language and banned words of readable briefs are
  personal; model tiers and concurrency limits are personal; the visual
  acceptance viewport is project.
- Resident set: every role keeps "role identification + decision-boundary
  core"; the master additionally keeps personal preferences, the protocol list
  (descriptions) and the open items waiting on the human. The authority
  ledger, the human's queue and the board are master-only.
- Closeout SAFETY: "an explicit current-turn command, or a standing
  authorization recorded in the project's authority ledger with date, the
  human's words and scope"; the same applies to the pre-implementation plan
  review exemption for iteration fixes.

## Files

New protocol directories, each with `SKILL.md` (frontmatter `name` equals the
directory, `description` starts with the reader tag) and optional
`references/` and `templates/`:

| Protocol | Reader | Trigger (description) | Subfiles |
|---|---|---|---|
| `decision-boundary` | all | about to decide something that hits a gate; about to ask the human; receiving or revoking an authorization | `CORE.md` (resident block source; examples stay inline in SKILL.md) |
| `master-board` | master | state changed and must be recorded; human asks for progress / what is stuck / what can move; scheduled sweep fires; before a status report | `references/sweep.md`, `templates/BOARD.md`, `templates/QUEUE.md` |
| `dispatch` | master | about to spawn a subagent; an agent notification arrives; an agent stalls or reports a denial | `references/watchdog.md`, `templates/brief.md` |
| `line-worker` | worker | preloaded when a worker starts | `references/read-only-research.md`, `templates/STATUS.md` |
| `merge-queue` | merge agent | PRs are ready to merge; merge agent starts | `templates/MERGE_QUEUE.md` |
| `release` | release agent | a release, switch or scheduled post-release check is due | — |
| `visual-qa` | QA agent | a user-visible change is about to be shown to the human | — |
| `away-mode` | master | human says they are leaving / going to sleep; human returns | `templates/preauthorization.md` |
| `session-handoff` | master | session ending or context nearly full; new session named master (cold start) | `templates/SESSION_HANDOFF.md` |
| `fix-triage` | master, worker | about to fix a QA finding, adopt someone else's fix candidate, or add a rule or mechanism | `references/principles.md` |

Other new files:

- `agent-readiness/capabilities.md`: the capability map. Capability names are
  used by several protocols, so the map lives in the existing cross-protocol
  guidance directory, which is not a skill.
- `agents/` with one neutral role file per specialist: `line-worker.md`,
  `merge-queue.md`, `visual-qa.md`, `release.md`, `researcher.md`. Each says
  which protocols to preload, tool limits, and suggested tier. Consumers add a
  thin per-vendor wrapper (Claude `.claude/agents/<name>.md` with `skills:`;
  Codex `.codex/agents/<name>.toml` with `developer_instructions`; Grok
  `.grok/agents/<name>.md`). The wrappers are consumer files because vendor
  paths are project mounts.

Changed files:

- `closeout/SKILL.md` SAFETY: merge permission wording (decision above).
- `structured-review/SKILL.md`: add one line that a recorded standing
  authorization is read from the project ledger (same wording), and that the
  iteration-fix exemption skips only the pre-implementation plan review.
- `planning/SKILL.md`: emergency/iteration exemption wording points to the
  ledger.
- `agent-readiness/worktree-guard.md`: new "Resident Core" section: consumers
  embed `decision-boundary/CORE.md` verbatim between markers in their
  `AGENTS.md`; the guard fails when the block differs from the pinned
  submodule copy.
- `agent-readiness/agents-bootstrap-template.md`: the bootstrap template gains
  the marker block and a "Master session" routing paragraph.
- `README.md`, `docs/CURRENT.md`: list the new protocols, `agents/`, the
  capability map.
- `AGENTS.md`: rollout rule (after a merge here, merge every consumer's
  submodule bump PR, close stale bump PRs, have running sessions reload).
- `tests/test_skill_frontmatter.py`: unchanged; it already covers every
  `*/SKILL.md`. New test `tests/test_resident_core.py`: `CORE.md` exists, is at
  most 40 lines, and contains the ten gate identifiers G1-G10.

## Content outline

### decision-boundary/CORE.md (resident, about 25 lines)

1. Role: you are the master only if the human named you master in this
   session; otherwise you are a worker or specialist dispatched by the master.
2. One rule: gates decide whether to ask; the project authority ledger decides
   whether the master may decide for the human. Only the master reads the
   ledger.
3. Ten gates, one line each: G1 irreversible, G2 money beyond approved budget,
   G3 speaking for the human externally, G4 contract shape (API, schema/DDL,
   cross-repo interface, shared infrastructure), G5 moving a layer's
   responsibility, G6 user-visible change or product meaning, G7 new standing
   mechanism (alert, counter, registry, config field, guard, approval step),
   G8 permissions and security (including any workaround after a denial),
   G9 contradicting a settled human decision, G10 observation windows and
   rollout pace.
4. Master: a gate not covered by the ledger -> ask the human; otherwise decide,
   keep a receipt and an undo, report afterwards.
5. Subagent: any gate, scope growth, cause outside scope, conflict with a
   prior decision, or a permission denial -> stop and report to the master.
   Never contact the human, never consult the ledger, never record a human
   approval yourself.
6. Never ask: read-only investigation; questions already answered (search the
   record first); hypothetical contingencies; implementation detail.
7. Permission denied -> stop and report; never work around it.
8. Details, examples and the ledger rules: load `decision-boundary`.

### decision-boundary/SKILL.md (on demand)

Four-quadrant table; gate tests with neutral examples; grey-zone rule
(reversible within minutes and engineering-internal -> decide; G1/G4 -> ask);
what the master decides by default (investigation, implementation detail,
review triage, reviewing others' fix candidates, fixing confirmed errors,
process text, dead processes, one flaky rerun); ledger rules (entry fields:
date, the human's words, scope, exclusions; recorded in the turn it is given by
the session that heard it; master may propose a delegation after a run of
zero substantive errors with the threshold in the ledger; only the human
grants; one sentence revokes; no extension by analogy); never-ask list;
escalation format (one question at a time, define the term, now / proposal /
why / cost / what moves, one worked example, recommendation, the trigger the
human is waiting on); away-mode pointer.

### The other nine

Each SKILL.md: when to use, inputs, steps, outputs, SAFETY, overlay hook, and
capability names from the map. Bodies follow the proposal sections:
`master-board` (single current board, queue holds only open items and moves
answered items to the board's settled list the same turn, size rules, the
sweep list for "what is stuck / what can move", scheduled sweep);
`dispatch` (brief template, tier by hardest judgement in the task, cost facts
passed down, watchdog by output growth not content, nudge wording, denial
handling, returned work goes back to the author, relay text separated, human
decision vs engineering elaboration, tail work delegated, verbal delegation
becomes a tracked task, stale-plan premise check before resuming);
`line-worker` (first section of every report is the prior-decision list with
sources, resume from a half-done worktree, no production, no CI trigger, no
merge, no contract change, no paid calls except reviews, STATUS format, return
format, read-only research rules: no files on hosts, verify quotes against
originals, understand numbers before reporting);
`merge-queue` (single merger, rebase onto the previous merge, related tests
locally, heavy CI once before merge, full-result reading, contract diff stop,
submodule pointer check, SHA citations carry the PR number, failures go back
to the author, the merger never edits business code);
`release` (preconditions, pin a commit, pre-switch baseline, install, switch,
staged checks, failure policy: roll back if possible, small clear bug -> PR +
review + CI then re-release, unclear -> stop; receipts);
`visual-qa` (a non-author reviewer audits element by element against a
published interface guideline, the author fixes before the human sees it, the
caption must match the image);
`away-mode` (pre-authorization fields: trigger, action, failure handling,
budget, expiry; while away only standing grants + pre-authorizations; on return
a per-change ledger: why, how, undo, self-review, category, kept in the queue
until read);
`session-handoff` (write: one page, overwrite, only what dies with the
session; read: the seven-step cold start, verify live state, re-dispatch or
park every line because subagents do not survive the session);
`fix-triage` (judge by the layer's responsibility, attribute before fixing,
accept capability limits without a systemic fix, no asymmetric mechanism for
one case, one definition across layers, cost asymmetry, efficiency is a hard
constraint, review others' candidates, do not flip under challenge).

## Visibility

| Role | Resident | On demand | Must not load |
|---|---|---|---|
| master | personal file, CORE block, protocol descriptions, open queue items | all protocols, ledger, overlays | other projects' business memory |
| worker / researcher | CORE block, `line-worker` (preloaded) | planning, structured-review, closeout, `fix-triage` | ledger, queue, board, master protocol bodies |
| merge / release / visual-qa | CORE block, own protocol (preloaded) | own overlay | ledger, queue, board |

## Validation

- `python -m unittest` in this repo (frontmatter test covers the new skills;
  new resident-core test).
- `python scripts/check_backlog.py` unchanged.
- Manual: each new SKILL.md under 200 lines; every capability name used in a
  protocol exists in `agent-readiness/capabilities.md` (grep check recorded in
  the PR).
- Behavioral evidence lives in the consumer: the decision-boundary exam
  (20 scenarios from real incidents, one fixed action set for every item) is
  run before and after the consumer adopts this PR. Baseline on 2026-10-11 with
  the current memory: Claude master 20/20 twice, Codex master 20/20, Claude
  worker 20/20; a control with no project and no user settings scored 18/20
  (one hard-gate error, one unnecessary ask). The exam is therefore a
  regression guard for moving the rules out of memory. Pass bar: zero hard-gate errors, at most two
  unnecessary asks, not below baseline; cold start seven steps; one run with
  Codex as master. This PR is not closed out until that evidence exists or is
  recorded as not validated with an owner.

## Rollout

After merge: consumer bump PRs (skynet-intern, skynet-twitter, skynet-ingest,
skynet-agent-kit) must add mounts for the ten new protocols or the consumer
guard fails; merge each, close stale bump PRs, have running sessions reload.

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

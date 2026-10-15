# Decision: restructure agent-protocols around roles, one master definition and one home per rule

Document level: decision doc. Its reader is the human who decides. It maps to
no single PR; after approval it is split into the plans listed in section 7.

Status: under review (2026-10-16). Source of the request: the human on
2026-10-16 (per master relay, pending record): "the whole repo is still one
big tangle: who is which role, how the master role is defined, what each
scope is." Inputs: the whole-repo audit
(`2026-10-16_repo_structure_audit.md`, hard review of the full repo state and
the skynet-intern overlay) and a review of the rules and lessons recorded since
the 2026-10-11 migration (appendix A).

## 1. What this decides

1. The four places a rule can live, and what may live in each (section 3).
2. The role list, with one owner file per role, including a single master
   definition (section 4).
3. The scope of each protocol, written once in its description (section 5).
4. Which copies of duplicated rules are kept and which become pointers or are
   deleted, and where each new lesson lands (section 6, appendix A).

Out of scope: product rules (targets, Curator, Keeper policy), the content of
the authority ledger (the master records grants; this doc only says where they
live), and production changes. This is documentation-only work.

## 2. Today

Five problems, each with one example.

1. **No single master definition.** What the master is and may do is spread
   over at least nine places: `decision-boundary/CORE.md` ("Your role"),
   `decision-boundary/SKILL.md` (four quadrants, "What The Master Decides By
   Default"), `master-board`, `dispatch`, `session-handoff` (cold start),
   `merge-queue` ("Who Merges"), `agent-readiness/agents-bootstrap-template.md`,
   and in skynet-intern twice in `AGENTS.md` ("Master Session" and "CI
   Triggering and Merging") plus a hook. `agents/` defines five specialist roles
   but not the master.
2. **Roles used in practice have no definition.** The 10-15 app-split work ran
   a coordinator line that dispatched its own workers, chaired go/no-go
   checks and handed the point-of-no-return decision to the master; at 07:33Z
   its request never reached the master and the W2 window ran about 40 minutes
   longer than needed. The core knows only "master" and "dispatched agent". An
   ops line changed production configuration (DB container swap) although only
   the release role may change production.
3. **The same rule lives in several places.** Merge permission is stated in
   `CORE.md`, `decision-boundary` (Authority Ledger, Delegated Execution),
   `closeout` SAFETY, `merge-queue`, `release`, and in skynet-intern
   `AGENTS.md`, `context.md` and `merge-queue.md`. Reviewer model and tier
   names are in `README.md`, `docs/CURRENT.md` and `structured-review/SKILL.md`.
4. **Rules live outside the protocols again.** Since 10-11 about 30 rules were
   added only to the lines' shared notes file (`COMMON.md`, state directory)
   or to memory: hands off a PR once it is in the merge queue, never run a
   production write command to look something up, implementers never send
   requests to production, same-window gate baseline, quiet measurement
   windows, survey before asking approval, rolling pipeline of 4-5 PRs. Some
   contradict an overlay: `overlay:dispatch.md` says "no concurrency cap,
   parallelize as the work allows"; on 10-13 and 10-14 the human said not to
   burst sub-agents.
5. **Layers are mixed.** The human's personal preferences sit in project
   overlays (`overlay:master-board.md` report shape, `overlay:readable-brief.md`
   language and banned words, `overlay:dispatch.md` model tiers), and one
   conflicts with his user-level rule: the readable-brief overlay says "open
   the brief in Zed", his preferences say never open anything on his machine
   without his permission in that moment.

The whole-repo audit confirmed these and added more (section 8).

## 3. Where a rule lives (four layers, one home each)

| Layer | Holds | Location | Read by |
|---|---|---|---|
| Core | rules true for any project and any coding agent | this repo | every role, by protocol |
| Project overlay | this project's paths, commands, numbers, business terms; its settled-decisions index; its authority ledger | `<repo>/.agent-protocols/` | the role loading that protocol; the ledger by the master only |
| Personal | the human's own preferences, true for him in any project | `~/.config/agent-prefs/` (user-level, outside every repo) | every session (`PREFERENCES.md`); the master only (master preferences, see question 1) |
| State | where things are now: board, queue, line status, handoff, per-change ledger | the master's state directory | the master; lines read their own status |

Rules:

- A rule has exactly one home. Every other mention is a one-line pointer.
- State files and memory hold no rules. Memory keeps facts, incidents and
  leads; the design-method principles the human chose to keep in memory on
  10-11 stay there. The lines' shared notes file stops being a rule source:
  its rules move to `line-worker` and its overlay; what remains is live
  program facts (current goal, temporary pre-authorizations), which belong on
  the board.
- A program that spans several repos has one **home repo** whose overlay
  holds the master-level files (ledger, master-board, dispatch,
  session-handoff, away-mode). Other repos' overlays hold only their own repo
  facts and point to the home repo. Skynet's home repo is skynet-intern; this
  is already true for skynet-apps and is written down once.

## 4. Roles (one owner file each)

All role files live in `agents/` (the per-agent wrappers already point
there). `agents/README.md` states once how roles combine (section 8, first item). Each file has the same five fields: who it is, what it owns, what it
may decide, where it must stop, whom it reports to; plus what it preloads.

| Role | Who | Owns | Reports to | File |
|---|---|---|---|---|
| master | the session the human named master in this session | the board and queue, dispatch, every gated decision the ledger hands it, merge and release permission and their delegation, go/no-go at points of no return, all talk with the human; whether it also runs implementation lines: question 5 | the human | `agents/master.md` (new) |
| direct session | a session the human started without naming it master | its task | the human | resident core only |
| coordinator (if question 2 is (a)) | a dispatched agent that runs one multi-PR program and may dispatch its own workers | the program's plan, its workers, its go/no-go checklist | the master | a section of `agents/README.md`; no new authority tier |
| line-worker | implements one line | its worktree, branch, PR | master or coordinator | existing |
| researcher | read-only investigation | its findings | master or coordinator | existing |
| merge agent | the single merger | the merge queue | master | existing |
| production operator | runs official production commands for a named change: a release, a config change, an ops action | the change and its checks | master (or coordinator for checks) | `agents/release.md`, scope widened from "release" to "production change" |
| visual QA | non-author review of visible changes | its findings | whoever dispatched it | existing |

Activity roles that any agent can take, defined only in their protocol:
driver and reviewer (`structured-review`), author (`closeout`). They are not
agent roles and do not appear in the table above.

The coordinator's limits are the dispatched-agent limits plus: it may not
grant or widen any gate for its workers; a GO at a point of no return, a
switch, a merge or anything the ledger covers is asked of the master as a
message and acknowledged (section 6, rule N7); its workers report to it and
never to the master or the human directly.

Master ownership boundaries, written into `agents/master.md`:

- One master per project at a time. A session becomes master only when the
  human names it in that session; from that turn the earlier master session
  stops coordinating: it starts nothing new, takes no gated step, and hands
  its open items over through the handoff file. Running agents report to the
  new master after its cold start re-dispatches or parks them.
- Shared state has one writer. The master alone writes the board, the queue
  and the settled list. Who may write a ledger entry follows question 3. Each line writes only its own status file;
  release, ops and coordinator lines report results to the master, which
  updates the board (today `release` says "update the board" itself).
- The master's authority over project governance comes only from recorded
  ledger grants; without a grant it is not a governance layer.
- How much the master implements itself follows question 5.

The master file is the single definition. `CORE.md` keeps one sentence per
role and points to `agents/master.md`; `master-board`, `dispatch`,
`session-handoff` and `away-mode` are the master's procedures and say so in
their descriptions; consumer `AGENTS.md` files keep one pointer instead of
their own master section.

## 5. Protocol scopes

Directories stay flat (skill mounts require it). Every `SKILL.md` description
starts with its reader tag, as the operation protocols already do; the
lifecycle protocols get one too. `README.md` groups protocols by reader and
carries one line each; `docs/CURRENT.md` becomes a map of paths only, without
restating protocol bodies.

| Protocol | Reader | Owns | Does not own |
|---|---|---|---|
| decision-boundary | every role | gates, ledger rules, delegated execution (the single home of merge and release permission), never-ask, the information an escalation must carry, approval recording | role definitions (`agents/`); how questions are presented (personal preferences) |
| master-board | master | board, queue, settled list, sweep | agent supervision (dispatch) |
| dispatch | master, coordinator | briefs, tiers, watchdog, pacing, acknowledgements, relaying | how a worker works |
| line-worker | every dispatched agent | common dispatched-agent rules; implementation-worker restrictions in their own section; command shape; production contact rules | permission rules |
| merge-queue | merge agent, master | one merger, per-PR steps | who may grant merge permission; the project's CI topology (overlay) |
| release | production operator | any production change: preconditions, baseline, switch, staged checks, failure policy | window values (overlay); board updates (master) |
| away-mode | master | pre-authorizations before the human leaves, the per-change list on return | the ledger rules themselves |
| session-handoff | master | what dies with a session, the cold start | the master definition (`agents/master.md`) |
| visual-qa | visual QA agent | independent non-author review of visible changes before the human sees them | UI quality criteria (structured-review UI reference); final evidence accounting (closeout) |
| fix-triage | any author | whether something is wrong, attribution, smallest systemic fix | product error tolerances (overlay) |
| planning | any author | discussion to an executable plan | approval of decision docs (structured-review) |
| structured-review | driver, reviewer | review of plans and implementations, document levels, decision-doc approval | merge readiness (closeout); runner operations for drivers (a driver reference, not loaded into reviewer prompts) |
| closeout | author | final checks and delivery handoff | merge permission (decision-boundary); review criteria (structured-review) |
| readable-brief | author of a decision doc | turning a reviewed source into the human's brief | the approval rule (structured-review) |
| retrospective | any role after an incident | evidence-based learning and routing fixes | vendor transcript locations (agent-readiness) |
| backlog-maintenance | any author | the deferred-work registry | active plans |
| scout | scout executor | judgment-based discovery and candidate proposals | backlog states |
| agent-readiness | repo maintainers | bootstrap, guard, capability map | roles |
| agents | every role | role definitions and how roles combine | procedures (they link to protocols) |

## 6. Changes

### 6.1 Delete or point (deletion first)

| What | Today | After |
|---|---|---|
| merge permission text | 8 copies | `decision-boundary` Delegated Execution; others one-line pointer |
| ledger line-level lookup | 5 copies | `decision-boundary`; `CORE.md` short form |
| approval recording | 5 copies | `decision-boundary`; others pointer |
| reviewer model, tier, timeout names | README, CURRENT, SKILL | `structured-review/SKILL.md` only |
| command shape | line-worker, brief template, master-board overlay | `line-worker`; others pointer |
| master definition | 9+ places | `agents/master.md` |
| `docs/CURRENT.md` protocol paragraphs | changelog-style bodies | one line per path |
| lines' shared notes file as rule source | ~150 lines | removed; rules moved (appendix A) |
| stale overlay text | retrospective overlay (`~/.agent-protocols`, Codex transcripts, Phase 3.5E), context.md clipboard notes | deleted or updated |
| memory rule entries added since 10-11 | ask-only-nontrivial, self-check, plan-ahead, survey-before-asking | moved to protocols, archived, deleted |

### 6.2 New core rules from recent lessons

Each is general (true for any project); numbers stay in overlays.

- N1 `decision-boundary` Escalation: before asking approval of a fix, survey
  the root cause, industry practice and long-term correctness, and cite what
  was checked; never relay a line's first proposal unchecked (human 10-14).
- N2 `decision-boundary` Never Ask: filter a question list to the human's
  real choices (contracts, deleting data, product meaning, direction, external
  voice, what he reserved); decide the rest and report "decided: ..." (human
  10-12).
- N3 `dispatch` Keeping Lines Moving: a rolling pipeline of the next few PRs
  per line, few implementers at once, no bursts; before starting a far-ahead
  step write its upstream uncertainties (human 10-13, 10-14). Numbers in the
  overlay; the "no concurrency cap" line is replaced.
- N4 `master-board` sweep: list the running agents first; one line per line
  with its next item; any stated ETA that has passed is chased (10-12, merge
  queue stall 10-15).
- N5 `line-worker`: once a PR is handed to the merge queue the author does not
  push to it; changes go to the queue as requests (incident 10-15).
- N6 `line-worker` and `release` SAFETY: never run a production write command
  to look something up; implementers send no requests of any kind to
  production, including read-only page checks and load (incidents 10-15).
- N7 `dispatch` and `line-worker`: a request that blocks a window or a
  dependent (a GO, a plan approval, a point of no return) is sent as a message,
  not only written in a status file; the receiver acknowledges; the sender
  re-sends after a short silence and never waits silently (W2 10-15, release
  plan 10-13).
- N8 `release` Checks: a gate baseline is measured on the live release in the
  same window just before the switch; measurements run in an announced quiet
  window; a run taken under abnormal load is void and retaken, not counted as a
  failure (human 10-15; release22 and release27 rollbacks).
- N9 `line-worker`: wait on artifacts, never on process-name matches; every
  background wait has a bound and is stopped by its owner (10-12 cleanup).
- N10 `line-worker` SAFETY: never send the human's email or other personal
  information to an outside service, including request headers (incident
  10-11).
- N11 `dispatch` Relaying: text the human forwards is printed in full in the
  message, self-contained with its context, never only a file path (human
  10-14, 10-15).
- N12 `fix-triage`: before building a "standard" or mechanism, find what
  already exists in code and docs, what it covers and what is missing, and
  extend it (human 10-13).
- N13 `visual-qa` Output: the report header names the guideline used, its
  source and date; a report without it does not count (human 10-12).
- N14 `master-board`: sweep results go to a sweep log next to the board, not
  into the board; the settled list is kept current (today the board is about
  1,300 lines of sweep notes and its settled list stops at 10-09).

### 6.3 Project overlay updates (skynet-intern)

Moved from the shared notes file and memory: production read-query limits and
pausing in release windows; quiet-window slots in briefs; docker and local-key
hygiene; pyright and guard-test sets; lock-wait timeouts; perf A/B method;
gate numbers (+20 ms, load +1.0 void, two rounds of 160); long-lived tools
location; merge-queue test-only fixes. The master records in the ledger the
grants it heard and that are not there yet (the 10-15 baseline wording of
L14, the night pre-authorizations as dated temporary entries, the Feedbox
grants); this work does not record grants.

## 7. Plans after approval (each one PR, reviewed)

1. Core: roles (`agents/master.md`, role composition in `agents/README.md`,
   the coordinator section only if question 2 is (a), production operator
   scope, line-worker split), `CORE.md` role sentences, pointers replacing copies,
   README/CURRENT as maps, reader tags.
2. Core: new rules N1-N14, consumer assumptions moved out, driver-only runner
   text moved to a driver reference, guard freshness narrowed.
3. skynet-intern overlay and `AGENTS.md`: pointers, moved rules, stale text,
   personal preferences moved per question 1, merge text per question 4,
   submodule bump.
4. skynet-apps overlay: point to the home repo; submodule bump.
5. Personal files and memory: the master-preferences file (question 1),
   reviewer-model wording in the user-level files, memory archive and delete,
   shared notes file reduced to pointers (outside both repos; shown to the
   human before his files change).

After the last PR: one hard review of the full resulting repo state (not the
diffs) until it converges, a cold-start check with a fresh master session,
then the memory index pointers are updated.

## 8. Audit findings folded in

The whole-repo audit (hard tier, Codex Astra; thread in
`2026-10-16_repo_structure_audit.md`) confirmed problems 1-5 and added these,
each resolved here or listed as a question:

- **Authority role versus task role.** The repo never says how roles combine
  (a line worker is also a driver and an author). Resolution: `agents/README.md`
  states it once: the authority role (master, direct session, dispatched agent)
  sets permission and escalation; the task role (worker, researcher, merge
  agent, production operator, visual QA, coordinator) sets the work and the
  output; author, driver and reviewer are artifact responsibilities only and
  grant nothing.
- **Researcher versus line-worker.** The researcher preloads `line-worker`,
  whose "do not touch production" contradicts the researcher's brief-allowed
  production reads. Resolution: `line-worker` splits into "every dispatched
  agent" rules and "implementation worker" restrictions; production reads
  depend on the brief and the project overlay.
- **Approved contract changes.** `agents/line-worker.md` forbids contract
  changes, while the overlay prescribes migration and endpoint tests.
  Resolution: already settled by the resident core's exception for a gated
  action the brief names with its recorded permission (section 9, last
  paragraph); `agents/line-worker.md` is corrected to say so.
- **Merge permission versus merge execution.** `closeout` accepts a current-turn
  merge instruction from any session; `merge-queue` gives merging only to the
  master or its merge agent. Question 4.
- **Ledger provenance.** The rule says only the session that heard a grant
  records it, but most active ledger entries were written by an agent from the
  master's relay. This is a record problem, not evidence the grants are false.
  Question 3 and its reconciliation note.
- **Worktree guard versus merge queue.** The guard fails whenever `main`
  moves, forcing workers to rebase although the queue owns rebasing.
  Resolution: the guard checks freshness only when work starts and when it is
  prepared for the queue.
- **Absolute rules with known exceptions.** "The only acceptable blocker is a
  human decision" (`dispatch`) is deleted; the real blocker, its owner and the
  restart condition are recorded instead. Escalation presentation rules
  (one question per message, plain text) move to personal preferences; the
  core keeps only the information a question must carry.
- **Audit correction.** The audit says the consumer's CI runs on pull
  requests; its workflow triggers only on pushes to `main` and manual
  dispatch, so "a PR push starts nothing" is true there. The conclusion stands:
  the CI topology belongs in the overlay, not in the core.
- **Consumer assumptions in the core.** `merge-queue` assumes "push triggers
  nothing" and rebase merges; `fix-triage` assumes one record more or fewer is
  not an error and prefers redundancy; `closeout` assumes phase-output
  manifests; `fix-triage/references/principles.md` is referenced by nothing
  and holds blanket rules (every enum has `other`). Resolution: those
  statements move to the consumer overlay (they are true for skynet-intern);
  the core keeps "check the project's CI and merge contract" and "judge
  against the owning layer's contract"; the unreferenced file is deleted after
  its valid lines move to their owners.
- **Repeated inspections.** Visual checks, mechanism lifecycle, agent progress
  and evidence appear in two to four protocols. Resolution: one checklist per
  subject; later steps check that the evidence exists and still applies.
- **Stale and wrong text.** The retrospective overlay routes to a
  machine-global directory; the structured-review overlay and `README.md`
  examples omit the required tier or `--coding-agent`; the backlog overlay says
  CI runs on every PR head; `session-handoff` says to overwrite the template;
  `agents/researcher.md` gives an ambiguous path; `README.md` says "no copied
  protocol content" although the resident core is a checked copy; this repo
  mounts 7 of 17 skills for itself. All fixed in plan 1 or 3.
- **Size.** The runner sends every reviewer about 7,400 words of skill and
  references, including driver-only runner operations; `structured-review`
  (584 lines), `closeout` (393), `backlog-maintenance` (380) and the consumer
  `AGENTS.md` CI section (55 lines) carry detail one reader needs. Resolution:
  move driver-only runner operations to a driver reference that the runner
  does not load; no new size guard.

## 9. Questions for the human

Core questions (each changes who owns what):

1. **Where the master's personal preferences live.** Today the report shape,
   the question style, the model tiers, the quota rule and pacing numbers sit
   in skynet-intern's overlay, so a master in skynet-apps or any other repo
   does not see them; on 10-11 he classed model tiers and language as
   personal. Options: (a) a second personal file next to `PREFERENCES.md`
   that only the master reads (recommended: every master sees it in any repo,
   no other role loads it, which is what he asked for on 10-11); (b) a
   "when you are master" section in `PREFERENCES.md` (every session loads it);
   (c) keep them in the skynet-intern overlay.
2. **Nested dispatch (the coordinator).** On 10-13 to 10-15 the app-split
   coordinator dispatched its own workers and ran go/no-go checks. The protocols
   say only "it may dispatch its own subagents". Options: (a) define the
   coordinator with the limits in section 4: it never grants or widens a gate,
   every point of no return, switch, merge or ledger-covered step is asked of
   the master and acknowledged, its workers report only to it, and it cannot
   pass on a delegated execution it received (recommended: it matches how the
   split ran and closes the gap that delayed W2); (b) only the master
   dispatches; a program line asks the master to start each worker.
3. **Who may type a ledger entry from now on.** The rule is "only the session
   that heard the human records it". In practice the master that heard a
   grant has had another agent type it. Options: (a) the hearing session stays
   responsible: another agent may type the entry, but the hearing session
   checks the exact words and scope against what it heard before the entry
   becomes active (recommended: matches how entries are written, keeps one
   accountable session); (b) only the hearing session itself may write the
   file. Either way, the existing entries are reconciled by the master against
   the original conversations; any entry whose original words it cannot find
   is shown to the human with its full scope for re-confirmation, never as a
   bare id.
4. **Who executes a merge.** Permission comes from `decision-boundary`
   either way. Options: (a) core rule: one merger per repo at a time; while a
   master runs in the project only the master or its merge agent merges; a
   direct session merges on a current-turn instruction only when no master
   runs (recommended: two mergers on one repo is the collision the queue
   exists to prevent, and it holds for any project with a master); (b) the
   core says only "one merger at a time"; master-exclusive merging is project
   policy in each overlay.

5. **Does the master run implementation lines itself?** Today `dispatch`
   says only that tail work goes to a cheap agent "so the master stays on the
   main line"; nothing says whether the master may take a whole
   implementation line. Options: (a) the master coordinates: it decides,
   dispatches, merges and releases or delegates them, and does small checks
   and fixes itself, but every implementation line goes to a worker
   (recommended: the human relies on the master and its sweep to keep every
   line moving while he is away, which a master busy implementing cannot do;
   on 10-11 and 10-12 the lines stalled when the sweep did not push them);
   (b) the master may take an implementation line when it judges that faster,
   and says so on the board.

Confirm in passing (one answer accepts all; any one can be rejected):

6. The lines' shared notes file stops holding rules (they move into the
   protocols and the overlay); the collaboration rules added to memory since
   10-11 move the same way and are archived before deletion; the design-method
   principles he kept in memory on 10-11 stay there.
7. The board keeps state only: sweep notes move to their own log, the settled
   list is brought up to date, the queue keeps only open items.
8. Brief delivery: the master gives the path or a link and opens nothing on
   his machine (replaces "open it in Zed").
9. In his user-level files, "prefer Terra or Sol" becomes "Sol for normal,
   Astra for hard" (Terra was replaced on 09-24); the exact text is shown to
   him before the change.
10. Rollout: skynet-intern and skynet-apps get the new version first;
    skynet-agent-kit and skynet-ingest (49 commits behind, no resident core)
    get bump PRs after that; skynet-twitter belongs to another team, so it
    gets a note he forwards, not a PR from us.
11. No new standing mechanism (alert, counter, guard, config field) is added
    by this restructure.

Already settled, not asked: a worker may implement a contract change the
human already approved when its brief names the change and cites the
approval; this is the existing resident-core exception for "a gated action
your brief names exactly, together with the permission the master recorded".
Merging it still stops at the gated-surface check.

## Appendix A. Rules and lessons since 10-11, classified

Sources: the lines' shared notes file (state directory), the master board,
memory, the human's messages in the master session (10-11 to 10-16), the
user-level files. Status: in = already in the protocols; miss = missing;
conflict = contradicts the protocols or an overlay; stale = outdated text.
Layer: C core, O project overlay, P personal, S state/ledger (the master
records).

| # | Rule or lesson (date, source) | Status | Layer, home |
|---|---|---|---|
| A1 | Survey root cause, industry practice, long-term fit before asking approval of a fix (human 10-14) | miss | C decision-boundary Escalation + fix-triage (N1) |
| A2 | Ask only his real choices; decide the rest and report it (human 10-12) | partial | C decision-boundary Never Ask (N2) |
| A3 | Sweep pushes idle lines: agents first, one line per line, chase passed ETAs (human 10-11/10-12; merge stall 10-15) | partial | C master-board sweep (N4) |
| A4 | Rolling pipeline of 4-5 PRs, 3-4 implementers per line, no bursts, uncertainty note before far steps (human 10-13/10-14) | conflict with overlay "no cap" | C dispatch (N3); numbers O dispatch |
| A5 | Waits that are only our own rules compress to the standard checks; approved windows stay (human 10-14) | in (sweep item 5) | O release lists the approved windows |
| A6 | Quota exhausted: wait; never downgrade the model tier (human 10-13, replaces 10-12 night) | miss | P master preferences (question 1) |
| A7 | Releases never reset the ramp clock (human 10-12) | project decision | S settled list; umbrella plan |
| A8 | Non-author guideline QA before screenshots; report names guideline, source, date (human 10-12) | partial | C visual-qa (N13); O visual-qa names the guideline |
| A9 | Author hands off after the PR enters the merge queue (incident #1682, 10-15) | miss | C line-worker, merge-queue (N5) |
| A10 | Never run a production write command to look something up (incident 10-15) | miss | C line-worker, release SAFETY (N6) |
| A11 | Implementers send no requests to production, including page checks (incident 10-15) | ambiguous ("touch") | C line-worker (N6) |
| A12 | Gate baseline = same-window measurement of the live release (human 10-15 "改") | miss; ledger L14 text stale | C release Checks (N8); numbers O release; S ledger L14 wording |
| A13 | Quiet measurement windows announced with exact slots; load-void rule; warm-up and order rotation (master 10-14) | miss | C release (N8); numbers O release |
| A14 | Production read queries: statement timeout, batches, pause in release windows; briefs name quiet slots (10-12, 10-15) | miss | O line-worker, dispatch |
| A15 | Blocking requests (GO, plan approval, point of no return) sent as messages, acknowledged, re-sent on silence (W2 10-15, release plan 10-13) | miss | C dispatch, line-worker (N7) |
| A16 | Wait on artifacts not process names; bounded waits; anchored marker matches (10-12, 10-14) | miss | C line-worker (N9) |
| A17 | Never send the human's email or personal information to outside services (incident 10-11) | miss | C line-worker SAFETY (N10) |
| A18 | Docker hygiene: `--rm`, named volumes, no global prune (10-12) | miss | O line-worker |
| A19 | Unset model API keys before local servers (10-12) | miss | O line-worker |
| A20 | Long-lived tools under the state directory, not scratch (10-14) | miss | O master-board |
| A21 | Pyright on every changed file incl. scripts; boundary guard tests; route and error-envelope tests; lock wait exits non-zero (10-11 to 10-13) | partial | O line-worker, merge-queue |
| A22 | Merge queue may fix test-only typing or whitespace (10-11) | miss | O merge-queue |
| A23 | Local perf: alternating A/B, at least 5 rounds, under current load (10-13) | miss | O line-worker |
| A24 | Night pre-authorizations recorded as dated temporary ledger entries | practice gap (only in notes/memory) | S ledger (master records) |
| A25 | Feedbox built to launch independently, gates kept; three-tier redo with history rerun (human 10-14, 10-15) | not recorded | S ledger (master records) |
| A26 | Forwarded text printed in full with its context, never only a path (human 10-14/10-15) | partial (separators only) | C dispatch Relaying (N11) |
| A27 | Progress reports map steps to PRs with a progress bar (human 10-14) | miss | P master preferences |
| A28 | Before a new standard, find what exists and extend it; keep it light (human 10-13) | partial | C fix-triage (N12) |
| A29 | Guidance written for other agents is checked from a fresh agent's view (human 10-14) | miss | C closeout (cold-start check for agent-facing docs) |
| A30 | Coordinator line dispatching its own workers (app split 10-13 to 10-15) | used, undefined | C agents/README.md coordinator section (question 2) |
| A31 | Ops line changing production configuration (10-14/10-15) | used, outside release role | C production-operator scope in agents/release.md |
| A32 | Master is not a standing governance layer (human 10-11) | in (ledger overlay) | O ledger (keep) |
| A33 | Master-level files in one home repo for multi-repo work (skynet-apps copies intern overlays) | implicit | C README overlays section; O apps context |
| A34 | Personal preferences in overlays (report shape, banned words, model tiers) | conflict with 10-11 layering answer | P (question 1) |
| A35 | Readable-brief delivery "open in Zed" vs never open anything on his machine | conflict | P/O: give the path or link, open nothing |
| A36 | User-level files say "prefer Terra or Sol"; repo profiles are Sol (normal) and Astra (hard) since 09-24 | stale | P user-level files (shown to him first) |
| A37 | Lines told "use the Codex reviewer backend" without a reason; runner orders backends itself | stale | delete |
| A38 | Board: sweep notes inside the board, settled list stops at 10-09; queue keeps answered items | practice gap | C master-board (N14); S cleanup |
| A39 | Consumers skynet-agent-kit, skynet-ingest, skynet-twitter pinned 49 commits behind, no resident core | rollout gap | question 2 |
| A40 | Memory rule entries added since 10-11 (ask-only-nontrivial, self-check, plan-ahead, survey-before-asking) | duplicates after this work | archive and delete |

## Review Threads

### Reviewer pass 1 (other-plan, codex reviewer)

The human’s concern is that the repository does not clearly define its roles, the master’s responsibilities, or each protocol’s scope.

#### Blocking issues

##### Thread: Complete the master’s ownership boundary

`docs/agent_plans/2026-10-16_repo_restructure_decision.md:99–124` names the master as owner of the board and queue, but does not settle what happens when master sessions overlap or ownership transfers. It also leaves the board’s write boundary implicit. The audit identifies both gaps at `docs/agent_plans/2026-10-16_repo_structure_audit.md:181–189`. The proposed master definition should state who owns coordination during a handoff, who writes shared state, and that project governance authority comes only from recorded grants. These are role boundaries, not implementation details.

##### Thread: State the scopes that are currently “as today”

The scope table at `docs/agent_plans/2026-10-16_repo_restructure_decision.md:134–144` groups `away-mode`, `session-handoff`, `fix-triage`, and `visual-qa` as “as today,” and gives the lifecycle protocols one collective scope. That leaves part of the human’s central question unanswered, including the audit’s finding that `fix-triage` is not inherently a multi-agent workflow. Give each protocol a short ownership and exclusion boundary before splitting this decision into plans.

##### Thread: Present authority choices as real questions

The audit calls the master’s implementation role and merger ownership scope decisions. The decision doc places them, along with permission to implement approved contract changes, under “confirm in passing” (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:341–349`). In particular, the merger proposal does not present the audit’s alternative of project-specific exclusive merging (`docs/agent_plans/2026-10-16_repo_structure_audit.md:304–314`). Move these material boundaries into fairly framed choices or explain the prior human decision that settles each one. Also make downstream statements conditional on the answers: the coordinator is still listed unconditionally in plan 1 (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:225–227`).

##### Thread: Separate ledger policy from reconciliation of existing entries

Question 3 (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:332–339`) combines a prospective change to the direct-recipient recording rule with a single reconfirmation of several existing entries. Those entries have different scopes, and their IDs alone do not show the human what one answer would affirm. The other option, re-recording entries, does not by itself establish their original provenance. Ask separately whether a checked delegated scribe is permitted going forward and how the direct recipient should reconcile existing records against the original authorizations. Present any requested human reconfirmation with the actual scopes.

#### Non-blocking issues

##### Thread: Correct the audit’s CI evidence

The audit says the consumer CI workflow runs on pull requests (`docs/agent_plans/2026-10-16_repo_structure_audit.md`, “Consumer-specific operating and product assumptions”). The inspected consumer workflow has `push` on `main` and `workflow_dispatch`, with no pull-request trigger. The decision doc’s statement that ordinary PR pushes trigger nothing is consistent with that workflow. Correct the audit’s evidence; the decision to keep CI topology out of the generic protocol still stands.

#### Overall judgment

**Blocking issues remain.** The decision doc addresses all five audit findings marked blocking, but its master and protocol boundaries and several human questions need revision before it is ready for a readable brief.

#### Residual risks or validation gaps

This was a read-only review of the two artifacts and the cited consumer CI workflow. No files were changed; the worktree remained clean.

### Driver response to reviewer pass 1

- Master ownership boundary: accepted. Section 4 now states one master at a
  time and the handover, the single writer of shared state, governance only
  from ledger grants, and the coordination role with its prior source.
- Scopes "as today": accepted. Section 5 now gives every protocol its reader,
  what it owns and what it does not.
- Authority choices as questions: accepted for merge execution (now question
  4 with both options). The master's implementation role restates the
  existing `dispatch` rule and stays in passing with that source. Approved
  contract changes are settled by the resident core's named-action exception;
  section 9 says so instead of asking. Plan 1 is conditional on question 2.
- Ledger policy versus reconciliation: accepted. Question 3 now asks only the
  forward rule; reconciliation of existing entries is the master's job
  against the original words, and any entry it cannot source goes to the
  human with its full scope.
- Audit CI evidence: accepted; correction recorded in section 8 (the audit
  thread itself is append-only).

### Reviewer pass 2 (other-plan, codex reviewer)

The human’s concern is that the repository does not clearly define its roles, the master’s responsibilities, or each protocol’s scope.

#### Blocking issues

##### Thread: Ledger write ownership conflicts with question 3

Section 4 says the master alone writes the ledger (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:127–130`). Question 3 recommends allowing another agent to type an entry, while its alternative allows the session that heard the grant to write it (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:364–374`). The master-only statement rules out the recommended option before the human answers and may also rule out a direct session that heard a grant.

Keep the single-writer boundary for the board, queue and settled list. State ledger write ownership as a pending choice in question 3, then make the role boundary follow that answer. This needs no new mechanism. The pass 1 ledger-policy thread remains open.

##### Thread: Ask the human whether the master may run a whole implementation line

Section 4 says the master does not run whole implementation lines, and item 5 presents that as a restatement of `dispatch` (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:133–137,386–387`). The cited `dispatch` text assigns *tail work* to another agent so the master stays on the main line (`dispatch/SKILL.md:69–72`); it does not establish a categorical ban on implementation lines. The audit identified this as an unsettled master-scope choice (`docs/agent_plans/2026-10-16_repo_structure_audit.md`, “The master role”).

Present coordination as the recommendation, with a fair alternative that permits the master to take an implementation line when appropriate. Apply the answer to section 4. The pass 1 master-boundary thread remains open on this point.

#### Non-blocking issues

The pass 1 protocol-scope thread is resolved: section 5 now gives each protocol a reader, ownership and exclusion boundary. The merge-execution choice is fairly presented in question 4. The approved-contract exception is supported by `decision-boundary/CORE.md`. The CI correction is recorded in section 8.

#### Overall judgment

**Two blocking issues remain.** The decision doc is not yet ready for its readable brief.

#### Residual risks or validation gaps

This was a read-only review of the revised decision doc, audit, pass 1 response and cited current protocols. The worktree remained clean. No claim is made about the provenance of existing ledger grants.

### Driver response to reviewer pass 2

- Ledger write ownership: accepted. Section 4 keeps the single writer for the
  board, the queue and the settled list; ledger writing follows question 3.
- Master implementation role: accepted. It is now core question 5 with both
  options; section 4 and the role table follow the answer.

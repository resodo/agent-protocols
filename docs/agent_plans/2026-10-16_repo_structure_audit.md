# Whole-repo structure audit (review request)

Document level: review request for a decision doc (no PR is opened from this
file; its findings feed the restructure decision doc).

Status: active (2026-10-16).

## Why

The human said on 2026-10-16 (relayed by the master; per master relay,
pending record): the repo still feels like "one big tangle": who is which
role, how the master role is defined, and what each scope is, are unclear.
He asked for an independent, hard review of the **complete current repo
state**, not of a recent diff, before any restructuring.

This review is the input to a restructure decision doc. Nothing is changed in
this pass.

## What to review

Review the repository as it stands at this commit, every file that carries
rules, plus one consumer overlay that shows how the core is used:

1. This repo (core): `README.md`, `AGENTS.md`, `docs/README.md`,
   `docs/CURRENT.md`, `docs/agent_plans/README.md`, and every protocol
   directory: `decision-boundary/` (including `CORE.md`), `master-board/`,
   `dispatch/`, `line-worker/`, `merge-queue/`, `release/`, `visual-qa/`,
   `away-mode/`, `session-handoff/`, `fix-triage/`, `planning/`,
   `structured-review/` (the `SKILL.md` and its `references/`; the runner script
   only where its text states rules), `closeout/`, `readable-brief/`,
   `retrospective/`, `backlog-maintenance/`, `scout/` (the `SKILL.md`),
   `agent-readiness/`, and `agents/`.
2. One consumer overlay, read-only, at the relative path
   `../../../skynet-intern/main/` from this worktree: its `AGENTS.md`
   (sections "Decision boundary (resident core)", "Master Session",
   "CI Triggering and Merging") and every file in its `.agent-protocols/`
   directory, including `authority-ledger.md` and `context.md`. Cite these
   as `overlay:<file>` (for example `overlay:dispatch.md`), never with an
   absolute path.

Dated plans under `docs/agent_plans/` are provenance, not instructions; read
them only to check whether a rule's history explains a conflict.

## Questions

Answer each with concrete file and section citations.

1. **Roles.** List every role the repo defines or implies (master, direct
   session, dispatched agent, line worker, researcher, merge agent, release
   agent, visual QA, driver, reviewer, author, and any role that exists in
   practice but has no definition, such as an agent dispatched by the master
   that itself dispatches and coordinates other agents). For each: where it
   is defined, what it may and may not do, whom it reports to. Flag roles that
   are defined in more than one place, defined inconsistently, or used but
   never defined.
2. **The master role.** Is there one place that defines what the master is,
   what it owns, what it may decide, and what it must not do? List every
   place that states part of the master's duties or powers. Is the set
   complete and consistent? What is missing?
3. **Scope boundaries.** For each protocol, what does it claim as its scope
   (its description line and body)? Where do two protocols claim the same
   thing? Where does a protocol reach into another's scope? Are the three
   families (development lifecycle: planning, structured-review, closeout,
   readable-brief, retrospective, backlog-maintenance, scout; multi-agent
   operation: decision-boundary, master-board, dispatch, line-worker,
   merge-queue, release, visual-qa, away-mode, session-handoff, fix-triage;
   guidance: agent-readiness, agents) clearly separated, and does a reader
   know which one to load?
4. **Single source of truth per rule.** Find rules stated in more than one
   place (core vs core, core vs overlay, overlay vs consumer `AGENTS.md`).
   Examples to check, not an exhaustive list: merge permission; the
   ledger-entry line-level lookup; "only the session that heard an approval
   records it"; deletion first and premise before fix; command shape that
   avoids platform confirmations; reviewer model and tier names. For each:
   which copy should be the source, and which copies should become pointers
   or be deleted.
5. **Conflicts.** Rules that contradict each other, or an overlay that
   weakens a core `SAFETY` rule, or a consumer document that contradicts the
   overlay or the core.
6. **Layering.** Is each item in the right layer: core (true for any project
   and any coding agent), project overlay (names this project's paths,
   scripts, numbers, business terms, or this human's grants for this project),
   or the human's personal preferences (true for him in any project; these
   live in a user-level file outside both repos)? Flag personal preferences
   that sit in the core or in an overlay, and project details in the core.
7. **Orphans and stale text.** Files, sections or references that nothing
   routes to, paths that no longer exist, retired mechanisms still described,
   indexes (`README.md`, `docs/CURRENT.md`) that are out of date or restate
   protocol bodies instead of pointing at them.
8. **Size and progressive disclosure.** Which always-loaded text (resident
   core, descriptions, consumer `AGENTS.md` sections) carries detail that only
   one role needs? Which protocol bodies are too long for what they do?

## Output

Group findings by the eight questions. For each finding: severity (blocking
for the restructure / should fix / note), the exact citations, what is wrong,
and the smallest correct fix, deletion first (would deleting, merging or
pointing resolve it before adding anything?). End with a short proposal for a
target structure: the role list with one owner file each, where the master
role is defined, and where each family of rules lives. Do not propose new
standing mechanisms unless deleting or merging cannot solve the problem.

## Review Threads

### Reviewer pass 1 (other-plan, codex reviewer)

The human’s concern is that the repository does not clearly explain who each role is, what the master owns, or where each rule belongs.

Reviewed the complete requested protocol state at `a8d71cb`, including all 17 skills, the specified references and templates, role definitions, readiness guidance, indexes, and all 19 consumer overlay files. The consumer snapshot was `65e0734c`, with protocol pin `7627985`. The audited protocol directories have no differences between that pin and this review target; the consumer’s resident core also matches `decision-boundary/CORE.md`. The conflicts below therefore cannot be dismissed as version skew.

**Blocking findings concern decisions the restructure must settle, not permission to complete this audit.** This audit is complete and can feed the decision document. It does not approve a target structure or authorize implementation. All findings below remain open for driver classification.

Citations beginning `overlay:` refer to the named consumer. `overlay:AGENTS.md` denotes its repository entrypoint; other such citations denote files in its `.agent-protocols/` directory.

#### 1. Roles

##### Thread: Authority roles and task roles are not composed explicitly

**Severity: blocking for the restructure.**

The repository defines three authority roles, several specialist jobs, and review responsibilities, but never states how they combine. A line worker can also be a driver and an author; a reviewer can also be a dispatched agent. Loading a task protocol must not silently change the session’s authority or reporting relationship.

The existing inventory is:

| Role or responsibility | Current definition and allowed work | Restrictions and reporting |
|---|---|---|
| Human decision-maker | Final authority for scope, tradeoffs, acceptance and permission. `structured-review/references/collaboration.md:5–12`; `decision-boundary/SKILL.md:107–135`. | Grants authority; does not become an agent role. |
| Master | Named by the human in the current session; decides ungated engineering work and gated work covered by its ledger. `decision-boundary/CORE.md:4–19`; `decision-boundary/SKILL.md:86–135`. | Uncovered gates go to the human; cannot manufacture approval or bypass denials. Owns coordination through several other protocols. |
| Direct session | Human-tasked without being named master. `decision-boundary/CORE.md:4,18`; `decision-boundary/SKILL.md:28–34`. | May do ungated work; asks the human at gates; cannot use the master’s ledger. No separate workflow definition exists. |
| Dispatched agent | Started by another agent; works inside its brief, including exactly delegated gated actions. `decision-boundary/CORE.md:19`; `decision-boundary/SKILL.md:162–193`. | Reports to its dispatcher in the core, but to “the master” in the long form. Cannot contact the human or discover authority in the ledger. |
| Line worker | Implements a work line; may edit, test locally, push, open PRs and obtain reviews. `agents/line-worker.md:3–12`; `line-worker/SKILL.md:19–67`. | No production, CI triggering, merging, contract changes or non-review paid calls. Reports to the master. |
| Researcher | Read-only investigation, including production reads allowed by the brief. `agents/researcher.md:3–10`; `line-worker/references/read-only-research.md:3–22`. | No unauthorized writes, including temporary production files. Reports through the preloaded line-worker workflow, whose production prohibition conflicts with this role. |
| Merge agent | Single merger; may rebase, check, invoke pre-merge CI, merge authorized PRs and rerun a flaky job once. `agents/merge-queue.md:3–12`; `merge-queue/SKILL.md:19–61`. | Cannot fix business code, discover its own authority or pass unresolved gated changes. Reports failures to the author line/master. |
| Release agent | Executes a named, authorized release and staged checks; may roll back reversible parts. `agents/release.md:3–11`; `release/SKILL.md:15–58`. | Official production commands only; separately authorized irreversible steps; cannot change windows. Reporting is specified, but the recipient is not named in this skill. |
| Visual QA agent | Independent, non-author review; may run the app, use check accounts and capture screenshots. `agents/visual-qa.md:3–10`; `visual-qa/SKILL.md:18–45`. | Cannot fix the author’s code or send material directly to the human. Produces findings for author correction. |
| Driver | Owns the artifact body, classifies findings and decides revisions. `structured-review/SKILL.md:490–543`. | Human retains final authority; driver cannot unilaterally resolve a reviewer disagreement. Reporting to a dispatcher versus directly to the human is not composed with the authority roles. |
| Reviewer | Critically checks the artifact and normally owns thread resolution. `structured-review/SKILL.md:465–481`; `structured-review/references/collaboration.md:68–80`. | Runner-backed reviewer returns text without editing; runner performs write-back. `structured-review/SKILL.md:250–253`. |
| Author | Produces and fixes the work reviewed or merged. Used in `dispatch/SKILL.md:69–70`, `merge-queue/SKILL.md:59–60`, and `visual-qa/SKILL.md:8–10,38–44`. | No canonical definition. It should describe responsibility for an artifact, not grant authority. |
| Intermediate coordinator | Implied by permission for an agent to dispatch its own subagents. `dispatch/SKILL.md:43–51`. | No recorded layer definition covers this coordination responsibility: no clear brief ownership, upward reporting, delegation or revocation rule for the intermediate parent. |
| Scout executor | Collects evidence, interprets it and proposes candidates. `scout/SKILL.md:22–47,172–194`. | Cannot promote candidate lifecycle states or alter open/closed items as Scout. This is a task function, not a new authority role. |
| Closeout owner | Driver-owned verification and delivery handoff. `closeout/SKILL.md:21–29`. | Closeout itself does not grant merge permission. This is another responsibility a session holds, not an authority class. |
| Operator, protocol maintainer, runner caller | Operator locates evidence or performs acceptance; maintainers update integrations; caller owns private run retention. `retrospective/SKILL.md:41–52`; `closeout/SKILL.md:203–209`; `structured-review/references/recovery.md:92–98`. | These are named responsibilities without a general agent-role contract. They should not imply extra execution rights. |

**Smallest correct fix:** add the composition explanation to the existing `agents/README.md`: authority role determines permission and escalation; task role determines work and output; author/driver/reviewer determine artifact responsibility. Specialist definitions should state only their additional permissions, restrictions and required workflows.

For nested dispatch, make a human decision explicit:

- Remove the recursive-dispatch sentence and support only direct master dispatch; this has the smallest documentation and operational cost.
- Or support nested engineering decomposition while retaining the dispatched boundary and reporting through the immediate parent. This needs a short definition of the parent’s coordination duties and whether already-delegated execution can be passed further.

Do not silently create another master or give an intermediate coordinator ledger authority.

#### 2. The master role

##### Thread: No single file defines the master’s complete contract

**Severity: blocking for the restructure.**

**There is no complete master definition in one place.** The resident core identifies the master and summarizes authority, but it does not define its operational scope. `agents/` contains five specialist definitions and no master definition.

The master’s duties and powers are distributed as follows:

| Responsibility | Current sources |
|---|---|
| Appointment, gates, default decisions, grants and revocation | `decision-boundary/CORE.md:4–21`; `decision-boundary/SKILL.md`, “Four Quadrants,” “Gate Tests,” “What The Master Decides By Default,” “Authority Ledger,” and “Delegated Execution.” |
| Board, human queue, settled decisions, status reports and sweeps | `master-board/SKILL.md:8–53`; `master-board/references/sweep.md:6–29`; `overlay:master-board.md:5–45`. |
| Work allocation, model tier, briefs, monitoring, result checking and returning failures | `dispatch/SKILL.md:21–79`; `dispatch/references/watchdog.md:6–17`; `overlay:dispatch.md:5–20`. |
| Production requests and escalations from workers | `line-worker/SKILL.md:34–45,62–67`; `overlay:line-worker.md:49–59`. |
| Merge ownership, exclusive delegation, queue admission and CI reruns | `merge-queue/SKILL.md:19–61`; `overlay:AGENTS.md:231–274`; `overlay:merge-queue.md:5–32`. |
| Release permission, staged checks and failure handling | `release/SKILL.md:15–58`; `overlay:release.md:5–18`. |
| Independent visual review before human presentation | `visual-qa/SKILL.md:8–10,36–46`; `overlay:master-board.md:35`; `overlay:visual-qa.md:5–14`. |
| Away-time preauthorization and return accounting | `away-mode/SKILL.md:14–44`; `overlay:away-mode.md:5–8`. |
| Session continuity, cold start and re-dispatch | `session-handoff/SKILL.md:18–53`; `agent-readiness/agents-bootstrap-template.md:44–46`; `overlay:session-handoff.md:5–10`. |
| Fix adoption and engineering judgment | `decision-boundary/SKILL.md:94–101`; `fix-triage/SKILL.md:15–47`; `overlay:fix-triage.md:5–15`. |
| Use of grants during planning, review and closeout | `planning/SKILL.md:56`; `structured-review/SKILL.md:371–380`; `closeout/SKILL.md:92–119`. |
| Brief delivery | `readable-brief/SKILL.md:141–154`; `overlay:readable-brief.md:34–45`. |
| Project governance authority and its eventual transfer | `overlay:authority-ledger.md:8–16,24–36`. This explicitly says the master is not a standing governance layer. |
| Startup routing and machine-dependent capabilities | `overlay:AGENTS.md:31–40`; `agent-readiness/capabilities.md:19–35,48–60`. |

The important missing boundaries are:

1. **Coordination versus implementation.** The text encourages dispatch and assigns tail work away, but does not say whether the master is primarily a coordinator, may author arbitrary work, or should execute only work that cannot be delegated.
2. **Coordination versus governance.** The consumer correctly distinguishes them in a master-only ledger. That project boundary is easy to miss when the master is otherwise described as the default decision-maker.
3. **Intermediate coordinators.** There is no defined relationship between master responsibilities and agents managing other agents.
4. **Ownership transfer.** A master is named per session, but the generic contract does not settle overlapping master sessions, transfer of running work, or the point at which the previous session’s coordination ownership ends. The merge queue covers only one part of this.
5. **State write ownership.** The master keeps the board, yet the release workflow says “Update the board” without routing that update through the master (`release/SKILL.md:55–58`). Worker status and master summaries need an explicit writer boundary.

**Smallest correct fix:** consolidate the role contract into `agents/master.md`, linking to operational protocols rather than copying their procedures. It should define appointment, scope, reports, delegation, state ownership and exclusions. Keep project governance grants in the consumer ledger.

The choice about how much implementation the master performs, and whether intermediate coordinators are supported, belongs in the decision document. There is no existing definition sufficient to infer those answers.

#### 3. Scope boundaries

The descriptions generally identify useful triggers. The problem is overlapping policy ownership and incomplete composition, rather than all 17 protocols being unnecessary.

| Protocol | Claimed scope in description/body | Boundary assessment |
|---|---|---|
| `planning` | Discussion to executable scope, options, validation and review path. `planning/SKILL.md:3,8–20,32–45`. | Appropriate lifecycle scope. Decision-document construction and approval are largely owned elsewhere. |
| `structured-review` | Review artifacts and responses. `structured-review/SKILL.md:3,8–37`. | Also owns document taxonomy, decision approval, general fix principles, human escalation and a large runner operations manual. |
| `closeout` | Final hygiene and delivery. `closeout/SKILL.md:3,8–10,21–69`. | Correctly distinguishes review from delivery, but repeats review checks and substantial authorization policy. |
| `readable-brief` | Convert a final reviewed source into a faithful human-readable brief. `readable-brief/SKILL.md:3,8–19`. | Useful output boundary. Repeats approval and annotation lifecycle owned by structured review. |
| `retrospective` | Evidence-based learning and routing prevention work. `retrospective/SKILL.md:3,8–20,103–123`. | Clear purpose. Vendor transcript discovery and project ownership of backend limitations do not belong in its general workflow. |
| `backlog-maintenance` | Deferred-work registry and lifecycle. `backlog-maintenance/SKILL.md:3,8–18`. | Clear boundary from active plans; schema and examples dominate the body. |
| `scout` | Judgment-based discovery and candidate proposals. `scout/SKILL.md:3,8–13,63–88`. | Correctly separates discovery from CI and candidate schema from backlog ownership. |
| `decision-boundary` | Authority, gates, grants and escalation. `decision-boundary/SKILL.md:3,8–12`. | Applies to all work, including direct sessions; it is cross-cutting, not merely multi-agent operation. Also contains master work allocation and communication preferences. |
| `master-board` | Current state, human queue and sweep. `master-board/SKILL.md:3,8–15`. | State ownership is useful; sweep monitoring overlaps dispatch/watchdog responsibilities. |
| `dispatch` | Agent creation, briefs, model tier, monitoring and returned work. `dispatch/SKILL.md:3,21–79`. | Description is master-only, while the body permits recursive dispatch. |
| `line-worker` | Dispatched work/research execution and handoff. `line-worker/SKILL.md:3,8–10`. | Mixes common dispatched-agent behavior with implementation-worker prohibitions, causing the researcher conflict. |
| `merge-queue` | Exclusive serial integration of ready PRs. `merge-queue/SKILL.md:3,19–61`. | Useful coordination scope; also hard-codes a consumer CI and merge strategy. |
| `release` | Approved deployment, switch, staged checks and failure policy. `release/SKILL.md:3,15–58`. | Mostly a useful generic skeleton. “Fix through a PR” and “update the board” need ownership routing. |
| `visual-qa` | Independent review before presenting a visible change. `visual-qa/SKILL.md:3,8–10,23–40`. | Useful independence and timing contract; overlaps structured-review UI checks and closeout screenshot accounting. |
| `away-mode` | Temporary grants before absence and accounting afterward. `away-mode/SKILL.md:3,14–44`. | Fits a distinct trigger; should consume the authority and state contracts rather than redefine them. |
| `session-handoff` | Persist transient state and cold-start a new master. `session-handoff/SKILL.md:3,18–53`. | Fits a distinct trigger; should reference the master’s startup contract rather than serve as its accidental definition. |
| `fix-triage` | Decide whether a result is wrong, attribute cause, choose a systemic fix. `fix-triage/SKILL.md:3,15–47`. | General engineering/model-analysis work, not inherently multi-agent. Contains product-specific error and cost assumptions. |

##### Thread: The three families are an index arrangement, not an operational routing model

**Severity: should fix.**

`README.md:9–36` separates lifecycle protocols, master/subagent operation and guidance. However:

- `decision-boundary` applies to direct sessions as well as multi-agent work.
- `fix-triage` applies to an individual engineer fixing a result.
- `agents/` defines executable permissions and preloads; calling it only “guidance” understates its authority.
- `agent-readiness/` contains mandatory setup contracts, not only advice.
- Lifecycle workflows apply inside operational roles; the families cannot be mutually exclusive loading sets.

**Smallest correct fix:** keep the families as navigation headings, but add a short role-and-trigger route to the existing role index. Make authority rules cross-cutting. Do not solve this by creating another mandatory umbrella workflow or moving all directories.

##### Thread: Several protocols repeat the same inspection rather than consume its result

**Severity: should fix.**

Examples:

- Visual checks: `visual-qa/SKILL.md:23–40`, `structured-review/references/ui-review.md:9–68`, `structured-review/references/review-lenses.md:150–185`, and `closeout/SKILL.md:211–235`.
- Mechanism lifecycle: `structured-review/references/review-lenses.md:92–120` and `closeout/SKILL.md:156–175`.
- Agent progress: `master-board/references/sweep.md:12–14` and `dispatch/references/watchdog.md:6–15`.
- Evidence and traceability: structured-review’s readiness/lenses and `closeout/SKILL.md:130–144,177–209`.

These are not all redundant gates: independent QA, quality review and final delivery checks answer different questions. The missing boundary is when a later step may consume existing evidence and when changed work requires another exercise.

**Smallest correct fix:** retain each trigger and output, choose one substantive checklist per subject, and have later steps verify that the relevant evidence exists and remains applicable. Do not add another review round merely to reconcile the current documents.

#### 4. Single source of truth per rule

##### Thread: Assign rule ownership before shortening the copies

**Severity: should fix; the authorization conflicts identified in question 5 are blocking.**

The following ownership assignments are recommendations, not claims that the repository already consistently follows them.

| Rule | Recommended source | Copies to reduce to pointers or narrow checks |
|---|---|---|
| Gate definitions | `decision-boundary/CORE.md`; examples and interpretation in `decision-boundary/SKILL.md`, “Gate Tests.” | Keep the consumer embedding as an intentional verbatim copy. Avoid new independently edited gate lists. |
| Grant validity, delegation and revocation | `decision-boundary/SKILL.md`, “Authority Ledger” and “Delegated Execution.” | `closeout/SKILL.md:100–114`, `merge-queue/SKILL.md:26–35`, `release/SKILL.md:17–25`, and overlay merge-permission prose should reference this contract. |
| Line-level lookup of one delegated entry | `decision-boundary/SKILL.md:162–185`. | The full algorithm is repeated in `decision-boundary/CORE.md:19`, `closeout/SKILL.md:106–109`, `merge-queue/SKILL.md:30–35`, `release/SKILL.md:22–25`, and `overlay:authority-ledger.md:3–6`. Keep a short resident warning and one detailed procedure. |
| Only the direct recipient records human approval | `decision-boundary/SKILL.md:114–122,195–202`. | `structured-review/SKILL.md:376–380`, `line-worker/SKILL.md:64–73`, `dispatch/SKILL.md:90`, and `readable-brief/SKILL.md:145–147` need application-specific pointers, not separate formulations. |
| Who may merge | Authority contract plus `merge-queue/SKILL.md`, “Who Merges,” for the execution owner. | Closeout should check permission and deliver readiness, not define a competing merger class. Consumer `context`, `closeout`, `merge-queue` and `AGENTS.md` should point to the same project rule and ledger entry. |
| Deletion first and premise before fix | Currently `structured-review/SKILL.md:407–417,506–520`, with the corresponding review lens. | `fix-triage/SKILL.md:27–30` already points correctly. Remove substantive restatements from `docs/CURRENT.md:40–47`; do not copy them again into a new master charter. |
| Denials versus preferred command shape | Denial boundary: `decision-boundary/CORE.md:21`. Existing command-shape detail: `line-worker/SKILL.md:47–52`, pending relocation if made universal. | `dispatch/templates/brief.md:12–13` repeats shell details; `overlay:master-board.md:39–45` already points back but repeats examples. Preserve the stop-on-denial rule; remove duplicated syntax recipes. |
| Reviewer backend, profile and tier behavior | `structured-review/scripts/claude_structured_review.py:27–74` for executable configuration; one structured-review operating reference for its documented contract. | Delete profile tables and tier-policy retellings from `README.md:133–178`, `docs/CURRENT.md:20–35`, and `closeout/SKILL.md:54–64`. Tests should continue checking intended behavior; they are not redundant documentation. |
| Human approval of decision documents | `structured-review/SKILL.md`, “Document Levels.” | `readable-brief` owns transformation and delivery. It should reference the approval rule; `overlay:readable-brief.md:39–45` need only project-specific delivery/annotation facts. |
| Review thread authorship and resolution | `structured-review/references/collaboration.md`. | `structured-review/SKILL.md:534–552` should summarize and link. Both files are currently loaded into every runner review. |
| Required project gate sequence | `overlay:context.md:24–50`. | `overlay:planning.md:10–21`, `overlay:structured-review.md:43–50`, `overlay:closeout.md:23–25`, and consumer closeout prose should state only their stage’s input/output and point to the sequence. |
| UI inspection criteria | Existing structured-review UI reference/lens. | `visual-qa` should own independence, timing, findings and recheck; closeout should own final evidence accounting. |
| Scope paths and CI commands | Relevant project overlay, with executable behavior in the named project scripts. | Schema/route/migration paths repeat in `overlay:decision-boundary.md:11–16` and `overlay:merge-queue.md:13–15`; pre-merge script internals repeat in `overlay:AGENTS.md:260–281`. Reference their owner instead. |

The resident copy is an intentional exception to ordinary single-source rules: it has an owner and a comparison mechanism. In-memory inspection confirmed the consumer’s copy matches. That is different from independently maintained prose copies.

#### 5. Conflicts

##### Thread: Active ledger entries describe relay-based recording forbidden by core SAFETY

**Severity: blocking for the restructure.**

`decision-boundary/SKILL.md:120–122,199` permits recording only by the session that received the human’s authorization. `structured-review/SKILL.md:376–380` says relay-based records remain pending.

However, `overlay:authority-ledger.md:20–22` says active entries were recorded from a relayed answer on the master’s instruction. Individual entries also cite relay-based records, including L6, L11 and L14 (`overlay:authority-ledger.md:29,34,36`).

This is a concrete conflict between the ledger’s documented provenance and the shared SAFETY rule. It is **not evidence that the human never granted the underlying permissions**. The review cannot reconstruct the original conversations or silently invalidate a genuine grant.

**Smallest correct fix:** the direct recipient should reconcile the durable record from the original authorization. If the intended policy permits a delegated scribe, that changes the current approval-recording boundary and must be decided explicitly upstream. Do not fix it by treating a relay as a direct receipt or weakening only the overlay.

##### Thread: Worker restrictions conflict with researcher permissions and the delegated-execution exception

**Severity: blocking for the restructure.**

- `agents/researcher.md:5–8` preloads `line-worker` and permits production reads allowed by the brief.
- `line-worker/SKILL.md:37–38` prohibits touching production and requires handing the request to the master.
- `overlay:line-worker.md:51–52` permits assigned read-only production work.
- `dispatch/templates/brief.md:8–10` first allows named exceptions, then says any core gate stops the agent.
- `decision-boundary/CORE.md:19` expressly permits exactly delegated gated actions.

The overlay’s production allowance is not itself an override of a labeled `SAFETY` bullet: the conflicting prohibition is in “While Working.” Nevertheless, a researcher loading the prescribed files receives incompatible operational instructions.

The same design problem appears when `overlay:line-worker.md:39–41` prescribes checks for migrations and new endpoints, while `agents/line-worker.md:9–10` categorically prohibits contract changes.

**Smallest correct fix:** separate common dispatched-agent rules from implementation-worker restrictions. State that researcher production reads depend on its explicit brief and project boundary. Reference the central delegation exception rather than rewriting “any gate stops” in each brief.

The decision document must settle whether a worker may execute an already-approved contract change. Do not quietly infer that permission from the existence of migration tests.

##### Thread: Closeout and merge-queue disagree about who may use a direct merge instruction

**Severity: blocking for the restructure.**

`closeout/SKILL.md:92–105` accepts a named current-turn merge instruction without limiting that branch of permission to the master. Its master/delegate restriction is attached to ledger authorization.

`merge-queue/SKILL.md:19–25` instead gives merging exclusively to the master or its one dedicated merge agent. The consumer repeats that exclusive ownership in `overlay:context.md:37–41` and `overlay:AGENTS.md:245–264`.

A human-tasked direct session therefore has a valid permission path under closeout but no execution-owner path under merge-queue.

**Smallest correct fix:** distinguish permission from execution ownership in one sentence and reference the owners. Decide whether exclusive master merging is universal or a project policy. If it is project policy, remove the universal ownership claim from generic closeout/merge guidance; if universal, closeout must route an authorized direct session’s request to the merger. This is a scope decision, not merely wording cleanup.

##### Thread: Worktree freshness requirements undermine the serial integration boundary

**Severity: should fix; settle the boundary in the decision document.**

`agent-readiness/worktree-guard.md:69–73` intentionally fails a repeated guard run whenever the default branch advances, until the feature branch is rebased. The consumer requires the guard before shared protocol use (`overlay:AGENTS.md:124–127`).

Meanwhile, `merge-queue/SKILL.md:8–10` explains that repeatedly rebasing every work line as the default branch advances causes the work and CI multiplication the queue is meant to avoid. It assigns final serial rebasing to the merger (`merge-queue/SKILL.md:43–58`).

A worker resuming planning or review can consequently be forced to perform integration work before reaching the integration owner.

**Smallest correct fix:** narrow the existing freshness requirement to the events that need it, such as creating work and preparing integration. Protocol availability during an established review should not silently become a command to rebase. Do not create another guard to compensate for this policy mismatch.

##### Thread: Several absolute instructions contradict recognized exceptions

**Severity: should fix.**

| Conflict | Evidence | Smallest correct fix |
|---|---|---|
| Only a human decision may block a line, although permission denial and external failures must stop work. | `dispatch/SKILL.md:67–79`; `line-worker/SKILL.md:43–52`; `dispatch/references/watchdog.md:8–12`. | Delete “The only acceptable blocker…” and retain the requirement to record the real blocker, owner and restart condition. |
| The source of an exception to the short observation check differs. | `decision-boundary/SKILL.md:74–77` says “unless the ledger says otherwise”; `release/SKILL.md:43–46` says “unless the overlay says otherwise”; `overlay:release.md:14–17` supplies the two-hour dependency gate. | Point both to the approved release schedule; distinguish permission evidence from operational schedule parameters. |
| Brief-only fixes need no re-review, but only the reviewer may close a thread. | `readable-brief/SKILL.md:124–138`; `structured-review/references/collaboration.md:70–80`. | Declare how the already-authorized brief-only exception is recorded and closed. Do not add an extra review contrary to the brief protocol. |
| Plain-text, one-at-a-time questioning is stated absolutely, while mechanisms and away-time grants are batched. | `decision-boundary/SKILL.md:65–68,148–159`; `away-mode/SKILL.md:16–29`. | Move presentation preferences to the user-level source and make the specific batching behavior an explicit exception where retained. |

**Note:** L14’s reduced-acceptance permission is not automatically a conflict with the generic evidence policy. `structured-review/SKILL.md:562–567` allows explicit human acceptance of a scoped residual limitation. It still requires accurate `Partial`/`not validated` reporting. Its provenance problem is the earlier ledger thread; the mere presence of a scoped exception should not produce a second invented blocker.

#### 6. Layering

##### Thread: Personal preferences remain in core protocols and project overlays

**Severity: should fix.**

The intended separation is documented in `README.md:48–70`, `dispatch/SKILL.md:14–15`, and `decision-boundary/SKILL.md:155–160`. The historical origin also explicitly classified model tiers, concurrency, brief language and banned words as personal preferences (`docs/agent_plans/2026-10-11_decision_boundary_and_master_protocols_plan.md:48–55`). That plan is provenance, not an additional current instruction.

| Current location | Misplaced content | Recommended home |
|---|---|---|
| `decision-boundary/SKILL.md:148–160`; `master-board/SKILL.md:41–43`; `dispatch/SKILL.md:81–84` | One-question format, mandatory numeric example, report ending and forwarding separators. These closely repeat the consumer’s explicitly personal master preferences. | User-level preferences; keep only the required decision information in core. |
| `overlay:master-board.md:28–37` | Chinese report headings, question style, page preferences and forwarding format. | User-level preferences. Retain project production/report fields in the overlay. |
| `overlay:dispatch.md:5–20` | Subscription-specific Opus/Sonnet selection, excluded models, concurrency policy and reporting language. | User-level model/subscription preferences; dispatch references that source. |
| `overlay:readable-brief.md:5–45` | Reader-specific banned words, terminal glyph constraints, reading time and editor-opening behavior. | User-level reader/delivery preferences. Keep the repository’s source language and filename conventions as project facts. |
| `overlay:context.md:10–14`; `overlay:planning.md:37–39` | Terminal clipboard and personal handoff behavior. | User/tool configuration, not generic project workflow. |
| `overlay:line-worker.md:7–12`; `overlay:session-handoff.md:5–10` | Machine layout, Git transport and old-machine archive location. | Separate personal machine instructions from project commands and project state identity. |

The readable-brief instruction to open an editor also conflicts with the currently loaded personal preference requiring permission in that moment before opening applications. The smaller correction is to remove automatic app-opening from the project overlay and defer to current delivery preferences.

Do not move every number or device detail out indiscriminately. The visual viewport/browser acceptance targets in `overlay:visual-qa.md:5–8` can be legitimate project test requirements. The historical adoption plan explicitly classed viewport acceptance as project policy. Test-container limits likewise describe a real execution environment; identify that environment without turning it into a universal rule.

##### Thread: Consumer-specific operating and product assumptions have become generic rules

**Severity: should fix.**

1. **CI and merge strategy.** `merge-queue/SKILL.md:55–62` asserts that pushing triggers nothing, expensive CI runs immediately before merge, and rebase merges rewrite hashes. The same repository’s `.github/workflows/ci.yml:3–7` actually runs on pull requests. Generic queue coordination should not assume the consumer’s CI topology or merge method.

2. **Product error tolerance.** `fix-triage/SKILL.md:17–19,34–37` treats one extra or missing record as not inherently erroneous and prefers grounded redundancy when downstream cleanup exists. Those assumptions fit the named consumer pipeline, but are not general facts about all software. Keep “judge against the owning layer’s contract”; move the pipeline-specific tradeoff to `overlay:fix-triage.md:10–13`.

3. **Enum policy.** The unreferenced `fix-triage/references/principles.md:8–9` requires every enum to have an `other` bucket. That is a schema-design decision, not a universally correct fix principle. Delete the blanket rule rather than add exceptions.

4. **Document layout.** `closeout/SKILL.md:243–249,312–322` hard-codes phase-output and manifest conventions. These should be conditional on the repository’s documentation contract. A universal closeout skill should not introduce a manifest mechanism into every consumer.

5. **Vendor behavior.** Transcript discovery in `retrospective/SKILL.md:41–52`, notification assumptions in `dispatch/references/watchdog.md:3–4`, and session-lifetime assumptions in `session-handoff/SKILL.md:8–10,42–45` belong with agent capabilities or clearly stated limitations. The common workflow should not assume every agent has identical persistence or notification behavior.

**Smallest correct fix:** delete universal assertions where a reference to the project contract is sufficient. Move vendor-specific operational detail to existing readiness guidance. Do not compensate with new per-project switches for each inherited assumption.

The named consumer’s business rules, governance grants, production commands, contract paths and test commands generally belong in its overlays or the project documents those overlays cite. The ledger’s Keeper transition is an appropriate project-specific boundary.

#### 7. Orphans and stale text

##### Thread: Fix-triage has an unreferenced policy file

**Severity: should fix.**

`fix-triage/references/principles.md` carries substantive rules but has no explicit inbound reference in the active Markdown corpus. The same search found the expected references to `dispatch/references/watchdog.md` and `line-worker/references/read-only-research.md`, providing a positive control for the search.

**Smallest correct fix:** delete principles already owned elsewhere; move any remaining valid principle into its actual owner. Merely linking the entire file would make unsupported blanket rules, including the enum rule, newly reachable.

##### Thread: Current instructions still route to retired or contradictory behavior

**Severity: should fix.**

- `overlay:retrospective.md:15` directs generic changes to a machine-global protocol directory, contrary to `README.md:72–89` and `overlay:AGENTS.md:124–153`, which require the canonical repository and pinned submodule. Replace that route with the canonical source workflow.
- `overlay:structured-review.md:10–18` gives a new-call example without explicit tier or coding-agent identity. The current contract requires a tier and requests explicit identity (`structured-review/SKILL.md:133–167`). Update the example or point to the canonical example.
- `README.md:118–127` supplies a runner example without `--coding-agent` although its following prose requests it. Correct the example; do not add another explanation.
- `overlay:backlog-maintenance.md:82–86` says CI checks every pull request head, while `overlay:AGENTS.md:233–239` and `overlay:closeout.md:44–50` say pushes run nothing and evidence comes from pre-merge execution. Replace the stale claim with a pointer to the current CI owner.
- `session-handoff/SKILL.md:20` says to overwrite `templates/SESSION_HANDOFF.md` in the state directory, whereas `overlay:session-handoff.md:5` names the output as `SESSION_HANDOFF.md`. Say “write the handoff file using the template.”
- `agents/researcher.md:5` uses an ambiguous `references/read-only-research.md` path outside the protocol directory. Qualify it as `line-worker/references/read-only-research.md`.

I did not find a missing top-level protocol directory among the requested entries. Placeholder paths, optional overlay paths and production-host paths are not broken repository links merely because they do not exist in this checkout.

##### Thread: Discovery and indexes do not consistently describe the current package

**Severity: should fix for the indexes; note for local mounts.**

- `README.md:87` says “No … copied protocol content,” while the resident-core contract deliberately requires a verbatim copy (`agent-readiness/worktree-guard.md:148–173`). State that exception explicitly.
- `docs/CURRENT.md:20–53` reproduces detailed structured-review policy rather than mapping its owner. This is a second operating manual inside the current index.
- The project’s native `.agents/skills/` and `.claude/skills/` directories each expose seven lifecycle protocols; the ten newer operational skills are absent. All seven existing mounts resolve correctly. This is a local discovery gap, not evidence that the ten protocols are inaccessible: the indexes still name them.
- `docs/agent_plans/README.md`, “Current Records,” is a selective historical list, not a complete active-work index. Rename it accordingly or point explicitly to current work; do not turn it into another exhaustive registry.

**Smallest correct fix:** shorten indexes to role, trigger and owner links. For local mounts, either make the intended maintenance-only subset explicit or expose the missing skills using the existing mount arrangement. No new discovery mechanism is needed.

#### 8. Size and progressive disclosure

##### Thread: Entry files and reviewer prompts load details for the wrong reader

**Severity: should fix.**

Measured sizes in this snapshot:

| Surface | Size | Main opportunity |
|---|---:|---|
| `decision-boundary/CORE.md` | 23 lines, 458 whitespace-delimited words | Keep role identification, gates, stop/escalation rules and a short delegated-action exception. Move the detailed ledger lookup procedure out of the long dispatched-agent bullet. |
| Consumer `AGENTS.md` | 296 lines | Its “CI Triggering and Merging” section alone is 55 lines. Keep the ownership prohibition and route; move script internals, retries and bootstrap history to the merge overlay/runbook. |
| `README.md` | 178 lines | Runner policy occupies much of the second half. Replace with the canonical operating-reference link and one valid example. |
| `docs/CURRENT.md` | 114 lines | The structured-review entry is 34 lines. Reduce it to a source map. |
| `structured-review/SKILL.md` | 584 lines | Separate reviewer/driver operating checklists from runner operations, recovery, compatibility and document-policy detail. |
| Runner’s skill plus two mandatory references | 1,009 lines, about 7,400 words | Every reviewer receives both roles’ procedures and extensive driver-only runner guidance before task artifacts and overlays. |
| `closeout/SKILL.md` | 393 lines | Extract conditional UI, document/submodule and mechanism checks; reference authority and review evidence contracts. |
| `backlog-maintenance/SKILL.md` | 380 lines | Move schema examples and detailed field reference behind the short add/update/query/close workflow. |
| `agent-readiness/worktree-guard.md` | 253 lines | Acceptable as a specialist reference if it remains on demand; avoid copying its implementation sketch into entrypoints. |

The operational skills are mostly short, at 46–91 lines; they do not need wholesale merging merely to reduce file count. Their chief problem is repeated authority text and ambiguous role composition.

The resident-core test checks at most 40 lines (`tests/test_resident_core.py:30–33`). That is not evidence of low reading cost: the largest instruction is compressed into one line. Do not add another size guard; simplify the text according to what every role actually needs.

**Smallest correct fix:** move existing detail behind conditional references and remove duplicate prose. Preserve the essential denial and escalation boundary in resident text. The reviewer prompt should retain the required review standard, while driver-only runner operation belongs in driver guidance.

#### Overall judgment

The repository has useful workflow components, but it lacks a coherent role contract above them. Its principal structural faults are:

- authority roles and task responsibilities are mixed without composition rules;
- the master’s definition is distributed across workflows and consumer policy;
- authorization and execution ownership have competing formulations;
- personal and consumer-specific rules have entered supposedly generic policy;
- indexes and entrypoints repeat procedures instead of routing readers to their owners.

**The audit is ready to inform the restructure decision document. The restructure itself is not ready for implementation until the blocking role, master-scope, approval-provenance and merge-ownership decisions are settled.**

#### Residual risks and validation provenance

- Findings are based on reviewer inspection, Git snapshot comparison, file inventory, reference searches and in-memory text comparison.
- No files were written, staged or committed. No bootstrap/guard scripts, paid calls, production commands or workflows were run.
- Core and consumer HEADs were unchanged and both worktrees were clean at the final check.
- No claim is made about current vendor capability support, live CI behavior, production state or the truth of historical approvals beyond the inspected records.
- Script/test inspection was limited to structural and policy evidence. This was not a runner correctness review or a new execution-based certification of any guard.
- The consumer ledger was inspected as explicitly requested audit evidence, not used as authorization for reviewer actions.

#### Target-structure proposal — recommended, not yet approved

Keep existing protocol package paths initially. Reorganize ownership and reading routes before undertaking directory moves.

| Role or responsibility | One recommended owner file |
|---|---|
| Authority-role vocabulary: direct session, dispatched agent, and how roles combine | `agents/README.md` |
| Master’s complete role contract | `agents/master.md`, consolidating existing duties and linking to their procedures |
| Line worker | `agents/line-worker.md` |
| Researcher | `agents/researcher.md` |
| Merge agent | `agents/merge-queue.md` |
| Release agent | `agents/release.md` |
| Visual QA agent | `agents/visual-qa.md` |
| Author, review driver and reviewer responsibilities | `structured-review/references/collaboration.md` |
| Scout execution responsibility | `scout/SKILL.md` |
| Closeout responsibility | `closeout/SKILL.md` |
| Intermediate coordinator, if supported | A subsection of the dispatched-agent contract in `agents/README.md`; no new authority tier |
| Human authority | `decision-boundary/SKILL.md`; actual project grants remain in the project ledger |

Organize the rule families as follows:

1. **Cross-cutting authority:** `decision-boundary/CORE.md` is the resident summary; `decision-boundary/SKILL.md` owns permission, provenance, delegation and escalation. Other protocols consume that contract.
2. **Development lifecycle:** planning, structured review, closeout, readable briefs, retrospectives, backlog maintenance and Scout retain their outputs. Fix triage and visual QA are supporting workflows available to the relevant roles.
3. **Multi-agent operation:** master-board owns coordination state; dispatch owns briefs and agent supervision; line-worker owns work execution/handoff; merge-queue and release own their execution procedures; away-mode and session-handoff own their distinct transitions.
4. **Agent integration guidance:** `agent-readiness/` owns setup and vendor capability details. `agents/` owns role definitions. Neither should duplicate project business policy.
5. **Project and personal layers:** overlays retain project paths, commands, acceptance targets, settled business decisions and grant records. User-level instructions own language, report style, subscription/model preferences and personal machine behavior. `AGENTS.md`, `README.md` and `docs/CURRENT.md` become short routing surfaces, with the resident core as the deliberate checked copy.

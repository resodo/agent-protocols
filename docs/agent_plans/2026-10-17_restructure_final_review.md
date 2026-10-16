# Whole-repo review after the restructure (review request)

Document level: review request (no PR is opened from this file's findings
alone; blocking findings get fix PRs).

Status: active (2026-10-17).

## Why

The approved restructure decision (`2026-10-16_repo_restructure_decision.md`)
requires, after its five plans, a hard review of the **full resulting state**
(not the diffs) until it converges. Plans 1-4 merged: agent-protocols #45, #46,
#47; skynet-intern #1712; skynet-apps #44. Plan 5 (personal files and memory,
outside all repos) is done and is not reviewable here.

## What to review

1. This repo at this commit: every protocol, `agents/`, `agent-readiness/`,
   `README.md`, `AGENTS.md`, `docs/CURRENT.md`, `docs/README.md`.
2. skynet-intern, read-only, at the relative path `../../../skynet-intern/main/`
   from this worktree: `AGENTS.md`, every file in `.agent-protocols/`,
   `scripts/agent_protocols_guard.sh`, `scripts/ops/hooks/agent_role_reminder.py`,
   `docs/collaboration/worktree_feature_protocol.md`. Cite as `intern:<path>`.
3. skynet-apps, read-only, at `../../../skynet-apps/main/`: `AGENTS.md`, every
   file in `.agent-protocols/`, `scripts/agent_protocols_guard.sh`. Cite as
   `apps:<path>`.

## Questions

1. Did the restructure achieve the decision's target (sections 3-5): one role
   file per role with the same fields; one master definition; each protocol's
   reader and scope stated; each rule in one home with pointers elsewhere;
   core vs overlay vs personal correctly placed?
2. Contradictions or gaps introduced by the restructure: rules that now
   disagree, pointers to sections that do not exist or do not contain the
   rule, rules dropped in a move, a weakened `SAFETY` rule.
3. Remaining duplication or stale text (indexes, examples, overlays restating
   the core).
4. Role scenarios, each answered from the files only: a master taking over; a
   coordinator at a point of no return; a direct session told to merge while a
   master runs; a researcher told to read production; a worker whose brief
   cites an approved contract change; an agent typing a ledger entry; a
   production operator doing a configuration change; a line handing a PR to
   the merge queue and then wanting to fix a typo.

## Output

Findings by question, each with severity (blocking / should fix / note),
citations, and the smallest fix, deletion first. Say explicitly whether the
state has converged (no blocking findings).

## Review Threads

### Reviewer pass 1 (other-plan, codex reviewer)

The human wants clear role boundaries, one master definition, and one authoritative home for each rule across the shared protocols and both consumers.

Reviewed the full protocol state at `7c1a92b`, intern at `0159329f6`, and apps at `67e488d6`. Both consumers pin `c615ae5`; the shared review checkout differs from that revision only by this review request.

#### Blocking issues

##### Thread: Coordinator procedures contradict its reporting and write boundaries

**Questions 1, 2 and 4 — blocking.**

`agents/README.md:36` requires a coordinator to escalate gates to the master and prohibits passing delegated permission onward. Its workers report to the coordinator. `agents/master.md:41` reserves board writes to the master.

However, the coordinator also loads `dispatch`:

- `dispatch/SKILL.md:58` tells the dispatcher to write the board.
- `dispatch/SKILL.md:66` tells it to relay results and denials directly to the human.
- `dispatch/templates/brief.md:4` identifies every dispatcher as the master; line 10 routes every worker’s escalation to the master.

Following these instructions bypasses the coordinator or gives it duties reserved to the master. This is a conflict within the coordinator’s required reading, not an unsettled role choice.

**Smallest fix:** qualify the master-only actions in `dispatch`; coordinators report those results to the master. Replace fixed “master” routing in the brief template with the actual dispatcher, retaining the existing production-operator exception. No new role or mechanism is needed.

##### Thread: Cold start assumes that all previous agents have stopped

**Questions 2 and 4 — blocking.**

`agents/master.md:33` describes takeover from an earlier master and explicitly accounts for running agents. But `session-handoff/SKILL.md:44` concludes that every previously running line “has no agent now” and directs redispatch or parking.

Appointment of a new master does not establish that an earlier worker, reviewer or production command has terminated. Following the unconditional redispatch instruction can create two agents working on the same line, contrary to the takeover boundary.

**Smallest fix:** delete the assertion that every agent is gone. Use the existing live-state check to distinguish surviving work from terminated work before redispatching. Reissue gated delegations only after the new master’s check, as already required by `decision-boundary/SKILL.md:217`.

##### Thread: Apps has two competing sources for production instructions

**Questions 1, 2 and 4 — blocking.**

`apps:AGENTS.md:39` classifies `release` among the parameters inherited from intern. Its local-overlay list at line 46 omits `release`. Yet `apps:.agent-protocols/release.md` exists, and `apps:.agent-protocols/line-worker.md:23` explicitly routes production work to it.

These sources are materially different. The apps overlay names its configuration and migration chain (`apps:.agent-protocols/release.md:8`, `:19`); intern names its live-runtime configuration and operator-output location (`intern:.agent-protocols/release.md:12`, `:20`). The generic protocol requires the operator to obtain commands, receipts and checks from the project release overlay (`release/SKILL.md:15`).

**Smallest fix:** remove `release` from the blanket home-repo inheritance list and identify the apps release overlay as authoritative for apps commands and configuration. Where shared measurement policy applies, point explicitly to that policy. This follows the approved separation between shared master state and each repository’s facts (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:98`).

##### Thread: Apps does not supply its own contract surfaces to the merge check

**Questions 1 and 2 — blocking.**

`merge-queue/SKILL.md:48` requires a mechanical check of the contract paths supplied by the overlay. `apps:.agent-protocols/merge-queue.md:14` lists only the protocol submodule pointer.

The inherited intern gate map names intern schemas, route declarations and `backend/alembic/` (`intern:.agent-protocols/decision-boundary.md:11`). It does not identify apps’ accounts contract or application migration chain. Apps itself documents additional contract surfaces at `apps:AGENTS.md:99`, `:113` and `:130`, including:

- `accounts/skynet_accounts/schemas.py`;
- `accounts/openapi/auth_api.json`;
- `backend/openapi/generated/app_api.json`;
- `backend/app/applications/migrations/`.

A merger following the configured list lacks the repository-specific inputs needed to perform the required contract check.

**Smallest fix:** complete the existing apps gated-surface instructions with its actual contract, route and migration locations, using one local source and a pointer from the merge overlay. Keep the shared authority ledger in intern. This needs no new permission or checker.

##### Thread: An isolated ledger lookup can return superseded permission scope

**Questions 2 and 4 — blocking.**

`decision-boundary/SKILL.md:205` requires a delegated executor to inspect only the cited ledger entry immediately before acting. But `intern:.agent-protocols/authority-ledger.md:39` still gives L14 the old “production vs PC2 + 20 ms” criterion. L14a, on the following row, replaces that criterion with a same-window baseline; L14b adds the measurement method.

An executor verifying only L14 sees a scope that the same ledger has superseded. An executor verifying only L14a does not receive the underlying reduced-acceptance grant. The current representation conflicts with the deliberately narrow lookup procedure.

**Smallest fix:** make L14’s current scope reflect the recorded amendments, preserving the original words and amendment provenance. Keep amendment rows as historical references instead of competing current instructions. Do not widen ledger access or seek fresh approval for an already recorded decision.

#### Non-blocking issues

##### Thread: Remaining copies prevent completion of the one-home cleanup

**Questions 1 and 3 — should fix.**

Full permission conditions remain in `intern:.agent-protocols/context.md:32`, `intern:.agent-protocols/closeout.md:10`, `intern:.agent-protocols/merge-queue.md:25`, `apps:.agent-protocols/context.md:37` and `apps:.agent-protocols/merge-queue.md:21`. These exceed the approved one-line-pointer rule (`docs/agent_plans/2026-10-16_repo_restructure_decision.md:91`).

There is also stale preference routing: `session-handoff/SKILL.md:41` locates model-tier rules in the project overlay, while `dispatch/SKILL.md:14` places them in user-level instructions. `readable-brief/SKILL.md:29` still assigns personal reading preferences to overlays.

**Smallest fix:** replace duplicate permission conditions with references to Delegated Execution; correct preference pointers. Preserve actual project-specific restrictions and parameters.

##### Thread: The active worktree guide retains incompatible commands

**Questions 2 and 3 — should fix.**

`intern:docs/collaboration/worktree_feature_protocol.md:90` still instructs agents to use `git worktree add` and a sibling-directory layout. Cleanup at line 270 likewise bypasses Worktrunk. These disagree with `intern:.agent-protocols/line-worker.md:7`.

The same guide permits squash merging at line 263, while `intern:.agent-protocols/closeout.md:7` requires rebase merging.

**Smallest fix:** delete the obsolete creation, cleanup and merge-choice recipes and point to the current worktree and merge instructions. Keep this document’s useful scope-isolation and migration guidance.

##### Thread: Ledger activation prose still describes completed work as pending

**Question 3 — should fix.**

L14a, L14b, L15 and L16 are marked active, but `intern:.agent-protocols/authority-ledger.md:45` still says they grant nothing until activation and a confirmation record are added.

Commit `intern:0159329f6` records activation by the master who received the confirmation. That evidence makes this a stale-record problem, rather than evidence that the grants lacked confirmation.

**Smallest fix:** reconcile the pending paragraph and entry records with that recorded activation. Do not reopen the human’s authorization.

##### Thread: Current routing does not fully expose the agreed source map

**Questions 1 and 3 — should fix.**

The four-layer ownership definition and home-repo rule are clear in `docs/agent_plans/2026-10-16_repo_restructure_decision.md:80`, but `README.md:65` explains only generic and local-overlay loading. The current map does not route maintainers to the complete ownership definition.

Also, the resident core’s `agents/master.md` pointer (`decision-boundary/CORE.md:4`) is not a consumer-relative path. Both consumers provide the correct vendored path elsewhere, so this is recoverable, but the embedded pointer itself is misleading.

**Smallest fix:** add a current pointer to the approved ownership definition, and make the resident-core role pointer explicitly relative to the protocol checkout. Avoid another copy of the ownership table.

#### Overall judgment

**The state has not converged. Five blocking threads remain.**

1. **Did the restructure achieve the target? Partly.** The six role files now contain the common fields; the coordinator and direct-session exceptions match the decision. The master has a clear definition, and all 17 protocol descriptions identify their readers. Permission ownership and runner-operation routing are substantially clearer. Coordinator procedure conflicts, consumer ownership mistakes and remaining copies prevent full acceptance.

2. **Are there contradictions, missing rules or weakened safeguards? Yes, as detailed above.** Inspection of the changed `SAFETY` sections found that the merge-permission and approval-recording rules were retained through pointers or the approved scribe distinction. The blocking problems concern how current instructions compose and which effective facts an executor reads.

3. **Does duplication or stale text remain? Yes.** The non-blocking threads identify remaining permission copies, preference-routing errors, obsolete worktree instructions and incomplete ledger cleanup. Historical review comments need no modernization.

4. **Role scenarios, answered from the files:**

| Scenario | Answer from the current files |
|---|---|
| Master taking over | The newly named master owns coordination; the earlier master stops new and gated work (`agents/master.md:33`). Load and verify state, then renew delegations. **Blocked by the cold-start assumption about surviving agents.** |
| Coordinator at a point of no return | Message the master, obtain its answer and resend an unacknowledged request; never grant or redelegate permission (`agents/README.md:36`, `dispatch/SKILL.md:90`). **Its supporting dispatch instructions need correction.** |
| Direct session told to merge while a master runs | It does not execute the merge. Only the master or its designated merger executes while a master runs (`decision-boundary/SKILL.md:194`). |
| Researcher told to read production | It may do so only within its brief and project restrictions (`agents/researcher.md:5`). Intern additionally requires master assignment, bounded read-only queries and the stated release-window restrictions (`intern:.agent-protocols/line-worker.md:72`). |
| Worker whose brief cites an approved contract change | It may implement the exact authorized change; other gates still stop it. It does not merge or contact production (`agents/line-worker.md:6`, `line-worker/SKILL.md:80`). |
| Agent typing a ledger entry | It types a `proposed` entry. Only the session that directly heard the grant compares the words and scope and activates it (`decision-boundary/SKILL.md:123`). Typing is not approval. |
| Production operator changing configuration | The brief names the change, official command, receipt and permission. Record the previous value or undo, check preconditions and baseline, then perform read-back and the named health check; report to the master (`release/SKILL.md:22`, `:31`, `:47`, `:73`). **Apps’ competing overlay routing prevents an unambiguous project-specific answer.** |
| Author wants to fix a typo after queue handoff | Send the correction to the merger; do not push to the queued branch (`line-worker/SKILL.md:82`, `merge-queue/SKILL.md:31`). A returned PR follows the queue’s explicit return-to-author path (`merge-queue/SKILL.md:57`). |

#### Residual risks and validation gaps

- Validation was reviewer-performed file inspection, Git inspection and read-only comparisons. Both consumers have matching resident-core copies and correctly resolving mounts for all 17 protocols.
- Bootstrap and guard scripts were inspected but not executed. No tests, production commands, network freshness checks or independent fresh-master exercise were performed.
- Personal-file and memory migration remains outside this review’s scope.
- All three inspected worktrees remained clean. The review branch has no upstream, and no cached remote ref contains its head; publication was not verified.
- No files were written, staged or committed.

### Driver response to reviewer pass 1

Classification: every blocking and should-fix finding accepted. Core fixes are
in this branch; consumer fixes go in one PR per consumer (skynet-intern,
skynet-apps), each with its own plan and reviews, bumping to this branch's
merge.

Core (this branch):

- Coordinator procedures: `dispatch` After Dispatching and When An Agent
  Reports now route a coordinator's board updates, relays and denials to the
  master; the brief template names the actual dispatcher and routes reports
  and gates to it, keeping the production-operator exception.
- Cold start and surviving agents: `session-handoff` step 4 no longer assumes
  every agent is gone; it checks whether the earlier master and its agents
  still run, takes over a live line by messaging it, re-dispatches only lines
  confirmed stopped, and re-issues delegations after the check.
- Preference pointers: `session-handoff` step 2 points model tiers to the
  master preferences; `readable-brief` Local Overlay assigns reader
  preferences to the user level and leaves project facts to the overlay.
- Resident core: the role pointer says `agents/master.md` "in the
  agent-protocols checkout" (consumers must re-copy the core).
- `README.md` gains "Where A Rule Lives" pointing to the approved four-layer
  definition, without copying its table.

Consumer PRs (next): intern L14 current scope consolidated with amendment
provenance and the stale pending paragraph reconciled; permission copies in
intern and apps overlays replaced by pointers; intern worktree guide's
obsolete recipes removed; apps release overlay made authoritative for apps;
apps gated surfaces listed; resident core re-copied in both.

### Reviewer pass 2 (impl, codex reviewer)

The human’s concern is that the restructured protocols give each role clear instructions and keep each rule in one authoritative home. I reviewed `HEAD~1..HEAD` against the pass-1 findings, limited to the shared core fixes. The worktree was clean.

#### Blocking issues

##### Thread: Cold-start takeover assumes cross-session messaging works

`session-handoff/SKILL.md:48` tells a new master to take over a surviving agent by messaging it. The capability map documents Codex follow-up messaging through the agent’s **parent** thread (`agent-readiness/capabilities.md:53`); it does not establish that a new master session can reach an agent owned by the earlier session. The instruction gives no path when the agent is known to be running but cannot be reached. That leaves the claimed takeover and delegation check incomplete.

**Smallest fix:** say to park the line until the running agent can be reached and acknowledges the handoff, using an available documented route. Do not redispatch or reissue that line’s gated delegation in the meantime. No new mechanism is needed.

##### Thread: Brief-language fallback overrides the reader’s preference

`readable-brief/SKILL.md:29-32` correctly puts the reader’s language preference in user-level instructions. Line 34 then says that, without a project overlay, the brief must use the source document’s language. For an English decision document and a reader whose user-level preference is Chinese, the fallback produces the wrong brief.

**Smallest fix:** use the reader’s user-level preference when present; fall back to the source language only when no reader preference is recorded.

#### Non-blocking issues

None in the scoped core fixes.

#### Overall judgment

The coordinator routing, dispatch brief, master-preference pointer, resident-core pointer, and README source-map pointer address their pass-1 findings by direct inspection. Cold-start handling and readable-brief preference routing remain **Partial** for the reasons above. The core fixes are **not yet ready for closeout**. This judgment does not assess the deferred consumer PR fixes or declare the full restructure converged.

#### Residual risks and validation gaps

This documentation-only pass used the changed diff, current instructions, and concrete reading scenarios. No scripts or tests were run, and no files were written. Cross-session agent messaging was not demonstrated; the capability map is the recorded basis for that finding.

### Driver response to reviewer pass 2

- Cold-start takeover: accepted; a live or unknown line is parked until its
  agent is reachable through a documented route and acknowledges the
  handoff; no second agent, no re-issued delegation before that.
- Brief language: accepted; the reader's user-level preference wins, the
  source language is only the fallback.

### Reviewer pass 3 (impl, codex reviewer)

The human wants the restructured protocols to give each role clear instructions and keep each rule in one authoritative home. I reviewed `HEAD~1..HEAD`, the requested artifacts, and the existing threads. The worktree is clean.

#### Blocking issues

##### Thread: A stopped agent cannot acknowledge handoff

`session-handoff/SKILL.md:47-53` permits redispatch when the previous agent is confirmed stopped, but then says to re-issue the line’s gated delegation “only after” that agent is reached and acknowledges handoff. A stopped agent cannot do that. The instruction leaves the replacement agent’s delegation path unclear, despite `decision-boundary/SKILL.md:221-222` requiring the new master to recheck the ledger before re-issuing it.

**Smallest fix:** state the two cases separately. For a confirmed stopped agent, recheck the ledger before delegating to its replacement. For a live agent, keep the line parked until the agent acknowledges handoff. This needs no new mechanism.

#### Non-blocking issues

`session-handoff/SKILL.md:8` still says subagents die with the session, while its cold-start procedure now explicitly checks for surviving agents. Remove that blanket claim so the opening does not undermine the procedure.

#### Overall judgment

The brief-language thread is **resolved** by `readable-brief/SKILL.md:34-35`: the reader’s recorded preference takes priority, with the source language as fallback. The cold-start thread is **Partial**. It now safely parks live or unknown agents, but the stopped-agent delegation path above needs correction. The scoped core fixes are **not yet ready for closeout**. Consumer findings remain outside this pass.

#### Residual risks and validation gaps

This documentation-only review used the committed diff and direct reading of the instructions. No scripts or tests were run. Cross-session messaging was not demonstrated; the revised procedure parks a line when contact is unavailable.

### Driver response to reviewer pass 3

- Stopped-agent delegation path: accepted; delegations are re-issued for a
  stopped line when it is re-dispatched, and for a live line after its
  agent's acknowledgement.

### Reviewer pass 4 (impl, codex reviewer)

The human wants the restructured protocols to give each role clear instructions and keep each rule in one authoritative home. I reviewed `HEAD~1..HEAD` against the pass 3 response. The worktree is clean.

#### Blocking issues

None. **The stopped-agent delegation thread is resolved.** `session-handoff/SKILL.md:47-54` now separates the two paths: a confirmed stopped line can receive a new delegation when re-dispatched; a live line waits for its agent to acknowledge handoff. `decision-boundary/SKILL.md:221-222` requires the new master to recheck the ledger before either delegation.

#### Non-blocking issues

The pass 3 wording issue remains: `session-handoff/SKILL.md:8` says subagents die with the session, while the cold-start procedure checks for surviving agents. Remove the blanket claim. The explicit live-state check prevents this wording issue from blocking the scoped fix.

#### Overall judgment

The pass 3 blocking finding is resolved. **The scoped core fix is ready for closeout.** This judgment does not cover the consumer findings or declare the full restructure converged.

#### Residual risks and validation gaps

This documentation-only pass used the committed diff and direct inspection. No scripts or tests were run. Cross-session messaging was not demonstrated; the procedure parks a live line when its agent cannot be reached.

# Convergence review after the final-review fixes (review request)

Document level: review request (no PR is opened from this file's findings
alone; blocking findings get fix PRs).

Status: active (2026-10-17). Second full-state pass: after agent-protocols #48, skynet-intern #1715 and skynet-apps #45 merged (all pinned at 194d1fd). The first pass and its fixes are in `2026-10-17_restructure_final_review.md`.

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

Reviewed the current instructions at `22b0476`, intern’s local `main` at `1900ec4a321d`, and apps’ local `main` at `bd99ab8d10ed`. Both consumers pin `194d1fd`; the shared review checkout differs from that revision only by the convergence-review request.

#### Blocking issues

##### Thread: Apps’ authoritative release overlay still describes an obsolete operating procedure

**Questions 1, 2, 3 and 4 — blocking.**

The previous routing conflict is fixed: `apps:AGENTS.md:46` now identifies the local release overlay as authoritative. Its contents still describe the earlier accounts-only deployment:

- `apps:.agent-protocols/release.md:9` supplies `switch.sh --migrate-to` as the migration procedure. That flag migrates **accounts only**, as confirmed by `apps:scripts/ops/switch.sh:135` and `apps:docs/runbooks/host_split_operations.md:60`. Applications migrations instead use `apps-migrate.sh`, before switching to the new release (`apps:scripts/ops/apps-migrate.sh:32`).
- `apps:.agent-protocols/release.md:12` assumes the shared host and omits the conditional host-selection requirement. The current runbook requires a named host when the hosts file exists (`apps:docs/runbooks/host_split_operations.md:38`).
- `apps:.agent-protocols/release.md:19` retains a manual first-deployment exception because no `current` exists. The current official switch supports that case directly (`apps:docs/runbooks/host_split_operations.md:52`).

These are operational differences, not merely missing background. A master preparing an applications migration or first switch on another host gets conflicting instructions from the newly designated authority and the current runbook. The generic release protocol expressly obtains commands and required flags from that overlay (`release/SKILL.md:15`).

**Smallest fix:** delete the obsolete P18 procedure and replace it with pointers to the current host-operation runbook and the documented applications migration sequence. Keep accounts-only migration guidance explicitly scoped to accounts. Preserve the shared gate-measurement pointer. No new script, permission or mechanism is needed.

**Validation:** walk two documentation-only scenarios: a release containing an applications migration, and a first switch on a configured host without `current`. Both should identify the existing official command, host selection, sequence and receipts consistently.

#### Non-blocking issues

##### Thread: Brief review still looks for personal preferences in the overlay

**Questions 1 and 3 — should fix.**

`readable-brief/SKILL.md:29` correctly assigns reading preferences to user-level instructions. Its self-review still checks “the overlay’s” reading-time target and banned words (`readable-brief/SKILL.md:114`). The reviewer’s narrow lens repeats that obsolete source (`structured-review/references/review-lenses.md:319`).

**Smallest fix:** change those references to the reader’s user-level preferences. Do not copy the preferences back into overlays. The earlier preference-routing finding is therefore only partly resolved.

##### Thread: Handoff introduction still says all subagents die with the session

**Questions 2 and 3 — should fix; carried forward from the previous pass 4.**

`session-handoff/SKILL.md:8` retains the blanket claim, while its corrected cold-start procedure explicitly handles surviving or unreachable agents (`session-handoff/SKILL.md:44`).

**Smallest fix:** delete the blanket assertion. The explicit live-state procedure keeps this wording issue non-blocking.

#### Overall judgment

**The state has not converged. One blocking thread remains: the current contents of apps’ release overlay.**

The structural target is substantially achieved: six role files contain the common fields, the coordinator boundary is defined, the master has one definition, all 17 protocols identify their readers, and the indexes route to the four-layer ownership definition. The remaining blocker concerns the correctness of project facts in their designated home.

The first full-state review’s findings are accounted for as follows:

| Earlier finding | Resolution in the current state |
|---|---|
| Coordinator reporting and board-write conflicts | **Resolved.** `dispatch/SKILL.md:58` and `:68` distinguish coordinator reporting; `dispatch/templates/brief.md:4` names the actual dispatcher. |
| Cold start assumes previous agents stopped | **Resolved.** `session-handoff/SKILL.md:44` distinguishes stopped, live and unknown states; unreachable lines stay parked. The introductory wording remains non-blocking above. |
| Apps has competing release-overlay sources | **Resolved as a routing issue.** `apps:AGENTS.md:46` selects the local overlay. Its obsolete contents are the separate blocker above. |
| Apps lacks local contract surfaces | **Resolved.** `apps:.agent-protocols/merge-queue.md:14` includes application and accounts routes, schemas, contracts, migrations, imported DDL and models. |
| Isolated L14 lookup returns superseded scope | **Resolved.** `intern:.agent-protocols/authority-ledger.md:39` contains the effective baseline and measurement method; amendment provenance is retained. |
| Permission copies and preference routing | **Partly resolved.** The cited permission conditions became pointers, and the model/language sources were corrected. Brief-review preference references remain above. |
| Obsolete worktree and merge commands | **Resolved.** `intern:docs/collaboration/worktree_feature_protocol.md:80` uses Worktrunk with `origin/main`; `:256` requires rebase merge; `:258` uses Worktrunk cleanup. |
| Active ledger grants described as pending | **Resolved.** `intern:.agent-protocols/authority-ledger.md:45` records the completed activation and its provenance. |
| Incomplete source map and misleading core pointer | **Resolved.** `README.md`, “Where A Rule Lives,” supplies the ownership route; `decision-boundary/CORE.md:4` qualifies the protocol-checkout path. |

The requested role scenarios now read as follows:

| Scenario | Answer from the files |
|---|---|
| Master taking over | Verify live state; redispatch only confirmed stopped lines. Park live or unknown lines until reachable and acknowledged; recheck the ledger before renewing delegation (`session-handoff/SKILL.md:44`; `decision-boundary/SKILL.md:217`). |
| Coordinator at a point of no return | Message the master, wait for its answer, and resend an unacknowledged request. It cannot grant or pass on permission (`agents/README.md:36`). |
| Direct session told to merge while a master runs | It does not execute the merge; execution belongs to the master or its designated merger (`decision-boundary/SKILL.md:194`). |
| Researcher told to read production | Its brief must allow the read, subject to project restrictions. Intern requires master assignment, bounded read-only queries and release-window restrictions (`agents/researcher.md:5`; `intern:.agent-protocols/line-worker.md:72`). |
| Worker implementing an approved contract change | It may implement the exact change named with recorded permission. Other gates and the merge-surface check remain (`agents/line-worker.md:6`; `line-worker/SKILL.md:88`). |
| Agent typing a ledger entry | It types a `proposed` entry; only the session that heard the grant verifies and activates it (`decision-boundary/SKILL.md:123`). |
| Production operator changing configuration | The brief names the command, target, receipt and permission; record the previous value, check preconditions, perform read-back and health checks, and report to the master. **Apps’ project instructions still need the correction above** (`release/SKILL.md:22`, `:31`, `:47`, `:73`). |
| Author wants to fix a typo after queue handoff | Send the correction to the merger; do not push to the queued branch. A returned PR follows the explicit return-to-author path (`line-worker/SKILL.md:82`; `merge-queue/SKILL.md:57`). |

#### Residual risks and validation gaps

- Evidence is reviewer-performed file inspection, Git inspection and read-only comparisons. All three repositories have correctly resolving mounts for all 17 protocols; both consumer resident-core copies match.
- Guard scripts were inspected, not executed. No tests, production commands or network freshness checks were run.
- The approved fresh-master cold-start exercise remains a subsequent step. Personal-file and memory migration is outside this review.
- All three worktrees remained clean. The review branch has no upstream; publication was not verified. No files were written, staged or committed.

### Driver response to reviewer pass 1

- Apps release overlay (blocking): accepted; fixed in skynet-apps
  (branch `release-overlay-current-2026-10`): the P18 procedure is deleted;
  the overlay points to `docs/runbooks/applications.md` (release, rollback,
  `apps-migrate.sh`) and `docs/runbooks/host_split_operations.md` (`--host`
  and its data-only exceptions, first switch creates `current`, monitoring);
  `switch.sh --migrate-to` is stated as accounts-only; runbook-written manual
  steps are admitted and recorded; the sign-in outage covers every switch.
  Reviewed in 3 passes, no blocking issues; both scenarios walked.
- Brief-review preference source: accepted; `readable-brief` self-review and
  the review lens read the reader's user-level preferences.
- Handoff introduction: accepted; the blanket "subagents die" claim is gone.

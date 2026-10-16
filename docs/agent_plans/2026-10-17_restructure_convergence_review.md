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

### Driver note before pass 2

Merged since pass 1: skynet-apps #48 (release overlay points to the current
runbooks), agent-protocols #50 (brief-review preference source, handoff
intro), #49 (STATUS records agent, tier, dispatcher), skynet-intern #1717
(`docs/CURRENT.md` is a short map). Both consumers still pin `194d1fd`; the
bump to the current `main` is queued. The differences between `194d1fd` and
this checkout are #49 and #50 only (no resident-core change). Pass 2 reviews
the full state again and says whether it has converged.

### Reviewer pass 2 (other-plan, codex reviewer)

人类的要求是明确角色边界、统一 master 定义，并让共享协议与两个消费者中的每条规则都有明确的权威来源。

本轮检查完整当前状态：共享仓库 `355e926`，intern 本地 `main` 的 `db212ab52`，apps 本地 `main` 的 `1d4bef31`。共享协议内容与本地 `main` 的 `50f70f7` 一致；两个消费者仍固定在 `194d1fd`。

#### Blocking issues

**无阻塞问题。**

#### Non-blocking issues

##### Thread: 两个消费者仍重复定义推送租约规则

**问题 1、3 — should fix，非阻塞。**

`merge-queue/SKILL.md:44` 已定义记录准备时的远端提交、使用显式 `--force-with-lease`、远端变化时停止的规则。`intern:.agent-protocols/merge-queue.md:27` 和 `apps:.agent-protocols/merge-queue.md:39` 又分别复述了一遍。

三处目前要求一致，因此不阻塞收敛，但仍留下三个维护位置。

**最小修复：**将两个覆盖文件中的规则正文换成共享协议的指针。intern 的事故记录可以保留为来源说明。无需新增脚本或检查机制。

#### Pass 1 thread resolutions

| 原线程 | 本轮裁定与证据 |
|---|---|
| Apps 发布覆盖文件仍描述旧流程 | **Resolved.** `apps:.agent-protocols/release.md:11` 指向当前发布与迁移流程；`:18` 包含主机选择、三个固定操作 data 主机的例外、首次切换与监控发布；`:33` 要求操作命令或 runbook 明确写出的步骤及其记录。 |
| 简报审查仍从覆盖文件读取个人偏好 | **Resolved in shared source.** `readable-brief/SKILL.md:114` 与 `structured-review/references/review-lenses.md:317` 均改为读取用户级偏好。消费者采用情况见下方限制。 |
| 交接介绍仍断言所有子代理随会话结束 | **Resolved in shared source.** `session-handoff/SKILL.md:8` 已承认子代理可能存活，与 `:44` 的实际状态检查一致。消费者采用情况见下方限制。 |

对 apps 的两条阅读场景进行了重新核对：

- **包含 applications 迁移的发布：**安装版本，使用 `apps-migrate.sh` 在 data 主机迁移，再按常规流程切换；accounts 的 `--migrate-to` 保持独立。覆盖文件、`apps:docs/runbooks/applications.md` 第 2.1 节和相关脚本一致。
- **配置了主机文件、尚无 `current` 的首次切换：**安装目标版本，指定 `--host` 执行切换，由切换命令创建 `current`；监控另经 `publish-monitoring.sh` 发布。覆盖文件与 `apps:docs/runbooks/host_split_operations.md` 第 2–4 节一致。

#### Overall judgment

**按本文件“无阻塞问题”的标准，当前状态已收敛。** 消费者版本更新和新 master 接管演练仍须完成，不能据此宣布整个重构已经交付结束。

对四个问题的结论：

1. **结构目标已实现。** 六个角色文件具备共同字段，协调者在 `agents/README.md` 中定义，master 的权威定义位于 `agents/master.md`；17 个协议均标明读者。`README.md` 的 “Where A Rule Lives” 给出四层归属。
2. **未发现新的阻塞性矛盾、遗漏或被削弱的 SAFETY 要求。** 之前涉及协调者报告、接管存活代理、apps 发布来源、合同检查范围和 L14 有效范围的问题仍保持修复。
3. **仍有非阻塞重复和已记录的版本滞后。** 具体重复见上方线程；消费者更新见下方限制。
4. **八个角色场景均有一致答案：**

| 场景 | 文件给出的行为 |
|---|---|
| Master 接管 | 核实代理实际状态；已停止的重新派发，存活或状态未知的先暂停接管；确认联系及交接后才恢复委托。`session-handoff/SKILL.md:44`；`decision-boundary/SKILL.md:217`。 |
| 协调者遇到不可逆节点 | 向 master 发消息并等待答复；未确认时重发，不能自行授权或转授。`agents/README.md:36`。 |
| Master 运行期间，直接会话收到合并要求 | 由 master 或其指定的唯一合并代理执行。`decision-boundary/SKILL.md:194`。 |
| 研究代理读取生产 | 简报必须允许，并遵守项目限制；intern 要求 master 分派、有界只读查询及发布窗口限制。`agents/researcher.md:5`；`intern:.agent-protocols/line-worker.md:72`。 |
| 工作者实现已批准的合同变更 | 仅实现简报明确列出的已授权变更；合并仍经过合同范围检查。`agents/line-worker.md:6`；`line-worker/SKILL.md:89`。 |
| 代理代录授权条目 | 只能录为 `proposed`；由直接收到授权的会话核对并激活。`decision-boundary/SKILL.md:123`。 |
| 生产操作员修改配置 | 简报指定变更、命令、凭据记录及权限；保存旧值、检查前提，执行后读回并检查健康状态。`release/SKILL.md:22`、`:47`。 |
| 作者交队列后想修错字 | 将修改请求交给合并代理，不再自行推送；被退回后按返回作者流程处理。`line-worker/SKILL.md:83`；`merge-queue/SKILL.md:57`。 |

#### Residual risks and validation gaps

- **消费者更新尚未完成。** 两个消费者的 gitlink 和实际子模块均为 `194d1fd`，尚未采用简报偏好、交接介绍及 STATUS 身份字段的更新。驱动者已在本文件 “Driver note before pass 2” 中记录待更新事项；交付要求见 `AGENTS.md:58`。
- 证据来自 reviewer 的文件、Git 和只读比较。三个仓库的两套技能挂载均为 **17/17** 正确目标；两个消费者的常驻规则副本均与本次共享源码一致。
- 未运行 bootstrap、guard、测试、生产命令或网络新鲜度检查；不将静态检查视为这些机制的运行证明。远端 PR、CI 和合并元数据未独立核验。
- 新 master 接管演练仍是后续步骤；个人文件和记忆迁移不在本轮审查范围。
- 三个工作区检查结束时均干净。审查分支没有 upstream；本轮未写入、暂存或提交文件。

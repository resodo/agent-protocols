# Review profiles, cancellation, and session recovery

Status: historical implementation and review record

## Decisions and scope

The human requested one PR covering upgraded hard reviewers, more usable time
limits, driver-controlled stopping, session recovery, and real dogfooding.
Normal remains Opus 5 / GPT-5.6 Terra; hard becomes Fable 5.1
(`claude-fable-5-1`) / GPT-6 Astra (`gpt-6-astra`); all retain xhigh.
The latest human decision sets normal to 1800 seconds and hard to 3600 seconds.
Explicit positive timeout overrides remain supported; legacy auto uses normal.
Both tiers retain the same readiness gate and cross-vendor routing.

Driver: Codex. Reviewer: Claude through this checkout's bundled runner.
Plan and implementation reviews use hard because this is shared protocol
self-modification involving cancellation, persistent state, and recovery.

## Implementation contract

1. Update profiles and tier-dependent timeout resolution. Remove the obsolete
   900/1800 guidance. Record whether timeout came from profile or explicit flag.
2. Add a cooperative stop command (`--stop-run RUN --stop-reason REASON`) that
   writes a request to the private run directory. Running reviewer observes it,
   records the reason, terminates its process group gracefully with a bounded
   grace period, then kills remaining group members if necessary. SIGINT and
   SIGTERM use the same cleanup path. User/driver stop and timeout remain
   incomplete outcomes, never successful reviews. Waiting/polling tool returns
   do not stop a reviewer. Silence alone is not evidence of lack of progress.
3. Persist private metadata atomically before launching and as session ID becomes
   available. Capture Claude session_id and Codex thread.started/thread_id.
   Preserve original launch constraints and review target fingerprint. Raw logs
   and provider transcripts remain private, outside tracked content. Existing
   JSON consumers retain existing fields; new lifecycle fields are additive.
4. Add `--resume-run RUN` to a regular invocation with the same scope/profile
   arguments. Restore only a recorded session ID from an eligible stopped,
   interrupted, or timed-out attempt. Never select --last. Use Claude -p
   --resume ID or codex exec resume ID with explicit model/effort and equivalent
   permissions. Append a continuation instruction requesting one complete final
   review, treating interrupted tools as uncertain. Preserve original prompt
   constraints. Resume is conversation recovery, not a suspended computation.
5. Each attempt gets separate logs; a run chain has a private advisory lock and
   authoritative latest-attempt pointer. Hold the lock through verification and
   write-back. Reject concurrent resume, stale attempts, completed/failed
   write-back attempts, missing session state, changed worktree/HEAD/artifacts/
   focus/profile/protocol, and unsupported persistence. No automatic retries or
   silent fresh-session fallback. Each attempt receives its configured timeout;
   report cumulative attempt time separately. Session/transcript retention is
   owned by the caller and installed CLI, not a new global cleanup daemon.
6. On complete output, use the existing untouched-worktree and output validation
   before appending/committing exactly once. A crash during finalization must not
   become a resumable attempt. Stop requests after reviewer completion do not
   retroactively cancel successful write-back. Ensure descendant processes have
   exited before checking repository state or allowing recovery.
7. Update SKILL, README, current map, plan index, and reusable recovery guidance.
   The driver may stop with a concrete recorded reason; remove the old blanket
   ban on driver cancellation. Outer process lifetime must cover reviewer time
   plus teardown, while individual polling waits may be short.

## Concrete lifecycle and recovery rules

- `RUN` is the absolute attempt log directory, printed at launch. Each attempt
  persists `outcome=running`, `phase=created/launched/session_captured`, runner
  PID, reviewer PID/PGID once launched, and timestamps. Capture the first valid
  session_id on any Claude event, and Codex thread.started/thread_id.
- Start reviewers in their own POSIX process group. Atomically persist each
  phase change. Only terminal timeout/stopped/interrupted with
  cleanup_complete=true and a captured session ID may resume. Running, created,
  launched, session_captured, error, failed, finalizing, and success are NOT
  resumable, even if their lock was released. Abrupt runner death therefore
  fails closed; it cannot start another writer. Record PID/PGID for diagnosis,
  but never automatically kill a recorded PID after a crash (PID reuse).
- A live runner holds the chain flock through finalization. Stop uses a file
  request in the exact latest attempt directory; stale handles are rejected
  with the latest attempt path; if the chain lock is free,
  report no live runner and do not signal the recorded PID. The command returns
  after queuing, explicitly says it is not an acknowledgement, and directs the
  caller to poll metadata for the terminal outcome. A crashed running attempt
  requires operator diagnosis and a fresh review, not automatic orphan repair.
- Terminate the owned process group with SIGTERM, wait a bounded grace period,
  then SIGKILL remaining members and reap the leader. Confirm no executing
  members remain (zombies are not executing); failure makes the attempt an
  error, ineligible for resume. Detached descendants outside the process group
  are not managed; document this limitation rather than claiming universal
  descendant cleanup.
- Exact Claude resume shape: `claude -p --resume ID --permission-mode auto
  --model MODEL --effort EFFORT --output-format stream-json
  --include-partial-messages --include-hook-events --verbose`, prompt on stdin.
  Exact Codex shape: `codex exec resume ID - --json -m MODEL
  -c model_reasoning_effort=EFFORT -c sandbox_mode="workspace-write"
  --output-last-message FILE`, cwd explicitly set by Popen. Neither initial nor
  resumed calls pass --ephemeral or --no-session-persistence. Live Codex dogfood
  inspects recorded rollout context for the effective workspace-write policy.
- Fingerprint inputs: canonical worktree, pre-launch HEAD, artifact/thread-file
  sha256 hashes, complete built prompt hash (including protocol and overlays),
  runner source hash, mode, type, topic, focus, backend, model, effort, tier,
  reason, binary path, and binary version. Timeout may change on resume; target
  and reviewer constraints may not. Private metadata is trusted local state,
  not a portable or untrusted import format. Resume validates UUID session IDs
  and rejects a backend that emits a different session ID or cannot load it.
- Persist phase=finalizing and outcome=finalizing BEFORE any append. Defer
  the runner's own SIGINT/SIGTERM through this section; a terminal interrupt can
  still stop a git child and leave a non-resumable dirty append; late requests never undo completed
  output. Failed finalization is terminal and cannot resume. Before-resume HEAD
  and clean-status checks provide a second backstop. No automatic replay of
  write-back, even after a crash between file write and commit.
- Preserve outcomes success/failed/error/timeout; add running/finalizing/stopped/
  interrupted. Timeout remains exit 2; driver stop uses 3; SIGINT/SIGTERM use
  130/143. Late signals in finalization are recorded without converting success
  to interruption. Every resumed attempt receives a fresh time limit, records
  attempt elapsed time and cumulative elapsed time, and uses distinct logs.
- Use nonblocking pipe reads/writes so partial log lines or a reviewer that does
  not consume stdin cannot suspend timeout/cancellation checks. Drivers whose
  tools impose shorter execution lifetimes launch in supported background mode
  and poll; a per-poll wait budget is not a process lifetime budget.

## Validation and acceptance

- Unit/integration tests with fake CLIs for both backend argument shapes, early
  session capture, real signal/stop/timeout cleanup including child processes,
  recovery to completion, separate logs and metadata, missing/mismatched session,
  changed target, exclusive resume, repeated completion, and interrupted write-back.
- Exercise every new fail-closed guard negatively and verify the intended error
  rather than an unrelated setup failure; evidence belongs in tests or execution
  notes (per current protocol evidence-discipline rules).
- Run repository CI commands: backlog schema check, root tests, structured-review
  tests, scout tests, and compile. Inspect CLI help and visible status/recovery errors.
- Live dogfood on a clean disposable fixture repository with a synthetic review
  artifact: each new hard backend starts, captures its session ID, is stopped or
  timed out after persisted progress, and resumes to a complete validated review.
  At least one live write-back run verifies exactly one review commit. Confirm
  retained context with a harmless session-only marker if practical. Do not use
  a fabricated CLI smoke as evidence of provider recovery.
- Run implementation review with the updated runner on the committed feature
  worktree. Resolve blockers; retain sanitized evidence in this plan. Keep private
  raw outputs outside git. Push one PR, check CI, finish closeout without merging.

## Limits and fallback

Recovery depends on the same machine's CLI persistence; it cannot reconstruct
unsaved generation or guarantee restoration of an in-flight external command.
If a live model or recovery path is unavailable, report the actual evidence and
leave that acceptance item incomplete rather than claiming success. A runner
crash may require a new review; broad arbitrary-crash repair is outside scope.

## Implementation and execution evidence

Driver-reported validation, 2026-09-06:

| Acceptance | Evidence | Status |
| --- | --- | --- |
| Models and 1800/3600 profiles | Matrix and timeout tests cover both backends, normal/hard/legacy auto and explicit overrides | Done |
| Cooperative stop and signals | Real fake-provider subprocess tests observe stop exit 3, SIGINT 130, SIGTERM 143, cleanup and successful recovery | Done |
| Timeout without blocking I/O | Tests exercise partial lines, closed output pipes, unread large stdin, and ignored SIGTERM requiring SIGKILL | Done |
| Recovery guards | Tests execute concurrent/stale/completed/running/finalizing/failed/error attempts, missing/wrong IDs, missing provider history, changed HEAD/prompt/protocol/model/effort/version and unverified cleanup | Done |
| Write-back ordering | Tests inject failure between append and commit, restore clean target to reach the eligibility guard, and observe rejection; late signal/stop tests finish once | Done |
| Claude Fable 5.1 live recovery | Claude Code 2.1.261, hard/xhigh: stopped with exit 3, cleanup verified, same session resumed successfully, random session-only marker retained, seeded empty-input defect found, exactly one review commit, clean fixture | Done |
| GPT-6 Astra live recovery | Codex CLI 0.153.4, hard/xhigh: explicit 150-second test limit produced timeout exit 2, same thread resumed successfully, marker retained, seeded defect found, exactly one review commit, clean fixture | Done |
| Codex permissions on resume | Original and resumed native rollout turn_context both record model gpt-6-astra, effort xhigh, workspace-write and network_access=false | Done |
| Repository validation | CI-backed on implementation commit 5925cb8: 107 review tests, 18 root tests, 31 Scout tests, backlog check and compile; driver diff check passed | Done |
| Independent review and remote CI | Claude passes 3 and 4 found no blockers; Threads 11–14 resolved in f5176b0. CI python passed on 5925cb8 (run 34013734391). Final PR-head checks are reported in the handoff | Done |

Both live smokes used isolated synthetic repositories, not this implementation
as the defect fixture. Success means the recovery workflow completed; the seeded
artifact was correctly judged NOT ready because average([]) divides by zero.
Claude cumulative attempt time was about 100 seconds; Codex about 208 seconds.
Raw logs, exact session IDs, and provider transcripts remain private temporary
execution output. They are not committed. Tests additionally cover the final
best-effort kill fallback when process-table verification itself fails; that
failure path is simulated, not claimed as a live-provider observation.

The retained limits are intentional: POSIX process groups only, no detached
process ownership, no arbitrary runner-crash recovery, and same-machine CLI
transcript retention owned by the caller. No planned feature has been deferred.

Closeout: the implementation, independent review, and live recovery acceptance
items are complete. PR #30 contains the single delivery branch. The feature
worktree and main checkout were checked for unrelated edits; no merge action is
authorized or performed by this record. Main has no branch protection or active
rulesets; the repository CI workflow nevertheless runs all listed suites, with
no test suite excluded or configured as non-blocking. Final remote head and CI
status are reported in the PR handoff rather than stored as a self-referential
commit assertion in this document.

## Review Threads

### Reviewer pass 1 (impl-plan, claude reviewer)

Human concern, restated: long hard reviews were being killed by outer tool limits and their work lost, so the driver wants a deliberate stop, recovery of the same reviewer session, and no chance of the review being written back twice.

Verified before judging: branch `feat/review-resume` at `ac881d1`, worktree clean, plan committed. I read the plan, the full runner `structured-review/scripts/claude_structured_review.py`, its tests, `structured-review/SKILL.md`, `closeout/SKILL.md`, `README.md`, `docs/CURRENT.md`, `docs/agent_plans/README.md`, `docs/backlog.yml`, and `.github/workflows/ci.yml`. I checked the installed CLIs directly: `claude --help` (Claude Code 2.1.261), `codex exec --help` and `codex exec resume --help` (codex-cli 0.153.4). I ran one throwaway `claude -p --output-format stream-json` call to confirm the session-id field shape. No structured-review run logs exist in this worktree's private run directory, so the Codex `thread.started` shape is not verified locally.

Runner facts the plan depends on, as they stand today:
- `run_claude` launches the reviewer with `subprocess.Popen` in the runner's own process group and, on timeout, calls `proc.kill()` on the direct child only; nothing records the child's PID or tracks descendants.
- `write_metadata` runs once, after the reviewer exits; nothing is persisted before or during the run except logs.
- `append_and_commit_review` creates the commit, then `verify_write_mode` checks it. A verification failure therefore reports `failed` with a review commit already on HEAD.
- `main` catches `KeyboardInterrupt` at top level and returns 130 without cleanup or metadata.

#### Blocking issues

##### Thread 1: The attempt state model and resume-eligibility inputs are not defined, and the orphaned-reviewer case is unhandled

Plan items 2, 5, and 6 list what must be rejected and say descendants must have exited "before ... allowing recovery", but nothing says what the eligibility check reads or how liveness is decided. Implementing item 2's process-group termination requires launching the reviewer in its own session or group. That has a consequence the plan does not name: when the runner itself dies abruptly (SIGKILL from an outer tool, which is the very scenario motivating this plan), the reviewer survives as an orphan in its own group, still running and still writing the Claude or Codex session on disk. A later `--resume-run` would find the advisory lock released, see no terminal outcome, and start a second `claude -p --resume ID` against a session another live process is writing. Today's runner cannot detect this because it records no PID.

Please add to the plan body:
1. The persisted attempt phases and their transitions, for example `created`, `launched` (runner pid, child pid, child pgid, launch time), `session_captured`, `reviewer_exited`, `finalizing`, and terminal `committed`/`printed`/`failed`/`stopped`/`timeout`/`interrupted`. Item 3's "before launching and as session ID becomes available" should become "at each phase change", written atomically.
2. The eligibility rule in terms of those fields: resume only from `launched` or `session_captured` with a recorded session id, and only when the recorded child pgid is verified dead (with launch time or command check to guard against pid reuse).
3. The decision for a live orphan: reject with an error that names the pgid and never kill it automatically, or decide otherwise, but decide in the plan.
4. What `--stop-run` reports when no runner is alive to observe the request, since the request is observed by the runner, not by the reviewer process.

Without this the acceptance rows "missing/mismatched session", "exclusive resume", and "interrupted write-back" have no named state or intended error to assert, which is exactly the "unrelated setup failure" the plan's own evidence rule forbids.

##### Thread 2: The Codex resume argument shape cannot be derived from the plan, and `codex exec resume` lacks `--sandbox`

Item 4 says `codex exec resume ID` "with explicit model/effort and equivalent permissions". On the installed codex-cli 0.153.4, `codex exec resume` accepts `-c`, `-m`, `--json`, `-o/--output-last-message`, and `-` for stdin, but does not accept `-s/--sandbox`, `-C/--cd`, `--add-dir`, `--approve-for-me`, or `-p/--profile`, all of which `codex exec` accepts and one of which (`--sandbox workspace-write`) `codex_argv` relies on today. "Equivalent permissions" therefore cannot be expressed with the current flag. The implementer would have to choose between relying on the thread's inherited sandbox policy (not documented in the help) and `-c sandbox_mode="workspace-write"`.

Please pin in the plan the exact resume argv for both backends, the Codex sandbox mechanism on resume, and a dogfood observation that the resumed Codex reviewer actually ran under workspace-write. If that observation is not available, record it as a residual risk and note that the runner's untouched-worktree and HEAD checks catch a stray write after the fact but do not prevent it. Also state that `--ephemeral` (Codex) and `--no-session-persistence` (Claude) are never passed on either the initial or resumed run, since item 5's "unsupported persistence" rejection presumes persistence was requested.

##### Thread 3: Exactly-once write-back is asserted but the ordering that makes it hold is unstated

Item 6 says a crash during finalization must not become resumable and that late stop requests do not cancel a successful write-back. These are enforcing claims; the plan should state the mechanism, not only the property:
1. Marker before mutation: persist the non-resumable `reviewer_exited`/`finalizing` phase before `append_and_commit_review` touches the thread file.
2. Signals deferred during finalization: SIGINT, SIGTERM, and stop requests set a flag rather than raising, so nothing can interrupt between the thread-file write and `git commit`. Today a Ctrl-C there would leave a dirty thread file and metadata that still says running.
3. The backstop: resume compares HEAD and clean status against the launch snapshot, so a commit that landed without a recorded terminal phase is still rejected.
4. `failed` after `finalizing` is terminal and non-resumable. This matters today because the runner commits first and verifies second, so a verification failure can report `failed` with a valid review commit already on HEAD; the prior plan's Thread 3 on `AP-BL-0006` in `docs/agent_plans/2026-08-07_evidence_discipline_rules_plan.md` describes that false-failure shape.

The "interrupted write-back" test should inject the failure between the append and the commit and assert both the intended non-resumable error and that a subsequent resume cannot produce a second commit.

#### Non-blocking issues

##### Thread 4: Capture the first event carrying a session id, not the `init` event

Verified live with `--output-format stream-json --verbose`: in this environment the first stream line is a `system`/`hook_started` event that already carries `session_id`; the `system`/`init` event came third and also carries `cwd`, which is useful for the fingerprint. Whether hooks fire depends on user configuration, so capture on the first event with a string `session_id` rather than waiting for `init`. The Codex `thread.started`/`thread_id` shape is not verified locally; verify during implementation and mirror the observed event in the tests' fake CLI.

##### Thread 5: Fingerprint composition is unspecified

Item 3's "review target fingerprint" and item 5's rejection list name worktree, HEAD, artifacts, focus, profile, and protocol, but not the concrete inputs. Name them so the implementer does not guess. A workable set: recorded worktree root, pre-launch HEAD, sha256 of each artifact and of the thread file, sha256 of the full built prompt (which already covers focus, protocol sections, and overlays), mode, type, backend, model, effort, tier, and reviewer binary version.

##### Thread 6: Define the `RUN` identifier and print it at launch

`--stop-run RUN` and `--resume-run RUN` need a documented identifier: the chain directory name under the private runs directory, a full path, or an id file. Today the run directory is printed only on completion; the driver needs it at launch to be able to stop.

##### Thread 7: The new timeout profile forces background launch for Claude Code drivers; say so and list the tests that change

With normal 1800 s and hard 3600 s, a Claude Code driver's single tool call has a ceiling well below the runner timeout, so item 7's "individual polling waits may be short" implies detached launch plus polling on metadata or exit code. Say that in the SKILL text that replaces the current "outer wait budget" paragraph. Recording timeout source needs the argparse default to become `None`. Tests that pin the old values and will need deliberate updates: `test_default_timeout_is_fifteen_minutes`, `test_hard_review_with_default_timeout_emits_guidance`, `test_skill_requires_outer_wait_budget_to_cover_runner_timeout`, and `test_skill_and_closeout_pin_central_reviewer_selection_policy` (pins `claude-fable-5` and `gpt-5.6-sol`).

##### Thread 8: Late stop requests and new outcome values

State that a stop request or signal arriving after `reviewer_exited` is recorded as late and ignored, and that `--stop-run` returns after the runner acknowledges or after a bounded wait, reporting which. Name the new `outcome` values (for example `stopped`, `interrupted`) and the exit code for a stopped run, since `outcome` is an existing field consumers may match on and timeout already uses exit code 2.

##### Thread 9: Deferred pieces need a backlog home, and the indexes need this plan

"Broad arbitrary-crash repair" and any retention or orphan-cleanup work left out at closeout should be registered in `docs/backlog.yml` per the backlog protocol rather than living only in this plan's Limits section. `docs/agent_plans/README.md` does not yet list this plan; item 7 covers it, but note that `docs/CURRENT.md` also needs its structured-review description and "Last updated" line changed.

#### Overall judgment

Not yet ready for implementation. The scope is bounded and feasible against the current runner, the model and timeout changes are mechanical, and the validation section is unusually strong on negative evidence. The three blocking threads are plan-text gaps rather than design flaws: name the attempt states and the orphan policy, pin both resume argument shapes with the Codex sandbox mechanism, and state the finalization ordering. Once those are in the body this should be ready without a change in scope.

#### Residual risks and validation gaps

- macOS has no parent-death signal, so an orphaned reviewer after a runner SIGKILL can only be detected, not prevented. The plan should treat that as inherent and rely on Thread 1's liveness check.
- Claude resume requires the same project directory as the original run; a moved worktree yields "session not found". That error path should be distinguishable from "session id never captured".
- Codex `thread.started` shape and inherited sandbox on resume are unverified locally.
- Fable 5.1 and GPT-6 Astra availability for dogfood is not checked here; the plan's fallback wording already covers the honest-incomplete case.
- Session and transcript retention is left to the CLIs; a resume long after the fact may find the session gone, which is the "missing session state" path and should be tested as such.

### Driver response to reviewer pass 1

- Accepted Threads 1, 2, 3, 4, 5, 6, 7, 8: concrete lifecycle section now pins
  phases, argv, sandbox, fingerprint, handle, signal behavior, and exit codes.
- Thread 1 eligibility suggestion partially rejected: launched/session_captured
  are never resumable after abrupt runner death. Only terminal attempts with
  verified cleanup may resume. This deliberately avoids orphan/PID-reuse repair.
- Thread 9 accepted for index updates. A new orphan-repair/retention subsystem is
  outside the accepted task; existing CLI retention ownership is intentional,
  not incomplete implementation. No speculative follow-up mechanism is added.
- Ready for reviewer recheck of these plan clarifications. No code edited yet.

The prompt builder contains no timeout, run directory, or timestamp, so hashing the complete built prompt while letting the timeout change on resume is consistent. I have everything needed. Writing the review now.

### Reviewer pass 2 (impl-plan, claude reviewer)

Human concern, restated: long hard reviews were being killed by outer tool limits and their work lost, so the driver wants a deliberate stop, recovery of the same reviewer session, and no chance of the review being written back twice.

Scope of this pass: recheck of the new `Concrete lifecycle and recovery rules` section and the driver response, per the focus. No live CLI calls were made; CLI flag support was verified in pass 1.

Verified before judging: branch `feat/review-resume` at `039370c`, worktree clean. Read `git show 039370c` (67 added lines, plan only), then the full plan. Cross-checked the new section against `structured-review/scripts/claude_structured_review.py` as it stands today:
- `claude_argv` is `-p --permission-mode auto --model M --effort E --output-format stream-json --include-partial-messages --include-hook-events --verbose`, prompt on stdin. The pinned resume shape is this list plus `--resume ID`, so "equivalent permissions" holds by construction for Claude.
- `codex_argv` relies on `--sandbox workspace-write` and sets no `-C`; `Popen` already passes `cwd=config.worktree`. The `-c sandbox_mode="workspace-write"` substitution is the only expressible mechanism on `codex exec resume`, as pass 1 found.
- Exit codes in use today are 0, 1, 2 (timeout, via `RunnerError(exit_code=2)`), and 130 (`KeyboardInterrupt`). Code 3 is free, so the new stop code does not collide.
- `build_prompt` contains no timeout, run directory, timestamp, or attempt-specific value. Hashing the complete built prompt while allowing the timeout to change on resume is therefore consistent. Codex's per-attempt `--output-last-message` path is in argv, not the prompt, so it does not disturb the fingerprint.
- Today's `proc.stdin.write(prompt)` is a blocking write on a pipe, which is exactly the hang the new nonblocking-pipe rule targets.

#### Thread resolutions for pass 1

##### Thread 1: attempt state model, eligibility, orphan policy, stop with no live runner

Resolved. The new section names the phases (`created`, `launched`, `session_captured`, `finalizing`), the outcomes, and an eligibility rule stated purely in persisted fields: only terminal `timeout`/`stopped`/`interrupted` with `cleanup_complete=true` and a captured session ID may resume. The driver's partial rejection of my suggestion (resuming from `launched`/`session_captured` after verified child death) is accepted as the better design. Because `cleanup_complete` is written only by the runner's own termination path, an orphaned reviewer after an abrupt runner death leaves the attempt at `running`, which is never resumable, so the second-writer hazard I raised cannot arise without any PID liveness or PID-reuse logic. The stop-with-no-live-runner behaviour (lock free, report no live runner, do not signal the recorded PID) answers item 4. One implementation note, not a reopen: the rejection error for a `running`/crashed attempt should print the recorded runner PID, reviewer PGID, and launch time, since the plan records them "for diagnosis" and the error is where the operator will look.

##### Thread 2: Codex resume argv and sandbox

Resolved. Both argv shapes are pinned, the Codex sandbox mechanism on resume is `-c sandbox_mode="workspace-write"` with cwd set by `Popen`, `--ephemeral` and `--no-session-persistence` are excluded from both initial and resumed calls, and the plan commits live dogfood to inspecting the recorded rollout context for the effective policy. The fallback if that observation is unavailable is carried in `Limits and fallback` and in the residual risks below.

##### Thread 3: exactly-once write-back ordering

Resolved. The section states the mechanism in the order I asked for: `finalizing` persisted before any append, SIGINT/SIGTERM and stop requests deferred through finalization, failed finalization terminal and non-resumable, before-resume HEAD and clean-status checks as the backstop, and no automatic replay even after a crash between file write and commit. In `print-review` mode the same marker should precede the stdout print. Either way an attempt whose reviewer exited normally can never become resumable under the Thread 1 rule, so the property holds in both modes. The injected-failure test I described remains the acceptance evidence and is covered by the "interrupted write-back" row.

##### Thread 4: capture the first event carrying a session id

Resolved. "Capture the first valid session_id on any Claude event" is now in the body.

##### Thread 5: fingerprint composition

Resolved. Inputs are enumerated, including runner source hash and binary path/version, with timeout explicitly excluded. Verified above that the built prompt is deterministic across attempts.

##### Thread 6: RUN identifier printed at launch

Resolved. `RUN` is the absolute attempt log directory, printed at launch. See Thread 10 for one clarity point on multi-attempt chains.

##### Thread 7: background launch and changed tests

Resolved. The body now states that drivers with shorter tool lifetimes launch in supported background mode and poll, and that a per-poll wait budget is not a process lifetime budget. The list of tests that pin old values stays in pass 1 as implementer guidance; it does not need to be in the plan body.

##### Thread 8: late requests, new outcomes, exit codes

Resolved. New outcomes are named additively, timeout keeps 2, stop uses 3, SIGINT/SIGTERM use 130/143, and late signals in finalization are recorded without converting success to interruption. The driver chose "returns after queuing, explicitly not an acknowledgement, poll metadata" over a bounded ack wait. That is a valid and simpler decision.

##### Thread 9: backlog home and index updates

Resolved by driver decision. Index updates are accepted under item 7. Orphan repair and retention are treated as non-goals rather than deferred work, so no backlog item is required now. If closeout leaves a real acceptance item incomplete (for example the Codex sandbox observation), the closeout protocol registers that at closeout time. Human may overrule.

#### Blocking issues

None. All three pass 1 blocking threads are closed by the new section.

#### Non-blocking issues

##### Thread 10: State how `--stop-run` and `--resume-run` treat a non-latest attempt directory

`RUN` is an attempt directory, a chain can hold several attempts after resumes, and stop writes to "the exact latest attempt directory". The body does not say what happens when the caller passes an earlier attempt's `RUN`: reject with an error naming the latest attempt directory, or follow the latest-attempt pointer transparently. Item 5's "reject stale attempts" implies rejection, and both readings are safe, so this is a one-sentence clarification that can be settled during implementation and covered by the "exclusive resume" test. It does not gate implementation.

#### Overall judgment

Ready for implementation. The new section turns every enforcing claim from pass 1 into a stated mechanism, and the eligibility rule is stricter and simpler than what I proposed. The accepted trade-off should be visible to the human in one sentence: only a runner that gets to run its own cleanup path (timeout, stop request, SIGINT, SIGTERM) produces a resumable attempt. An outer SIGKILL of the runner, or a runner crash, loses the review by design and requires a fresh run, with background launch and polling as the mitigation. That is consistent with the human's original concern as long as drivers follow the new launch guidance. Further plan-text rounds would add low value; the remaining items belong to implementation review.

#### Residual risks and validation gaps

- Guard reach at implementation review: eligibility, exclusive resume, and exactly-once write-back are state-machine claims. Tests must execute the transitions and observe the result: resume attempted against `running`, `finalizing`, `success`, and `failed` attempts; concurrent resume against a held chain lock; failure injected between append and commit followed by a resume that must produce no second commit. Reading and review do not count as evidence for these.
- The rule "rejects a backend that emits a different session ID" assumes both CLIs preserve the id on resume. If either legitimately emits a new id, every resume fails closed and the first dogfood run will show it immediately. The same applies to UUID validation of Codex thread ids, which pass 1 could not verify locally. Treat either as a plan amendment, not a silent relaxation.
- Codex sandbox on resume: if the rollout context does not expose the effective policy, the untouched-worktree and HEAD checks catch a stray write after the fact but do not prevent it. Record that outcome honestly rather than leaving the acceptance row implied.
- Process-group termination confirms "no executing members" but detached descendants outside the group are unmanaged by design. macOS still has no parent-death signal. Both are now accepted limits rather than open questions.
- Retention of CLI sessions remains with the CLIs. A late resume that finds the session gone is the "missing session state" path and must be tested as such.

### Driver response to reviewer pass 2

Accepted Thread 10: stale stop/resume handles fail and name the latest attempt.
All prior blocking threads were resolved by Claude; implementation started.

### Reviewer pass 3 (impl, claude reviewer)

Human concern, restated: long hard reviews were being killed by outer tool limits and their work lost, so the driver wants a deliberate stop, recovery of the same reviewer session, and no chance of the review being written back twice.

Verified before judging: branch `feat/review-resume` at `001acde`, worktree clean, five commits ahead of `origin/main`, nine files changed. I read the full diff and the current runner end to end, the new `structured-review/tests/test_recovery.py`, the updated existing tests, `structured-review/SKILL.md`, `structured-review/references/recovery.md`, `README.md`, `docs/CURRENT.md`, and `docs/agent_plans/README.md`. Executed here:

- `python -m unittest test_recovery -v`: 17 tests pass in about 34 seconds, all with real subprocesses and a fake provider.
- `python -m unittest test_claude_structured_review`: 87 pass.
- `python -m compileall -q structured-review scout` and `git diff --check origin/main..HEAD`: clean.
- CLI help, plus the visible stop and resume rejection messages for a nonexistent attempt directory.
- Two throwaway probes against the fake provider (not committed): one counting metadata writes per stream event, one raising `KeyboardInterrupt` in the window after the reviewer exits and before the finalization marker. Results are in Threads 11 and 12.
- Not executed here: `scripts/check_backlog.py`, the root tests, and the scout tests all import PyYAML, which is absent from my local interpreter. Those three rows stay driver-reported. No live provider calls were made, per the focus. Remote CI is still pending per the plan's own table.
- A grep for the retired values (`claude-fable-5`, `gpt-5.6-sol`, 900 seconds, the old `--timeout-sec 1800` guidance, "outer command/tool wait budget", "not an external interruption") finds them only in historical plans under `docs/agent_plans/`, which is correct.

#### Traceability against the implementation contract

| Item | Status | Evidence |
| --- | --- | --- |
| 1. Profiles, tier timeouts, timeout source | Done | Constants at `structured-review/scripts/claude_structured_review.py:31-38`; `timeout_source` set in `config_from_args`; `test_profiles_default_and_override_for_both_backends` covers normal, legacy auto, hard, and explicit override for both backends. |
| 2. Cooperative stop, signals, group cleanup, exit codes | Done | `request_stop`, `cleanup_process`, `captured_signals`; `test_stop_command_and_signals_cleanup_and_can_resume` observes exit 3, 130, and 143 from a real runner subprocess with a real grandchild, verifies the group is gone, then resumes; `test_graceful_stop_escalates_when_reviewer_ignores_sigterm` covers SIGKILL escalation. |
| 3. Atomic metadata, early session capture, fingerprint, private logs | Done, one efficiency defect (Thread 11) | `atomic_json` does fsync then rename; first session-bearing event captured for Claude, `thread.started` for Codex; `review_fingerprint` matches the plan's input list with timeout excluded. |
| 4. `--resume-run`, exact argv shapes, continuation instruction | Done | `claude_argv` and `codex_argv` match the pinned shapes exactly; argv asserted in `test_both_backends_timeout_resume_and_exactly_one_commit`; the continuation text at `:1284` is not asserted by any test (Thread 14). |
| 5. Per-attempt logs, chain lock, latest pointer, rejection set, fresh timeout, cumulative time | Done | `attempt_context` holds `chain_lock` through the yield; `require_latest` rejects stale handles by naming the latest path; tests execute running, finalizing, success, failed, and error outcomes, missing, invalid, and `--last` session ids, unverified cleanup, changed focus, model, effort, protocol, HEAD, artifact, and binary version, a dirty target, a held lock, and a stale stop. |
| 6. Finalizing marker before append, deferred signals, exactly-once, descendants gone before repo check | Done, with two narrow windows (Threads 12 and 13) | `write_metadata(outcome="finalizing")` precedes `append_and_commit_review`; `cleanup_process` runs before the post-run snapshot; `test_failure_between_append_and_commit_is_terminal` restores the clean target so the eligibility guard itself is what rejects; `test_late_signal_during_finalization_is_recorded_not_replayed` fires a real in-process SIGTERM plus a late stop file and observes one success and a refused resume. |
| 7. Docs: SKILL, README, CURRENT, plan index, recovery reference, blanket ban removed | Done | Diffs read; the old "do not kill a reviewer early" paragraph is replaced by the reasoned-stop text; `docs/CURRENT.md` last-updated line moved to 2026-09-06. |

Guard reach: the state-machine claims from pass 2's residual list (resume against `running`, `finalizing`, `success`, and `failed`; concurrent resume against a held lock; failure injected between append and commit followed by a resume that must produce no second commit) are each executed by a test that observes the specific intended error string rather than an unrelated setup failure. After a successful resume, a second write-back is refused three independent ways: stale-attempt rejection for the old handle, `outcome=success` rejection for the new one, and a fingerprint HEAD mismatch. I traced the write-back path and found no state in which an attempt is both resumable and has a review commit.

#### Blocking issues

None.

#### Non-blocking issues

##### Thread 11: Every session-bearing stream event rewrites metadata with an fsync

At `structured-review/scripts/claude_structured_review.py:1342-1346`, each event whose session id matches falls through to `patch_metadata`, which performs a JSON read, a second read inside the patch, a dump, an `fsync`, and an `os.replace`. In Claude Code's stream-json output every top-level message carries `session_id`, and `--include-partial-messages` turns every text delta into a message. My probe with a fake provider emitting 300 session-bearing events produced 310 metadata writes. A one-hour Fable review can emit tens of thousands of events, so the runner spends its event loop on synchronous disk I/O and lags behind the pipe. Stop and timeout checks happen only between loop iterations, so detection latency grows with the backlog. Correctness is unaffected and the live dogfood succeeded, so this is not blocking. Suggested fix: keep the captured id in a local variable, do the "changed session ID" comparison in memory, and call `patch_metadata` only on the first capture.

##### Thread 12: A signal in the gap between reviewer exit and the finalization marker discards a completed review

`run_claude` restores default signal handlers when its `captured_signals` block exits at `:1317`, and finalization only re-arms them at `:1641`. Between those points `run()` takes a git snapshot and decides the outcome (`:1631-1632`). My probe raised `KeyboardInterrupt` from that snapshot call: the attempt ended with `outcome=error`, `cleanup_complete=true`, `review.md` fully written, and resume refused. That is the fail-closed result the plan requires. By the same reading, a SIGTERM there (not executed) kills the runner with `outcome=running`, which is also non-resumable. The cost is that a review the reviewer had already finished is thrown away for a signal that lands in a window the length of one `git status`. Suggested fix: open one `captured_signals` scope around the snapshot, the outcome decision, and finalization, so a signal in that window is recorded as late exactly as it is a few lines later. The plan sentence "SIGINT and SIGTERM use the same cleanup path" would then hold without exception.

##### Thread 13: The `git commit` child remains exposed to a terminal SIGINT during finalization

Found by reading, not executed. `run_git` at `:291` spawns git in the runner's own process group. The runner defers its own SIGINT during finalization, but a terminal Ctrl-C is delivered to the whole foreground group, so git itself dies. The result is `CalledProcessError`, `outcome=error`, thread file appended but uncommitted, and resume refused. That is safe and matches the documented "requires inspection and a fresh review" rule, but the SKILL sentence "During finalization, signals are deferred" over-promises slightly. Either run finalization git commands with SIGINT ignored in the child, or add half a sentence to `structured-review/references/recovery.md` saying a terminal interrupt can still stop the commit and leave the thread file dirty. Driver-queued stops are unaffected because they send no signal.

##### Thread 14: Small evidence and usability gaps

- The continuation instruction prepended on resume (`:1284`) is not asserted by any test. The fake provider reads stdin and discards it; recording the prompt and asserting its first sentence would close the gap cheaply.
- Pass 2 asked, as an implementation note, that the rejection for a `running` or crashed attempt print the recorded runner PID, reviewer PGID, and launch time. The error at `:1191` and the no-live-runner error at `:1139` both tell the operator to inspect those values but do not print them. One-line improvement.
- The PyYAML-dependent check rows and the remote CI row are driver-reported or pending. Closeout should convert them to CI-backed provenance before treating the PR as validated.

#### Overall judgment

Ready for closeout. The implementation matches the accepted contract item by item, the negative tests exercise the real transitions and assert the intended error strings, and I could not construct a path to a second review commit or to resuming an attempt that had reached finalization. Threads 11 and 12 are each a few lines and I recommend fixing them before the PR, but neither weakens the exactly-once or fail-closed guarantees. This pass is not a merge-readiness handoff; that belongs to closeout after CI.

#### Residual risks and validation gaps

- Live provider behaviour is driver-reported only: same-session resume on Claude Code 2.1.261 and Codex CLI 0.153.4, the Codex workspace-write policy on resume, and the marker-retention check. I did not rerun them and cannot independently confirm them here. The sanitized evidence is consistent with the runner's own checks, since resume refuses a different id, so a successful dogfood implies the id was preserved.
- Linux CI has not yet run this branch. The `ps -eo pgid=,stat=` parsing, `flock`, and the kqueue versus epoll selector paths are exercised only on macOS so far.
- The runner now imports `fcntl` at module load, so the whole script is POSIX-only, not just the recovery feature. Consistent with the SKILL text, but worth one sentence if any consumer runs it elsewhere.
- Detached descendants, orphaned reviewers after a runner SIGKILL, PID reuse, and CLI transcript retention remain the accepted limits from pass 2. The implementation neither narrows nor widens them.

### Driver response to implementation review

- Accepted Thread 11: capture session identity in memory, persist only the first
  observation, and still reject any changed identity. A 300-event test observes
  one capture write and fewer than 15 metadata updates for the whole attempt.
- Accepted Thread 12: one shared signal list spans reviewer execution, post-exit
  snapshot, outcome decision, and finalization. Real SIGINT/SIGTERM injected in
  the snapshot window each preserve a completed review and exactly one commit.
- Accepted Thread 13 via documentation: the runner defers its own signals, but a
  foreground git child can still be interrupted. This leaves a non-resumable
  failed finalization requiring inspection. Driver-queued stops do not signal git.
- Accepted Thread 14: assert the continuation instruction received on stdin,
  print PID/PGID/start time for crashed/non-resumable attempts, and finish remote
  CI before closeout. Full local PyYAML-dependent checks passed in the isolated
  environment; reviewer environment lacked that dependency, which is not a pass.
- Driver-found CI correction: four legacy tests mocked reviewer execution but
  not the new version query. Mock that query too. All 107 review tests passed
  with Claude/Codex absent from PATH in a disposable source copy. Also preserve
  an actionable RunnerError for a missing explicitly selected executable.
- No scope, model, effort, or timeout policy changes. Ready for narrow resolution
  recheck of these corrections, then closeout.

### Reviewer pass 4 (impl, claude reviewer)

Human concern, restated: long hard reviews were being killed by outer tool limits and their work lost, so the driver wants a deliberate stop, recovery of the same reviewer session, and no chance of the review being written back twice. This pass is the narrow recheck of the driver's correction commit `5925cb8` against Threads 11-14.

Verified before judging: branch `feat/review-resume` at `5925cb8`, worktree clean, in sync with `origin/feat/review-resume`. I read the full correction diff (runner, both test files, `structured-review/SKILL.md`, `structured-review/references/recovery.md`, and the 22-line driver response in this plan; the plan body is unchanged). Executed here:

- `python -m unittest discover -s structured-review/tests -v` with both `claude` and `codex` removed from `PATH` (confirmed absent with `command -v` before the run): 107 tests pass in about 46 seconds, exit 0, worktree still clean afterwards. This reproduces the driver's isolation claim independently.
- `python -m compileall -q structured-review scout` and `git diff --check origin/main..HEAD`: clean.
- One throwaway probe (not committed) against the fake provider for the guard that Thread 11 rewired: a second event carrying a different valid session ID now fails the attempt with `backend changed session ID during attempt`, `outcome=failed`, `cleanup_complete=true`, and the first ID retained in metadata; the positive control (same ID repeated) completes with `outcome=success`. No existing test covers this rejection, so the probe stands in for it.
- Remote CI checked through `gh`: run `34013734391` on head `5925cb8` completed `success` with every step green (backlog check, root tests, structured-review tests, scout tests, compile) on Ubuntu with Python 3.12. The earlier failed run `34013223179` was on head `001acde`, which matches the driver's account of the four legacy tests that mocked reviewer execution but not the version query. PR `#30` exists and is still a draft.
- No live provider calls were made, per the focus. PyYAML is still absent from my local interpreter, so the backlog check, root tests, and scout tests are CI-backed for this pass, not reviewer-rerun.

#### Thread resolutions

##### Thread 11: Every session-bearing stream event rewrites metadata with an fsync

Resolved. `structured-review/scripts/claude_structured_review.py:1318` seeds `captured_session` from the resume ID, and the session block at `:1351-1362` compares in memory and calls `patch_metadata` only on the first observation (`elif not observed_session`). The invalid-ID, wrong-resume-ID, and changed-ID rejections remain in front of that branch, and my probe above observed the changed-ID rejection firing with the new in-memory comparison. `test_session_capture_is_persisted_once_for_many_events` (`structured-review/tests/test_recovery.py:283`) drives 300 session-bearing events through the real fake provider and asserts exactly one `session_captured` write and fewer than 15 metadata updates for the entire attempt; because `write_metadata` routes through `patch_metadata`, that bound covers all metadata I/O, not only the session path. Passed locally and in CI.

##### Thread 12: A signal in the gap between reviewer exit and the finalization marker discards a completed review

Resolved. `captured_signals` now accepts a shared list (`:1278-1289`), `run()` opens one scope alongside `attempt_context` (`:1641-1642`), `run_claude` nests on the same list through `logs.signals` (`:1332`), and finalization nests on it again (`:1656`). Nested scopes restore the outer lambda on exit, so from reviewer launch through the success write there is no instant at which the default handler is installed. The per-`run_claude` `late_signals` patch is gone and success records `list(late_signals)` at `:1668`, so the accounting is a single list rather than a read-modify-write of metadata. `test_actual_signals_in_post_exit_snapshot_do_not_lose_completed_review` (`:298`) sends a real SIGINT and a real SIGTERM to the runner's own PID during the post-exit `git_snapshot` call (I confirmed the second call site at `:1647` is that snapshot and no other call sits between it and the pre-launch one at `:1636`), then observes `outcome=success`, `late_signals=[sig]`, exactly one review commit, and a refused resume with `not resumable: outcome=success`. Before this fix the SIGINT case produced `outcome=error` in my pass 3 probe and the SIGTERM case would have killed the process, so the test discriminates. Side benefit: a signal during the incomplete-path metadata write (`:1652-1654`) is now captured instead of interrupting the write, which closes a small way to leave a timed-out attempt stuck at `outcome=running`. The contract sentence "SIGINT and SIGTERM use the same cleanup path" now holds without the gap exception.

##### Thread 13: The `git commit` child remains exposed to a terminal SIGINT during finalization

Resolved by documentation, as the driver chose. `structured-review/SKILL.md:224-226` now says the runner defers its own signals and that a terminal interrupt can still stop a git child and leave an uncommitted thread append; `structured-review/references/recovery.md:54-56` says the same with the Ctrl-C framing and the non-resumable consequence. The SKILL text loaded into this very prompt already carries the new sentence, which confirms the runner reads the updated file. Cosmetic only: line 224 of `SKILL.md` runs to 123 characters inside a paragraph otherwise wrapped at 80; there is no markdown lint in CI, so rewrap at the driver's convenience or not at all.

##### Thread 14: Small evidence and usability gaps

Resolved.

- Continuation instruction: the fake provider now writes its stdin to `stdin.txt` (`structured-review/tests/test_recovery.py:41`) and the resume test asserts the prompt starts with `Continue the interrupted review in this same conversation.`, contains `ONE complete final review` and `The original scope`, and still contains the original focus text `Review the plan.` (`:130-134`). This matches the runner text at `:1297-1303` and proves the original prompt survives behind the preamble. The file is overwritten by the resumed attempt, so a stale copy from the initial attempt would fail the `startswith` assertion. Passed for both backends.
- Diagnostics: `attempt_diagnostics` (`:1129-1134`) prints `runner_pid`, `reviewer_pgid`, and `started_at` with a `created_at` fallback, and is used by both the no-live-runner stop error (`:1148`) and the non-resumable-outcome error (`:1204`). I checked that `write_metadata` omits `started_at` when there is no result (`:1047-1048`), so the fallback actually reaches `created_at` for a pre-launch crash rather than printing `None`. `test_no_live_runner_stop_does_not_signal_recorded_pid` (`:274`) asserts the real runner PID value and the presence of the other two fields.
- Provenance: the PyYAML-dependent rows and the Linux-only code paths (`ps -eo pgid=,stat=` parsing, `flock`, epoll selector) are now CI-backed by run `34013734391` on the current head. The evidence table in this plan still lists "Independent implementation review and remote CI" as Pending; closeout should replace that row with this pass and the CI run ID.

##### Driver-found CI correction

Accepted as described. The four legacy tests now mock `binary_version` alongside `run_claude`, and `review_fingerprint` converts an `OSError` from the version query into `reviewer binary unavailable: <path>; install it or check the explicit backend binary flag` (`:1161-1164`), covered by `test_missing_explicit_binary_has_actionable_runner_error` (`:319`). `binary_version` uses `check=False` and handles `TimeoutExpired`, so only a missing or unexecutable binary reaches that branch, which is the right scope for the message.

#### Blocking issues

None.

#### Non-blocking issues

None new. The two items above that need follow-up (stale Pending row in the evidence table; optional rewrap of `SKILL.md:224`) belong to closeout and need no reviewer round.

#### Overall judgment

Ready for closeout. Threads 11 through 14 are resolved: each fix is a few lines, each is exercised by a test that runs the real transition and asserts the intended outcome, and the full suite passes both locally with the provider binaries hidden and in remote CI on the reviewed head. No scope, model, effort, or timeout policy changed. This is not a merge-readiness handoff; PR `#30` is still a draft and closeout owns the final rechecks and the evidence-table update.

#### Residual risks and validation gaps

- Two signal windows remain outside the shared handler by construction: the pre-launch window inside `attempt_context` (lock, fingerprint, metadata creation) and the instant after the outer signal scope exits while the chain lock is released. In the first, no reviewer has started and the attempt fails closed as a non-resumable `running` record with diagnostics printed; in the second, metadata is already terminal and write-back is complete. Nothing is lost in either, so I am recording them rather than asking for more code.
- Live provider behaviour remains driver-reported from the earlier dogfood; this pass did not rerun it and the correction commit does not touch the provider argv shapes.
- The changed-session-ID rejection is covered only by my uncommitted probe. It is a small negative guard on a path the driver did not change semantically; adding it to `test_recovery.py` is cheap if the driver wants it in the suite, but I am not reopening a thread for it.
- Detached descendants, orphaned reviewers after a runner SIGKILL, PID reuse, and CLI transcript retention remain the accepted limits from pass 2, unchanged.

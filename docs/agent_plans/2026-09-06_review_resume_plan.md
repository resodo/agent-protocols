# Review profiles, cancellation, and session recovery

Status: active implementation plan

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
  request in the exact latest attempt directory; if the chain lock is free,
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
  SIGINT/SIGTERM through this section; late requests never undo completed
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

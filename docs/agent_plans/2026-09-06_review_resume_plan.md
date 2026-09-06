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

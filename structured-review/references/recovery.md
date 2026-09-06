# Review recovery operations

This is driver guidance. The reviewer still uses the same required review lenses.

## Run, stop, resume

A normal attempt has a 1800-second default; hard has 3600 seconds. A positive
`--timeout-sec` overrides either profile. Defaults never derive from mechanical
complexity recommendations. Use background execution if your calling tool
cannot keep a process alive for the whole limit plus at least 30 seconds.

Example initial invocation (all paths below are illustrative):

```sh
python structured-review/scripts/claude_structured_review.py \
  --worktree /path/to/repo --mode print-review --type impl \
  --artifact docs/change.md --focus 'Check acceptance and recovery behavior.' \
  --reviewer-backend codex --review-tier hard \
  --tier-reason 'Concurrent recovery correctness'
```

The runner prints `run_log=...` before launching. Use that absolute attempt
path as RUN. Inspect its `metadata.json` and private stream logs for progress.
To request a stop:

```sh
python structured-review/scripts/claude_structured_review.py \
  --stop-run /path/to/attempt --stop-reason 'Repeated tool failures; investigate before continuing'
```

The command only queues a request; it does not acknowledge termination. Poll
metadata until `stopped`, `interrupted`, or `timeout`, and verify
`cleanup_complete=true`. Then repeat the original invocation with
`--resume-run /path/to/attempt`, omitting `--run-log-dir`. A new attempt path is
printed. Always use that newest path for subsequent stop/resume commands.
`--timeout-sec` may change; target and reviewer constraints may not.

## State and failure handling

| Outcome | Meaning | Resume | Exit |
| --- | --- | --- | --- |
| running | Created/launched/session captured | No | Running |
| timeout | Attempt time limit reached | With session ID and verified cleanup | 2 |
| stopped | Driver request handled | With session ID and verified cleanup | 3 |
| interrupted | SIGINT/SIGTERM handled | With session ID and verified cleanup | 130/143 |
| finalizing | Output validation/write-back began | No | Running |
| success | Printed or appended/committed and verified | No | 0 |
| failed/error | Backend, validation, cleanup, or runner failure | No | Nonzero |

The chain lock is held through finalization. Before appending any text, the
runner persists a non-resumable marker. Failure or a crash during write-back
requires inspection and a fresh review, never replaying the old write-back.
Late stop requests/signals do not retroactively cancel a completed result.
A changed HEAD, dirty target, changed artifact/prompt/protocol/profile/binary,
missing ID, stale attempt, or live chain produces an explicit rejection.

An outer SIGKILL or runner crash can leave an orphaned reviewer. A released lock
is not permission to resume: nonterminal state is rejected. Stop refuses a
chain with no live lock owner and never kills a stored PID (it may be reused).
The caller must diagnose the recorded PID/PGID and tool processes before a fresh
review. The runner controls its POSIX process group, not detached descendants.
If group cleanup cannot be verified, the attempt fails and cannot resume.

## Persistence and provider behavior

Claude uses `-p --resume ID` with explicit model/effort/permission mode. Codex
uses `exec resume ID - --json`, explicit model/reasoning effort, and
`-c sandbox_mode="workspace-write"` because the resume subcommand has no
`--sandbox` flag. Neither launch uses ephemeral/no-session-persistence flags.
The resumed backend must confirm the original UUID; missing transcripts or a
new session ID fail rather than silently starting over. CLI user settings,
hooks, and provider state remain environment dependencies; keep them stable.

Recovery reuses persisted conversation history and tool results. Unsaved
reasoning and in-flight commands are not checkpoints; they may need rechecking.
A new attempt receives a fresh time limit; metadata records both attempt and
cumulative elapsed seconds. There are no automatic retries.

Run state is trusted private local data, with atomically replaced metadata.
The original machine's provider transcript store must also remain available.
The caller owns retention; delete only after deciding recovery is no longer
needed. Do not put raw logs, transcripts, or machine-specific paths in git.
Protocol maintainers update argv, parsing, negative guard tests, and this guide
when CLI/model changes break the live recovery smoke. Tests with fake CLIs prove
runner logic; a real stop/timeout followed by resume proves provider integration.

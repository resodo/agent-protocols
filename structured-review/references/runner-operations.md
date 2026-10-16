# Runner Operations (driver-only)

Driver-facing operation of the structured-review runner. The runner does not
load this file into reviewer prompts. The rule for when the runner is the
default is in `../SKILL.md`, "Default Runner Rule".

## Selection

For the backend, `--reviewer-backend auto` tries **Claude > Codex > Grok**,
excluding the current coding agent. Missing binaries and authoritative
exhausted-allowance errors advance to the next eligible backend without asking
the human. No provider-balance polling or persistent availability cache is used.

Pass `--coding-agent NAME` on new calls (`claude`, `codex`, `grok`, `kimicode`,
or another agent name). Explicit identity overrides inherited environment
markers. Without it, Claude/Codex markers identify those drivers; conflicting
markers require explicit identity or an intentional backend pin. Grok drivers
must pass `--coding-agent grok`, because no reliable marker is pinned. Another
or unrecognized coding agent excludes none; unknown identity warns that
same-agent exclusion cannot be guaranteed.

Examples: Codex driver with Claude allowance exhausted -> Grok; Kimi Code driver
with Claude exhausted but Codex available -> Codex. Explicit backend pins do not
fall back. Resume keeps the recorded backend and identity and never re-enters
automatic selection. See the recovery reference for failure categories.

For repo-backed gates, the driver must pass `--review-tier normal` or
`--review-tier hard`. The review type, artifact count, artifact length, and
keywords never change that selection or its model profile.

Normal is the default. Keep hard scarce: before choosing it, judge whether this
task belongs to roughly the hardest 20% of tasks you handle. Major design, major
architecture changes, or unusually difficult bugs can qualify when the actual
reasoning difficulty warrants it. The 20% is a judgment aid, not a numerical
quota or a mechanically enforced percentile.

`hard` requires `--tier-reason` with a non-empty, concrete explanation of what
makes this task unusually difficult. Routine shared-protocol edits, artifact
count, document length, Closeout Review type, keywords, and mechanical runner
recommendations alone do not qualify. Use normal when in doubt. The runner
rejects `--tier-reason` with normal or auto; it cannot validate your subjective
difficulty judgment.

For compatibility, omitted `--review-tier` and explicit `--review-tier auto`
select `normal`, emit a deprecation warning, and record
`legacy-auto-compatibility`. They never select a hard-profile model. Migrate
callers to an explicit tier; removing auto or making omission fail closed is a
later reviewed change after known consumers migrate.

The runner still recommends `hard` when any of these mechanical signals is
present; otherwise it recommends `normal`:

- type is `closeout-review`;
- artifact body size before `## Review Threads` is greater than 1,000 lines;
- an `impl` review has multiple artifacts;
- artifact body or focus names production/runtime/deploy/rollout,
  architecture/migration, security/data-safety, multi-repo/multi-agent/release,
  broad protocol-change, or explicit high-complexity scope recognized by the
  runner's pinned signal table.

The keyword signals cannot tell a decision doc from a plan, so a docs-only
decision doc that names architecture or migration still gets a `hard`
recommendation; keep `normal` for decision docs, as `Document Levels` in `../SKILL.md` says.

The recommendation and its reasons are observational. They are shown in the
prompt, start log, and metadata but never alter selected tier, model, timeout,
scope, or readiness. Use clear, concrete focus text; do not add keywords to
force a recommendation.

The resolved profile matrix is:

| Reviewer backend | `normal` model / effort | `hard` model / effort |
| --- | --- | --- |
| `claude` | `claude-opus-5-5` / `high` | `claude-fable-5-1` / `xhigh` |
| `codex` | `gpt-6-sol` / `high` | `gpt-6-astra` / `xhigh` |
| `grok` | `grok-4.7` / `medium` | `grok-4.7` / `xhigh` |

The prompt, start log, and run metadata separately record selected tier,
selection source, driver reason, recommended tier, recommendation reasons,
final model/effort, and whether model/effort came from the profile or an
explicit provider flag. Metadata temporarily retains deprecated
`review_tier`/`review_tier_reasons` compatibility keys. Tier selects model routing and the default time limit: both tiers apply the same readiness standard, and `hard` does not
authorize invented scope or low-value findings. Review threads continue to
record the reviewer backend in each pass heading.

Automatic fallback never selects the identified coding agent. An intentional
explicit backend pin remains an override, not an automatic fallback.

## Runner Modes

Use `write-commit-to-plan` for normal plan and implementation artifacts that
have a `## Review Threads` section:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree /path/to/target-repo \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/example_plan.md \
  --artifact docs/example_plan.md \
  --coding-agent codex \
  --review-tier normal \
  --focus "Review acceptance, validation, scope, and role boundaries." \
  --topic "example plan"
```

In both modes the reviewer runs read-only and returns the review text. In
`write-commit-to-plan` the runner itself appends that text verbatim under the
thread file's `Review Threads` section and creates the `structured-review:`
commit, so the append-only thread contract holds by construction.

`--artifact`, `--thread-file`, and `--focus-file` accept only paths inside
`--worktree`; any other path fails with `path escapes worktree`. Write a long
focus to a file inside the worktree, or pass it inline with `--focus`.

Use `print-review` when appending review threads would pollute a durable
reference artifact, such as a published doc, skill, protocol overlay, or other
reference file.

For Closeout Review, default to `print-review` for durable closeout reports or
reference artifacts. Use `write-commit-to-plan` only when the driver explicitly
provides a thread file that already has a `## Review Threads` section.

Do not commit or edit files in the worktree while a review run is in flight:
`print-review` aborts with `print-review changed HEAD`, and the runner warns
that the review target changed.

The explicit runner `--mode` is the write-back authorization for that run. The
driver still owns the decision after receiving reviewer output.

Pass `--reviewer-backend claude|codex|grok` to pin the reviewer backend; the
default `auto` uses ordered selection excluding the identified driver.

Pass `--review-tier normal|hard` for every new repo-backed call. Provider-
specific `--model`, `--effort`, `--codex-model`, `--codex-effort`, `--grok-model`,
and `--grok-effort` flags
override only the selected backend's profile and are intended for deliberate
exceptions. A non-hard tier cannot use those flags to select that backend's
pinned hard-only profile model; select hard and provide `--tier-reason` instead.
Grok shares its model across tiers, so that model is allowed for normal too.
Effort overrides remain deliberate exceptions with provenance; do not use them
to evade the rare-hard guidance.
Repeating the pinned hard model as an override on a valid hard run is allowed.
If a caller supplies an override for the non-selected provider, the runner
warns that the flag is ignored.

The matrix, recommendation signal table, and legacy-auto compatibility path
are durable protocol mechanisms. When a provider model or signal changes, or
when known consumers have migrated enough to remove auto, update the runner
constants, its tests and this reference in one reviewed change; update
`README.md` or `docs/CURRENT.md` only if their routes change. Do not silently replace a pinned profile through a mutable
alias.

Use `--protocol-dir` only when testing or intentionally running against a
different checkout of this protocol. By default the runner uses the
`structured-review` directory that contains the script.

## Timeout Discipline

Defaults are 1800 seconds for normal (including legacy auto) and 3600 seconds
for hard, on all three backends. `--timeout-sec` explicitly overrides the positive
per-attempt limit. Metadata records timeout source and cumulative attempt time.
Recovery grants a fresh attempt limit, not a remaining slice of the first run.

The driver may stop a reviewer with a concrete reason, using `--stop-run` and
`--stop-reason`. Quiet output or elapsed time alone does not prove lack of
progress; examine progress, repeated failures, changed task needs, or budget.
A stopped review is incomplete, never a passed quality gate.

The outer process lifetime must cover the runner timeout plus cleanup and
metadata writing (allow at least 30 seconds of teardown buffer). If the calling
agent's tool imposes a shorter lifetime, launch using its supported background
execution and poll the run metadata. A short per-poll wait budget is fine;
polling must not kill the process. A heartbeat shows runner liveness, not
substantive reviewer progress.

The runner prints the attempt log directory at launch. Stop requests are
queued there; queueing is not acknowledgement. Poll `metadata.json` until a
terminal outcome before resuming. SIGINT/SIGTERM and timeout clean up the owned
POSIX process group, first gracefully and then forcibly if needed. Detached
processes outside that group are not managed. During finalization, the runner
defers its own signals and late stop requests do not undo completed write-back. A terminal interrupt can still stop a git
child and leave an uncommitted thread append; inspect it before a fresh review.

## Recovery

Use `--resume-run ATTEMPT_DIRECTORY` with the same original scope/profile
arguments (omit `--run-log-dir`). Timeout may be changed. Each attempt has its
own logs; always use the latest attempt directory printed at launch. Old
attempt handles fail with the latest path, rather than silently redirecting.

Recovery is supported for Claude, Codex, and Grok on POSIX systems, and restores a
persisted CLI conversation, not an in-flight computation. Only cleaned
`timeout`, `stopped`, or `interrupted` attempts with a captured session ID may
resume. A runner crash or outer SIGKILL is not resumable; inspect its recorded
PID/PGID for a possible orphan before starting a fresh review. The runner never
signals a stale PID from metadata. Missing CLI history, changed target or
reviewer constraints, a running chain, and finalizing/completed/failed attempts
are rejected. No --last selection, automatic retry, or fresh-session fallback.

Run metadata and provider transcripts are trusted private local state. Retain
both on the original machine for as long as recovery is needed; copying just
the run log is insufficient. The caller owns retention and cleanup. Do not
commit raw logs or transcripts. Keep model/effort, CLI binary/version, worktree,
commit, artifacts, focus, and protocol stable across recovery. An incomplete
attempt never appends review threads. The runner marks finalization before
mutation and holds the chain lock through verification and write-back.

See `recovery.md` for commands, outcomes, and compatibility checks.
That operational reference is driver guidance, not a runner-loaded review lens.

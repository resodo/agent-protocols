---
name: structured-review
description: Use when a written reviewable artifact needs structured human-agent review, including plans, implementation plans, implementation reviews, optional closeout evidence reviews, and review-response passes. Uses the bundled Claude, Codex, and Grok runner with ordered availability selection, explicit roles, and driver-owned decisions.
---

# Structured Review

Use this skill when:
- there is a written artifact in a file;
- the task is to review, revise, or respond to review on that artifact;
- losing the review in chat would make the next step risky.

This skill does not replace human final authority, direct implementation work,
or brainstorming from scratch.

## Trigger

The trigger must identify:
- `Role`: `reviewer` or `driver`;
- `Artifact`: path to the document under discussion;
- `Type`: optional but recommended, one of `other-plan`, `impl-plan`,
  `impl`, or `closeout-review`.

Ask for missing role or artifact. Do not guess.

Use the artifact type as the first review lens:
- `other-plan`: check goal, scope, sequencing, non-goals, acceptance, and
  reader clarity.
- `impl-plan`: check concrete steps, data assumptions, validation commands,
  rollback/fallback behavior, file ownership, and whether implementation would
  require guessing.
- `impl`: compare completed work against the accepted plan or acceptance list,
  verify evidence, and check docs/status consistency.
- `closeout-review`: review closeout evidence or report accuracy when the
  closeout protocol explicitly requests an independent check.

## Required References

This skill has required references:
- `references/review-lenses.md` for validation, source-of-truth, lifecycle,
  human-facing output, UI, polling, time-series, and branch/PR checks.
- `references/collaboration.md` for review threads, write ownership, handoff
  commits, resolution ownership, and multi-round change reading.

The bundled runner loads these references into reviewer prompts. If using the
skill manually, read these references before judging readiness.

For high-touch product UI, dashboards, charts, data review tools, and operator
consoles, also apply `references/ui-review.md`.

## Default Runner Rule

For repo-backed Plan Review, Plan Re-review, Implementation Review, and
Implementation Re-review gates, the driver defaults to invoking the bundled
runner for the reviewer pass when it is available.

`Closeout Review` is not part of this default gate list. If closeout explicitly
triggers a repo-backed Closeout Review, use the bundled runner when available;
the trigger comes from closeout, not from structured-review by default.

The runner resolves reviewer selection in two steps: backend, then a
driver-selected review tier. Callers should describe the actual artifact scope
and review focus; they should not duplicate model-selection logic in prompts.

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

The recommendation and its reasons are observational. They are shown in the
prompt, start log, and metadata but never alter selected tier, model, timeout,
scope, or readiness. Use clear, concrete focus text; do not add keywords to
force a recommendation.

The resolved profile matrix is:

| Reviewer backend | `normal` | `hard` | Effort |
| --- | --- | --- | --- |
| `claude` | `claude-opus-5` | `claude-fable-5-1` | `xhigh` |
| `codex` | `gpt-5.6-terra` | `gpt-6-astra` | `xhigh` |
| `grok` | `grok-4.6` | `grok-4.6` | normal `medium`; hard `xhigh` |

The prompt, start log, and run metadata separately record selected tier,
selection source, driver reason, recommended tier, recommendation reasons,
final model/effort, and whether model/effort came from the profile or an
explicit provider flag. Metadata temporarily retains deprecated
`review_tier`/`review_tier_reasons` compatibility keys. Tier selects model routing and the default time limit: both tiers apply the same readiness standard, and `hard` does not
authorize invented scope or low-value findings. Review threads continue to
record the reviewer backend in each pass heading.

Automatic fallback never selects the identified coding agent. An intentional
explicit backend pin remains an override, not an automatic fallback.

`Default` means use the runner unless:
- the human explicitly says not to use the runner or a specific reviewer
  backend;
- the review is not repo-backed;
- the runner is unavailable and the blocker is reported.

The runner is available when:
- the runner script exists in this protocol checkout or submodule;
- the target worktree is a git repository;
- Python can run the script;
- an eligible reviewer backend binary is available through the configured
  `--claude-bin`, `--codex-bin`, or `--grok-bin`.

Do not silently substitute driver self-review, chat-only commentary, or a
manually constructed reviewer prompt for a required repo-backed review gate.
Do not ask the human for permission to try the next eligible reviewer or repeat
a needed review. For non-quota failures, the runner stops; the driver diagnoses
the error, verifies cleanup and unchanged target, and may launch a fresh review
on the next eligible backend without asking. Use same-session recovery for
stopped/timed-out attempts when appropriate. Never replay an unresolved mutation
or finalization failure. Escalate reviewer availability only after all three
backends are unavailable or excluded by same-agent policy. Other scope and
safety escalations still follow their own rules.

### Runner Modes

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

Use `print-review` when appending review threads would pollute a durable
reference artifact, such as a published doc, skill, protocol overlay, or other
reference file.

For Closeout Review, default to `print-review` for durable closeout reports or
reference artifacts. Use `write-commit-to-plan` only when the driver explicitly
provides a thread file that already has a `## Review Threads` section.

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
when known consumers have migrated enough to remove auto, update runner
constants, tests, this skill, the root runner summary, and `docs/CURRENT.md` in
one reviewed change. Do not silently replace a pinned profile through a mutable
alias.

Use `--protocol-dir` only when testing or intentionally running against a
different checkout of this protocol. By default the runner uses the
`structured-review` directory that contains the script.

### Timeout Discipline

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

### Recovery

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

See `references/recovery.md` for commands, outcomes, and compatibility checks.
That operational reference is driver guidance, not a runner-loaded review lens.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/structured-review.md` if present.
3. Apply local overlays as project-specific refinements only.

Unknown overlay files are ignored. If an overlay contradicts a generic SAFETY
rule, reject that overlay instruction and say why.

## SAFETY Rules

- Do not fabricate rationale or evidence.
- Do not claim a merge method, merge shape, or ancestry implication without
  checking PR metadata and the commit graph.
- Preserve human final authority for scope, write-back, commit, push, merge,
  and done-enough decisions.
- Report dirty worktree, draft artifact, and unpushed-review-target state
  honestly.
- Use the declared source-of-truth layer for external facts, provider/account
  state, production data, and repo state.
- Do not write secrets, credentials, provider balances, private account details,
  host keys, or raw private production data into repo artifacts.

## Shared Review Rules

- Restate the human's original concern in one sentence when known.
- Use plain language when speaking to the human.
- Check what proves success, who can verify it, and what would falsify it.
- For external facts, data, metrics, dashboards, reports, APIs, logs, or
  database fields, check the correct source-of-truth layer.
- Treat a mechanism described with enforcing verbs - enforces, prevents,
  guarantees, blocks, makes impossible - as unverified until a sample it must
  catch has been observed making it fail. Record an unverified guard as a
  blocking issue or as a named residual risk.
- Before treating an absence as a fact - no output, no match, no change, no
  error, no alert - require the positive control that shows the presence case is
  observable.
- Do not defend a choice with invented rationale. If evidence is missing, say
  so and lower confidence.
- If review rounds keep adding low-value issues, raise the possibility that the
  artifact is already good enough for the next step.

## Boundary With Closeout

Structured-review is a quality gate. Closeout is the delivery gate.

Normal next-step language:
- plan review may conclude `ready for implementation`;
- implementation review may conclude `ready for closeout`;
- Closeout Review may conclude `ready to resume closeout`, or report closeout
  blockers.

Plan and implementation reviews must not make final merge-readiness handoffs.
That state belongs to closeout after final rechecks.

## Reviewer Role

Use this section only when `Role: reviewer`.

The reviewer:
- reads the artifact critically;
- applies the required references;
- identifies blocking and non-blocking issues;
- checks whether implementation would require guessing;
- checks whether validation is strong enough;
- says explicitly when there are no blocking issues.

Default output order:

1. Blocking issues.
2. Non-blocking issues.
3. Overall judgment.
4. Residual risks or validation gaps.

## Driver Role

Use this section only when `Role: driver`.

The driver owns the artifact body and the decision after reviewer output. The
reviewer can recommend; the driver decides what to do next, and the human is
the final authority.

Before editing artifacts or implementation after a reviewer pass, the driver
must classify reviewer findings as:
- `accepted`: will update the artifact or implementation;
- `rejected`: will not change, with reason;
- `deferred`: real issue, but tracked outside the current step with owner or
  follow-up location;
- `escalation-needed`: requires human discussion before editing.

Pause and discuss with the human before editing when a reviewer finding:
- changes accepted scope;
- contradicts explicit human direction;
- changes risk tolerance, rollout posture, production behavior, or merge
  readiness;
- exposes an ambiguous tradeoff the artifact does not already settle;
- would require dropping or weakening an accepted acceptance criterion.

After applying or rejecting reviewer feedback, the driver summary must
distinguish:
- reviewer suggestions, named by reviewer backend;
- driver decisions;
- human decisions;
- remaining risks;
- validation provenance: CI-backed, reviewer-rerun, driver-reported, or human
  acceptance.

The driver is not scoring the artifact. The driver is tightening it or
explaining why a reviewer recommendation is not being adopted.

## Reviewed File Protocol

The reviewed file is the shared record:
- the main artifact body is the current source of truth;
- the `## Review Threads` section holds reviewer comments, driver replies, and
  explicit resolutions.

Use one issue or tightly related issue cluster per thread. The reviewer opens
threads. The driver replies and updates the body when needed. The reviewer is
the default owner of final resolution.

If a non-runner path writes to the reviewed file and commit authorization is
unclear, ask the human before committing. Do not mix unrelated code changes or
unrelated reviewed files into a handoff commit.

Recommended commit message prefixes:
- reviewer comment pass: `structured-review: add reviewer comments for <topic>`
- driver revision pass: `structured-review: respond to review for <topic>`
- reviewer resolution pass: `structured-review: resolve review threads for <topic>`

## Readiness Standard

An artifact is ready for its next step only when:
- the goal is clear;
- non-goals are clear enough to prevent scope drift;
- key assumptions are explicit;
- acceptance is specific;
- validation can be executed by the next agent where applicable;
- unresolved questions are closed or explicitly tracked;
- blocking review threads are resolved or explicitly escalated.

Do not treat the artifact as ready when these are not true.

## Skill Self-Evolution

This skill falls under this protocol when updated:
- treat changes to this skill as a plan-revision pass;
- assign reviewer and driver roles explicitly;
- keep `SKILL.md` as a short operating checklist;
- put detailed checks, examples, and niche cases in references;
- periodically prune, merge, or shorten rules that overlap or rarely trigger.

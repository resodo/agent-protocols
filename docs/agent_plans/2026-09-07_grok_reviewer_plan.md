# Grok reviewer and ordered availability policy

Status: active implementation plan; plan review pending.

## Goal and accepted decisions

Add Grok Build as the third structured-review backend. For automatic selection,
try Claude, then Codex, then Grok, excluding the current coding agent. Advance
when a provider authoritatively reports exhausted credits or usage allowance.
Examples: Codex driver and unavailable Claude allowance selects Grok; Kimi Code
driver and exhausted Claude allowance selects Codex when usable.

Use `grok-4.6` for both tiers: normal `medium`, hard `xhigh`. Keep Claude/Codex
profiles unchanged. Keep common modes, explicit tier rationale, 1800/3600-second
attempt defaults, timeout override, heartbeat, private logs, stop, and guarded
same-session resume. A resumed review stays on its recorded backend.

Driver: Codex. Reviewer: first eligible provider under the accepted policy.
Work branch: `feat/grok-review`, based on fresh `origin/main` at `277edca`.
All changes belong in a linked worktree. No merge is authorized by this plan.

## Evidence and implementation boundary

The existing runner has a backend registry and common process-group lifecycle,
but profile selection, session parsing, CLI flags, and binary resolution contain
two-provider branches. Auto selection currently excludes the detected driver
but fails without fallback. Recovery fingerprints cover backend, model, effort,
binary/version, target HEAD/files, prompt, and runner contents.

Installed Grok Build 1.0.13 advertises `grok-4.6`, explicit `--resume` UUID,
`--session-id`, `--prompt-file`, `--reasoning-effort`, permission controls, and
`streaming-messages-json`. Official reasoning documentation supports medium and
xhigh: https://docs.x.ai/developers/model-capabilities/text/reasoning.
CLI help establishes argument shape; live output must establish event/session
and recovery behavior before claiming integration complete.

Files: `structured-review/scripts/claude_structured_review.py`, existing and new
structured-review tests, `structured-review/SKILL.md`, recovery reference,
`README.md`, `docs/CURRENT.md`, and this dated plan/evidence record. Inspect
affected consumers for stale two-provider assumptions. Do not change Scout's
independent provider policy or unrelated backlog items.

## Five gates

1. Plan: commit this reviewable plan and establish CLI evidence.
2. Plan review: invoke the existing checkout runner with Claude, hard tier
   because this changes shared routing and recovery contracts. Resolve blocking
   threads before implementation. If Claude has no allowance, the current
   two-backend runner cannot select Grok and Codex is excluded by user policy.
   Report the bootstrap conflict before substituting a manual review or
   implementing a backend ahead of the gate; agree the bootstrap path with the
   human. Never label a failed provider call a passed review.
3. Implementation: implement the accepted plan and tests only after plan review.
4. Implementation review: dogfood automatic routing through the updated runner,
   resolve findings and re-review required fixes.
5. Closeout: verify traceability, documentation lifecycle, safety and git state;
   hand off the feature for human merge without merging it.

## Implementation design

### Provider adapter and profile

Register Grok with its own binary, argv, output parser, final-result extraction,
session event extraction, and version retrieval. Add `--grok-bin`,
`--grok-model`, `--grok-effort`; allow `--reviewer-backend grok`. Selected-provider
overrides apply only to that provider, including after fallback; ignored flags
warn. Both Grok tiers share a model, so the existing hard-model-only guard must
apply only when normal and hard models differ. Hard still requires a reason.

Use headless Grok with explicit model/effort, persisted conversation, and review
permissions. Verify actual stdout before settling stream parsing. Use a private
prompt file if Grok cannot accept the current stdin contract. Reviewers return
text; the runner alone validates and appends/commits. Invalid/error/empty output
cannot be treated as a successful review. Preserve common cleanup and mutation
checks. Verify permission behavior and process ownership in the live smoke.

### Ordered selection and credit evidence

Provide an explicit coding-agent identity argument to cover Kimi Code and other
drivers without reliable environment markers. Retain known Claude/Codex marker
detection and add Grok detection only from verified CLI evidence; conflicting
markers fail with actionable identity guidance. An explicit identity resolves
inherited markers. Unknown identities exclude none of the three providers.

For auto, construct the ordered candidate list excluding the driver. A missing
binary is unavailable and may be skipped with a recorded reason. Attempt each
eligible provider at most once. Explicit backend pinning does not fall back.
Use provider error envelopes / authoritative CLI failures for quota detection,
never artifact text, tool output, model-generated prose, or internal token
estimates. No balance polling, persistent balance cache, or guessed credit
count. A successful review establishes current usability, not remaining credit.

Keep exhausted attempts as terminal private evidence, with provider, reason
category, and next candidate provenance. Clean process group and unchanged
worktree/HEAD are prerequisites to advancing. Authentication, permission,
network, malformed output, generic rate limiting without allowance evidence,
timeouts, interruptions, write-back failures, and unknown failures stop with
diagnostics. Exhausting all candidates is an incomplete gate with a useful
error, never same-agent fallback. Do not commit raw provider responses or
account details.

### Recovery

Fresh fallback attempts are separate provider conversations. Resume loads the
latest attempt's original backend before auto selection, retains the original
profile/scope/binary fingerprint, and never falls back or starts a new session.
Changing explicit backend/identity or constraints must be rejected when it
would change the review. Preserve lock, cleanup, latest-attempt, dirty-target,
missing/mismatched-session, nonterminal/finalization, and duplicate-write guards.
Only cleaned timeout/stopped/interrupted attempts with observed persisted
session evidence are resumable. Timeout overrides may change on resume.

## Acceptance and validation

- CLI/profile tests: both Grok tiers and overrides; normal shared-model allowed;
  unchanged existing profiles and defaults; dry-run/help expose real behavior.
- Ordered selection tests: every driver including Kimi/unknown; conflicting and
  explicit identity; missing binaries; exhausted first/second candidates; no
  eligible candidate; explicit pins. Execute fake-provider subprocesses to prove
  actual call order, exclusion, and successful write-back exactly once.
- Negative credit controls: quota-like prose/tool output must not trigger
  fallback; structured exhausted-allowance failure must trigger it. Prove
  auth/network/generic-rate-limit, dirty-target, timeout, stop, and finalization
  failures do not select another provider.
- Grok parser tests from sanitized real event shapes: session, final text,
  usage where present, error result, malformed/truncated/empty streams.
- Lifecycle integration tests across three adapters: timeout/stop then same-ID
  resume, defaults/override, stale handle, concurrent resume, missing history,
  mismatched ID, changed scope/profile/binary, and single append/commit.
- Live Grok review plus deliberate reasoned stop and resume with preserved
  conversation evidence. Record actual final model/effort and outcome. Fake CLI
  tests alone cannot mark provider integration Done.
- Dogfood implementation review under this session's Codex driver identity.
  Record actual provider outcome and selected reviewer without private billing
  details. If Claude availability changes, do not fabricate exhaustion; cover
  deterministic fallback with fixtures and explicitly smoke Grok as well.
- Run `python -m unittest discover -s structured-review/tests`, Scout regression
  tests, and compile checks matching CI. Inspect help output and live logs for
  normal, exhausted/empty, and recovery UX. Record provenance per criterion.

## Maintenance, rollback, and limitations

Protocol maintainers own backend order, identity markers, profile constants,
provider error classification, argv and stream schemas. Update constants, tests,
skill and current documentation together when CLI/model changes or live smoke
fails. Remove obsolete markers/error variants only with replacement evidence;
prefer one shared lifecycle and ordered registry over provider-specific copies.
Private transcripts/log retention belongs to the caller on the original
machine; no persistent provider-availability cache is introduced.

Rollback is a revert of this feature's code/docs commits; new Grok attempts then
cannot resume through the old runner. Do not rewrite private run fingerprints
or translate conversations between providers. Deployment, account funding,
provider authentication changes, merges, and consumer submodule bumps are out
of scope.

## Review Threads

I inspected the committed plan, the current runner and tests, and Grok Build 1.0.13 help. The review below is the full thread text for the runner to append.

### Reviewer pass 1 (impl-plan, grok reviewer)

Verified before judging: branch `feat/grok-review` at `85db1cd` (one commit ahead of `origin/main` `277edca`), worktree clean, plan committed, implementation not started. Read `docs/agent_plans/2026-09-07_grok_reviewer_plan.md`, `structured-review/scripts/claude_structured_review.py`, `structured-review/tests/test_claude_structured_review.py`, `structured-review/tests/test_recovery.py`, `structured-review/SKILL.md`, `structured-review/references/recovery.md`, `README.md`, `docs/CURRENT.md`, and `.github/workflows/ci.yml`. No local `.agent-protocols/` overlay. Compared the plan against the installed Grok Build 1.0.13 CLI help the plan cites. Human authorization for this Grok bootstrap review is taken as resolving gate 2; that path is not reopened here.

Human concern: add Grok as a third structured-review backend and change auto-selection so a driver can advance to the next eligible provider when the current one authoritatively reports exhausted allowance, without guessing routing, failure classes, or recovery.

#### Thread 1 — Blocking: credit-fallback classification has no pinned authoritative signal

The new policy is to advance only on an authoritative exhausted-allowance failure, and to stop on auth, permission, network, malformed output, generic rate limiting, timeout, interrupt, write-back, and unknown failures. That split is the whole fallback feature. The plan never names the signal an implementer must match.

Today every Claude `result` with `is_error` or `subtype != success`, and every Codex `turn.failed`, becomes a generic `protocol_error` in `run_claude`. There is no quota category, no adapter-owned classifier, and no reason-category field in metadata. The plan forbids using artifact text, tool output, model prose, or token estimates, which is the right negative rule, but it does not pin the positive rule: event type, field path, exit code, or sanitized envelope per provider.

Acceptance asks tests to prove “structured exhausted-allowance failure must trigger it” and that quota-like prose must not. Those tests cannot be written without inventing the structure. Guard Reach applies: fallback described as advancing when a provider “authoritatively reports” exhaustion is unverified until the sample it must catch is named. Claude and Codex already exist; this session’s bootstrap problem is exactly Claude allowance failure, yet that envelope is not recorded in sanitized form. Grok’s envelope is also unnamed.

What would resolve this:

1. For Claude, Codex, and Grok, pin the exhausted-allowance signal from observed CLI evidence (event type and fields, and/or exit code), as sanitized fixtures, or sequence a fail-closed capture step that forbids fallback until those fixtures exist.
2. Put classification on the backend adapter next to argv/parse/finalize/session extraction, so it does not become a third inline two-provider branch beside the current `result` / `turn.failed` checks.
3. Name the private reason-category values and the attempt outcome for exhausted attempts. Terminal non-resumable (`failed`, or a new non-resumable outcome) matches “terminal private evidence” and existing resume rejection of `failed`. Do not make exhaustion resumable, and do not treat it as success with empty review text.

Until that is in the plan body, an implementer can either miss real exhaustion (this gate fails closed forever) or advance on auth/rate-limit/generic errors (the stop list is violated).

#### Thread 2 — Blocking: Grok new/resume argv and session evidence are not implementable from the plan

The plan lists Grok Build 1.0.13 flags (`--resume` UUID, `--session-id`, `--prompt-file`, `--reasoning-effort`, permission controls, `streaming-messages-json`) as if they were a coherent recovery contract. Installed 1.0.13 help gives those flags opposite jobs. The last accepted recovery plan pinned exact Claude and Codex argv strings; this plan needs the same for Grok.

From Grok 1.0.13 help:

- `--session-id` sets a UUID for a **new** conversation. With `--resume`/`--continue` it is valid only with `--fork-session`, which creates a new session ID. It does not resume.
- `--resume` resumes by ID. Omitting the ID, or passing a title, can bind a different session. UUID-shaped values are IDs; the runner must pass the recorded UUID and must not omit it.
- `--continue` resumes the most recent session for the cwd, not the recorded ID.
- `--fork-session` changes the session ID. The current runner would then hit “backend did not resume the recorded session ID; fresh-session fallback refused”, or worse if the new ID is treated as success.
- `--restore-code` restores a repository snapshot on resume. That is out of scope and unsafe for a review.
- Grok’s own `--worktree` creates a git worktree. The runner already uses `--worktree` as the target-repo flag. Grok must not receive that flag.
- `streaming-messages-json` is Anthropic Messages API wire format. That format has no session UUID. Claude recovery keys on `session_id`; Codex on `thread.started` / `thread_id`. Session extraction is still an inline two-provider branch in `run_claude`, not on `ReviewerBackend`. If Grok’s chosen stream has no session field, capturing “observed persisted session evidence” requires a different mechanism, such as pre-assigning `--session-id` on the **new** attempt and resuming with `--resume <uuid>` only.
- Headless entrypoints are not pinned. `grok -p`/`--single`, `grok --prompt-file`, and `grok agent stdio` are different programs. Reviews must inspect local files with tools. “Single-turn” in Grok help is not yet shown to be a tool-using agent loop equivalent to `claude -p`.

“Verify actual stdout before settling stream parsing” is correct for parser details and does not replace an argv/session contract. Live stop/resume smoke remains required, as the plan already says.

What would resolve this: pin exact new-attempt argv and resume argv (flags, order, stdin vs private `--prompt-file` under the run-log directory, permission/sandbox flags, model/effort flags). State how session evidence is observed (named stream field vs runner-preassigned UUID). Explicitly forbid `--continue`, `--fork-session`, `--restore-code`, and Grok `--worktree`. Require the resumed backend to confirm the same UUID, matching the existing Claude/Codex guard. Move session extraction onto the adapter so Grok is not another `if backend ==` in `run_claude`.

#### Thread 3 — Blocking: auto identity and candidate construction are not a closed CLI contract

Goal and examples are clear at policy level: ordered Claude, then Codex, then Grok, excluding the current coding agent; missing binaries may be skipped; explicit pins do not fall back; unknown identities exclude none. Implementation still has to guess the public CLI and one same-agent hole.

Missing from the plan body:

1. The identity flag name and allowed values. This repo’s previous backend plan named `--reviewer-backend {auto,claude,codex}` before coding. Tests that require “every driver including Kimi/unknown; conflicting and explicit identity” cannot lock a flag the plan does not name, or a Kimi value (`kimi` vs `kimi-code` vs unknown).
2. Marker vs explicit precedence is partly stated (“explicit identity resolves inherited markers”; conflicting markers fail with identity guidance) but not as a table an implementer can code: env-only Claude/Codex, env-only Grok once verified, explicit identity with inherited foreign markers, both Claude and Codex markers with no identity, unknown with no markers.
3. Same-agent contradiction. The plan says never same-agent fallback, and also that unknown identities exclude none of the three providers. Grok detection is deferred until verified CLI evidence. Grok 1.0.13 help and `grok inspect` do not document a driver marker analogous to `CLAUDECODE` or `CODEX_THREAD_ID`. A Grok driver that omits the identity flag is therefore unknown, so auto tries Claude, then Codex, then Grok. That is same-agent review on the exact exhaustion path this feature adds. Either require Grok drivers to pass identity until markers are verified, or treat unmarked Grok as a named residual risk with a SKILL warning; do not leave both rules in force as if they compose.
4. Resume vs auto algorithm against the current code path. Today `config_from_args` calls `resolve_reviewer_backend` before `review_fingerprint`. Fingerprint stores the resolved backend, not `auto`. With fallback, a later `--reviewer-backend auto` resume would re-resolve and could pick a different provider if Claude allowance returned, then fail the fingerprint or, if someone short-circuits the fingerprint, silently start a new provider conversation. The plan’s “load the latest attempt’s original backend before auto selection, never fall back” is the right rule; write the algorithm: resume does not re-enter the candidate loop; `auto` is compatible with the recorded backend; an explicit `--reviewer-backend` or identity that disagrees with the recorded attempt is rejected; timeout may change; binary/model/effort/scope/prompt/runner still fingerprint.

Also record the SKILL change this policy requires: current text fails closed when an auto-selected binary is missing. The plan’s skip-and-advance rule is an accepted behavior change if SKILL, README, and `docs/CURRENT.md` are updated in the same change, and if tests replace `test_auto_marker_resolved_missing_binary_errors` with skip-to-next plus recorded reason. Explicit pins must still fail, not skip.

What would resolve this: name the identity flag and values; publish the exclusion table; close the unmarked-Grok same-agent hole; pin resume+auto as “recorded backend, no candidate loop.”

#### Thread 4 — Non-blocking: Grok’s hard/normal split is effort-only

The shared-model exception to `require_hard_profile_model_has_hard_tier` is necessary. As written, that guard compares the selected model to the backend’s hard model; `grok-4.6` for both tiers would make every normal Grok run look like a forbidden hard-model override. Keep that exception.

Residual: Claude/Codex hard vs normal is a model change at the same `xhigh` effort. Grok hard vs normal is `medium` vs `xhigh` on one model. `--grok-effort xhigh` with `--review-tier normal` would likely be allowed, because the existing guard is model-only and the skill text blocks the pinned hard *model*, not effort. That matches Claude/Codex override behavior. Confirm in the plan that this is accepted, or add an effort guard. Do not block implementation on that choice.

Official reasoning-effort values for `grok-4.6` do include `medium` and `xhigh`. Unset Grok effort defaults to `high`, so argv tests must assert the runner always passes the profile effort.

#### Thread 5 — Non-blocking: record the bootstrap authorization in the plan body

Gate 2 still tells the next agent to stop and agree a bootstrap path if Claude has no allowance. The human already authorized this direct Grok plan review. After this pass, update that paragraph so implementation does not re-open a settled question. Not blocking.

Minor follow-through, not separate threads: add this plan to `docs/agent_plans/README.md` Current Records during the doc pass already in scope; `active_model` / `unused_profile_override_flags` / `RunConfig` still have two-provider branches that the adapter/registry work must absorb when Grok fields are added.

#### Overall judgment

Not ready for implementation. Goal, non-goals, rollback, file list, and the fake-subprocess plus live-smoke acceptance split are strong. The current runner diagnosis is accurate: backend registry and process-group lifecycle are shared, but profile selection, session parsing, CLI flags, binary resolution, and `resolve_reviewer_backend` are two-provider and fail closed with no fallback.

Three blocking gaps would force the implementing agent to guess the shared routing and recovery contract: the exhaustion classifier, Grok new/resume argv and session evidence, and the identity/auto/resume selection algorithm including the unmarked-Grok same-agent hole. Resolve those in the plan body and re-review that diff. Do not start runner changes against the current text.

#### Residual risks and validation gaps

- Live Grok stream shape, permission/sandbox behavior, and whether `-p`/`--prompt-file` is a tool-using agent remain residual even after argv is pinned; the plan already says fake CLIs cannot mark provider integration Done. Keep that.
- Fallback attempts must stay separate conversations and must write back at most once. The listed subprocess tests are the right check once candidate order and classification are specified.
- No persistent availability cache is the right non-goal. A successful review is not a remaining-credit reading; do not let metadata imply otherwise.
- CI commands in the plan match `.github/workflows/ci.yml` (`unittest discover` for `structured-review/tests` and `scout/tests`, plus compile). That part of acceptance is executable.

There are blocking issues. The artifact is not ready for implementation until threads 1–3 are resolved in the plan body.

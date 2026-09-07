# Grok reviewer and ordered availability policy

Status: active implementation record; plan review passed, implementation validation
and dogfood review in progress.

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

Human follow-up decisions: do not ask permission to try another available
reviewer or repeat plan reviews. Escalate reviewer availability only when all
three backends are unavailable or excluded by the same-agent policy. Keep other
scope/safety decisions distinct from availability. Implementation Review must
dogfood this branch's updated runner and real Grok, not substitute mock results.

Normal is the default. Reserve hard for roughly the hardest 20% of the agent's
tasks: major design, major architecture, or unusually difficult bugs. This is
a judgment aid, not a numerical quota. Require a concrete semantic reason;
routine protocol edits, artifact length/count, review type, keywords, or a
mechanical recommendation alone do not qualify. Update skill, CLI help, prompt,
README, CURRENT and closeout tier guidance consistently. Existing hard model,
effort and timeout profiles remain unchanged. Subsequent reviews of this change
use normal unless actual new difficulty justifies hard; the first pass's hard
configuration remains historical evidence.

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
2. Plan review: the existing checkout runner was invoked first; the human then
   authorized direct Grok bootstrap reviews using the checkout's prompt builder
   and append operation. This is settled authorization for as many plan review
   passes as needed. Resolve blocking threads before implementation. Never label
   a failed provider call a passed review. Later gates use the implemented runner.
3. Implementation: implement the accepted plan and tests only after plan review.
4. Implementation review: dogfood automatic routing through the updated runner,
   resolve findings and re-review required fixes.
5. Closeout: verify traceability, documentation lifecycle, safety and git state;
   hand off the feature for human merge without merging it.

## Implementation design

### Provider adapter and profile

Pin Grok argv to `grok --model MODEL --reasoning-effort EFFORT
--permission-mode plan --no-subagents --output-format streaming-messages-json
--prompt-file PRIVATE_ATTEMPT/prompt.md`; resume adds only `--resume UUID`.
The common runner writes the complete prompt file before spawning. Grok does
not consume the runner's stdin prompt. Do not pass `--session-id`, `--continue`,
`--fork-session`, `--restore-code`, or Grok's `--worktree`. The provider generates
the new UUID; the runner observes `session_id` on `system` and `result` events.
This exact entrypoint performed local reads and terminal commands in bootstrap
pass 1, emitted `system/init` with a UUID and model `grok-4.6`, and emitted
`result/subtype=success/is_error=false/result=<review>/session_id=<same UUID>`.
Usage is in final `usage`. This is observed CLI behavior, not inferred solely
from the Anthropic wire format. The result must have `stop_reason=end_turn`,
nonempty text and an observed consistent UUID; missing/truncated/error results
fail. Resume must confirm that same UUID. Adapter callbacks own session and
error extraction for all backends. Plan permission mode supports the observed
read-only review flow; any test execution limitations are reported, and the
common untouched-worktree check remains mandatory.

Register Grok with its own binary, argv, output parser, final-result extraction,
session event extraction, and version retrieval. Add `--grok-bin`,
`--grok-model`, `--grok-effort`; allow `--reviewer-backend grok`. Selected-provider
overrides apply only to that provider, including after fallback; ignored flags
warn. Both Grok tiers share a model, so the existing hard-model-only guard must
apply only when normal and hard models differ. Hard still requires a reason.
Explicit effort exceptions remain allowed (including normal plus Grok xhigh),
with source provenance; drivers must not use overrides to evade tier guidance.

Use headless Grok with explicit model/effort, persisted conversation, and review
permissions. Verify actual stdout before settling stream parsing. Use a private
prompt file if Grok cannot accept the current stdin contract. Reviewers return
text; the runner alone validates and appends/commits. Invalid/error/empty output
cannot be treated as a successful review. Preserve common cleanup and mutation
checks. Verify permission behavior and process ownership in the live smoke.

### Ordered selection and credit evidence

Public identity flag: `--coding-agent NAME`, accepting a nonempty normalized
lowercase name. `claude`, `codex`, `grok` exclude that backend; `kimicode` and
other names exclude none. Explicit identity wins over inherited markers.
Without it, CLAUDECODE means claude, CODEX_THREAD_ID or CODEX_SANDBOX means
codex, both families conflict, and neither means unknown. Grok has no verified
marker: its drivers MUST pass `--coding-agent grok`; all new repo-backed callers
should pass their known identity. Unknown cannot promise same-agent exclusion
and emits a warning. Explicit pins preserve intentional override behavior and
never fall back. No marker guesses are introduced.

Adapter classifiers return `credit_exhausted` only for pinned error envelopes:

- Claude: observed `type=result`, `is_error=true`, string `result` beginning
  `You've hit your weekly limit` followed by the CLI reset separator. Match a
  sanitized reset suffix, never a real account/reset value. An ordinary
  assistant message or successful result with identical text is not evidence.
- Codex: `type=turn.failed`, `error.message` beginning the upstream rendered
  `You've hit your usage limit.` or `You've hit your usage limit for `; exact
  `Quota exceeded. Check your plan and billing details.` is also supported.
  Source: upstream `codex-rs/protocol/src/error.rs` UsageLimitReachedError and
  QuotaExceeded, read 2026-09-07. Store sanitized synthetic fixtures with that
  provenance; they are source-backed, not a claim of live Codex exhaustion.
- Grok: no exhausted-allowance error fixture has been observed. Fail closed as
  `provider_error` until such evidence exists; it is the last candidate so no
  further automatic fallback depends on classifying its credit error. Do not
  invent Grok quota fields. A live success proves availability only.

`credit_exhausted` is persisted as reason category with terminal outcome
`failed`; `binary_unavailable` is a selection skip reason; other provider
failures use `provider_error`. Record attempted/skipped backends and reasons,
plus predecessor/successor private attempt paths. No raw billing text in git.
Binary skips are printed and retained in selection provenance. Every credit
attempt owns a separate recovery chain; the original `--run-log-dir` may hold
subdirectories for subsequent candidate chains with printed exact handles.

Non-quota failures stop the automatic candidate loop. The driver investigates
and may start a fresh review on the next eligible backend without asking a
human, after confirming cleanup and unchanged target. Timeout/stop should use
same-session recovery first. Do not retry mutation/finalization failures until
the target is repaired and verified. This distinguishes the mechanical credit
policy from the user's no-per-provider-permission workflow.

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

Resolve `--resume-run` metadata before candidate construction: auto selects the
recorded backend, explicit backend must agree, and resolved coding identity
must match the original. Do not enter the candidate loop. Keep all original
scope/profile/binary/runner fingerprint checks and allow only timeout changes.
Keep the resolved coding identity in new fingerprints; preserve legacy
fingerprint compatibility only where absent fields are semantically unchanged,
or explicitly reject legacy handles rather than weakening validation.

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

## Implementation evidence

Plan gate: Grok reviewer pass 2 closed all five threads and returned ready for
implementation. Driver accepted that result before editing executable code.

Implementation adds Grok adapter callbacks, profile/identity parameters,
ordered fresh-provider selection, private selection provenance, and fixed
backend/identity resume. Grok final results require an observed UUID and complete
successful end-turn result. Existing Claude/Codex invocation modes remain.
Protocol text now requires normal by default, rare-hard agent judgment, and no
per-provider availability permission questions.

Driver-reported checks already run: baseline 107 reviewer tests; 31 Scout
tests; backlog schema checker and 18 checker tests; compile checks and rendered
CLI help. Expanded reviewer suite: 120 tests passed in 65.128 seconds with
`python3 -m unittest discover -s structured-review/tests` (driver-reported).

| Acceptance | State | Evidence / remaining verification |
| --- | --- | --- |
| Grok profiles, overrides, defaults and CLI | Done | `test_grok_profiles_argv_help_and_override`, three-backend recovery profile matrix, rendered `--help` |
| Identity/order/exclusion, missing binaries and pins | Done | `test_every_driver_exclusion_order`, Kimi, identity, missing-binary and explicit-pin subprocess tests |
| Credit positive/negative controls and single write | Done | Fallback/provenance test; quota-like prose/tool controls; auth/network/rate/dirty/moved/malformed/finalization negatives |
| Grok output/session validation | Done | `test_grok_incomplete_error_and_malformed_results_never_write`; sanitized observed init/result shape |
| Fake CLI three-backend recovery and guards | Done | Expanded `test_recovery.py`; auto Grok resume after Claude recovers; Grok stop/profile-change guards |
| Real updated-runner Grok dogfood and resume | Done | Driver-reported live run on `1d78679`: automatic selection reached Grok, stop cleaned the process group without target changes, resume confirmed the same UUID, final outcome success and exactly one review commit `d12ce52` |
| Documentation and hard/availability policy | Done | Skill, help, prompt, root/current/recovery/closeout guidance and plan index updated |
| Implementation Review / closeout | Partial | Real dogfood review and final handoff remain |

Real dogfood/recovery must be completed and recorded before closeout. No mock
result substitutes for a live review gate.

Live integration evidence (driver-reported, with reviewer corroboration in
implementation pass 1): selected normal / `grok-4.6` / `medium`. The initial Grok
attempt stopped after completed reads, with cleanup verified and no write-back.
The resumed attempt confirmed the original UUID and finished successfully;
metadata showed clean `1d78679` before and clean `d12ce52` after. Private
conversation export contained pre-stop reads followed by the continuation
instruction. Reviewer independently reran 13 Grok selection tests and returned
ready for closeout. Raw provider responses, session IDs, and transcripts remain
private and are not committed.

Before final handoff the driver reproduced and fixed one additional parameter
edge: an absent Claude binary must be skipped before validating its model
override. Eligible providers still enforce the hard-only model guard. The
reviewer's obsolete-selection-helper cleanup was accepted, and generic provider
failure metadata and the recovery example were made consistent. These small
changes receive a fresh real Grok implementation re-review after regression.

Post-review regression: 119 reviewer tests passed in 63.695 seconds
(driver-reported). Count changed from 120 because two obsolete helper tests
were removed and one production override-selection regression was added.

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

### Driver response 1 (Codex)

- Thread 1 accepted: pin error envelope classifiers and reason categories in
  the body. Claude uses observed CLI evidence, Codex uses upstream error source;
  Grok unknown errors fail closed rather than fabricating a quota signature.
- Thread 2 accepted for exact argv and adapter ownership. The premise that the
  selected stream lacks UUIDs is rejected by this real bootstrap run: both
  system init and final result carried the same UUID. The body records the
  actual event shape, prompt-file tool loop, plan permissions, forbidden flags,
  final-result requirement, and live resume acceptance still to execute.
- Thread 3 accepted: name `--coding-agent`, pin explicit/environment precedence,
  require Grok drivers to identify themselves, and resolve resume metadata before
  any auto candidate construction. Unknown identity warns about exclusion limits.
- Thread 4 accepted: effort overrides retain existing exception semantics and
  explicit provenance; docs prohibit evading the rare-hard guidance via overrides.
- Thread 5 accepted: the bootstrap authorization is recorded and settled.
- Human follow-ups added: no per-provider availability permission requests;
  roughly top-20%-difficulty hard guidance; actual updated-runner implementation
  dogfood mandatory. These are human decisions, not reviewer suggestions.

Validation provenance: driver-reported baseline 107 tests passed; Grok pass 1
was a real tool-using review with successful terminal result. Real runner Grok
recovery and ordered fallback remain planned, not claimed complete. Request
reviewer resolution of threads 1–3 and review of the human-directed additions.

### Reviewer pass 2 (impl-plan, grok reviewer)

Verified before judging: branch `feat/grok-review` at `454e3ee`, worktree clean, implementation not started. Inspected `git diff bb2e470 454e3ee -- docs/agent_plans/2026-09-07_grok_reviewer_plan.md` and Driver response 1 first, then the updated Goal, Five gates, Provider adapter, Ordered selection, Recovery, and Acceptance sections. Compared those pins against the current runner's argv, session extraction, fingerprint, hard-model guard, and missing-binary fail-closed path, plus installed Grok help for `--permission-mode plan` and `--prompt-file`. No local `.agent-protocols/` overlay.

Human concern: close the three blocking routing/recovery gaps, then confirm the human policy additions (no per-provider permission, rare hard for about the hardest 20 percent of tasks, real updated-runner Grok dogfood) are implementable without guessing.

#### Thread 1 — Blocking: credit-fallback classification has no pinned authoritative signal

Resolved. Artifact body updated in Ordered selection and credit evidence.

Claude is pinned to an observed `type=result` / `is_error=true` envelope whose string `result` begins `You've hit your weekly limit`, with sanitized reset-suffix fixtures and an explicit rule that a successful or ordinary assistant copy of the same text is not evidence. Codex is pinned to `type=turn.failed` / `error.message` prefixes from upstream `codex-rs/protocol/src/error.rs` (`You've hit your usage limit.` / `You've hit your usage limit for `) plus exact `Quota exceeded. Check your plan and billing details.`, with source-backed sanitized fixtures allowed and no live-account-exhaustion requirement. Grok unknown errors fail closed as `provider_error`. Reason categories are named: `credit_exhausted` with terminal `failed`, `binary_unavailable` as a skip, other failures as `provider_error`. Classification belongs on adapter callbacks. That is enough to write the negative and positive credit tests without inventing envelopes.

#### Thread 2 — Blocking: Grok new/resume argv and session evidence are not implementable from the plan

Resolved. Artifact body updated in Provider adapter and profile.

New-attempt argv is exact: `grok --model MODEL --reasoning-effort EFFORT --permission-mode plan --no-subagents --output-format streaming-messages-json --prompt-file PRIVATE_ATTEMPT/prompt.md`. Resume adds only `--resume UUID`. Forbidden flags are named. Session evidence is observed `session_id` on `system` and `result`, with the same UUID required on resume. The bootstrap observation (tool-using prompt-file loop, `system/init` UUID, successful `result` with the same UUID) supersedes the pass-1 premise that this stream has no session field. Adapter callbacks own session and error extraction. Live stop/resume remains an acceptance item, not a missing argv contract.

#### Thread 3 — Blocking: auto identity and candidate construction are not a closed CLI contract

Resolved. Artifact body updated in Ordered selection and Recovery.

Public flag is `--coding-agent NAME` (nonempty normalized lowercase). `claude` / `codex` / `grok` exclude that backend; `kimicode` and other names exclude none. Explicit identity wins inherited markers; env-only Claude/Codex markers and both-families conflict are unchanged; Grok has no verified marker and its drivers must pass `--coding-agent grok`. Unknown warns and cannot promise same-agent exclusion. Resume resolves metadata before candidate construction: `auto` keeps the recorded backend, explicit backend/identity disagreement is rejected, and the candidate loop is not entered. Missing binaries may be skipped with a recorded reason; explicit pins still do not fall back. SKILL/README/`docs/CURRENT.md` remain in the same-change file list for that behavior change.

#### Thread 4 — Non-blocking: Grok’s hard/normal split is effort-only

Resolved. Artifact body updated in Provider adapter and Goal.

The shared-model hard-model guard exception stays. Explicit effort overrides remain allowed, including normal plus Grok `xhigh`, with provenance. Docs must say drivers must not use those overrides to evade the rare-hard guidance. Profiles are unchanged.

#### Thread 5 — Non-blocking: record the bootstrap authorization in the plan body

Resolved. Artifact body updated in Five gates.

Direct Grok bootstrap via the checkout prompt builder and append path is settled authorization for remaining plan-review passes. Later gates use the implemented runner. This is not reopened.

#### Blocking issues

None.

#### Non-blocking issues

None that should delay implementation. Treat the pinned argv/session/classifier paragraphs as source of truth if they overlap older discovery hedges in the same sections (stdin vs prompt-file is already decided: write the private prompt file; Grok does not consume the runner stdin prompt). Adding this plan to `docs/agent_plans/README.md` Current Records remains in-scope documentation follow-through from pass 1.

#### Overall judgment

Ready for implementation.

Threads 1–3 are closed by body pins, not by driver assertion alone. Human additions are in the Goal and gates and do not reopen those contracts:

- No per-provider permission is a driver/SKILL workflow rule, distinct from the runner’s automatic `credit_exhausted` candidate loop. Non-quota failures still stop that loop; the driver may start a fresh review on the next eligible backend without asking, after cleanup and an unchanged target. Escalate availability only when every backend is unavailable or excluded by same-agent policy.
- Rare hard is a judgment aid for roughly the hardest 20 percent of tasks (major design, major architecture, unusually difficult bugs), not a quota and not a runner-enforced count. Mechanical signals, artifact length/count, review type, and keywords still do not qualify. Skill, CLI help, prompt, README, `docs/CURRENT.md`, and closeout tier guidance update in the same change; existing hard model/effort/timeout profiles stay. Subsequent reviews of this change stay on normal unless new semantic difficulty appears.
- Implementation Review must dogfood this branch’s updated runner and a real Grok call. Automatic Codex-driver routing may still land on Claude if Claude is actually available; do not fabricate exhaustion. Deterministic fallback stays on fixtures, and Grok must still be smoked for real.

An implementing agent can code adapters, identity, ordered selection, fingerprints, and tests from this body without inventing CLI contracts.

#### Residual risks and validation gaps

- Live Grok stop/resume through the implemented runner is still unexecuted. Fake CLIs cannot mark provider integration Done. Keep that acceptance row.
- Grok credit classification remains fail-closed until an exhausted-allowance envelope is observed. That is accepted, not a gap to fill with invented fields.
- Common spawn currently writes the review prompt on stdin. Grok’s prompt channel is the private file; close or omit that stdin prompt rather than dual-feeding. Live smoke is the check.
- A successful review still proves current usability only, not remaining credit. No availability cache.
- Fallback chains must stay separate conversations, print exact successor handles, and write back exactly once. The planned fake-provider subprocess tests remain the right guard.

There are no blocking issues. The artifact is ready for implementation.

Verified before judging: branch `feat/grok-review` at `1d78679` (five commits ahead of `origin/main` `277edca`), worktree clean, no local `.agent-protocols/` overlay. Inspected `git diff origin/main` for the runner, `structured-review/tests/test_grok_selection.py`, `structured-review/tests/test_recovery.py`, `structured-review/tests/test_claude_structured_review.py`, `structured-review/SKILL.md`, `structured-review/references/recovery.md`, `README.md`, `docs/CURRENT.md`, `closeout/SKILL.md`, and `docs/agent_plans/README.md`. Compared that diff item-by-item to the accepted plan body after reviewer pass 2. Independently re-ran `python3 -m unittest discover -s structured-review/tests -p 'test_grok_selection.py'` (13 tests, OK). Scout, backlog, and unrelated checker paths were not in the feature diff. This live Grok session already carried the runner continuation prefix after an interrupted attempt.

Human concern: add Grok as the third reviewer backend with ordered Claude then Codex then Grok selection, authoritative exhausted-allowance fallback, same-session recovery, append-once write-back, no per-provider permission questions, and rare-hard guidance, then dogfood the updated runner with a real Grok implementation review.

### Reviewer pass 1 (impl, grok reviewer)

#### Blocking issues

None.

#### Thread 1 — Non-blocking: leftover `resolve_reviewer_backend` still pins the retired two-provider mapping

Live selection is `coding_identity` plus `BACKEND_ORDER` in `run()`, and resume never re-enters that loop. That matches the accepted plan: Claude then Codex then Grok, skip missing binaries, fall back only on pinned `credit_exhausted`, exclude `--coding-agent`, and keep explicit pins from falling back.

`resolve_reviewer_backend` is no longer called from `config_from_args` or `run()`, but it still implements the old mapping (Claude marker -> Codex reviewer, Codex marker -> Claude, neither -> Claude). `test_resolve_reviewer_backend_cross_vendor_auto` and `test_resolve_reviewer_backend_both_markers_error` keep that unused helper green. The live contract is covered by `test_grok_selection.py`, which I re-ran.

This does not change current behavior. It is leftover two-provider surface area: a later edit could wire the helper back in and silently restore the old auto rule. Prefer deleting the helper and those two tests, or turning them into assertions that production selection does not call it.

Not blocking for closeout.

#### Traceability against the accepted plan

| Acceptance item | State | Evidence |
| --- | --- | --- |
| Grok profiles, overrides, defaults, CLI | Done | `REVIEW_MODEL_MATRIX` pins `grok-4.6` at `medium`/`xhigh` and 1800/3600s; `grok_argv` matches the accepted new/resume argv; shared-model hard-model guard is skipped when normal and hard models are equal; `--help` includes `--coding-agent` and the hardest-20% text. Covered by `test_grok_profiles_argv_help_and_override`. |
| Identity, order, exclusion, missing binaries, pins | Done | Explicit identity wins; env Claude/Codex markers and conflict remain; unknown warns; Grok has no driver markers. `run()` skips `coding_agent_excluded` and `binary_unavailable`, attempts each eligible backend once, and explicit pins raise `CreditExhausted` without a second call. Covered by `test_every_driver_exclusion_order`, `test_kimi_selects_available_codex`, `test_missing_binary_skip_and_all_missing`, `test_pins_never_fall_back`. |
| Credit positive/negative controls and single write | Done | Adapter classifiers: Claude weekly-limit `result` with `is_error=true`; Codex `turn.failed` usage-limit/quota envelopes; Grok fail-closed as `provider_error`. Prose/tool copies, auth/network/generic rate limit, dirty/moved HEAD, malformed credit, and write-back failure do not select another provider. Fallback writes exactly one review commit. Re-ran those tests in this session. |
| Grok output/session validation | Done | Final Grok result requires `end_turn`, nonempty text, and a consistent UUID; missing/truncated/malformed/empty/`max_turns`/error paths do not write. `prompt_on_stdin=False` and tests assert empty stdin plus `--prompt-file`. Forbidden `--session-id`/`--restore-code` asserted in the fake CLI. |
| Fake three-backend recovery and guards | Done | Timeout/stop then same-ID resume, stale handle, concurrent resume, missing/mismatched session, changed scope/profile/binary/identity/backend, and single append remain in `test_recovery.py` and `test_auto_resume_keeps_grok_when_claude_recovers_and_rejects_changes` / `test_grok_stop_then_same_session_resume_and_profile_guard`. Resume fingerprint includes `coding_agent`; timeout is not fingerprinted. |
| Documentation and hard/availability policy | Done | Skill, prompt, CLI help, `README.md`, `docs/CURRENT.md`, `closeout/SKILL.md`, `structured-review/references/recovery.md`, and `docs/agent_plans/README.md` Current Records all state ordered fallback without per-provider permission, rare-hard judgment, and Grok 4.6 medium/xhigh. |
| Real updated-runner Grok dogfood and resume | Partial, in progress on this gate | This review is a live Grok `impl` pass through the updated runner. The session already received the same-conversation continuation prefix after an interrupt, which is the recovery contract. Closeout still needs the driver to record the actual stop/resume outcome and selected model/effort. Fake CLI tests cannot close that row by themselves. |

Scout’s independent provider policy and `docs/backlog.yml` were not changed.

#### Overall judgment

Ready for closeout.

The committed runner implements the accepted selection, classifier, recovery, append-once, and documentation contracts without requiring the next agent to guess argv, identity, or fallback rules. Subsequent reviews of this change should stay on `normal` unless new semantic difficulty appears; the mechanical hard recommendation on this artifact (length, two artifacts, keyword signals) does not change readiness.

Do not treat this pass as merge authorization. Closeout still owns final git/CI/handoff rechecks and must record the live stop/resume result in the evidence table.

#### Residual risks and validation gaps

- Grok exhausted-allowance classification remains fail-closed until a real envelope is observed. That is the accepted policy, not a defect.
- Full `python3 -m unittest discover -s structured-review/tests` (driver-reported 120), Scout (31), and checker (18) were not re-run in this session. I independently re-ran the 13 Grok selection tests, including the fallback, negative-credit, append-once, and stop/resume cases that this review is supposed to stress.
- Live stop/resume integration: plan-mode Grok in this session could read the worktree and run the selection tests. Resume restored the original scope and asked for one complete review rather than a delta. The in-band skill copy was truncated and offloaded both before and after resume; the runner-written private prompt file remains the full source of truth. Driver must resume the latest attempt directory printed at launch, poll `metadata.json` to a terminal outcome, and must not treat a stopped attempt as a passed gate. A stop during finalization/write-back is still not resumable; inspect an uncommitted thread append before a fresh review.
- No persistent availability cache was added. A successful Grok review proves current usability, not remaining credit.

There are no blocking issues.

### Driver response 2 (implementation, Codex)

- Grok implementation Thread 1 accepted: remove the unused two-provider helper
  and its two tests; production identity/order tests remain authoritative.
- Driver-found parameter bug accepted: skip unavailable binaries before applying
  their profile overrides. Add a positive skip case and a negative eligible-
  provider hard-only-model guard to prevent accidental weakening.
- Driver consistency follow-through: classify incomplete/nonzero provider
  results as provider_error and make the recovery example normal by default.
- Live dogfood acceptance is now Done with actual terminal success and one
  review commit, as recorded in the body. Same UUID was observed on resume and
  pre-stop history persisted. No source/model-run transcripts enter git.

Request Grok resolution of implementation Thread 1 and review of the focused
post-review changes. Human policy and accepted scope are unchanged.

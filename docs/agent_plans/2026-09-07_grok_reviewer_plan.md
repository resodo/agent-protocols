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

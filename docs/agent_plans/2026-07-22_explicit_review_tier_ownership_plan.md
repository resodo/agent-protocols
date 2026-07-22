# Explicit Review Tier Ownership Plan

Status: implementation and review artifact for shared protocol PR #27
Source branch: `feature/explicit-review-tier`

## Context

The structured-review runner currently treats review type, artifact length,
artifact count, and keyword matches as authority to select `hard`. That can
route an ordinary review from the normal Claude profile
(`claude-opus-4-8` / `xhigh`) to the hard Claude profile
(`claude-fable-5` / `xhigh`) without a driver decision or rationale.

The observed downstream failure was a routine Closeout Review that selected
Fable solely because its type was `closeout-review`, exhausted the available
provider spend, and produced no usable review. The responsibility boundary is
therefore the defect: the runner may surface mechanical signals, but the driver
that owns task context must own the tier decision.

## Human Decisions

1. The driver owns review tier selection.
2. Normal reviews use Opus by default; hard reviews use Fable only after an
   explicit driver choice with a concrete rationale.
3. Closeout type, artifact count, body length, and keywords must never change
   the selected tier or model.
4. Runner signals may produce a recommendation, but normal and hard use the
   same quality gate and scope.
5. Plan Review and Implementation Review for this change use Claude Opus 4.8
   at `xhigh`; Fable is not authorized for this change.
6. The shared protocol change lands through a PR and is not merged without
   named, current-turn human authorization. Downstream synchronization uses
   the existing repository-dispatch/submodule-bump workflow.

## Goal

Separate driver selection from runner recommendation so an explicit tier is
the only normal path to a tiered model profile, while preserving a safe
compatibility window for callers that still omit `--review-tier`.

## Non-Goals

- Do not change cross-vendor backend auto-selection.
- Do not add a policy engine, model preflight call, or new review scope.
- Do not change reviewer write/commit verification, sandboxing, streaming,
  timeout enforcement, or provider authentication.
- Do not edit downstream vendored submodule contents.
- Do not rewrite the historical 2026-07-20 plan.

## Design

### 1. Driver-owned selection with a safe compatibility window

Keep `--review-tier {auto,normal,hard}` for one compatibility window, but make
the protocol require new repo-backed calls to pass `normal` or `hard`:

- explicit `normal` selects the normal profile;
- explicit `hard` selects the hard profile and requires a non-empty
  `--tier-reason`;
- omitted tier or explicit `auto` selects `normal`, emits a deprecation
  warning, and never changes model from runner signals;
- `--tier-reason` is rejected for `normal` and `auto`; it is valid only with
  explicit `hard`, where whitespace is stripped and the remaining value must
  be non-empty.

This staged behavior prevents existing callers from failing all at once while
also removing the paid-model hazard immediately. Removing `auto` or making an
omitted tier fail closed is a later reviewed change after downstream callers
have migrated.

The existing provider override flags remain available. The pinned hard-profile
models (`claude-fable-5` and `gpt-5.6-sol`) cannot be selected through a normal
or auto tier override; callers must select `hard` and provide the reason.
This check applies only to the selected backend: the Claude hard slug is
guarded for a Claude review and the Codex hard slug for a Codex review.
Explicit hard plus a reason plus a redundant override to that backend's pinned
hard model remains valid. Other explicit custom model/effort overrides retain
their existing provenance. The SKILL and README override paragraphs will state
this carve-out directly.

### 2. Recommendation is observational only

Retain the current deterministic checks, including Review Threads exclusion
and UTF-8 artifact validation, but move them into recommendation calculation:

- `recommended_tier` is `hard` when any existing type, size, multi-artifact,
  or named complexity signal is present; otherwise it is `normal`;
- `recommendation_reasons` records the matching signals;
- the recommendation never mutates `selected_tier`, profile, timeout, scope,
  or readiness standard;
- a hard recommendation with a normal selection is visible in stderr, prompt,
  and metadata without blocking the driver choice.

### 3. Selection and provenance schema

Replace the ambiguous internal tier fields with:

- `selected_tier`;
- `tier_selection_source`: `explicit-driver` or
  `legacy-auto-compatibility`;
- `driver_tier_reason`;
- `recommended_tier`;
- `recommendation_reasons`.

Prompt provenance and the start log show all five fields plus final model,
effort, and their existing sources. Metadata adds the same five fields.

For compatibility, metadata retains `review_tier` as an alias of
`selected_tier` and `review_tier_reasons` as selection provenance only. It no
longer stores recommendation signals under a selection-named key. These alias
keys are documented as deprecated; no versioned metadata consumer exists in
this repo, so an additive schema change is sufficient. The legacy reasons are
deterministic:

- explicit normal: `["explicit --review-tier normal"]`;
- explicit hard: `["explicit --review-tier hard", "driver tier reason: <reason>"]`;
- omitted or explicit auto: `["legacy --review-tier auto compatibility selected normal"]`.

### 4. CLI and documentation contract

Add `--tier-reason` and useful `--help` text. Update:

- `structured-review/SKILL.md` to require explicit driver selection, explain
  hard rationale examples, preserve the profile matrix, and make equal quality
  gates explicit;
- `closeout/SKILL.md` to remove the automatic-hard claim and state that
  Closeout Review type alone does not justify hard;
- `README.md` examples and runner summary to pass explicit `normal` and explain
  legacy `auto` behavior;
- `docs/CURRENT.md` and the agent-plan index to identify the active contract.

`agent-readiness/agents-bootstrap-template.md` and
`agent-readiness/worktree-guard.md` were checked and contain no review-tier CLI
or model-routing guidance, so they require no content change. This repo has no
separate changelog or release-note convention; this reviewed plan, PR, and
current-map update are the durable change record.

### 5. Tests to replace or add

Delete or rewrite tests that assert auto selection changes the tier:

- Closeout Review auto-hard;
- greater-than-1,000-lines auto-hard;
- multi-artifact implementation auto-hard;
- keyword auto-hard;
- default auto selection provenance.

Replace them with tests that assert those inputs can recommend hard while the
selected tier and model stay normal. Add coverage for:

- explicit normal -> Opus;
- explicit hard plus reason -> Fable;
- hard without a reason -> fail closed;
- whitespace-only hard reason -> fail closed;
- reason supplied with normal or auto -> fail closed;
- pinned hard-profile model override without explicit hard/reason -> fail;
- explicit hard plus reason plus the same pinned hard-model override -> pass;
- `auto` compatibility warning and no auto-upgrade;
- selection, rationale, recommendation, final model, and source in prompt and
  metadata;
- rewrite `test_prompt_records_tier_profile_and_sources` for the expanded
  selection/recommendation block;
- rewrite the Codex metadata assertions in
  `test_run_codex_prefers_last_message_file_and_records_metadata` for the new
  fields and exact legacy aliases;
- CLI help and protocol/closeout prose consistency;
- exact 2x2 profile matrix and all unaffected runner behavior.

### 6. Rollout

Open a shared protocol PR from this branch. Do not merge it. After a human
merges the PR, the existing push-to-`main` repository dispatch will ask
`skynet-intern` to bump its `external/agent-protocols` submodule to the merged
default-branch commit.

Downstream drivers should update every formal runner call to pass:

```text
--review-tier normal
```

or, only for a genuinely difficult review:

```text
--review-tier hard --tier-reason "<specific semantic difficulty>"
```

The downstream bump PR should verify mounts, update local call sites, run its
guard/tests, and point to the final shared `main` commit rather than this
feature-branch commit.

## Files Expected To Change

- `structured-review/scripts/claude_structured_review.py`
- `structured-review/tests/test_claude_structured_review.py`
- `structured-review/SKILL.md`
- `closeout/SKILL.md`
- `README.md`
- `docs/CURRENT.md`
- `docs/agent_plans/README.md`
- this plan and a closeout evidence artifact

## Validation

Driver-run commands:

```bash
python -m unittest discover -s structured-review/tests -p 'test_*.py' -v
python -m unittest discover -s scout/tests -p 'test_*.py' -v
python -m unittest discover -s tests -p 'test_*.py' -v
python -m compileall -q structured-review scout scripts tests
python scripts/check_backlog.py
python structured-review/scripts/claude_structured_review.py --help
git diff --check
```

Also run dry-run CLI cases for explicit normal, explicit hard with reason,
legacy auto with a hard recommendation, and hard-without-reason failure. Unit
tests remain authoritative for exact prompt and metadata fields.

## Review Gates

1. Plan Review: bundled runner, `write-commit-to-plan`, `Type: impl-plan`,
   explicitly Claude `claude-opus-4-8` / `xhigh`, tier `normal`.
2. Plan Re-review: required for unresolved blocking threads.
3. Implementation Review: bundled runner, `write-commit-to-plan`, `Type: impl`,
   explicitly Claude `claude-opus-4-8` / `xhigh`, tier `normal`.
4. Implementation Re-review: required for unresolved blocking threads.
5. Closeout: create a durable closeout artifact and run Closeout Review with
   the same explicit Opus/`xhigh`/normal selection because this changes shared
   protocol source-of-truth files and paid-model routing.
6. PR handoff: verify branch freshness, pushed CI, review threads, docs/status,
   and PR metadata; stop at ready for human merge.

## Acceptance Criteria

- Closeout type, multiple implementation artifacts, more than 1,000 artifact
  lines, and every existing complexity keyword can recommend hard but cannot
  alter selected tier or model.
- Explicit normal routes Claude to `claude-opus-4-8` / `xhigh`.
- Explicit hard with a reason routes Claude to `claude-fable-5` / `xhigh`.
- Explicit hard without a reason fails before reviewer invocation.
- Legacy auto always selects normal, warns clearly, and records compatibility
  provenance.
- Prompt and metadata distinguish driver selection/reason from runner
  recommendation/reasons and record the final model/source.
- Normal and hard retain identical scope and quality rules.
- Backend auto-selection and unrelated runner behavior do not change.
- All repo validation and structured-review gates pass.
- A shared protocol PR is open; no merge or downstream submodule edit occurs.

## Mechanism Lifecycle And Risks

`structured-review/SKILL.md` owns the explicit-tier contract, profile matrix,
recommendation table, and compatibility lifecycle. A future change may remove
`auto` only after known consumers have migrated and must update runner, tests,
README, current map, and downstream guidance together.

The main compatibility risk is that legacy calls continue on normal instead of
failing, so their driver ownership is not yet fully explicit. The deprecation
warning and additive provenance make that debt visible while eliminating
automatic high-cost routing. Recommendation false positives remain possible,
but they become informational and therefore cannot spend more or expand scope.

## Implementation Record

Implemented on 2026-07-22 without scope divergence:

- split runner configuration and provenance into driver-owned selected tier,
  selection source/reason, and runner-owned recommended tier/reasons;
- retained the existing signal table only for recommendations and made legacy
  auto select normal with a deprecation warning;
- required a stripped non-empty reason for hard, rejected reasons on normal or
  auto, and blocked selected-backend pinned hard-model overrides from bypassing
  the hard contract;
- kept the exact normal/hard profile matrix, backend auto-selection, quality
  gate, timeout, sandbox, write verification, and provider override provenance;
- updated structured-review, closeout, README, current-map, CLI help, prompt,
  start log, metadata aliases, and tests. The inspected readiness/bootstrap
  documents had no tier-routing call site and were intentionally unchanged.

Driver validation:

- structured-review: 87 tests passed;
- Scout: 31 tests passed;
- root: 18 tests passed;
- compileall, backlog validation, runner help, and `git diff --check` passed;
- explicit-normal dry-run: selected normal / explicit-driver / Opus 4.8 /
  `xhigh`;
- explicit-hard-with-reason dry-run: selected hard / explicit-driver / Fable 5
  / `xhigh`; this was configuration-only and did not invoke Fable;
- legacy-auto Closeout Review dry-run: selected normal / legacy-auto /
  recommended hard from review type / Opus 4.8;
- hard-without-reason dry-run: failed before reviewer invocation with exit 1.

Implementation Review completed with no blocking or non-blocking findings and
no re-review was required. Delivery and CI evidence are recorded in
`docs/agent_plans/2026-07-22_explicit_review_tier_closeout.md` and PR #27.
Merge authority remains human-owned.

## Review Threads

I have inspected the plan, the current runner (`structured-review/scripts/claude_structured_review.py`), the existing tests, the SKILL/closeout/README prose, the metadata schema, and the downstream dispatch workflow (`.github/workflows/dispatch-skynet-intern.yml`). The plan's description of current behavior is accurate on every point I checked (auto-hard signal set, metadata keys, `--model` override applying after the profile mapping, and the push-to-`main` → skynet-intern dispatch). Here is my review.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

Backend: claude · Model: `claude-opus-4-8` · Effort: `xhigh` · Tier: `normal` (explicit driver selection). Fable is not used for this review, per Human Decision 5.

Original concern, restated in one sentence: a routine Closeout Review was auto-routed to the hard Fable profile purely because its type was `closeout-review`, burned the provider spend, and returned nothing usable — so mechanical runner signals must stop owning the tier/model decision, and the context-owning driver must own it explicitly.

#### Blocking issues

None. The goal, non-goals, human decisions, acceptance criteria, and validation are clear and grounded in the actual code. An implementer could build this without inventing scope. I verified the plan's claims against the runner: `resolve_review_tier` (lines 328-356) does auto-upgrade on closeout type / >1000 lines / multi-artifact impl / keyword; `resolve_review_profile` (lines 359-381) applies `--model` after the tier→profile map, so `--review-tier normal --model claude-fable-5` currently yields Fable — exactly the hazard the plan closes; the metadata block (lines 966-967) stores `review_tier`/`review_tier_reasons`; and `dispatch-skynet-intern.yml` fires on push to `main` to `MAGI-Systems-01/skynet-intern`, matching Section 6. Nothing here prevents proceeding to implementation.

#### Non-blocking issues

The following are worth closing (or explicitly deferring) before implementation to avoid an implementation re-review round. They are clarity/completeness gaps, not design defects.

**Thread A — `--tier-reason` argument-combination matrix is incomplete (CLI compatibility / would-require-guessing).**
Design section 1 specifies four cases: explicit `normal` → normal; explicit `hard` → requires non-empty `--tier-reason`; omitted/`auto` → normal + warning; `--tier-reason` with `auto` → fail. It does not specify `--tier-reason` combined with explicit `normal`. By the plan's own logic ("`--tier-reason` with `auto` fails because it would imply driver ownership without an explicit tier"), a reason on `normal` is similarly meaningless, but the plan leaves the implementer to guess ignore vs. warn vs. error. Also undefined: whether a whitespace-only `--tier-reason` counts as "non-empty" for hard. Recommend stating both explicitly (a reasonable default is: reject `--tier-reason` with any tier other than `hard`, and strip-then-require-non-empty for `hard`) and adding them to the Section 5 test list. This is the one place the focus's "whether implementation would require guessing" bites.

**Thread B — the `--model` → pinned-hard-model restriction changes the override contract but isn't in the doc-update list (metadata provenance / documentation lifecycle).**
Design section 1 adds a real behavior change: "The pinned hard-profile models (`claude-fable-5` and `gpt-5.6-sol`) cannot be selected through a normal or auto tier override; callers must select `hard` and provide the reason." This directly narrows what `structured-review/SKILL.md` lines 159-165 currently promise ("Provider-specific `--model` … override only the selected backend's profile and are intended for deliberate exceptions"). Section 4's doc list updates SKILL.md/README generally but does not name this carve-out. Please have the SKILL.md and README override paragraphs explicitly state that the pinned hard model is unreachable via `--model`/`--codex-model` on a non-hard tier, so a downstream driver relying on `--model` overrides is not surprised. Two small specification points for the implementer: (a) confirm the check is per-selected-backend (block claude's hard model only on the claude backend, codex's only on codex), and (b) confirm `--review-tier hard --tier-reason … --model claude-fable-5` remains allowed (redundant, not an error). The Section 5 test "pinned hard-profile model override without explicit hard/reason -> fail" covers the failing case; add a passing-case assertion for the redundant-but-valid combination.

**Thread C — the deprecated `review_tier_reasons` alias has an underspecified value in the new scheme (metadata provenance).**
Section 3 says metadata keeps `review_tier` "as an alias of `selected_tier`" (a clean 1:1) and keeps `review_tier_reasons` "as selection provenance only," no longer carrying recommendation signals. `review_tier` is unambiguous. But `review_tier_reasons` isn't a strict alias of any single new field — for an explicit hard run it would need to convey selection source and/or the driver reason, and for a legacy-auto run it would convey the compatibility source. State exactly what string(s) `review_tier_reasons` carries in each of the three selection paths (explicit-normal, explicit-hard, legacy-auto) so the metadata test (`test`, currently asserting `["auto: no hard signals"]` at test line 1185) can be rewritten deterministically rather than to whatever the implementer happens to emit.

**Thread D — two existing prompt/metadata assertion tests will break and aren't individually named (test replacement completeness).**
Section 5 lists five auto-hard tests to delete/rewrite and ten coverage items to add — this maps cleanly onto the existing tests I read (`test_closeout_review_auto_selects_hard`, `test_artifact_body_over_one_thousand_lines_auto_selects_hard`, `test_multi_artifact_implementation_review_auto_selects_hard`, `test_each_complexity_phrase_auto_selects_hard`, `test_default_review_tier_is_normal_with_profile_provenance`). Two more existing tests will also break under the expanded prompt block and new metadata keys but aren't called out: the prompt assertions at test lines 1145-1148 (`- Review tier: …`, `- Tier selection: …`, `- Model source: …`) and the metadata assertions around lines 1184-1185. The plan's coverage item "selection, rationale, recommendation, final model, and source in prompt and metadata" implicitly absorbs them, so this is a completeness note, not a gap — just confirm those two are rewritten, not merely left to fail. Positive note: the plan correctly preserves the Review-Threads-exclusion invariant (Section 2, "Retain … Review Threads exclusion … but move them into recommendation calculation"), which keeps `test_review_threads_are_excluded_from_size_and_complexity_signals` meaningful — good catch to keep that subtle behavior.

#### Overall judgment

Ready for implementation, with the four non-blocking threads above recommended for closure first. The responsibility boundary is stated correctly and is the right fix: the runner keeps computing signals but they become an observational `recommended_tier`/`recommendation_reasons` that can never mutate `selected_tier`, profile, timeout, or scope (Section 2), and the driver owns tier via explicit flags. CLI compatibility is handled sensibly — the staged window keeps legacy `auto`/omitted callers running on `normal` with a deprecation warning instead of a hard failure, while removing the paid-model hazard immediately, and the plan is honest that fail-closed removal is a separate future reviewed change. Metadata provenance is expanded to five named fields with additive deprecated aliases. Test replacement is thorough. Downstream rollout matches the real dispatch mechanism and correctly insists the downstream bump point at the merged `main` commit, not this feature branch. The mechanism-lifecycle section names SKILL.md as the contract owner and requires runner+tests+README+current-map+downstream to move together for any future `auto` removal. Normal and hard keep an identical readiness standard and scope, consistent with the tier-affects-routing-only rule I am applying to this very review.

#### Residual risks / validation gaps

- Compatibility-debt risk is real and disclosed (Section "Mechanism Lifecycle And Risks"): legacy `auto`/omitted callers keep running without explicit driver ownership until they migrate. The plan accepts this deliberately; the deprecation warning plus additive provenance make the debt visible, and — critically — legacy-auto can no longer reach a paid model, so the debt is cosmetic, not a spend hazard. Acceptable.
- Metadata semantic change: `review_tier_reasons` changes meaning (selection provenance, not signal list). I confirmed the only in-repo consumers are the tests, so the plan's "no versioned metadata consumer exists in this repo" holds for this repo. The run-metadata JSON is a per-run log artifact, not a protocol source file, so a downstream metadata parser is unlikely; but the claim is scoped to this repo, and any external tool that parsed signal reasons out of `review_tier_reasons` would see a behavior change. Low likelihood, disclosed, acceptable.
- Recommendation false positives remain possible but, by construction, become informational only — they cannot spend more or expand scope. Correct.
- Validation is executable by the next agent: I confirmed `scout/tests`, `tests/`, and `scripts/check_backlog.py` all exist, so the Section "Validation" command block is runnable and not aspirational. The dry-run CLI cases (explicit normal, explicit hard with reason, legacy auto with a hard recommendation, hard-without-reason failure) give end-to-end coverage beyond unit tests. Good.

No blocking issues. I recommend the driver resolve or explicitly defer Threads A-D, then proceed to implementation under the same explicit Claude `claude-opus-4-8` / `xhigh` / `normal` gate the plan specifies.

### Driver response 1 (impl-plan)

- **Thread A — accepted.** Section 1 now rejects `--tier-reason` for normal
  and auto and requires explicit-hard reasons to remain non-empty after
  stripping whitespace. Section 5 names all three argument-combination tests.
- **Thread B — accepted.** Section 1 now specifies a selected-backend-only
  hard-model guard, preserves explicit hard + reason + redundant pinned-model
  overrides, and requires both SKILL and README override prose to document the
  carve-out. Section 5 adds the passing case.
- **Thread C — accepted.** Section 3 now gives exact `review_tier_reasons`
  arrays for explicit normal, explicit hard, and legacy auto.
- **Thread D — accepted.** Section 5 now names the existing prompt and Codex
  metadata tests that must be rewritten for the expanded fields.

All reviewer suggestions were accepted. No human decision changed, no scope
expanded beyond clarifying the already accepted interface, and no residual
thread is deferred or escalated. Ready for reviewer resolution.

All four threads are now grounded and internally consistent. I've confirmed:

- **Thread A** — Section 1 completes the matrix (`--tier-reason` rejected for `normal`/`auto`; valid only with `hard`, stripped-then-non-empty). `resolve_review_tier` (lines 328-356) shows explicit tiers currently pass through with no reason handling, so this is a clean additive change. All three combination tests named in Section 5.
- **Thread B** — `resolve_review_profile` (lines 359-381) already keys the override off the selected backend (`claude_model if backend == BACKEND_CLAUDE else codex_model`) and applies `--model` unconditionally over the profile (line 375-377) — exactly the hazard. The plan's selected-backend-only guard, redundant-override-valid carve-out, doc mandate, and passing test are all consistent with the code.
- **Thread C** — metadata keys `review_tier`/`review_tier_reasons` confirmed (lines 966-967); current auto path emits `("auto: no hard signals",)` (line 356). The three new deterministic arrays cleanly replace it and match the `'; '.join(...)` prompt rendering (line 452).
- **Thread D** — both named tests exist: `test_prompt_records_tier_profile_and_sources` (line 1134) and `test_run_codex_prefers_last_message_file_and_records_metadata` (line 1153, currently asserting `["auto: no hard signals"]` at line 1185 — exactly the Codex alias that Thread C's new legacy array forces to change).

The driver accepted all four and the plan body carries the fixes. Here is my resolution pass.

---

### Reviewer resolution pass (impl-plan, claude reviewer)

Backend: claude · Model: `claude-opus-4-8` · Effort: `xhigh` · Tier: `normal` (explicit driver selection). Fable is not used for this review, per Human Decision 5. Re-review scope: driver response 1 and the updated plan body, verified against `structured-review/scripts/claude_structured_review.py` and `structured-review/tests/test_claude_structured_review.py`.

#### Thread A — Resolved. Argument-combination matrix is now complete.
Section 1 now states: "`--tier-reason` is rejected for `normal` and `auto`; it is valid only with explicit `hard`, where whitespace is stripped and the remaining value must be non-empty." That closes both gaps I raised — reason-on-`normal` (now an explicit reject, consistent with the reason-on-`auto` reject) and whitespace-only reason (now strip-then-require-non-empty). Section 5 names all three tests (`hard without a reason -> fail closed`, `whitespace-only hard reason -> fail closed`, `reason supplied with normal or auto -> fail closed`). The omitted-tier case is covered by the plan's consistent "omitted or explicit auto" bucketing, so no separate case is needed. `resolve_review_tier` (lines 328-356) currently does no reason handling, confirming this is a clean additive contract, not a rewrite of existing branch logic. No guessing remains.

#### Thread B — Resolved. Override carve-out is specified and documented.
Section 1 now specifies (a) the guard is per-selected-backend — "the Claude hard slug is guarded for a Claude review and the Codex hard slug for a Codex review" — which matches `resolve_review_profile`'s existing per-backend override selection (lines 369-372); and (b) "Explicit hard plus a reason plus a redundant override to that backend's pinned hard model remains valid." The doc-lifecycle gap is closed: "The SKILL and README override paragraphs will state this carve-out directly." Section 5 adds the passing case (`explicit hard plus reason plus the same pinned hard-model override -> pass`) alongside the existing failing case. The narrowing of the current `--model` override promise (lines 375-377 apply the override unconditionally today) is now explicitly reflected in the doc-update list.

#### Thread C — Resolved. Legacy alias values are exact and deterministic.
Section 3 now pins `review_tier_reasons` for all three selection paths: explicit normal `["explicit --review-tier normal"]`; explicit hard `["explicit --review-tier hard", "driver tier reason: <reason>"]`; omitted/auto `["legacy --review-tier auto compatibility selected normal"]`. These are internally consistent: the explicit-normal value matches the current `f"explicit --review-tier {raw}"` shape (line 336) and renders correctly through the `'; '.join(...)` prompt line (line 452), and the omitted/auto value cleanly supersedes the current `["auto: no hard signals"]` (line 356). The metadata test can now be rewritten to a fixed expected value rather than to whatever the implementer emits.

#### Thread D — Resolved. Breaking prompt/metadata tests are named.
Section 5 now names both existing tests that would otherwise silently break: `rewrite test_prompt_records_tier_profile_and_sources for the expanded selection/recommendation block` and `rewrite the Codex metadata assertions in test_run_codex_prefers_last_message_file_and_records_metadata for the new fields and exact legacy aliases`. Both exist (lines 1134 and 1153), and the second currently asserts `["auto: no hard signals"]` at line 1185 — precisely the alias Thread C's new legacy array forces to change — so the two threads are mutually reinforcing. The Review-Threads-exclusion invariant is preserved (Section 2), keeping `test_review_threads_are_excluded_from_size_and_complexity_signals` (line 316) meaningful.

#### Overall judgment — Ready for implementation.
No blocking issues. Threads A-D are all resolved in the plan body and grounded in the actual runner and test code; the four items I raised were the only clarity/completeness gaps, and each now has an unambiguous interface contract plus named test coverage. The responsibility boundary (driver owns tier via explicit flags; runner signals become observational `recommended_tier`/`recommendation_reasons` that cannot mutate selection, profile, timeout, or scope) is intact, and normal/hard keep an identical readiness standard — consistent with the tier-affects-routing-only rule applied to this review. I did not add new scope or low-value findings; the argument matrix, selected-backend hard-model guard, exact legacy metadata values, and named test rewrites are now unambiguous.

#### Residual risks / validation gaps.
- The compatibility-debt risk (legacy `auto`/omitted callers keep running on `normal` without explicit driver ownership until migration) remains real and is deliberately accepted; the deprecation warning plus additive provenance make it visible, and legacy-auto can no longer reach a paid model, so it is cosmetic debt, not a spend hazard. Unchanged from pass 1, still acceptable.
- `review_tier_reasons` changes meaning (selection provenance, not signal list). The only in-repo consumers are the tests being rewritten; disclosed and scoped to this repo. Acceptable.
- Validation is executable by the next agent (the Section "Validation" command block and dry-run CLI cases are runnable). No new gaps introduced by the response-1 edits.

Implementation may proceed under the same explicit Claude `claude-opus-4-8` / `xhigh` / `normal` gate the plan specifies. This is a plan-review conclusion of `ready for implementation`; it is not a merge-readiness handoff, which belongs to closeout after final rechecks.

I've completed a thorough verification. Every accepted plan criterion traces to the committed implementation, all validation evidence reproduces independently, and no live doc carries a stale auto-hard claim. Here is my review.

---

### Reviewer pass 1 (impl, claude reviewer)

Backend: claude · Model: `claude-opus-4-8` · Effort: `xhigh` · Tier: `normal` (explicit driver selection). Fable is not used for this review, per Human Decision 5 and the task instruction.

A note before findings, because it is itself evidence: for this very review the runner *recommended* `hard` with seven mechanical signals (`artifact body lines 4173 > 1000`, multi-artifact, production/architecture/security/multi-agent/protocol/explicit-complexity), yet the driver explicitly selected `normal` and I am running on Opus, not Fable. The mechanism under review is dogfooding correctly in this pass: signals recommended, the driver decided, and no paid-hard model was reached. I am applying the ordinary readiness standard and did not invent scope because a hard recommendation was present.

Original concern, restated in one sentence: a routine Closeout Review was auto-routed to the paid Fable profile purely because its type was `closeout-review`, burned the provider spend and returned nothing usable — so mechanical signals must stop owning the tier/model decision and the context-owning driver must own it explicitly, without breaking legacy callers.

I compared the committed work (implementation commit `structured-review: make review tier driver-owned`) against every accepted acceptance criterion and Design section, read the runner and tests in full, and independently reproduced the validation.

#### Blocking issues

None. Every accepted criterion is implemented, tested, and independently reproducible. Implementation may proceed to closeout.

#### Traceability against accepted acceptance criteria

Each row is `Done` with concrete, reproduced evidence.

| # | Accepted criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Closeout type, multi-artifact, >1,000 lines, and every complexity keyword can recommend hard but cannot alter selected tier/model | Done | `recommend_review_tier` returns an observational `(tier, reasons)` tuple (`claude_structured_review.py:334-358`); `config_from_args` threads it only into `recommended_tier`/`recommendation_reasons` (`:1217-1219`, `:1283-1284`); tests `test_closeout_review_recommends_hard_without_changing_selected_tier`, `test_artifact_body_over_one_thousand_lines_only_recommends_hard`, `test_multi_artifact_implementation_review_only_recommends_hard`, `test_each_complexity_phrase_only_recommends_hard`, `test_representative_keywords_never_change_selected_tier_or_model`. Dry-run: closeout+auto recommended hard, stayed normal/Opus. |
| 2 | Explicit normal → `claude-opus-4-8`/`xhigh` | Done | `REVIEW_MODEL_MATRIX` (`:48-57`); `test_review_model_matrix_is_exact_for_both_backends_and_tiers`; dry-run 1 printed `normal / explicit-driver / claude-opus-4-8 / profile`. |
| 3 | Explicit hard + reason → `claude-fable-5`/`xhigh` | Done | Same matrix; dry-run 2 printed `hard / explicit-driver / driver reason / claude-fable-5`. |
| 4 | Hard without a reason fails before reviewer invocation | Done | `resolve_review_tier` raises in `config_from_args` (`:372-374`, called `:1220`) before `run()`; `test_explicit_hard_without_reason_fails_before_profile_resolution`; dry-run 4 exited 1 with no reviewer launch. |
| 5 | Legacy auto/omitted → normal, clear warning, compatibility provenance | Done | Auto branch (`:362-365`), default `--review-tier auto` (`:1173`), deprecation warning (`:1223-1228`), `legacy_review_tier_reasons` (`:378-384`); `test_legacy_auto_selects_normal_with_compatibility_provenance`; dry-run 3 emitted the deprecation warning and the recommend-hard notice. |
| 6 | Prompt + metadata distinguish driver selection/reason from recommendation/reasons and record final model/source | Done | `build_prompt` five-field block + routing-only line (`:487-498`); `write_metadata` five new fields + `review_tier`/`review_tier_reasons` aliases + `model`/`effort`/`*_source` (`:1007-1017`); `test_prompt_records_tier_profile_and_sources`, `test_run_codex_prefers_last_message_file_and_records_metadata`. |
| 7 | Normal and hard retain identical scope and quality rules | Done | Prompt line `Review tier affects model routing only … same readiness standard at both tiers` (`:498`); `SKILL.md:120-123`. |
| 8 | Backend auto-selection and unrelated runner behavior unchanged | Done | `resolve_reviewer_backend` (`:964-977`), `claude_argv`/`codex_argv`, timeout/heartbeat, write-verification all unchanged; `test_resolve_reviewer_backend_cross_vendor_auto` and the full read-only/commit-shape suite still pass. |
| 9 | Selected-backend pinned hard-model guard | Done | `require_hard_profile_model_has_hard_tier` keys off the selected backend's hard slug and the resolved model (`:412-419`, called `:1243`); `test_pinned_hard_model_override_requires_hard_tier_for_selected_backend` (claude+codex), `test_redundant_pinned_hard_model_override_is_valid_with_hard_reason`. Dry-run: `--review-tier normal --model claude-fable-5` exited 1; `--review-tier hard --tier-reason … --model claude-fable-5` passed with `model source: explicit --model`. |

#### Verification of the specific focus items

- Driver ownership: confirmed. `resolve_review_tier` maps auto→`legacy-auto-compatibility`, explicit normal/hard→`explicit-driver`; the recommendation never feeds selection.
- Legacy auto safety: confirmed. Auto/omitted resolves to `normal` on the profile path and can never reach a hard model — the override guard also fires for `auto`+pinned-hard-model, so the paid-model hazard is closed on every non-hard path.
- Hard rationale enforcement: confirmed. Whitespace is stripped, empty is rejected (`:372-374`); `test_tier_reason_is_required_only_for_explicit_hard` covers `hard/None`, `hard/"   "`, and reason-on-`normal`/`auto`.
- Recommendation-only signals: confirmed, including preservation of the Review-Threads-exclusion invariant via `read_artifact_body` (`:323-331`) and `test_review_threads_are_excluded_from_size_and_complexity_signals`.
- Prompt/metadata provenance: confirmed, and the deterministic legacy alias arrays match Design section 3 exactly for all three selection paths (reproduced in `test_run_codex_prefers_last_message_file_and_records_metadata` and `test_prompt_records_tier_profile_and_sources`).
- Docs consistency: confirmed. `structured-review/SKILL.md` (explicit-tier contract, matrix, recommendation-only, override carve-out at `:182-189`), `closeout/SKILL.md` (`:54-62`, automatic-hard claim removed, "does not select `hard` merely because its type is `closeout-review`"), `README.md:123-138`, and `docs/CURRENT.md:20-26` are mutually consistent and single-sourced to the SKILL. A repo-wide grep found no stale "auto-selects hard" language in any live source-of-truth doc; the only hits are the historical `2026-07-20` plan (correctly left unrewritten per Non-Goals) and the active plan's own change description. `agent-readiness/` and `AGENTS.md` carry no tier/model-routing content, matching the plan's claim that they needed no change.
- Validation evidence: independently reproduced — `structured-review` 87 tests, Scout 31, root 18, `compileall`, `check_backlog.py`, `git diff --check`, all four plan dry-run cases, plus the guard and non-selected-provider-override warning. The Implementation Record's numbers are accurate.
- Unchanged backend scope: confirmed. The implementation commit touched exactly the seven expected artifacts and nothing else.

#### Non-blocking issues

None require a change. Two small observations, both already correct:

- `docs/agent_plans/README.md` appears in the plan's "Files Expected To Change" but is absent from the implementation commit. This is fine: the index entry for the `2026-07-22` plan was added when the plan was created, and it is present and accurate today. No action needed.
- The `review_tier_reasons` alias for an explicit-hard run embeds the driver reason verbatim. Because `build_prompt` runs the whole-prompt local-path guard (`:532`) and metadata is a `.git`-scoped run-log artifact (not committed), there is no leakage path. No action needed.

#### Overall judgment — Ready for closeout.

The responsibility boundary the human asked for is implemented cleanly: mechanical signals are computed into an observational `recommended_tier`/`recommendation_reasons` that cannot mutate `selected_tier`, profile, timeout, scope, or the readiness standard; the driver owns the tier via explicit `--review-tier`; hard requires a stripped non-empty rationale; and the selected-backend pinned-hard-model guard closes the `--model`/`--codex-model` bypass on every non-hard tier while still allowing the redundant-but-valid hard override. The legacy-auto compatibility window keeps omitted/`auto` callers running on normal with a deprecation warning and additive provenance, eliminating the paid-model hazard immediately without a hard failure — exactly the staged migration the plan accepted. Docs are consistent and single-sourced, provenance is fully recorded in prompt/start-log/metadata, and every validation command reproduces. This is an implementation-review conclusion of `ready for closeout`; it is not a merge-readiness handoff, which belongs to closeout after final rechecks.

#### Residual risks / validation gaps

- Compatibility debt (accepted, disclosed): legacy `auto`/omitted callers keep running on `normal` without explicit driver ownership until they migrate. The deprecation warning plus additive provenance make the debt visible, and — verified here — legacy-auto can no longer reach a paid model even with a pinned-hard-model override, so the debt is cosmetic, not a spend hazard.
- `review_tier_reasons` changed meaning (selection provenance, not signal list). The only in-repo consumers are the rewritten tests; scoped to this repo and disclosed.
- Process gates outside this review's scope remain pending and are correctly listed as such in the Implementation Record: the shared protocol PR / CI verification and human merge handoff (Review Gate 6) and the closeout evidence + Closeout Review (Gate 5). I make no merge-readiness claim here.

No blocking issues. I recommend the driver proceed to the closeout gate under the same explicit Claude `claude-opus-4-8` / `xhigh` / `normal` selection the plan specifies for this change.

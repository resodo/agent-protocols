# Explicit Review Tier Ownership Plan

Status: active implementation and review record
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

Pending gates: Implementation Review, any required re-review, closeout evidence
and Closeout Review, PR/CI verification, and human merge handoff.

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

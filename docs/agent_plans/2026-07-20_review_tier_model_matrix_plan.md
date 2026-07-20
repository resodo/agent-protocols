# Structured Review Tier And Model Matrix Plan

Status: implementation review passed; closeout pending
Branch: `feature/review-tier-model-matrix`
Worktree: `agent-protocols-review-tier`

## Context

The structured-review runner currently has one default model per reviewer
backend:

- Claude Code: `opus` with `xhigh` effort;
- Codex: `gpt-5.5` with `xhigh` reasoning effort.

The runner already selects the reviewer backend across vendors when
`--reviewer-backend auto` is used:

- Claude Code driver -> Codex reviewer;
- Codex driver -> Claude Code reviewer;
- no recognized driver marker -> Claude Code reviewer;
- both driver families detected -> fail and require an explicit backend.

The human wants to preserve that rule while adding a second automatic axis:
review tier. Review callers should not need to choose models directly for
ordinary use. The runner should select `normal` or `hard` from review size and
complexity, then resolve a pinned 2x2 backend/tier model profile.

The model matrix was explicitly accepted by the human after checking current
provider guidance and the locally installed CLI catalogs:

| Reviewer backend | Normal | Hard | Effort |
| --- | --- | --- | --- |
| Claude Code | `claude-opus-4-8` | `claude-fable-5` | `xhigh` |
| Codex | `gpt-5.6-terra` | `gpt-5.6-sol` | `xhigh` |

Provider rationale:

- Anthropic recommends Opus 4.8 at `xhigh` for coding/agentic work and Fable 5
  at `xhigh` for the most capability-sensitive workloads.
- OpenAI describes Terra as the everyday successor for work previously given
  to GPT-5.5 and Sol as the flagship for complex, open-ended coding and
  reasoning.
- Full model slugs are pinned rather than mutable aliases so a provider alias
  update cannot silently change the review gate.

Sources:

- `https://platform.claude.com/docs/en/about-claude/models/choosing-a-model`
- `https://platform.claude.com/docs/en/build-with-claude/effort`
- `https://developers.openai.com/api/docs/guides/latest-model`
- `https://learn.chatgpt.com/docs/models#where-each-model-shines`

Baseline validation on fresh `origin/main` (`58a0830`) is green:

- structured-review: 65 tests;
- Scout: 31 tests;
- root tests: 18 tests;
- total: 114 tests.

## Human Decisions

1. Use exactly two reviewer backends: Claude Code and Codex.
2. Keep cross-vendor backend selection as the default. A caller outside either
   recognized agent family defaults to Claude Code.
3. Add two review tiers: `normal` and `hard`.
4. Use the pinned 2x2 model matrix above, with `xhigh` for all four profiles.
5. Choose the tier automatically from artifact size and review complexity.
6. Update structured-review and Closeout Review guidance so callers provide
   enough scope context and do not maintain competing backend/tier rules.
7. Create a PR; merging remains human-owned.

## Problem

The current runner cannot express review difficulty independently from backend.
Its model defaults are attached directly to provider-specific CLI flags, and
the prompt and metadata record only backend/model/effort. Consequently:

- routine and unusually demanding reviews use the same model;
- model selection requires provider-specific override knowledge;
- the reason for a selected model is not visible in the reviewer prompt or run
  metadata;
- Closeout Review has no explicit instruction to carry its high-impact trigger
  context into model-tier selection;
- GPT-5.5 and a mutable Claude `opus` alias no longer represent the accepted
  defaults.

## Goal

Make reviewer selection a deterministic two-step policy:

1. resolve the reviewer backend from driver identity;
2. resolve `normal` or `hard` from explicit override or review evidence, then
   select the pinned model/effort profile.

The selection must be visible, testable, overridable, and single-sourced in the
structured-review protocol and runner.

## Non-Goals

- Do not add more reviewer backends or more than two tiers.
- Do not run both reviewer backends for one gate.
- Do not use an LLM preflight call to classify tier before the real review.
- Do not change write-mode append/commit verification, reviewer sandboxing,
  timeout behavior, or review-thread ownership.
- Do not change provider authentication, subscriptions, CLI installation, or
  global agent configuration.
- Do not remove provider-specific model/effort override flags.
- Do not make Closeout Review run by default; closeout remains the owner of its
  trigger list.
- Do not update historical plans merely because they name older models.

## Proposed Design

### 1. Central profile matrix

Define one runner-owned matrix keyed by resolved backend and tier:

```text
claude/normal -> claude-opus-4-8, xhigh
claude/hard   -> claude-fable-5, xhigh
codex/normal  -> gpt-5.6-terra, xhigh
codex/hard    -> gpt-5.6-sol, xhigh
```

Use full model slugs. Keep the existing `--model`, `--effort`,
`--codex-model`, and `--codex-effort` flags as explicit per-provider
overrides. Their precedence is:

1. resolve backend;
2. resolve review tier;
3. load the matrix profile;
4. replace model and/or effort only when the corresponding explicit override
   was supplied.

This preserves intentional caller pins while making ordinary calls independent
of provider-specific model flags.

### 2. Review tier interface

Add:

```text
--review-tier {auto,normal,hard}
```

Default: `auto`.

Explicit `normal` or `hard` wins and records `explicit --review-tier` as the
selection reason. `auto` uses conservative, deterministic signals available to
the runner without a second model call.

### 3. Automatic tier policy

Resolve `hard` when any hard signal exists:

1. review type is `closeout-review`. Closeout Review is exceptional and only
   triggered for durable/high-impact evidence, conflict-sensitive contracts,
   large phase/release handoffs, ambiguous provenance, or unresolved risk;
2. total artifact size exceeds 1,000 lines, matching the existing large-review
   timeout heuristic;
3. an `impl` review has multiple artifacts, matching the existing multi-file
   implementation-review heuristic;
4. artifact or focus text contains an explicit high-complexity/high-impact
   scope signal in a small, named policy table:
   - production/runtime/deploy/rollout: `production-facing`,
     `production change`, `production rollout`, `runtime-facing`,
     `runtime behavior`, `deploy-facing`, `deployment plan`, or `rollout
     plan`;
   - architecture/migration: `architecture-facing`, `architecture change`,
     `system architecture`, `data migration`, `schema migration`, or
     `migration plan`;
   - security/data safety: `security-sensitive`, `security review`, `security
     boundary`, `data safety`, `data loss`, or `destructive data`;
   - multi-repo/multi-agent/release: `multi-repo`, `multi-agent`, `release
     plan`, or `release handoff`;
   - broad protocol change: `broad protocol change`, `protocol-wide change`,
     or `protocol self-evolution`;
   - explicit complexity: `complex review`, `high-risk`, `hard review`, or
     `large review`.

Otherwise resolve `normal`.

The complexity scan is intentionally conservative: a false-positive `hard`
selection costs more but preserves review quality; a false-negative can
underpower a high-impact gate. Keep the signal table small and named. Do not
derive tier from arbitrary token counts, reviewer output, git churn, or hidden
provider behavior.

Matching is case-insensitive and uses whole words/phrases, so `production` does
not match `reproduction` and `hard` does not match `hardware`. Hyphenated
phrases match only the listed spelling; adding alternate spellings is a policy
change. Whitespace inside a listed multi-word phrase matches any non-empty
whitespace run, including line breaks and indentation in wrapped Markdown.
Reasons record the category name, not the matched artifact text.

For both the line count and complexity scan, use only the artifact body before
the first top-level `## Review Threads` heading. Excluding review threads keeps
the resolved tier stable across plan/re-review rounds and avoids reviewer prose
changing the next reviewer's model. Focus text is always scanned in full.
Count lines with Python `splitlines()` across all artifact bodies and resolve
hard only when the total is strictly greater than 1,000.

Every artifact must be an existing readable UTF-8 regular file. A missing,
directory, unreadable, or non-UTF-8 artifact fails before reviewer invocation
with a relative-path `RunnerError`; the runner must not silently skip a tier
input or fall back to normal.

The runner returns both the resolved tier and human-readable reasons. Tests pin
each signal category, normal fallback, and explicit overrides.

### 4. Prompt and observability

Add a reviewer-selection block to the prompt before task-specific focus:

```text
Reviewer selection:
- Backend: claude|codex
- Review tier: normal|hard
- Tier selection: <reason list>
- Model: <resolved model>
- Effort: <resolved effort>
```

Tell the reviewer that tier affects model routing, not the readiness standard:
normal reviews must still report blockers honestly, and hard reviews must not
invent extra scope or low-value findings.

Add the resolved tier and reasons to:

- `RunConfig`;
- stderr start log;
- `metadata.json` (`review_tier`, `review_tier_reasons`);
- dry-run prompt output.

Use `None` as the argparse default sentinel for the four provider-specific
model/effort override flags. After loading the selected profile, replace only
values whose flags are non-`None`. Add `model_source` and `effort_source` to
`RunConfig`, prompt, and metadata; each is either `profile` or the exact
provider-specific override flag such as `explicit --codex-model`. This keeps a
custom model from being misrepresented as a matrix-selected value.

When a review resolves hard while `timeout_sec` is the default 900 seconds,
emit a non-fatal stderr notice that hard reviews usually warrant
`--timeout-sec 1800`. Do not automatically change timeout semantics: callers
may intentionally keep a shorter bound.

Review pass headings continue to name the backend; they do not need to encode
the tier because metadata and prompt own that provenance.

### 5. Backend selection contract

Keep the current backend resolver mechanically unchanged except for prose and
tests that lock the full policy:

- Claude marker only -> Codex;
- Codex marker only -> Claude;
- neither -> Claude;
- both -> error requiring explicit `--reviewer-backend`;
- explicit backend -> explicit choice.

The structured-review skill should state this as the canonical backend rule.
Closeout should defer to it rather than restating the matrix or driver-marker
implementation.

### 6. Closeout Review integration

`closeout/SKILL.md` keeps the canonical Closeout Review trigger list. Add a
short boundary rule:

- invoke the structured-review runner with `Type: closeout-review` and enough
  artifact/focus context to explain the trigger;
- let structured-review own backend, tier, model, and runner-mode selection;
- do not duplicate or override the 2x2 matrix in closeout;
- `closeout-review` resolves hard by default under the centralized tier policy,
  while an explicit tier remains an operator escape hatch.

### 7. Protocol and repo documentation

Update:

- `structured-review/SKILL.md`: backend selection, tier policy, matrix,
  overrides, prompt provenance, lifecycle owner;
- `closeout/SKILL.md`: delegate backend/tier/model selection and require useful
  trigger context;
- `README.md`: document `--review-tier` and the 2x2 profiles in runner usage;
- `docs/CURRENT.md`: describe automatic cross-vendor/tiered reviewer routing
  and update the current-map date;
- `docs/agent_plans/README.md`: index this plan.

### 8. Tests

Extend `structured-review/tests/test_claude_structured_review.py` to cover:

- exact four-profile model/effort matrix;
- default `auto` tier;
- small ordinary artifact -> normal;
- explicit normal/hard overrides;
- `closeout-review` -> hard;
- total artifact lines over 1,000 -> hard;
- a small pre-thread body with a `## Review Threads` section that pushes the
  full file over 1,000 lines remains normal;
- multi-artifact `impl` -> hard;
- each named complexity category -> hard;
- model and effort flags override only the selected provider profile;
- override detection uses `None` parser sentinels and prompt/metadata record
  `model_source` and `effort_source`;
- Claude and Codex argv receive the resolved profile;
- prompt contains backend, tier, reasons, model, and effort;
- metadata contains resolved tier and reasons;
- stderr start log names the tier;
- hard tier at the default timeout emits 1800-second guidance without changing
  the configured timeout;
- SKILL prose keeps backend/tier rules and closeout boundary single-sourced;
- all existing backend, write/print, sandbox, redaction, timeout, and stream
  tests remain green.

## Files Expected To Change

- `structured-review/scripts/claude_structured_review.py`
- `structured-review/tests/test_claude_structured_review.py`
- `structured-review/SKILL.md`
- `closeout/SKILL.md`
- `README.md`
- `docs/CURRENT.md`
- `docs/agent_plans/README.md`
- this plan

## Acceptance Criteria

- Default backend selection is Claude driver -> Codex, Codex driver -> Claude,
  unknown/other driver -> Claude, both markers -> explicit-choice error.
- `--review-tier auto` is the default and resolves deterministically from the
  documented size/type/complexity signals.
- Small ordinary plan and implementation-plan artifacts resolve `normal`.
- Closeout Review, >1,000 total artifact lines, multi-artifact implementation
  review, and every named high-complexity category resolve `hard`.
- Explicit `--review-tier normal|hard` overrides automatic classification.
- Effective profiles are exactly:
  - Claude normal: `claude-opus-4-8` / `xhigh`;
  - Claude hard: `claude-fable-5` / `xhigh`;
  - Codex normal: `gpt-5.6-terra` / `xhigh`;
  - Codex hard: `gpt-5.6-sol` / `xhigh`.
- Existing provider-specific model/effort flags remain accepted and override
  only the resolved provider profile.
- Prompt, stderr start log, and metadata state the resolved tier; prompt and
  metadata include the selection reason.
- Tier changes model routing only; protocol readiness standards stay identical.
- Closeout keeps its trigger list and delegates backend/tier/model policy to
  structured-review.
- No write-mode, git verification, sandbox, stream parsing, timeout, secret
  scanning, or path-redaction regression.
- All repo tests and static checks pass.
- A PR is opened from `feature/review-tier-model-matrix`; no merge is performed.

## Validation Plan

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

Before closeout, run one minimal, read-only live smoke against each new Codex
slug (`gpt-5.6-terra` and `gpt-5.6-sol`) with `xhigh`, using a trivial prompt
and no repo writes. Record success or the exact availability blocker as
driver-run provenance. Unit tests remain the source for argv construction;
these live probes cover current CLI/account model acceptance only.

Reviewer reruns the relevant tests during implementation review when its
sandbox permits. CI results and exact required-check names are recorded during
closeout.

## Review Gates

1. Plan Review: bundled runner, `write-commit-to-plan`, `Type: impl-plan`,
   cross-vendor Claude reviewer because the driver is Codex. Until tier support
   exists, pin `claude-fable-5` / `xhigh` explicitly for this broad protocol
   change and use `--timeout-sec 1800`.
2. Plan Re-review: required if the first reviewer opens blocking threads.
3. Implementation Review: bundled runner, `Type: impl`, default backend auto
   selection and new tier auto selection. This change should dogfood Claude
   hard routing and record the resolved model/tier.
4. Implementation Re-review: required for unresolved blocking findings.
5. Closeout: driver-owned checklist plus Closeout Review because this PR
   changes source-of-truth protocol files, runner behavior, and tests. The
   Closeout Review uses `Type: closeout-review` and the new selection policy.
6. PR handoff: ready for human merge only after branch freshness, review
   threads, pushed CI, documentation lifecycle, and PR metadata are verified.

## Mechanism Lifecycle

The structured-review protocol owns the matrix and tier policy. Maintain them
when:

- a provider retires or renames a pinned model;
- a CLI catalog no longer accepts a slug or effort;
- provider guidance materially changes model positioning;
- run metadata or representative review evals show normal reviews are
  underpowered or hard reviews are over-selected;
- the existing 1,000-line/large-review timeout heuristic changes.

Removal/update process:

1. verify current official provider documentation and local CLI support;
2. update the matrix, SKILL prose, runner constants, tests, and README in one
   protocol change;
3. run representative normal and hard review gates;
4. preserve explicit override flags as a rollback path until the new defaults
   are validated.

The named complexity categories are a maintained policy surface. Their owner is
`structured-review/SKILL.md`; the runner table and tests implement that policy.
Avoid adding one-off keywords without a demonstrated classification gap.

## Risks

- Keyword signals can classify a negated mention (for example, "not
  production") as hard. This is an intentional conservative bias and is made
  visible in reasons/metadata.
- A complex review with no named signal and less than 1,000 artifact lines can
  remain normal. Callers retain explicit `--review-tier hard`, and the SKILL
  tells drivers to use it when known complexity is not mechanically visible.
- Pinned model slugs will age. The lifecycle contract and explicit overrides
  provide detection and rollback.
- Changing parser defaults to profile-resolved values can accidentally break
  explicit model overrides. Dedicated precedence tests prevent this.
- Closeout Review always resolving hard increases cost, but Closeout Review is
  already exceptional and high-impact; normal closeout does not invoke it.
- The plan and implementation themselves exercise the runner while it is being
  changed. Plan review uses the pre-change runner with explicit hard model
  settings; implementation and closeout reviews dogfood the new behavior.

## Implementation Record

Implemented without scope divergence:

- added backend/tier profile resolution, exact automatic hard-signal policy,
  artifact-body validation, selection provenance, and timeout guidance to the
  bundled runner;
- updated structured-review, closeout, root runner guidance, and the current
  protocol map so structured-review remains the single policy owner;
- expanded structured-review coverage from 65 to 80 tests, including every
  phrase, the strict 1,000-line boundary, Review Threads exclusion, exact 2x2
  profiles, explicit override provenance, error paths, prompt/metadata fields,
  and timeout guidance.

Driver validation on 2026-07-20:

- structured-review: 80 tests passed;
- Scout: 31 tests passed;
- root: 18 tests passed;
- backlog validation, runner compilation/help smoke, and `git diff --check`
  passed.

Pending gates: implementation review, both read-only Codex model smokes,
Closeout Review, PR/CI verification, and human merge handoff.

## Review Threads

I've completed my inspection — runner code, closeout skill, docs, and a fresh test-suite run all verified against the plan's claims. Here is the complete review for the thread file.

I inspected the plan, the runner, the tests, the closeout skill, and the docs the plan proposes to change, and I re-ran all three test suites to confirm the claimed green baseline (65 + 31 + 18 = 114, all passing). The plan's description of current behavior is accurate throughout: the backend resolver matches the stated contract exactly, the current defaults are `opus`/`gpt-5.5` at `xhigh`, and the 1,000-line and multi-file heuristics do exist today as timeout-discipline prose. One issue blocks implementation; the rest is tightening. Here is my review.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

**Restated concern:** Is the accepted backend/model matrix, automatic normal-versus-hard tier policy, override precedence, prompt/metadata provenance, closeout boundary, lifecycle, and validation specified tightly enough that an implementer would not have to guess?

I inspected `docs/agent_plans/2026-07-20_review_tier_model_matrix_plan.md`, `structured-review/scripts/claude_structured_review.py` (backend resolver, argparse defaults, prompt builder, argv construction, metadata writer), `structured-review/tests/test_claude_structured_review.py` (including the existing SKILL-prose test precedent), `structured-review/SKILL.md`, `closeout/SKILL.md`, `README.md`, `docs/CURRENT.md`, and `docs/agent_plans/README.md`. I re-ran the three test suites; all green at the claimed counts (structured-review 65, scout 31, root 18). Validation provenance for that baseline is reviewer-rerun.

Verified plan claims, for the record:

- The backend contract in section 5 matches `resolve_reviewer_backend` exactly: Claude marker only -> Codex, Codex marker only -> Claude, neither -> Claude, both -> explicit-choice error, explicit backend wins.
- Current defaults are `opus` / `gpt-5.5` / `xhigh` as the Context states, and `--model`, `--effort`, `--codex-model`, `--codex-effort` all exist today.
- The 1,000-line and multi-file-implementation-review signals do mirror an existing heuristic (the SKILL timeout discipline), so signals 2 and 3 are anchored, not invented.
- `closeout/SKILL.md` already delegates runner policy ("this protocol does not duplicate that policy"), so section 6 is a small consistent addition, not a rewrite.
- The files-expected-to-change list is accurate: README has a runner-usage section, `docs/CURRENT.md` carries a Last-updated date to bump, and the plan index exists.
- The Review Gates section respects the closeout boundary: plan review concludes at ready-for-implementation, and merge-readiness stays with closeout.

#### Blocking issues

**Thread 1 — The complexity-signal table and its matching semantics are the core new policy, and they are not yet written down; two acceptance criteria cannot both be verified against a table that does not exist (blocking).**

Section 3 signal 4 defines six named categories, but the actual policy — the phrases and how they match — is deferred to implementation. This matters because plausible readings produce opposite behavior in this very repo:

1. **Phrase list is unwritten.** "Broad protocol change" could map to the keyword `protocol` (fires on essentially every plan in this repo, making `normal` unreachable) or to the literal phrase `broad protocol change` (fires almost never). Same spread for `release` vs `released`, `production` appearing in non-goals ("Do not change production behavior" is a stock non-goal line here), and `multi-agent` appearing in protocol prose. The acceptance criteria "small ordinary plan and implementation-plan artifacts resolve normal" and "every named high-complexity category resolves hard" pull in opposite directions, and which one wins depends entirely on the unwritten table. As drafted, the tests would define the accepted policy after the fact rather than pin a policy the human accepted.
2. **Matching semantics are unstated.** Case sensitivity, word/phrase boundaries, and substring behavior (`hard` in `hardware`, `production` in `reproduction`) change false-positive rates materially. One sentence fixes this.
3. **Scan scope is underspecified in a way that affects round-to-round determinism.** "Artifact or focus text" presumably means full artifact text — but does that include the `## Review Threads` section, which grows every round and quotes reviewer language dense with words like "production" and "security"? The same question applies to the >1,000-line count in signal 2: appended threads inflate the artifact, so a plan can silently flip normal -> hard between plan review and plan re-review. That flip may be acceptable (it errs conservative), but it should be a stated decision with a test pinning it, not an emergent artifact of `wc -l`.
4. **New I/O path needs a defined failure mode.** Today the runner never reads artifact contents (it only resolves paths); the tier scan makes it read every artifact. Define behavior for non-UTF-8 or unreadable artifacts (error vs. count-lines-only vs. skip-with-reason).

What clears this thread: pin the phrase table (it is small — the plan already insists it stay small and named), the matching rule, and the text-scope decision (including the Review Threads inclusion/exclusion choice for both the keyword scan and the line count) in the plan body or directly in the SKILL section this plan already designates as the policy owner. This is roughly fifteen lines of artifact text, not a re-plan. Without it, the implementer is not implementing an accepted policy; they are authoring one.

#### Non-blocking issues

**Thread 2 — Override precedence needs its detection mechanism named, and overridden values need provenance in the output (non-blocking).**

Section 1 says overrides apply "only when the corresponding explicit override was supplied," but the current parser gives all four flags concrete defaults, so supplied-vs-default is currently undetectable. The obvious fix is sentinel defaults (`default=None`), and the Risks section shows awareness of the hazard, but the plan never names the mechanism — one sentence would remove the last guess. Related provenance gap: when an explicit `--model` replaces a profile value, the new prompt block ("Tier selection: <reasons>" followed by "Model:") will imply the printed model came from the matrix when it did not — quietly recreating the exact provenance gap this plan exists to close. Recommend appending an explicit-override reason (or a `model_source` field in metadata) whenever a flag displaces a profile value, and adding that case to the precedence tests.

**Thread 3 — The Codex profiles reach main without a single live execution under this plan's own gates (non-blocking, residual risk).**

Because the driver is Codex, every in-plan review gate uses the Claude reviewer; `gpt-5.6-terra` and `gpt-5.6-sol` will only ever be asserted in argv-construction tests. Their usability provenance is the human's catalog check at plan time — which is recorded, and which I cannot independently verify from the reviewer sandbox (I did not fetch the cited provider pages; I am not disputing them, only noting the provenance layer). Cheap mitigation: a driver-run one-off smoke (`codex exec` with a trivial prompt against each slug) recorded at implementation review or closeout, or an explicit deferral note so closeout records the provenance honestly. The override flags remain the rollback either way, as the plan states.

**Thread 4 — Auto-hard tier and manual timeout selection now key off the same signals but are decoupled (non-blocking).**

Signals 2 and 3 replicate the large-review timeout heuristic, yet timeout stays manual with a 900-second default. Every auto-hard run driven by those signals (closeout-review, >1,000 lines, multi-artifact impl) pairs a slower, more deliberate model with the small-review timeout — a predictable timeout-then-rerun cost. The non-goal correctly keeps timeout behavior unchanged; the cheap fix is prose: have the SKILL note that hard-signal evidence usually also warrants `--timeout-sec 1800`, or have the runner log a one-line stderr notice when tier resolves hard under the default timeout. The plan's own gate 1 already pairs the hard model with 1800 seconds, so the pairing is understood — it just is not written as guidance.

#### Overall judgment

Not ready for implementation yet, on Thread 1 alone. The plan is otherwise strong: human decisions are recorded and separated from proposals, the backend contract matches the code exactly, non-goals fence scope cleanly, the matrix is pinned to full slugs with a real lifecycle contract (owner, staleness signals, removal process), the closeout boundary is handled by delegation rather than duplication, and the test list is implementable in the existing suite's style, including the SKILL-prose checks. Once the signal phrase table, matching rule, and scan-scope decision are pinned in the artifact body, this is ready for implementation. Threads 2 through 4 are driver's-choice tightening.

#### Residual risks and validation gaps

- **Negation and quotation false positives are accepted, not solved.** The plan owns this bias explicitly ("not production" classifying hard) and makes it visible in reasons/metadata. Note the sharper corollary once Thread 1 is settled: any artifact that documents the tier mechanism itself (SKILL and README diffs, future plans quoting the table) will scan hard under full-text matching. Conservative and cost-only, but worth knowing before the first "why was this trivial doc review hard-tier" question.
- **Tier flip across review rounds** (artifact growth via appended threads) is deterministic but surprising; resolve inside Thread 1's scope decision.
- **Codex slug liveness is deferred** (Thread 3); closeout should record its provenance as human-acceptance-plus-tests, not CI-backed, unless the smoke run is added.
- **Model positioning claims rest on cited provider pages plus recorded human acceptance.** That is the declared source-of-truth layer for this decision and it is documented in the plan; no in-repo validation can strengthen it further, only the lifecycle triggers can.

One blocking thread (Thread 1); no other blockers.

### Driver response 1

Accepted Thread 1 as blocking. The plan now pins the exact phrase table,
case-insensitive whole-word/phrase matching, category-only reason strings, and
the scan scope. Both line counting and keyword matching exclude the top-level
`## Review Threads` section so tier remains stable across review rounds; focus
text is scanned in full. Total lines use `splitlines()` and must be strictly
greater than 1,000. Missing, non-regular, unreadable, or non-UTF-8 artifacts
fail before reviewer invocation with a relative-path `RunnerError`.

Accepted Thread 2. The plan now requires `None` argparse sentinels for all four
provider-specific override flags and records `model_source` / `effort_source`
in prompt and metadata as either profile-derived or the exact explicit flag.

Accepted Thread 3. Closeout validation now includes one minimal read-only live
smoke for each Codex slug at `xhigh`; the result will be recorded as driver-run
provenance without treating it as CI-backed.

Accepted Thread 4. A hard-tier run that retains the default 900-second timeout
will emit non-fatal guidance to consider `--timeout-sec 1800`; timeout behavior
itself remains unchanged.

No reviewer finding changes the human-accepted matrix, cross-vendor backend
rule, two-tier scope, or merge authority. Ready for reviewer re-check of the
blocking thread and the accepted tightening changes.

The sweep gives concrete evidence: 3 of the 14 other plans would fire the keyword scan (mostly via quoted protocol vocabulary like `large review`), so `normal` remains the common case — the table achieves the balance pass 1 asked for. Everything checks out; here is the complete review for the thread file.

### Reviewer pass 2 (impl-plan, claude reviewer)

**Restated concern:** Did driver response 1 resolve blocking Thread 1, are the accepted Thread 2–4 changes now implementable without guessing, and does the revision delta introduce any new blocker?

Scope of this pass: I read the revision diff (`git show 5764cf1`), the full current plan body, and driver response 1, and spot-checked the runner against the claims the resolutions depend on. Confirmed: the four override flags carry concrete defaults today (`DEFAULT_MODEL` / `DEFAULT_EFFORT` / `DEFAULT_CODEX_MODEL` / `DEFAULT_CODEX_EFFORT` at `structured-review/scripts/claude_structured_review.py` lines 25–28), so the `None`-sentinel change is a real and necessary mechanism, not a no-op; `--timeout-sec` defaults to `DEFAULT_TIMEOUT_SEC = 900`; and the runner already owns a case-insensitive `^##\s+Review Threads\s*$` anchor (`REVIEW_THREADS_RE`, line 45), so the new scan-scope rule can reuse an existing, tested boundary rather than invent one. I also swept all 15 existing plans in `docs/agent_plans/` against the pinned phrase table: 3 of the 14 other plans contain at least one listed phrase (`large review`, `runtime behavior`, `multi-repo`, `migration plan`, `high-risk`), so under the new policy `normal` remains the common case and `hard` fires occasionally — the exact balance Thread 1 demanded, now verifiable against real corpus rather than assumed. No settled human decision is reopened by the revision: the matrix, cross-vendor backend rule, two-tier scope, and merge authority are untouched.

#### Thread resolutions

**Thread 1 — Resolved.** Artifact body updated in section 3. All four sub-points are closed: the phrase table is pinned (six categories, every entry a multi-word or hyphenated phrase — no bare `protocol`, `release`, or `production`, which was the failure mode that made `normal` unreachable); matching semantics are stated (case-insensitive, whole words/phrases, listed spellings only, category-name-only reasons); scan scope is decided for both the keyword scan and the line count (artifact body before the first top-level `## Review Threads` heading, focus text in full, `splitlines()` totals strictly greater than 1,000), making round-to-round tier stability a stated design property instead of an emergent artifact; and the new read path has a defined failure mode (missing, directory, unreadable, or non-UTF-8 artifact fails with a relative-path `RunnerError` before reviewer invocation, no silent skip or fallback to normal). The two acceptance criteria that previously pulled in opposite directions are now simultaneously verifiable, and the corpus sweep above confirms it empirically.

**Thread 2 — Resolved.** Artifact body updated in section 4 and the test list. `None` sentinels are named as the detection mechanism, and `model_source` / `effort_source` land in `RunConfig`, prompt, and metadata with pinned values (`profile` or the exact explicit flag). Minor and not a reopener: the prompt-block template in section 4 does not show the two source lines, but the paragraph after it requires them in the prompt and a test bullet asserts them, so no guessing of substance remains.

**Thread 3 — Resolved.** Artifact body updated in the Validation Plan. One minimal read-only live smoke per Codex slug at `xhigh` before closeout, recorded as driver-run provenance with unit tests kept as the argv source of truth — exactly the cheap mitigation proposed, with the provenance layer stated honestly rather than upgraded to CI-backed.

**Thread 4 — Resolved.** Artifact body updated in section 4 and the test list. The notice is non-fatal and timeout semantics stay inside the non-goal. Implementation note, not a condition: because `--timeout-sec` has a concrete default, "is the default 900" will most simply be implemented as `== 900`, which also fires the notice for an explicitly passed 900. That is harmless for a stderr hint; either detection reading satisfies the acceptance bullet.

#### Blocking issues

None. There are no blocking issues in this pass, and the revision delta introduces no new blocker.

#### Non-blocking issues

**Thread 5 — Two small gaps at the edges of the Thread 1 fix (non-blocking, driver's choice).**

1. Phrase-internal whitespace is unstated. Multi-word phrases wrap across lines in real markdown — this very plan renders `rollout plan` as `rollout` plus a newline and indentation inside its own section 3 list. If matching requires a literal single space, a wrapped phrase is a silent false negative, which is the direction the policy explicitly says it wants to avoid. One sentence fixes it: phrase-internal whitespace matches any whitespace run including newlines, or, alternatively, wrapped phrases are declared accepted misses.
2. The scan-scope decision has no pinning test. Pass 1 asked for the Review-Threads-exclusion choice to be a stated decision with a test pinning it; the decision is now stated in the body, but section 8 has no corresponding bullet. Add one: an artifact whose pre-threads body is small but whose `## Review Threads` section pushes the total past 1,000 lines resolves `normal`.

#### Overall judgment

Ready for implementation. Thread 1 is resolved at the level pass 1 asked for, Threads 2 through 4 are specified tightly enough to implement without guessing, and the delta stays inside the accepted human decisions and non-goals. Thread 5 is optional tightening the driver can fold into implementation or reject with a sentence; it does not gate the next step.

#### Residual risks and validation gaps

- Self-referential artifacts still scan hard because they quote the phrase table or protocol vocabulary; the corpus sweep makes this concrete (`large review` in the scout timeout plan is quoted timeout-discipline prose, and `README.md` line 3 contains `multi-agent`). Accepted cost-only bias carried over from pass 1, visible in reasons and metadata.
- The stricter artifact validation is a behavior change for previously tolerated bad inputs; it is strictly fail-fast and pre-invocation, so I see no regression path, and the existing-suite regression bullet in section 8 is what proves it.
- Codex slug liveness remains deferred to the pre-closeout smoke, with driver-run provenance recorded as such — unchanged from pass 1, now with a concrete mitigation in the plan.

No blocking threads open. Plan review concludes: ready for implementation.

### Driver response 2

Accepted optional Thread 5. Phrase-internal whitespace now matches any
non-empty whitespace run, including Markdown wrapping across lines, and the
test plan now pins that an oversized `## Review Threads` section cannot change
a small ordinary artifact from normal to hard. These tighten the accepted scan
semantics without changing scope or requiring another plan-review gate.

All verification is complete — full diff inspected, all 128 tests re-run green, static checks pass, three live dry-run smokes confirm the tier policy end-to-end, and the phrase table matches the plan verbatim. Here is the complete review for the thread file.

I inspected the full branch diff against `origin/main` (runner, tests, both SKILL files, README, docs map, plan index), re-ran every validation command in the plan, and exercised the new selection policy live with three read-only dry runs. The implementation matches the accepted plan without scope divergence. There are no blocking issues.

---

### Reviewer pass 3 (impl, claude reviewer)

**Restated concern:** Does the implemented runner, test suite, and documentation match the accepted plan — the pinned 2x2 matrix, deterministic tier classification, override precedence and provenance, single-sourced policy prose — without regressing the existing review-gate machinery?

Scope of this pass: the complete branch diff `origin/main..HEAD` (verified read in full: 312-line runner diff, 312-line test diff, all four doc diffs), the current runner source around every new code path, and the plan's Implementation Record. Validation provenance is reviewer-rerun unless noted: structured-review 79, Scout 31, root 18 tests — all green; `python -m compileall -q structured-review scout scripts tests`, `python scripts/check_backlog.py`, runner `--help`, and `git diff --check` all pass. I additionally ran three live `--dry-run` smokes: a small ordinary artifact resolved `normal` with `Model source: profile`; a focus naming `schema migration` and `rollout plan` resolved `hard` with exactly the two category-name reasons; and `--reviewer-backend codex --review-tier hard --codex-model gpt-custom` produced `Model: gpt-custom`, `Model source: explicit --codex-model`, `Effort source: profile` — mixed provenance recorded correctly. Finally, this review is itself a dogfood run of the new routing: my own prompt carried tier `hard` from six complexity-signal reasons with profile provenance, exactly as the policy predicts for a self-referential artifact.

#### Plan-to-implementation traceability

- Backend contract unchanged — **Done.** No `+`/`-` diff line touches `resolve_reviewer_backend` or the driver-marker constants; pre-existing backend tests remain green.
- `--review-tier auto` default, deterministic — **Done.** Parser defaults to `auto`; `resolve_review_tier` uses only review type, `splitlines()` counts, artifact count, and the pinned regex table — no model calls, clock, or randomness.
- Small ordinary artifact resolves `normal` — **Done.** Pinned by test and confirmed by live dry-run.
- `closeout-review`, >1,000 body lines, multi-artifact `impl`, and every named category resolve `hard` — **Done.** Tests cover all four signals; the phrase test iterates all 31 phrases individually; the boundary test pins 1,000 lines → `normal` and 1,001 → `hard`; the threads-exclusion test pins that an oversized `## Review Threads` section (1,500 lines of `security review`) changes neither the count nor the keyword scan — the Thread 5 test ask, delivered.
- Phrase table fidelity — **Done.** I programmatically extracted the runner's `HARD_COMPLEXITY_SIGNAL_PHRASES` and matched all 31 phrases verbatim against the plan body's backticked table; none missing, none extra. Matching semantics implement the accepted spec: `(?<!\w)…(?!\w)` boundaries (`preproduction changeover` stays normal — tested), `re.IGNORECASE`, `\s+` for phrase-internal whitespace including line wraps (tested), hyphenated phrases literal, reasons record category names only.
- Exact 2x2 profiles — **Done.** `REVIEW_MODEL_MATRIX` pins `claude-opus-4-8`/`claude-fable-5`/`gpt-5.6-terra`/`gpt-5.6-sol`, all `xhigh`; the matrix test asserts all four pairs.
- Override precedence and provenance — **Done.** All four provider flags now parse with `None` sentinels; `resolve_review_profile` replaces only supplied values and stamps `model_source`/`effort_source` as `profile` or the exact flag; tested on both the claude (`--model`) and codex (`--codex-model`/`--codex-effort`) sides and confirmed live.
- Artifact validation — **Done.** Missing, directory, unreadable, and non-UTF-8 artifacts all raise a relative-path `RunnerError` before reviewer invocation, including under an explicit tier (bodies are read before the explicit-tier early return); each case is tested.
- Prompt, start log, metadata — **Done.** The reviewer-selection block sits before task-specific focus with backend, tier, reasons, model, model source, effort, effort source, and the routing-only sentence; the start log gains `tier=`; `metadata.json` gains `review_tier`, `review_tier_reasons`, `model_source`, `effort_source` — all tested.
- Timeout guidance — **Done.** The non-fatal notice fires in the shared `run_claude` path (so it covers both backends) when tier is `hard` and `timeout_sec == 900`, without mutating the timeout; tested.
- Documentation single-sourcing — **Done.** `structured-review/SKILL.md` owns the backend rule, tier signals, matrix, override guidance, and lifecycle; `closeout/SKILL.md` delegates backend/tier/model/effort and forbids a competing closeout matrix; `README.md` summarizes `--review-tier` and the profiles; `docs/CURRENT.md` describes the routing with a bumped date; the plan is indexed in `docs/agent_plans/README.md`. The prose test pins the SKILL slugs and the closeout delegation sentences. No stale `gpt-5.5`/`opus` reference remains outside historical plans, per the plan's non-goal.
- No regression to write-mode, git verification, sandbox, stream parsing, timeout, secret scanning, or path redaction — **Done** (reviewer-rerun). The runner diff touches those paths only additively (two stderr prints, one prompt block, four metadata keys); all pre-existing tests pass.
- Test-count claim — **Done.** The Implementation Record's 65 → 79 claim matches: exactly 14 new test methods in the diff, 79 green on rerun.
- PR opened from `feature/review-tier-model-matrix` — **Deferred** to closeout by the plan's own gate ordering. Honest state: the branch is local-only, 6 commits ahead of `origin/main`, unpushed; no PR or CI exists yet.
- Codex live smokes (`gpt-5.6-terra`, `gpt-5.6-sol`) — **Deferred** to pre-closeout as the plan specifies; not yet run.

#### Blocking issues

None. There are no blocking issues in this pass.

#### Non-blocking issues

**Thread 6 — A non-selected provider's override flag is accepted and silently dropped (non-blocking, driver's choice).**

`resolve_review_profile` applies only the resolved backend's override pair, so with `--reviewer-backend auto` a caller can pin a model that never takes effect: in a Claude-driver environment (auto → codex reviewer), `--model claude-fable-5` parses cleanly and is discarded, and the run proceeds on `gpt-5.6-sol`/`gpt-5.6-terra` with `model_source: profile`. The metadata is truthful about what ran, but nothing surfaces that a supplied flag did nothing — the exact quiet-provenance shape this plan otherwise eliminates, though here it is pre-existing, documented semantics ("override only the selected backend's profile"). Cheap options: a one-line stderr notice when an override for the non-selected provider was supplied, a backlog entry, or an explicit one-sentence rejection in the driver response. None of these gates closeout.

#### Overall judgment

Ready for closeout. The implementation is faithful to the accepted plan at every point I could verify: the pinned matrix, the exact 31-phrase policy, strict-greater-than line threshold, Review Threads exclusion, explicit-tier and per-provider override precedence with honest provenance, fail-fast artifact validation, and single-sourced prose with tests pinning the load-bearing strings. Validation is reviewer-rerun end to end, including live dry-run exercise of normal, auto-hard, and explicit-override paths. Thread 6 is optional tightening. The pending gates the plan itself names — both Codex model smokes, Closeout Review, PR/CI verification, and human merge — belong to closeout, and the plan's status line states its own state accurately.

#### Residual risks and validation gaps

- **The self-referential hard bias is now observed in production, not just predicted:** this review's own run fired all six complexity categories on the plan document (which quotes the full phrase table) and routed to `claude-fable-5`. Cost-only, visible in the recorded reasons, and consistent with the accepted conservative design.
- **Phrase matching can span input seams:** `resolve_review_tier` joins focus and artifact bodies with a single newline and `\s+` crosses paragraph breaks, so a phrase can assemble across a boundary (for example a body line ending `security` followed by a line starting `review`). Strictly conservative direction — it can only promote to `hard` — and within the plan's stated whitespace rule, but worth knowing when a surprising category reason appears.
- **A non-UTF-8 `--focus-file` still raises a raw `UnicodeDecodeError`** rather than a `RunnerError`; the plan scoped fail-fast validation to artifacts, so this is pre-existing behavior outside accepted scope, noted for a future polish pass.
- **README and `docs/CURRENT.md` name the models in prose and are not test-pinned** (the prose test covers `structured-review/SKILL.md` and `closeout/SKILL.md`); keeping them synchronized on a future model change rests on the lifecycle checklist, which does name both files.
- **Codex slug liveness remains unverified** until the deferred driver-run smokes; unit tests prove argv construction only. Closeout should record that provenance as driver-run, not CI-backed.
- **The review target is unpushed** — closeout's branch/PR/CI verification is still ahead, and nothing in this pass substitutes for it.

No blocking threads open. Implementation review concludes: ready for closeout.

### Driver response 3

Accepted non-blocking Thread 6. The runner now emits a one-line stderr warning
when a model or effort override belongs to the non-selected provider, while
continuing to record the effective selected profile truthfully. Added coverage
for both directions (`claude` with a Codex-only flag and `codex` with a
Claude-only flag). This is an observability tightening only; the documented
override precedence and selected profile are unchanged. Implementation
Re-review will verify the delta before closeout.

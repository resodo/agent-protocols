# Structured Review Tier And Model Matrix Plan

Status: active implementation driver
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
   - production/runtime/deploy/rollout;
   - architecture/migration;
   - security/data safety;
   - multi-repo/multi-agent/release;
   - broad protocol change;
   - explicit `complex` / `high-risk` / `hard review` wording.

Otherwise resolve `normal`.

The complexity scan is intentionally conservative: a false-positive `hard`
selection costs more but preserves review quality; a false-negative can
underpower a high-impact gate. Keep the signal table small and named. Do not
derive tier from arbitrary token counts, reviewer output, git churn, or hidden
provider behavior.

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
- multi-artifact `impl` -> hard;
- each named complexity category -> hard;
- model and effort flags override only the selected provider profile;
- Claude and Codex argv receive the resolved profile;
- prompt contains backend, tier, reasons, model, and effort;
- metadata contains resolved tier and reasons;
- stderr start log names the tier;
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

## Review Threads


# Explicit Review Tier Ownership Plan

Status: active implementation driver
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
- `--tier-reason` with `auto` fails because it would imply driver ownership
  without an explicit tier.

This staged behavior prevents existing callers from failing all at once while
also removing the paid-model hazard immediately. Removing `auto` or making an
omitted tier fail closed is a later reviewed change after downstream callers
have migrated.

The existing provider override flags remain available. The pinned hard-profile
models (`claude-fable-5` and `gpt-5.6-sol`) cannot be selected through a normal
or auto tier override; callers must select `hard` and provide the reason.
Other explicit custom model/effort overrides retain their existing provenance.

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
this repo, so an additive schema change is sufficient.

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
- pinned hard-profile model override without explicit hard/reason -> fail;
- `auto` compatibility warning and no auto-upgrade;
- selection, rationale, recommendation, final model, and source in prompt and
  metadata;
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

## Review Threads


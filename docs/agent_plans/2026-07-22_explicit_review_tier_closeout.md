# Explicit Review Tier Ownership Closeout Evidence

Status: artifact for shared protocol PR #27
Scope: driver-owned structured-review tier selection and recommendation-only
runner signals

## Scope Reality

Changed:

- structured-review runner tier selection, rationale validation, hard-profile
  override guard, prompt/start-log/metadata provenance, CLI help, and tests;
- structured-review and closeout protocol guidance;
- root runner usage and current protocol map;
- the dated implementation/review plan and its index entry.

Unchanged:

- reviewer backend auto-selection;
- normal/hard profile matrix and `xhigh` effort;
- review scope and readiness quality gate;
- timeout enforcement, reviewer sandbox, streaming, write/commit verification,
  provider authentication, and downstream repository contents;
- readiness/bootstrap documents, which contain no tier/model-routing call site.

## Acceptance Traceability

| Acceptance item | Status | Evidence |
| --- | --- | --- |
| Closeout type does not auto-route hard | Done | Unit tests cover explicit normal and legacy auto Closeout Review; the latter recommends hard but selects Opus/normal. |
| Multi-artifact implementation review does not auto-route hard | Done | Unit test uses legacy auto with two artifacts and asserts normal/Opus plus hard recommendation. |
| More than 1,000 body lines does not auto-route hard | Done | Boundary test uses legacy auto at 1,000 and 1,001 lines; 1,001 recommends hard but remains normal/Opus. |
| Production/runtime/migration/security and related keywords do not auto-route hard | Done | Every signal phrase is recommendation-tested; representative categories use legacy auto and assert normal/Opus. |
| Explicit normal routes Opus | Done | Exact 2x2 matrix test and CLI dry-run show `claude-opus-4-8` / `xhigh`. |
| Explicit hard routes Fable only with rationale | Done | Matrix/argument tests and configuration-only dry-run show `claude-fable-5` / `xhigh` with driver reason. No Fable review was invoked. |
| Hard without reason fails closed | Done | Unit test and CLI case fail before reviewer invocation; whitespace-only reason is also rejected. |
| Recommendation cannot change selected tier/model | Done | Separate configuration fields, regression tests, dry-runs, and the seven-artifact Implementation Review dogfood prove the boundary. |
| Prompt and metadata record both provenance layers and final profile | Done | Prompt/metadata tests assert selected tier/source/reason, recommended tier/reasons, model/effort, and sources; start-log coverage asserts the same selection/recommendation split. |
| Legacy auto compatibility is explicit and safe | Done | Omitted/auto selects normal, warns, records `legacy-auto-compatibility`, and cannot bypass through the selected backend hard-model slug. |
| Existing tests, docs, and gates remain consistent | Done | Driver and reviewer validations below are green; live docs have no stale auto-hard claim. |

## Validation Provenance

Driver-reported and reproduced after implementation commit:

- `python -m unittest discover -s structured-review/tests -p 'test_*.py' -v`:
  87 passed;
- `python -m unittest discover -s scout/tests -p 'test_*.py' -v`: 31 passed;
- `python -m unittest discover -s tests -p 'test_*.py' -v`: 18 passed;
- `python -m compileall -q structured-review scout scripts tests`: passed;
- `python scripts/check_backlog.py`: passed;
- runner `--help` and `git diff --check`: passed;
- CLI cases: explicit normal passed on Opus profile; explicit hard with reason
  passed configuration on Fable profile without invoking Fable; legacy-auto
  Closeout Review stayed Opus/normal while recommending hard; hard without
  reason exited 1 before reviewer invocation.
- local run-metadata audit: all four successful reviewer invocations in this
  worktree record `claude-opus-4-8` / `xhigh` and return code 0; no reviewer
  invocation records Fable. The two post-implementation runs also record
  selected normal and recommended hard.

Reviewer-rerun provenance:

- Plan Review and Plan Re-review used Claude `claude-opus-4-8` / `xhigh` /
  explicit normal; four non-blocking plan-clarity threads were accepted and
  resolved before implementation;
- Implementation Review used the same explicit Opus profile, independently
  reproduced 87 + 31 + 18 tests, static checks, and dry-runs, found no blocking
  or non-blocking issues, and concluded `ready for closeout`;
- the Implementation Review itself received a hard recommendation from 4,173
  artifact lines, seven artifacts, and all signal categories, but still ran on
  explicitly selected normal/Opus. This is direct dogfood evidence.

CI-backed provenance:

- PR #27 `CI / python` passed on the initial pushed review head. Final PR-head
  status is verified from live PR checks during handoff rather than frozen in
  this artifact.

## Documentation And Mechanism Lifecycle

- `structured-review/SKILL.md` owns explicit tier selection, the profile
  matrix, recommendation signals, hard rationale rules, override guard, and
  legacy-auto lifecycle.
- A future auto removal is a separate reviewed protocol change after known
  consumers migrate; runner, tests, SKILL, README, current map, and downstream
  guidance must change together.
- `closeout/SKILL.md` retains Closeout Review triggers but no longer owns a
  competing tier policy.
- `README.md` and `docs/CURRENT.md` point new callers to explicit normal/hard.
- The 2026-07-20 automatic-tier plan remains untouched historical provenance.
- `agent-readiness/agents-bootstrap-template.md` and
  `agent-readiness/worktree-guard.md` were inspected and correctly require no
  change.
- The repo has no separate changelog/release-notes convention; this artifact,
  the reviewed plan, PR, and current map are the durable record.

## Safety And Git Hygiene

- This change commits no secrets, credentials, private account details, local
  user-home absolute paths, or generated private run outputs.
- Work occurred in linked worktree branch `feature/explicit-review-tier`, based
  on fetched `origin/main`; the main checkout was not edited.
- PR #27 targets `main`, is open and non-draft, and no merge was performed.
- No downstream submodule content was edited.

## Compatibility And Rollout Handoff

Existing omitted/auto calls continue instead of failing, but always use the
normal profile with a deprecation warning. New formal calls must use:

```text
--review-tier normal
```

or, only for genuine semantic difficulty:

```text
--review-tier hard --tier-reason "<specific reason>"
```

After a named human merges PR #27, the push-to-main repository dispatch should
trigger `skynet-intern` to open its normal submodule-bump flow. That downstream
PR should point `external/agent-protocols` at the merged shared-repo `main`
commit, update runner call sites to explicit tier, verify the skill mounts, run
the consumer guard/tests, and avoid direct edits inside the vendored submodule.

## Residual Risks

- Legacy callers still lack explicit driver ownership until migrated, but they
  cannot reach the pinned hard model and their compatibility source is visible.
- Deprecated metadata alias `review_tier_reasons` now contains selection
  provenance rather than recommendation signals; the new fields are the
  authoritative schema and the only in-repo consumers were updated.
- Pinned model slugs and the recommendation table require lifecycle maintenance
  under the structured-review contract.

Final merge authority remains human-owned. This artifact does not authorize or
record a merge.

# Review / Closeout Boundary Plan

Status: Draft for structured review

## Human Concern

Review and closeout are separate skills. Repo-backed structured-review gates
should default to the Claude runner, but closeout should remain a driver-owned
delivery checklist and should not silently become another mandatory
cross-agent/Claude review gate.

## Goal

Make the shared protocol explicit about:

- structured-review is the quality gate for plans, implementations, and
  optional closeout-report reviews;
- implementation review can say `ready for closeout`, not `ready for human
  merge`;
- closeout is the delivery gate and the only default protocol step that may
  hand off `ready for human merge`;
- closeout does not invoke Claude or another reviewer by default;
- driver must decide after reviewer output whether to accept, reject, defer, or
  escalate before making changes;
- Closeout Review is optional and triggered only by defined risk or explicit
  human request.

## Scope

1. Update `structured-review/SKILL.md`.
   - Add a boundary section between review and closeout.
   - Define normal next-step language:
     - plan review: `ready for implementation`;
     - implementation review: `ready for closeout`;
     - closeout-report review: `ready to resume closeout` or report blockers.
   - Forbid ordinary plan/implementation reviews from claiming `ready for
     human merge`.
   - Define `closeout-review` as an optional structured-review use case that
     reviews closeout evidence/report accuracy, not merge authority.

2. Update `closeout/SKILL.md`.
   - Add an explicit "Review Boundary" section.
   - State that closeout is driver-owned and does not run Claude/cross-agent
     review by default.
   - Require the driver to confirm relevant structured-review gates are already
     resolved before final handoff.
   - Define when closeout should trigger a Closeout Review:
     - human explicitly asks for one;
     - closeout artifact/report itself is durable or high-impact enough to
       review;
     - rebase/conflict touched source-of-truth docs, protocol files, tests, CI,
       deploy/runtime templates, or similar contracts;
     - the closeout spans a large phase, release, or multi-repo handoff;
     - validation provenance, PR/CI status, merge ancestry, or submodule final
       pointer is ambiguous;
     - the driver cannot classify residual risk without an independent reviewer.
   - Clarify that Closeout Review returns to closeout; it does not replace
     closeout and does not grant merge permission.

3. Update `README.md` only if its current workflow text conflicts with this
   boundary.

## Non-Goals

- Do not change Claude runner flags, permissions, logging, or artifact format.
- Do not make closeout default to Claude or a second coding agent.
- Do not add skynet-v2, skynet-data, or skynet-ops overlay changes in this PR.
- Do not grant the agent standing merge authority through protocol text.
- Do not create new long reference files unless the SKILL.md bodies become too
  large.

## Acceptance

- `structured-review/SKILL.md` clearly separates plan/implementation review
  readiness from merge readiness.
- `closeout/SKILL.md` clearly says closeout is the driver-owned delivery gate
  and only escalates to Closeout Review on defined triggers.
- No normal structured-review wording instructs a reviewer to say `ready for
  human merge` for a plan or implementation artifact.
- Closeout remains the place that may report `ready for human merge` after
  final rechecks.
- README, if changed, matches the same boundary.
- The work uses relative repo paths only in tracked content.

## Validation Plan

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
rg -n "ready for implementation|ready for closeout|ready for human merge|Closeout Review|Review Boundary" structured-review/SKILL.md closeout/SKILL.md README.md
git diff --check
```

## Downstream Follow-Up

After this shared protocol PR merges:

1. Update `skynet-v2` external submodule pointer and overlay wording if needed.
2. Update `skynet-data` external submodule pointer and overlay wording if needed.
3. Do not update `skynet-ops` unless a real incompatibility appears.

## Review Threads

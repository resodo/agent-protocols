# Scout Active-Surface Suppression And Review Timeout Plan

Status: active implementation plan

## Context

Two protocol gaps showed up during downstream use:

- A cold-start Scout run proposed a cleanup candidate for an actively developed
  Hot Watch surface. The finding was real enough to observe, but too early for
  backlog tracking while the feature is still moving.
- Codex-driven structured-review runs can set a long timeout for a Claude
  reviewer and still stop waiting early. The protocol needs to say that a
  configured timeout is the wait budget: the driver waits until the reviewer
  exits, the timeout expires, or an external interruption occurs.

## Goals

1. Prevent Scout from opening cleanup/refactor/dead-helper candidates against
   active feature surfaces by default.
2. Keep active feature observations visible as report-only evidence unless
   they are safety, correctness, data-safety, production-risk, or CI-blocking
   issues, or the human explicitly asks Scout to review that active surface for
   immediate action.
3. Define structured-review runner wait discipline: small/medium reviews use a
   15-minute timeout by default, large reviews use 30 minutes by explicit
   timeout, and drivers must not kill the reviewer early just because no output
   has appeared.
4. Add focused tests for the runner timeout default and timeout behavior.

## Non-Goals

- Do not change Scout runner schema or require overlays to declare active
  feature surfaces in this PR.
- Do not auto-detect feature activity mechanically from churn alone.
- Do not change reviewer model defaults.
- Do not change closeout or backlog-maintenance lifecycle state rules.
- Do not re-open or rewrite downstream PRs; the downstream Hot Watch backlog PR
  was closed separately as invalid under the new intended rule.

## Implementation Plan

1. Update `scout/SKILL.md`:
   - Add an active feature suppression rule under candidate rules.
   - Require Scout reports to classify suppressed active-surface cleanup as
     report-only and name the active owner/plan/backlog item when known.
2. Update Scout references:
   - `code-structure`: large/high-churn active feature surfaces are
     suppressors for cleanup candidates, not automatic split candidates.
   - `code-reachability-backend-python`: unused helpers/payload residue inside
     active feature surfaces are report-only unless safety/correctness/blocker.
   - `script-lifecycle`: active rollout/operator scripts are report-only until
     the rollout stabilizes unless they pose safety or CI risk.
   - `document-structure`: active plans can be long and messy while they are
     carrying current work; structure cleanup candidates should wait until the
     active phase stabilizes unless the document is misleading agents today.
3. Update `structured-review/SKILL.md`:
   - Add timeout sizing guidance: 900 seconds for small/medium review gates,
     1800 seconds for large review gates.
   - State that once the driver invokes the runner with a timeout, it must wait
     for completion, timeout, or external interruption; no early kill for
     impatience/no-output.
4. Update `structured-review/scripts/claude_structured_review.py`:
   - Change default timeout from 1800 to 900 seconds.
   - Make the start log include `timeout_sec` so the intended wait budget is
     visible in long runs.
   - Keep the existing process kill only at actual timeout.
5. Update `structured-review/tests/test_claude_structured_review.py`:
   - Assert the default timeout is 900 seconds.
   - Assert the runner waits for a quiet reviewer until it exits before the
     timeout instead of treating silence as failure.
6. Update indexes if needed:
   - `docs/CURRENT.md` only if runner behavior or reference map changes in a
     way the current map must mention. The likely change is not needed because
     no paths or protocol entrypoints change.

## Validation

- `python -m pytest structured-review/tests/test_claude_structured_review.py`
- `python -m pytest scout/tests/test_scout_runner.py`
- `python -m pytest tests/test_skill_frontmatter.py`
- `python -m pytest`
- `git diff --check`
- `python scripts/check_backlog.py`

## Acceptance

- Scout instructions make active feature cleanup/refactor/dead-helper findings
  report-only by default.
- The structured-review protocol clearly tells drivers to wait for the runner's
  configured timeout instead of killing reviewer processes early.
- Runner default timeout is 15 minutes, while large reviews can use 30 minutes
  through `--timeout-sec 1800`.
- Tests cover the changed timeout default and quiet-reviewer wait behavior.

## Review Threads


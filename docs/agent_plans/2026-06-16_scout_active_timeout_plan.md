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

I've inspected the plan, the four Scout references, the Scout `SKILL.md`, the structured-review `SKILL.md`, the runner script and its tests, `docs/CURRENT.md`, and confirmed the baseline (105 tests pass, backlog and `git diff --check` clean). Verified key claims: the runner default is indeed `DEFAULT_TIMEOUT_SEC = 1800` (line 29), the start log at lines 830-833 omits `timeout_sec`, and the timeout kill fires only on total elapsed time — silence triggers only a heartbeat log, never a kill (lines 853-865). `docs/CURRENT.md` does not encode the timeout value, so step 6's "no change needed" is correct.

Here is my review.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

Human's concern, restated: this plan should make Scout stop proposing cleanup/refactor/dead-code candidates against feature surfaces that are still being actively built, while keeping the structured-review runner from being abandoned before its configured timeout — and the plan must be concrete enough to implement and validate without guessing.

I inspected all referenced artifacts before judging. Two issues block readiness; the rest are non-blocking. I am not endorsing it as ready for implementation yet.

#### Thread 1 (blocking): "active feature surface" is undefined, and both obvious detection mechanisms are excluded

The entire Scout half of this plan turns on the concept "active feature surface," but the plan never defines how Scout decides a surface is one — and the Non-Goals remove the two mechanisms a reader would reach for:
- "Do not change Scout runner schema or require overlays to declare active feature surfaces" (no declarative source);
- "Do not auto-detect feature activity mechanically from churn alone" (churn is explicitly insufficient).

This leaves a hole. An implementer editing four references (`code-structure`, `code-reachability-backend-python`, `script-lifecycle`, `document-structure`) plus `scout/SKILL.md` has no shared definition to write, and the four edits will almost certainly diverge. Every existing subskill reference carries an explicit "Evidence Standard" list (active routing evidence, active entrypoint evidence, etc.); the new suppressor needs the parallel thing: an enumerated set of positive signals that establish "active feature under current development" (e.g., an active plan under `docs/agent_plans/`, an in-progress backlog item, a named owner, an explicit Hot Watch designation), plus what to do when activity is uncertain.

The motivating example pressure-tests this precisely. The Context says Scout wrongly proposed a backlog candidate for an "actively developed Hot Watch surface," and that the downstream backlog item was the very thing Scout should not have created. So at scan time that surface may have had no plan and no backlog item yet. If the suppression signal is "an active owner/plan/backlog item exists," the motivating case may slip through the rule meant to catch it. The plan must state:
1. what counts as evidence of an active feature surface (positive signal list), and
2. the default when activity is plausible but unproven (suppress to report-only, or admit as candidate).

Without (1) and (2), implementation requires guessing on the plan's central concept.

Note on the Mechanism Lifecycle lens: because the plan deliberately avoids a maintained allowlist and leans on judgment, the usual "who maintains the list / how do stale entries get removed" concern is largely avoided — that is a good choice. But it makes the evidence-definition above the load-bearing part, which is exactly what is missing.

#### Thread 2 (blocking): the wait-discipline prose has an "external interruption" loophole and does not address the real mechanism behind early kills

The runner already does not kill on silence. The kill at lines 855-858 fires only when total elapsed time exceeds `--timeout-sec`; a quiet reviewer just produces heartbeat logs and is waited on. So the reported failure ("Codex-driven runs can set a long timeout for a Claude reviewer and still stop waiting early") does not originate in the runner — it originates outside it, in the driver's own subprocess/tool timeout (or a manual interrupt) being shorter than `--timeout-sec`.

Given that, the drafted guidance in step 3 — "it must wait for completion, timeout, or external interruption; no early kill for impatience/no-output" — does not close the loop, for two reasons:
- "external interruption" is undefined and self-justifiable. A driver whose own bash/tool timeout fires at 5 minutes can call that an "external interruption" and consider itself compliant, which is exactly the behavior the plan is trying to stop. The SKILL needs to distinguish a genuine external interruption (human Ctrl-C, OS signal, infra failure) from the driver's own impatience-configured short timeout, and say the latter is not permitted.
- The actionable rule is missing: the driver must size its own outer wait (the bash/tool timeout it wraps the runner in) to at least the runner's `--timeout-sec`. Telling an agent to "be patient" without telling it to set its outer timeout `>=` the runner timeout leaves the failure mode fully intact, because the harness kills the subprocess regardless of the agent's intent.

Please make step 3 state the outer-timeout sizing requirement explicitly and define "external interruption" narrowly. As currently written, the fix may not prevent the failure it targets.

#### Thread 3 (non-blocking): exception sets are applied unevenly across the four references

Goal 2 names a canonical override list (safety, correctness, data-safety, production-risk, CI-blocking, or explicit human request). Step 2 then restates it differently per reference:
- `code-structure`: no exceptions restated ("suppressors for cleanup candidates, not automatic split candidates");
- `code-reachability`: "unless safety/correctness/blocker";
- `script-lifecycle`: "unless they pose safety or CI risk" (drops correctness, data-safety, production-risk);
- `document-structure`: "unless the document is misleading agents today" (a different, doc-appropriate override).

Decide and state whether the Goal-2 list is the canonical override set each reference must carry, or whether per-domain tailoring is intentional. Otherwise the implementer guesses whether to paste the full list or the abbreviated phrasing into each file. The doc-specific override for `document-structure` looks deliberate and reasonable; the `script-lifecycle` and `code-structure` omissions read as drift rather than intent.

#### Thread 4 (non-blocking): distinguish "active code" (normal candidate target) from "actively-being-built feature" (new suppressor)

`code-structure` already requires, in Candidate Admission, that "the module or cluster is active code under declared roots." So "active" already means "in-use / maintained" and is a precondition for candidacy. The new rule introduces a second sense of "active" — "currently under feature development" — that suppresses candidacy. If the references are not careful, the new rule can be read as "suppress all candidates, since all candidates are active code." Please have the plan instruct the implementer to name the distinction explicitly in the prose (maintained-and-stable vs being-actively-built), so the suppressor narrows the pool rather than emptying it. This ties back to Thread 1's evidence definition.

#### Thread 5 (non-blocking): no re-evaluation path for suppressed report-only observations

Goal 2 keeps suppressed findings "visible as report-only evidence," and the references say cleanup "should wait until the active phase stabilizes." But nothing says how or when a report-only observation is reconsidered once the surface stops being active. Per the Mechanism Lifecycle lens, a suppressed observation that is never revisited is a silent drop. The natural answer for a periodic discovery protocol is "the next Scout run re-evaluates report-only active-surface observations; once the activity signals are gone, normal admission applies" — please state that (or whatever the intended trigger is) so suppression is a deferral, not a disappearance.

#### Thread 6 (non-blocking): the default-timeout reduction is orthogonal to the stated problem and can reintroduce real timeouts

Problem #2 is "drivers stop waiting too early." Lowering the default from 1800 to 900 does not address that (the prose does) and points the opposite direction for the default case. It is a defensible independent change — most small/medium reviews finish well under 15 minutes, and forcing large reviews to opt into 1800 is reasonable — but please confirm it is wanted on its own merits, and note the tradeoff: a timeout discards the whole run and exits 2 (lines 1016-1019), so a legitimately long review that a driver forgets to size up now fails at 15 minutes where it previously had 30. To make the opt-in usable, the SKILL guidance should give at least a rough "large review" heuristic (e.g., multi-file `impl` reviews or artifacts over some size), rather than leaving "small/medium vs large" to unaided vibe.

#### Thread 7 (non-blocking): step 5 test framing and flakiness; consider locking the prose and log invariants

- Framing: since the runner already never kills on silence, the "waits for a quiet reviewer" test is a regression guard on existing behavior, not coverage of a new code path. Step 5's wording ("instead of treating silence as failure") could mislead the implementer into thinking the runner's wait loop needs changing — it does not. Recommend the plan say plainly that the only runner code changes are the default constant and the start-log line, and that the quiet-reviewer test is a characterization/regression guard.
- Flakiness: a quiet-reviewer test built on a fake binary that sleeps past the heartbeat but under the timeout introduces real wall-clock into the suite. Specify the approach (small `--heartbeat-sec`, a modest sleep, a generous `--timeout-sec`) or make the loop clock-injectable, so it does not become flaky.
- Coverage symmetry: the repo already locks SKILL invariants with string-assertion tests (`test_skill_separates_review_readiness_from_closeout_handoff`). Consider one small assertion for the new wait-discipline language in `structured-review/SKILL.md`, and one asserting `timeout_sec` appears in the start log — both cheap, and they make the "tests cover the changed behavior" acceptance real for the protocol prose, not just the constant.

#### Thread 8 (non-blocking): be honest that the Scout-side acceptance has no mechanical validation

The Validation section lists `pytest scout/tests/test_scout_runner.py` and the full suite, but those exercise runner mechanics, not the reference prose this PR actually changes. The Scout-side acceptance ("instructions make active feature cleanup/refactor/dead-helper findings report-only by default") is validated by reading the edited references, not by any test. That is fine for a protocol-prose change, but the plan should say so plainly so the next agent does not mistake a green suite for validation of the Scout behavior. Separately, the historical `docs/agent_plans/2026-06-04_claude_runner_plan.md` records "default 1800"; by this repo's convention dated plans are historical provenance and `docs/CURRENT.md` is the live map (and it does not encode the value), so leaving the old plan untouched is correct — a one-line acknowledgment that the historical figure is intentionally left as-is would remove any doubt.

#### Overall judgment

Not yet ready for implementation. The timeout half is mostly sound and accurately grounded in the code (the default-change, the start-log addition, and "keep the kill only at actual timeout" all match the current runner), but Thread 2 shows the wait-discipline prose, as drafted, may not actually stop the reported early-kill behavior. The Scout half has a load-bearing gap (Thread 1): its central concept is undefined and the two obvious definitions are ruled out, which guarantees divergent edits across four references. Resolve Threads 1 and 2, and the plan is close; Threads 3-5 materially improve correctness and consistency and are worth folding in before implementation; Threads 6-8 are tightening and honesty.

#### Residual risks and validation gaps

- Scout-side acceptance is prose-only with no executable check; correctness depends entirely on the quality of the definition added per Thread 1.
- The default-timeout reduction changes dev-tooling runtime behavior; under-sized long reviews now fail at 15 minutes and discard partial output (Thread 6) — flag for explicit human confirmation since it shifts runtime posture.
- The quiet-reviewer test risks wall-clock flakiness unless designed deliberately (Thread 7).
- "External interruption" remains a definitional risk until Thread 2 narrows it; otherwise the protocol can be satisfied on paper while the failure recurs in practice.

---

I have not written to any file or committed; per the runner contract the above is returned for append under `## Review Threads`. The worktree is clean and the baseline suite is green (105 passed), so the implementer starts from a known-good state.

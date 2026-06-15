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
   has appeared. Any outer shell/tool/agent wait budget must be at least the
   runner timeout.
4. Add focused tests for the runner timeout default and timeout behavior.

## Non-Goals

- Do not change Scout runner schema or require overlays to declare active
  feature surfaces in this PR.
- Do not auto-detect feature activity mechanically from churn alone. Recent
  churn is only one clue; it never proves active feature ownership by itself.
- Do not change reviewer model defaults.
- Do not change closeout or backlog-maintenance lifecycle state rules.
- Do not re-open or rewrite downstream PRs; the downstream Hot Watch backlog PR
  was closed separately as invalid under the new intended rule.

## Implementation Plan

1. Update `scout/SKILL.md`:
   - Add an active feature suppression rule under candidate rules.
   - Require Scout reports to classify suppressed active-surface cleanup as
     report-only and name the active owner/plan/backlog item when known.
   - Define "active feature surface" as a maintained surface that is currently
     being built, stabilized, rolled out, or acceptance-tested, not merely code
     that is active/in use.
   - Positive signals include a current plan, current map entry, active PR or
     worktree, explicit human statement, active backlog/progress entry, recent
     acceptance/rollout notes, or multiple recent commits tied to the same
     still-open feature. If activity is plausible but not proven, suppress
     cleanup/refactor/dead-helper candidates to report-only unless the finding
     is safety/correctness/data-safety/production-risk/CI-blocking.
2. Update Scout references:
   - `code-structure`: large/high-churn active feature surfaces are
     suppressors for cleanup candidates, not automatic split candidates. Make
     the maintained-and-stable versus actively-being-built distinction explicit
     so normal active code can still produce candidates.
   - `code-reachability-backend-python`: unused helpers/payload residue inside
     active feature surfaces are report-only unless safety, correctness,
     data-safety, production-risk, CI-blocking, or explicit human direction
     applies.
   - `script-lifecycle`: active rollout/operator scripts are report-only until
     the rollout stabilizes unless safety, correctness, data-safety,
     production-risk, CI-blocking, or explicit human direction applies.
   - `document-structure`: active plans can be long and messy while they are
     carrying current work; structure cleanup candidates should wait until the
     active phase stabilizes unless the document is misleading agents today or
     the canonical override list applies.
   - State that suppressed report-only observations are re-evaluated by later
     Scout runs after the active signals fade; suppression is deferral, not
     permanent dismissal.
3. Update `structured-review/SKILL.md`:
   - Add timeout sizing guidance: 900 seconds for small/medium review gates,
     1800 seconds for large review gates.
   - State that once the driver invokes the runner with a timeout, it must wait
     for completion, timeout, or external interruption; no early kill for
     impatience/no-output.
   - Define external interruption narrowly as a human stop request, OS/process
     signal, infrastructure failure, or session/tool crash. A driver-chosen
     outer timeout shorter than the runner timeout is not an external
     interruption; it violates the protocol.
   - Require the outer `exec`/shell/tool wait budget to be greater than or equal
     to the runner's `--timeout-sec` plus enough buffer for process teardown and
     metadata writing.
   - Give large-review heuristics: multi-file implementation reviews, broad
     protocol changes, production/runtime/deploy reviews, or review artifacts
     above roughly 1,000 lines should use `--timeout-sec 1800`.
4. Update `structured-review/scripts/claude_structured_review.py`:
   - Change default timeout from 1800 to 900 seconds.
   - Make the start log include `timeout_sec` so the intended wait budget is
     visible in long runs.
   - Keep the existing process kill only at actual timeout.
5. Update `structured-review/tests/test_claude_structured_review.py`:
   - Assert the default timeout is 900 seconds.
   - Add a quiet-reviewer regression test with a small heartbeat, modest sleep,
     and generous timeout, proving silence is not failure before timeout.
   - Assert `timeout_sec` appears in the reviewer start log.
   - Add a cheap SKILL prose assertion for the outer wait-budget rule.
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

The Scout-side change is primarily prose/reference behavior. The tests above
validate unchanged runner mechanics and skill frontmatter, but Scout active
feature suppression itself is validated by review of the edited `SKILL.md` and
reference prose.

## Acceptance

- Scout instructions make active feature cleanup/refactor/dead-helper findings
  report-only by default.
- The structured-review protocol clearly tells drivers to wait for the runner's
  configured timeout instead of killing reviewer processes early.
- Runner default timeout is 15 minutes, while large reviews can use 30 minutes
  through `--timeout-sec 1800`.
- Tests cover the changed timeout default and quiet-reviewer wait behavior.
- Historical dated plans that mention the old 30-minute default are left as
  historical provenance; no current index encodes that value.

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

### Driver response 1

Accepted Threads 1 and 2 as blocking. The plan now defines active feature
surfaces with positive evidence signals, states that plausible-but-unproven
activity suppresses cleanup/refactor/dead-helper candidates to report-only by
default, and distinguishes maintained active code from actively-being-built
feature work.

Accepted Threads 3 through 5. The plan now uses one canonical override list
across Scout references, adds domain-specific document wording without dropping
the canonical list, and states that later Scout runs re-evaluate suppressed
report-only observations after active signals fade.

Accepted Threads 6 through 8. The plan now records that the default reduction to
900 seconds is intentional, gives large-review heuristics for `--timeout-sec
1800`, frames the quiet-reviewer test as a regression guard, adds explicit
timeout-start-log and SKILL prose assertions, and calls out that Scout-side
suppression is prose/review validated rather than mechanically proven by the
runner tests.

Verified. The runner-side facts that the plan and Thread 2's resolution depend on still hold:
- `DEFAULT_TIMEOUT_SEC = 1800` at line 29 (the change target).
- The kill at lines 855-858 fires only on total elapsed time (`now - started > config.timeout_sec`); silence only emits a heartbeat (lines 862-863) — so the early-kill cannot originate in the runner, confirming the outer-wait sizing rule is the right fix.
- The stderr start log (lines 830-833) does omit `timeout_sec` (it appears only in the metadata JSON at line 793), so step 4's "make the start log include `timeout_sec`" targets a real gap.

Both blocking threads are resolved and no new blockers were introduced. Here is my review for append.

---

### Reviewer pass 2 (impl-plan, claude reviewer)

Re-review scope: driver response 1 and the revised plan body only — specifically whether blocking Threads 1 and 2 are resolved and whether the delta introduced any new blocker. I re-read the commit `09acb8b` diff and re-verified the runner facts the timeout fix depends on.

#### Thread 1 — Resolved

The revised plan now closes the load-bearing gap. Step 1 adds a single canonical definition ("a maintained surface that is currently being built, stabilized, rolled out, or acceptance-tested, not merely code that is active/in use"), an enumerated positive-signal list (current plan, current map entry, active PR/worktree, explicit human statement, active backlog/progress entry, recent acceptance/rollout notes, or multiple recent commits tied to the same still-open feature), and — critically — the default for the uncertain case: "If activity is plausible but not proven, suppress cleanup/refactor/dead-helper candidates to report-only." That plausible-but-unproven default is what saves the motivating example I flagged in pass 1: even when the Hot Watch surface had no plan or backlog item yet at scan time, plausible activity still routes the finding to report-only, so the rule catches the case it was written for. Both halves I asked for — (1) the positive-signal list and (2) the uncertain-case default — are present. Resolved.

#### Thread 2 — Resolved

The wait-discipline loophole is now closed on both axes. Step 3 narrows "external interruption" to "a human stop request, OS/process signal, infrastructure failure, or session/tool crash" and explicitly states "a driver-chosen outer timeout shorter than the runner timeout is not an external interruption; it violates the protocol" — removing the self-justifying escape hatch. It also adds the actionable rule that was missing: "Require the outer `exec`/shell/tool wait budget to be greater than or equal to the runner's `--timeout-sec` plus enough buffer for process teardown and metadata writing," reinforced in Goal 3. This is grounded correctly: I re-confirmed the runner kills only on total elapsed time and never on silence, so sizing the driver's outer wait `>=` the runner timeout is precisely the lever that prevents the reported early-kill. Resolved.

#### New blockers — None

The delta is additive prose clarification and introduces no contradictions with the runner code or with the rest of the plan. The runner-side claims the plan asserts (default `1800` → `900`; start log currently omits `timeout_sec`; kill only at actual timeout) all still match the script. No new blocking issue.

#### Non-blocking observations on the delta (carry into implementation, not gates)

1. Goal 3 states the outer budget must be "at least the runner timeout," while step 3 states "`>=` runner `--timeout-sec` plus enough buffer." These are not contradictory — step 3 is the precise rule and Goal 3 the floor — but the implementer should treat step 3 (`>=` timeout + teardown buffer) as the operative wording so the SKILL prose doesn't ship the looser Goal-3 phrasing as the rule.

2. Driver response 1 says the plan now "uses one canonical override list across Scout references," but in step 2 the `code-structure` bullet still does not restate the safety/correctness/data-safety/production-risk/CI-blocking list. That is defensible — the canonical override now lives once in the central step-1 SKILL rule, and `code-structure`'s bullet is about split-candidate suppression where the maintained-vs-being-built distinction is the operative concept — but the implementer should not read the response summary as requiring the full list pasted into `code-structure`. Worth a one-line steer in the prose so the four references point back to the single SKILL definition rather than each re-deriving it (which is the divergence Thread 1 was guarding against).

These are tightening notes only; neither blocks implementation.

#### Overall judgment

Ready for implementation. Both blocking threads from pass 1 (the undefined "active feature surface" concept, and the wait-discipline loophole that left the early-kill failure intact) are resolved in the plan body, and the non-blocking threads 3-8 were folded in. The central Scout definition is now single-sourced with an explicit uncertain-case default, and the timeout fix names the actual mechanism (outer wait `>=` runner timeout) instead of only asking the driver to "be patient." The two carry-forward notes above are for the implementing agent to honor, not gates.

#### Residual risks

- Scout-side acceptance remains prose/review-validated with no executable check (acknowledged in the plan's Validation note); correctness depends on the implementer keeping the four references consistent with the single step-1 definition rather than restating it divergently.
- The default-timeout reduction (1800 → 900) still shifts dev-tooling runtime posture: an under-sized long review now fails at 15 minutes and discards partial output. The plan records this as intentional and adds the large-review heuristic; flag it for explicit human confirmation at implementation since it changes runtime behavior, not just prose.

---

I have not written to any file or committed; per the runner contract the above is returned for append under `## Review Threads`.

I now have everything I need. The implementation commit (`7f4e06c`) touches exactly the planned files plus a benign self-index entry in `docs/agent_plans/README.md`; the runner diff is precisely the two intended changes with the kill logic untouched; the full suite is green (105 → 109, matching the four planned tests); backlog and `git diff --check` are clean; and `docs/CURRENT.md` is untouched and does not encode the timeout.

Here is my complete review thread for append under `## Review Threads`.

---

### Reviewer pass 1 (impl, claude reviewer)

Human's concern, restated: the committed work should match the accepted plan — Scout must route cleanup/refactor/dead-helper findings on actively-built feature surfaces to report-only by default, and the structured-review runner/SKILL must encode wait discipline (900s default, 1800s for large reviews, outer wait budget ≥ runner timeout, no early kill) — with tests covering the changed behavior and no regressions.

I inspected all nine artifacts in the commit, the runner diff, `docs/CURRENT.md`, and ran the plan's full validation set before judging. The plan reached "Ready for implementation" at reviewer pass 2; my job here is plan-to-implementation traceability plus regression and consistency checks.

#### Validation provenance (reviewer-rerun)

- `python -m pytest` → 109 passed (baseline was 105; the +4 are exactly the planned step-5 tests).
- `python -m pytest structured-review/tests/test_claude_structured_review.py scout/tests/test_scout_runner.py tests/test_skill_frontmatter.py` → 94 passed.
- `git diff --check` → clean. `python scripts/check_backlog.py` → exit 0. Worktree clean.
- `docs/CURRENT.md` unchanged and carries no timeout value; the only live `1800` references are the new `--timeout-sec 1800` large-review guidance in `structured-review/SKILL.md` and its test, which is intended.

#### Traceability against the accepted plan

| Plan item | Status | Evidence |
|---|---|---|
| 1. Active-feature suppression rule in `scout/SKILL.md` under Candidate Rules | Done | `scout/SKILL.md:90-114` (`### Active Feature Suppression`) |
| 1. Classify suppressed cleanup as report-only; name owner/plan/backlog/uncertainty | Done | `scout/SKILL.md:107-110` |
| 1. Define "active feature surface" vs ordinary active code | Done | `scout/SKILL.md:96-99` |
| 1. Positive-signal list + plausible-but-unproven default | Done | `scout/SKILL.md:101-105` (signals match plan verbatim; "plausible unresolved activity is enough to suppress") |
| 2. `code-structure`: suppressor not auto-split; maintained-vs-being-built distinction explicit | Done | `code-structure.md:140-146`, `166-168` |
| 2. `code-reachability`: unused helpers/payload residue report-only unless override | Done | `code-reachability-backend-python.md:105-110` |
| 2. `script-lifecycle`: active rollout/operator scripts report-only unless override | Done | `script-lifecycle.md:79-83` |
| 2. `document-structure`: active plans may be long/messy; wait unless misleading-today or override | Done | `document-structure.md:97-103` |
| 2. Suppression is deferral; later runs re-evaluate after signals fade | Done | `scout/SKILL.md:110`; restated in `code-structure.md:167-168` |
| 3. SKILL timeout sizing 900 / 1800 | Done | `structured-review/SKILL.md:131-134` |
| 3. Must wait for completion/timeout/external interruption; no early kill | Done | `structured-review/SKILL.md:136-146` |
| 3. Narrow "external interruption"; outer-timeout-shorter is a violation | Done | `structured-review/SKILL.md:138-144` |
| 3. Outer wait budget ≥ `--timeout-sec` + teardown buffer | Done | `structured-review/SKILL.md:141-143` |
| 3. Large-review heuristics | Done | `structured-review/SKILL.md:132-134` |
| 4. Default timeout 1800 → 900 | Done | `claude_structured_review.py:29` |
| 4. Start log includes `timeout_sec` | Done | `claude_structured_review.py:831` |
| 4. Kill only at actual timeout | Done | `claude_structured_review.py:855-865` (silence → heartbeat only); diff leaves the kill loop untouched |
| 5. Assert default timeout 900 | Done | `test_...py:250-255` |
| 5. Quiet-reviewer regression test | Done | `test_...py:638-684` |
| 5. Assert `timeout_sec` in start log | Done | `test_...py:596-636` |
| 5. SKILL prose assertion for outer-wait rule | Done | `test_...py:295-302` |
| 6. `docs/CURRENT.md` only if needed (not needed) | Done | unchanged; benign self-index entry added in `docs/agent_plans/README.md` |

Every in-scope plan item is Done with concrete evidence. No item is Missing, Partial, or silently deferred.

#### Blocking issues

None. The implementation faithfully matches the accepted plan, both blocking threads from the plan review (the undefined "active feature surface" concept and the wait-discipline loophole) are realized in the committed prose, and the runner change is exactly the two intended lines with no collateral edit to the kill loop.

#### Non-blocking observations

1. The canonical-override consistency is now *better* than reviewer pass 2 anticipated, and that is the right call. Pass-2 note 2 expected `code-structure` to lean on the central SKILL definition without restating the list; the implementer instead carried the full `safety/correctness/data-safety/production-risk/CI-blocking/explicit-human-direction` override into all four references (`code-structure.md:144-146`, `code-reachability-backend-python.md:109-110`, `script-lifecycle.md:82-83`, `document-structure.md:101-103`). This makes driver-response-1's claim that the plan "uses one canonical override list across Scout references" literally true in the code, and it closes Thread 1's divergence risk by construction rather than by cross-reference. No change needed; flagging only so the consistency is on the record.

2. The quiet-reviewer test (`test_...py:638-684`) carries a small real wall-clock dependency: fake reviewer sleeps 0.2s, `--heartbeat-sec 1`, `--timeout-sec 3`, asserting elapsed ≥ 0.15s and `not timed_out`. The 15× timeout margin matches the plan's accepted "modest sleep, generous timeout" design and the lower-bound assertion is safe, so I do not consider it flaky in practice. One honest limitation: because the sleep (0.2s) is under the heartbeat (1s), this test exercises the wait-and-finish path but not the heartbeat-emission path; that is acceptable since the test's stated purpose is "waits for a quiet reviewer before timeout," which it proves. If a future change wants heartbeat coverage too, a clock-injectable loop would remove the wall-clock entirely — not needed now.

3. `docs/agent_plans/README.md` gained a two-line index entry for this plan. It is related housekeeping, not scope drift, and does not mix unrelated changes into the commit. Fine.

#### Overall judgment

Ready for closeout. The committed implementation is a complete and faithful realization of the accepted plan: the Scout half single-sources the "active feature surface" definition in `scout/SKILL.md` and applies it consistently across all four references with the full canonical override list, and the timeout half names the real mechanism (outer wait ≥ runner timeout, narrow "external interruption") rather than only asking the driver to be patient. The runner change is minimal and correct, tests cover every changed behavior the plan promised, and the full suite, backlog checker, and whitespace check are green. No blocking mismatches or regressions.

Per the skill's boundary rule, this is an implementation-review readiness conclusion; final merge-readiness remains a closeout decision after final rechecks and the human's authority.

#### Residual risks and validation gaps

- Scout-side suppression is prose/review-validated only — there is no executable test asserting the reference behavior, which the plan explicitly acknowledges. I mitigated this by reading all four references plus the central SKILL rule and confirming they are mutually consistent and aligned to the single definition; correctness now depends on future edits keeping that consistency.
- The default-timeout reduction (1800 → 900) shifts dev-tooling runtime posture: an under-sized long review now fails at 15 minutes and discards partial output. The plan records this as intentional with a large-review heuristic; it remains a behavior change worth the human keeping in view, not a defect.
- The quiet-reviewer test's small wall-clock component (non-blocking item 2) is a low residual flakiness risk under extreme CI load only.

---

I have not written to any file or committed; per the runner contract the above is returned for append under `## Review Threads`.

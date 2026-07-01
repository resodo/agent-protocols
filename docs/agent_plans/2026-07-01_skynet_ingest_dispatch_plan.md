# Skynet Ingest Dispatch Workflow Plan

Status: implementation plan, awaiting structured review
Date: 2026-07-01
Driver: Codex

## Context

Skynet Ingest now vendors `external/agent-protocols` and already has a target
repo workflow named `Update Agent Protocols Submodule`. That target workflow is
triggered by `repository_dispatch` event type `agent-protocols-updated` and uses
the target-repo secret `SKYNET_INGEST_AUTOMATION_TOKEN` to update the submodule
pointer and open a PR.

The missing source-repo side is an `agent-protocols` workflow that dispatches to
`MAGI-Systems-01/skynet-ingest` whenever `agent-protocols/main` changes. This
should match the existing organization pattern used by Skynet V2 and Skynet
Twitter: each target repo has an automation token in the target repo, and a
separate dispatch token in `resodo/agent-protocols`.

Current secret presence has been verified by name only:

- `MAGI-Systems-01/skynet-ingest`: `SKYNET_INGEST_AUTOMATION_TOKEN`
- `resodo/agent-protocols`: `SKYNET_INGEST_DISPATCH_TOKEN`

No token values, credentials, or private account details are in scope for this
plan or any repo artifact.

## Goal

Add a source-side GitHub Actions workflow in `resodo/agent-protocols` that sends
the standard `agent-protocols-updated` repository dispatch event to
`MAGI-Systems-01/skynet-ingest`.

## Non-Goals

- Do not change Skynet Ingest target-side workflow behavior.
- Do not rotate, create, print, or commit secrets.
- Do not add broad GitHub Actions permissions to the workflow.
- Do not live-trigger a dispatch from the feature branch unless the human
  explicitly asks for that operational smoke.
- Do not change protocol source files, skill mounts, or downstream submodule
  pointers in this PR.

## Implementation

1. Add `.github/workflows/dispatch-skynet-ingest.yml`.
2. Copy `.github/workflows/dispatch-skynet-twitter.yml` verbatim and apply only
   the five target substitutions below:
   - workflow name;
   - step name;
   - `SKYNET_*_REPO` env var and value;
   - `SKYNET_*_DISPATCH_TOKEN` secret;
   - missing-secret message.
3. Preserve the existing dispatch workflow structure:
   - trigger on `push` to `main`;
   - allow `workflow_dispatch`;
   - set top-level `permissions: {}`;
   - keep `job: dispatch`, `name: dispatch`, `runs-on: ubuntu-latest`;
   - keep `SOURCE_REPOSITORY: ${{ github.repository }}` and
     `SOURCE_SHA: ${{ github.sha }}`;
   - keep `shell: bash` and `set -euo pipefail`;
   - use `GH_TOKEN: ${{ secrets.SKYNET_INGEST_DISPATCH_TOKEN }}`;
   - dispatch to `MAGI-Systems-01/skynet-ingest`;
   - send event type `agent-protocols-updated`;
   - include `client_payload.repository` and `client_payload.sha`.
4. Keep naming aligned with existing workflows:
   - workflow name: `Dispatch Skynet Ingest Protocol Update`;
   - step name: `Dispatch Skynet Ingest update`;
   - env var: `SKYNET_INGEST_REPO`;
   - missing-secret message: `SKYNET_INGEST_DISPATCH_TOKEN is not configured.`

## Validation

Run from the `agent-protocols` worktree:

```bash
python scripts/check_backlog.py
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout
```

Also validate the workflow file:

```bash
actionlint .github/workflows/dispatch-skynet-ingest.yml
```

If `actionlint` is unavailable locally, install or invoke it without committing
generated binaries or caches.

Validate structural consistency against the copied template. The diff should be
limited to the five target substitutions named in the implementation section:

```bash
diff -u .github/workflows/dispatch-skynet-twitter.yml .github/workflows/dispatch-skynet-ingest.yml
```

Before closeout, verify both required secret names still exist with `gh secret
list` and do not print secret values.

## Acceptance

- The new workflow is structurally consistent with the V2 and Twitter dispatch
  workflows.
- The workflow uses only `permissions: {}` and the dispatch token secret.
- The workflow targets `MAGI-Systems-01/skynet-ingest`.
- Local validation passes or any skipped command is explicitly reported.
- PR is opened in `resodo/agent-protocols` for human review/merge.
- Post-merge behavior is clear: the next push to `agent-protocols/main` should
  dispatch to Skynet Ingest, whose target workflow may open a submodule update
  PR only when the pinned submodule SHA changes.

## Risks

- The actual token permission cannot be proven from `gh secret list`; it can
  only be validated by a live workflow run. This plan avoids feature-branch live
  dispatch by default and leaves live validation to post-merge workflow behavior
  unless the human explicitly requests a smoke.
- If Skynet Ingest target workflow changes independently, this source workflow
  might dispatch successfully but target-side update behavior could differ.
- This repo currently has local `actionlint` validation but no CI-backed
  workflow-lint gate. Closeout must label workflow syntax and template
  consistency validation as driver-reported unless CI is expanded separately.
- The per-target dispatch workflow fan-out is deliberately retained for
  consistency with V2/Twitter. A future matrix-driven workflow could reduce
  duplication, but that maintenance redesign is outside this PR.

## Review Threads

I have everything I need. The two existing dispatch workflows are byte-for-byte identical except for five substitution points (workflow name, step name, `*_REPO` env var + value, `*_DISPATCH_TOKEN` secret, and missing-secret message), and the plan's naming section enumerates exactly those five points. The git remote confirms the source repo is `resodo/agent-protocols` as the plan's Context states. Here is my review.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

**Restated concern:** Is the Skynet Ingest dispatch workflow plan narrowly scoped, faithful to the existing V2/Twitter dispatch pattern, safe on secret/token boundaries, and equipped with enough validation and closeout criteria to hand to an implementer without guessing?

I inspected the artifact (`docs/agent_plans/2026-07-01_skynet_ingest_dispatch_plan.md`), both existing dispatch workflows (`.github/workflows/dispatch-skynet-v2.yml`, `.github/workflows/dispatch-skynet-twitter.yml`), the CI workflow (`.github/workflows/ci.yml`), and confirmed the source-repo identity via `git remote`.

#### Blocking issues

None. The plan is implementable as written without guessing. The two reference workflows are identical except for exactly the five substitution points the plan enumerates (workflow name, step name, `SKYNET_*_REPO` env var + value, `SKYNET_*_DISPATCH_TOKEN` secret, missing-secret message). Every enumerated value the plan specifies matches the established convention. Secret handling is safe: `permissions: {}` at top level, token sourced from `secrets.SKYNET_INGEST_DISPATCH_TOKEN`, no values printed/committed/rotated, and name-only verification via `gh secret list`. Non-goals cleanly fence scope. Source repo `resodo/agent-protocols` in the Context matches `git remote`.

#### Non-blocking issues

**Thread 1 — "Structurally consistent" is an acceptance criterion but has no concrete verification step (non-blocking).**
Acceptance says the new workflow must be "structurally consistent with the V2 and Twitter dispatch workflows," and the Python validation suite (`check_backlog.py`, the three `unittest discover` runs, `compileall`) does not exercise the new YAML at all — it mirrors CI as a regression sanity check but cannot validate this change. The only validation that actually covers the change is `actionlint` plus human eyeballing. Since the templates are byte-identical modulo five lines, consistency is cheaply *provable*: add a validation step that diffs the new file against a template and confirms only the enumerated lines differ (e.g. `diff dispatch-skynet-twitter.yml dispatch-skynet-ingest.yml` should show only the name/step/repo/token/message substitutions). That turns "structurally consistent" from an eyeballed judgment into a falsifiable check. Recommend adding it to the Validation section.

**Thread 2 — Implementation section omits a few structural elements; relies on "mirror the existing structure" (non-blocking).**
Item 2 enumerates `GH_TOKEN`, dispatch target, event type, and `client_payload.repository`/`.sha`, but not the `SOURCE_REPOSITORY: ${{ github.repository }}` / `SOURCE_SHA: ${{ github.sha }}` env vars, the `job: dispatch` / `name: dispatch` / `runs-on: ubuntu-latest` shape, or the `shell: bash` + `set -euo pipefail` body. These are all covered by "Mirror the existing dispatch workflow structure," and because the two templates are byte-identical the implementer cannot guess wrong — so this is not blocking. Flagging only for completeness: stating outright "copy `dispatch-skynet-twitter.yml` verbatim and apply only the five substitutions below" would remove any residual ambiguity.

**Thread 3 — No CI backstop for the workflow YAML; actionlint is local-only (non-blocking, residual risk).**
`ci.yml` runs only the Python suite; it does not run `actionlint`, so there is no automated gate on GitHub Actions syntax for this or any dispatch workflow. The plan correctly makes `actionlint` a local validation step and says to report it if skipped. That is acceptable for a single, template-derived file, but the residual risk is real: if `actionlint` is unavailable locally and the diff-vs-template check (Thread 1) is also skipped, a YAML/action-syntax error could reach `main` unguarded. Keeping both the `actionlint` run and the template diff as required-or-explicitly-reported validation mitigates this.

**Thread 4 — Per-target copy-paste fan-out has an unaddressed maintenance lifecycle; out of scope but worth recording (non-blocking / deferred candidate).**
This adds a third near-identical dispatch workflow (V2, Twitter, now Ingest), each requiring a hand-maintained trio: target-repo automation token, source-repo dispatch token, and a per-target workflow file. The review lens on durable mechanisms asks whether a manually maintained list could be replaced by a simpler default — here, a single matrix-driven dispatch workflow could collapse the duplication. This is explicitly against the plan's non-goals and should NOT be pulled into this PR, but it is worth capturing as a residual/deferred observation so the growing copy-paste set is a conscious org choice rather than drift. No action required for this plan.

#### Overall judgment

Ready for implementation. Goal, non-goals, and assumptions are explicit; the pattern is verified against real files rather than asserted; secret/token boundaries are handled safely; and the plan honestly scopes cross-repo facts (target workflow, event type, token permission) as name-only verified with live validation deferred to post-merge. The non-blocking threads are tightening suggestions, not gaps that force a re-plan. The strongest single improvement is Thread 1 (make "structurally consistent" a diff-verifiable step), but its absence does not block implementation.

#### Residual risks and validation gaps

- **Token permission is unprovable pre-merge.** The plan already states this in Risks: `gh secret list` proves the name exists, not that the token can POST cross-repo dispatches; only a live run proves it. Correctly deferred to post-merge; no feature-branch smoke by default. Note also that `workflow_dispatch` on a brand-new workflow generally only runs from the default branch, so a feature-branch manual smoke isn't trivially available anyway — the post-merge-only stance is sound.
- **Target-side behavior is out of this repo's control.** If `MAGI-Systems-01/skynet-ingest`'s `Update Agent Protocols Submodule` workflow, its expected event type, or `SKYNET_INGEST_AUTOMATION_TOKEN` change independently, this source workflow could dispatch successfully while target behavior diverges. Plan acknowledges this in Risks; it cannot be closed from this repo.
- **Validation provenance for closeout.** Because CI does not exercise the YAML, "structurally consistent" and "local validation passes" will be **driver-reported** (actionlint + template diff run locally), not **CI-backed**. Closeout should record that provenance honestly rather than implying CI coverage.

No blocking issues. This plan is ready for implementation; the driver should decide whether to adopt Threads 1–3 (recommend at least Thread 1) and whether to log Thread 4 as backlog.

### Driver response 1

Accepted Thread 1. The Validation section now requires a `diff -u` comparison
against `dispatch-skynet-twitter.yml`, with expected differences limited to the
five named substitutions.

Accepted Thread 2. The Implementation section now says to copy the Twitter
workflow verbatim and names the structural elements that must be preserved.

Accepted Thread 3. The Risks section now explicitly labels actionlint/template
validation as driver-reported unless CI is expanded separately.

Deferred Thread 4. The copy-paste fan-out is a real maintenance observation, but
the current PR intentionally matches V2/Twitter. No backlog item is added in
this PR because this change is only onboarding another existing consumer into
the current convention; a matrix redesign should be discussed separately if the
fan-out keeps growing.

All evidence gathered. The test "failures" are purely a missing local PyYAML dependency (CI installs it); the yaml-independent structured-review suite passed 65/65. Here is my complete impl review.

---

### Reviewer pass 2 (impl, claude reviewer)

**Restated concern:** Does the implemented `.github/workflows/dispatch-skynet-ingest.yml` faithfully match the accepted plan and the existing V2/Twitter dispatch pattern, hold the secret/token boundary, pass workflow-syntax validation, and is the plan's validation/status recorded well enough to hand to closeout?

I inspected the implemented workflow (`.github/workflows/dispatch-skynet-ingest.yml`), both reference templates (`.github/workflows/dispatch-skynet-twitter.yml`, `.github/workflows/dispatch-skynet-v2.yml`), the CI workflow (`.github/workflows/ci.yml`), the accepted plan and its Review Threads, and the commit that added the file (`fe48c53`). I re-ran the change-covering validations myself (actionlint, template diff) plus the plan's regression suite.

#### Blocking issues

None. The implementation is a faithful, minimal realization of the accepted plan and is safe to hand to closeout.

#### Plan-to-implementation traceability

| Accepted item | Status | Evidence |
| --- | --- | --- |
| Copy `dispatch-skynet-twitter.yml` verbatim; apply only the five substitutions | **Done** | `diff -u` against the template shows changes on exactly 6 lines, all within the five accepted substitution categories (name, step name, `SKYNET_INGEST_REPO` def+use, `GH_TOKEN` secret, missing-secret message). No structural drift. |
| Trigger on `push`→`main` + `workflow_dispatch` | **Done** | File lines 3–7, identical to templates. |
| Top-level `permissions: {}` | **Done** | Line 9. |
| `job: dispatch` / `name: dispatch` / `runs-on: ubuntu-latest` | **Done** | Lines 12–14. |
| `SOURCE_REPOSITORY`/`SOURCE_SHA`, `shell: bash`, `set -euo pipefail` | **Done** | Lines 20–24. |
| Token via `GH_TOKEN: ${{ secrets.SKYNET_INGEST_DISPATCH_TOKEN }}` | **Done** | Line 18. |
| Dispatch to `MAGI-Systems-01/skynet-ingest`, event `agent-protocols-updated`, `client_payload.repository`/`.sha` | **Done** | Lines 19, 33–37, 43. |
| Naming: workflow/step names, env var, missing-secret message | **Done** | Lines 1, 16, 19, 27 match the plan's naming section verbatim. |
| Workflow validated with `actionlint` | **Done (reviewer-rerun)** | `actionlint .github/workflows/dispatch-skynet-ingest.yml` → clean; `actionlint` over all workflows → clean. |
| Template-diff verification (accepted Thread 1) | **Done (reviewer-rerun)** | Diff limited to the five substitutions; no other lines differ. |
| `gh secret list` name-only pre-closeout check | **Deferred to closeout** | Correctly a closeout step per plan; not yet recorded. |
| PR opened in `resodo/agent-protocols` | **Deferred to closeout** | Out of scope for this gate. |

**Secret boundary:** Clean. `permissions: {}` grants the job zero token scope beyond the injected secret. The token is referenced only as `secrets.SKYNET_INGEST_DISPATCH_TOKEN` mapped into `GH_TOKEN`; no value is printed, committed, or rotated. The missing-secret branch echoes the secret **name** only, never a value, and `${GH_TOKEN:-}` safely guards the `set -u` unbound case. This matches the accepted plan's non-goals and SAFETY constraints.

**Workflow syntax/structure:** `actionlint` passes with zero findings on the new file and across all four workflows. Structure is byte-identical to the proven Twitter template outside the five substitutions.

#### Non-blocking issues

**Thread 5 — Validation evidence is not yet recorded in the plan; Status line is stale (non-blocking, closeout prerequisite).**
The plan's Validation section lists the commands to run, but the plan body records no results, and the `Status:` line still reads "implementation plan, awaiting structured review" even though the workflow is implemented and committed (`fe48c53`). This is normal at the impl-gate boundary, but before closeout the driver should update the plan to reflect implementation-complete and record validation provenance: actionlint clean, template diff limited to five substitutions, and the Python-suite result. This impl review already supplies reviewer-rerun evidence for the change-covering checks, so this is a documentation/closeout task, not an implementation defect.

**Thread 6 — Local Python suite could not fully execute here due to a missing PyYAML dependency; record provenance honestly (non-blocking).**
In this worktree the yaml-dependent tests (`tests`, `scout/tests`, `check_backlog.py`) error with `ModuleNotFoundError: No module named 'yaml'` — an environment gap, not a code failure. CI installs `PyYAML` (see `ci.yml`) so these pass on PR/push, and the yaml-independent `structured-review/tests` suite passed 65/65 locally. Importantly, as established in accepted Thread 1, this Python suite does not exercise the new YAML at all — the change-covering validation is `actionlint` + the template diff, both of which pass. So confidence in the change is unaffected, but closeout should label the Python-suite result as **CI-backed** (not local) and the workflow-lint/template-diff result as **driver/reviewer-reported**, matching the accepted Risks note that this repo has no CI-backed workflow-lint gate.

**Thread 7 — No central workflow index to update; confirms no docs drift (non-blocking, informational).**
I checked for a README or doc enumerating the dispatch workflow set; none exists at the repo root or in `.github/`, and no markdown file lists `dispatch-skynet-v2`/`dispatch-skynet-twitter`. So adding a third dispatch workflow introduces no stale index or doc that needs a parallel update — there is genuinely no missing docs change here. (The copy-paste fan-out remains the deferred Thread 4 observation from pass 1; no action for this PR.)

#### Overall judgment

Ready for closeout. The implementation is a verbatim template copy with exactly the five accepted substitutions and nothing else; secret boundaries are held; `actionlint` is clean; and every in-scope acceptance item is Done with concrete evidence or correctly deferred to closeout. The remaining items (Threads 5–6) are closeout bookkeeping — record validation provenance, refresh the stale Status line, run the name-only `gh secret list`, and open the PR — not implementation gaps.

#### Residual risks and validation gaps

- **Token permission remains unprovable pre-merge.** `gh secret list` proves the name exists, not that the token can POST cross-repo dispatches; only a live run proves it. Correctly deferred to post-merge with no feature-branch smoke by default, and `workflow_dispatch` on a new workflow generally only runs from the default branch anyway.
- **Target-side behavior is out of this repo's control.** If `MAGI-Systems-01/skynet-ingest`'s target workflow, expected event type, or `SKYNET_INGEST_AUTOMATION_TOKEN` change independently, this source workflow can dispatch successfully while target behavior diverges. Cannot be closed from this repo; already recorded in the plan's Risks.
- **No CI-backed workflow-lint gate.** `ci.yml` runs only the Python suite; `actionlint` is local/reviewer-run. For a single byte-identical template copy this is acceptable, and both `actionlint` and the template diff passed on review. Closeout should record this validation as driver/reviewer-reported, per the accepted Risks section.

No blocking issues. The implementation matches the accepted plan and the V2/Twitter pattern exactly, the secret boundary is safe, and workflow syntax is clean. Before closeout the driver should record validation provenance in the plan, update the stale `Status:` line, and complete the deferred name-only `gh secret list` + PR steps.

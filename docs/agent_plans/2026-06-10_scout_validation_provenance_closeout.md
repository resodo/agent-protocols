# Scout Validation Provenance Closeout Report

Status: artifact - closeout evidence for PR #13
Date: 2026-06-10
Scope: post-merge closeout of `docs/agent_plans/2026-06-06_scout_validation_provenance_plan.md`

## Delivery State

- PR #13 `Scout: require validation provenance in run artifacts`
  (`feature/scout-validation-provenance-v2` -> `main`) merged
  2026-06-06T19:27:48Z. The branch commits were rebase-merged; `main` carries
  the linearized commits `74b9249..3a9f24c` and the original feature branch is
  not an ancestor of `main`.
- Post-merge `main` CI run completed with success (2026-06-06T19:27:51Z).
- Downstream dispatch workflows `Dispatch Skynet V2 Protocol Update` and
  `Dispatch Skynet Data Protocol Update` both completed with success on the
  merge push, so adopting-repo submodule bumps were triggered by the existing
  mechanism named in the plan's closeout step.
- Both implementation review gates concluded in the plan thread: pass 3 (impl)
  and pass 4 (impl re-review) ended `Ready for closeout` with no blocking
  findings.

## Traceability

Acceptance criteria from the accepted plan, against merged `main` (3a9f24c):

| Acceptance criterion | State | Evidence |
| --- | --- | --- |
| Setup-only artifacts fail `scout_runner.py check` | Done | `test_check_requires_runner_validation_provenance` (scout/tests/test_scout_runner.py:186) |
| Dry-run artifacts recording `scout_runner.py check` pass | Done | `test_setup_and_check_report_artifacts` and dry-run positives via `add_validation_provenance` helper (scout/tests/test_scout_runner.py:92,153,247) |
| Write-enabled artifacts omitting backlog checker provenance fail (report side) | Done | `test_write_enabled_requires_backlog_checker_provenance` (scout/tests/test_scout_runner.py:312) |
| Write-enabled artifacts omitting backlog checker provenance fail (manifest side) | Done | `test_write_enabled_requires_manifest_backlog_checker_provenance` (scout/tests/test_scout_runner.py:335), empirically shown in pass 4 to fail under an unbounded `section_text` regression |
| Write-enabled artifacts recording both pass | Done | `test_write_enabled_manifest_declares_write_mode` (scout/tests/test_scout_runner.py:286) |
| Existing structural/immutability/Vulture tests keep passing | Done | full `scout/tests` suite green, 15 tests |
| `scout/SKILL.md` and runner agree on the contract | Done | impl review passes 3 and 4 checked SKILL/runner agreement; no blocking findings |

No `Partial`, `Missing`, or `Deferred` rows.

## Validation

Rerun against the merged code state (`3a9f24c`) from the closeout branch tip,
whose extra commits are docs-only so the code under test is identical.
Provenance: driver-reported, matching the CI command set:

- `python scripts/check_backlog.py` - pass (exit 0).
- `python -m unittest discover -s tests` - 15 tests OK.
- `python -m unittest discover -s structured-review/tests` - 41 tests OK.
- `python -m unittest discover -s scout/tests` - 15 tests OK.
- `python -m compileall -q structured-review scout` - clean.
- `git diff --check` - clean.

CI-backed provenance: the same command set passed on `main` after the merge
(CI run 2026-06-06T19:27:51Z, success).

## Mechanism Lifecycle

The merged work added durable mechanical rules to the Scout runner:

- `RUNNER_CHECK_PROVENANCE_TOKENS` and
  `WRITE_ENABLED_BACKLOG_PROVENANCE_TOKEN` in `scout/scripts/scout_runner.py`
  define the required provenance tokens. They live next to the heading
  contracts so a future runner rename exposes the coupling, per the accepted
  plan. Owner: Scout protocol maintainers in this repo. Update trigger:
  renaming the runner, changing the report/manifest contract, or changing the
  backlog checker expectation. Staleness signal: scout tests fail or adopting
  repos report false provenance failures.
- The check is intentionally syntactic (records of commands, not proof of
  execution). This boundary is documented in the plan's Risks section and was
  accepted in review.

## Documentation Consistency

Stale-status scan (closeout checklist 4.1) after merge, fixed in this closeout
branch:

- `2026-06-06_scout_validation_provenance_plan.md` header still said
  `draft for plan review`; now `historical - implemented and merged via PR #13`.
- `docs/agent_plans/README.md` Current Records was missing the Scout skill
  plan, the Scout validation provenance plan, and this closeout report; all
  three entries added.
- The four earlier merged plans (`2026-06-04_claude_runner_plan.md`,
  `2026-06-05_structured_review_runner_default_refactor_plan.md`,
  `2026-06-05_review_closeout_boundary_plan.md`,
  `2026-06-05_scout_skill_plan.md`) carried the same class of stale
  `Draft`/`in progress` headers from before the stale-status scan rule
  existed. Fixed in the same pass with per-plan PR merge evidence. Only the
  one-line `Status:` header was changed in each plan; review-thread text was
  not rewritten, consistent with the historical-record rule.

Source-of-truth docs required no changes: `README.md`, `AGENTS.md`,
`docs/README.md`, `docs/CURRENT.md`, and `docs/backlog.yml` contain no stale
merge-readiness or lifecycle wording for this work, and the merged change
added no new protocol entrypoints, runner paths, or references beyond what
`docs/CURRENT.md` already lists. No backlog items were opened or closed by
this work.

## Secret and Safety Check

The closeout diff touches only markdown status lines, the agent_plans index,
and this report. No secrets, credentials, user-home absolute paths, or
private run outputs are introduced. Verified with `git diff --check` and
diff inspection.

## Residual Risks

- Syntactic looseness and `--mode`-keyed backlog checking remain as documented
  and accepted in the plan's Risks section; unchanged here.
- The remote feature branch `feature/scout-validation-provenance-v2` still
  exists after the rebase merge. Deleting it is a human decision; closeout does
  not delete remote branches.
- Skynet V2/Data dispatches succeeded at the workflow level; verifying the
  resulting downstream submodule-bump PRs landed is owned by those repos'
  own workflows, not this closeout.

## Next Expected Step

Human review and merge of this closeout PR, then the task is closed. No
post-merge docs follow-up is expected; this report's wording remains true
after merge.

## Review Threads

### Reviewer pass 1 (closeout-review)

Human concern restated: confirm this closeout report's delivery-state,
traceability, validation-provenance, mechanism-lifecycle, and stale-status-scan
claims are accurate and complete against repo state, that fixing the four older
merged plans' Status headers here is correctly scoped and evidenced, and that no
tracked-doc wording becomes false after this closeout PR merges.

Scope of this pass: independent verification against PR #13 metadata, the commit
graph, GitHub Actions run history, the cited tests, the runner constants, and the
working tree on `feature/scout-provenance-closeout`. The validation suite was
rerun in this worktree (reviewer-rerun provenance).

#### Blocking

None. Every load-bearing claim checked out:

- Delivery state. PR #13 `Scout: require validation provenance in run artifacts`
  (`feature/scout-validation-provenance-v2` -> `main`) is MERGED at
  2026-06-06T19:27:48Z; merge commit `3a9f24c`. The four PR-introduced commits
  `806d517..3a9f24c` are single-parent and linear with `74b9249` as the parent
  of `806d517`, and `origin/feature/scout-validation-provenance-v2` (`710e2ce`)
  is not an ancestor of `main` — consistent with the report's rebase-merge and
  `74b9249..3a9f24c` claims. Post-merge `CI` run on `3a9f24c` is `success` at
  2026-06-06T19:27:51Z, and both `Dispatch Skynet V2 Protocol Update` and
  `Dispatch Skynet Data Protocol Update` are `success` on the same SHA/timestamp.
- Traceability. All seven rows resolve: the cited test names sit at the cited
  lines in `scout/tests/test_scout_runner.py` (186, 153, 92, 247, 312, 335,
  286), and plan review passes 3 and 4 both record `#### Blocking: None` with an
  `Overall judgment` of `Ready for closeout`.
- Validation. Reviewer-rerun in this worktree reproduces the report exactly:
  `python scripts/check_backlog.py` exit 0; `tests` 15 OK;
  `structured-review/tests` 41 OK; `scout/tests` 15 OK; `compileall` clean;
  `git diff --check` clean.
- Mechanism lifecycle. `RUNNER_CHECK_PROVENANCE_TOKENS` and
  `WRITE_ENABLED_BACKLOG_PROVENANCE_TOKEN` exist in
  `scout/scripts/scout_runner.py` (lines 42-43) and gate
  `require_validation_provenance`; owner/update-trigger/staleness-signal and the
  syntactic-boundary caveat are accurate.
- Stale-status scan. The five plan Status headers were each rewritten to
  `historical - implemented and merged via PR #N (date)`, and the PR/date pairs
  match GitHub: #9 (2026-06-04), #10 (2026-06-05), #11 (2026-06-05),
  #12 (2026-06-06), #13 (2026-06-06). Each diff touches only the one-line
  `Status:` header. A full sweep of `docs/agent_plans/*.md` shows no remaining
  `Draft`/`in progress` header, so the scan is complete. `historical` matches the
  status vocabulary documented in `docs/README.md`. The `docs/agent_plans/README.md`
  index gained exactly the three missing entries the report names.
- Post-merge wording. The closeout diff is docs-only (five plan headers, the
  index, this report); `README.md`, `AGENTS.md`, `docs/README.md`,
  `docs/CURRENT.md`, and `docs/backlog.yml` carry no stale merge-readiness or
  lifecycle wording for this work, matching the "no changes required" claim. No
  claim in this report becomes false once this PR merges.

#### Non-blocking

**N1. "Rerun ... at main (3a9f24c)" is a shorthand, not the literal worktree
HEAD.** This worktree's HEAD is the closeout branch tip (`6f680e5`), three
docs-only commits ahead of `3a9f24c`. Because those three commits touch only
`docs/agent_plans/`, the code under test (`scout/`, `tests/`,
`structured-review/`) is byte-identical to `3a9f24c`, so the rerun results are
equivalent and the numbers reproduce. Accurate in substance; the phrasing just
elides that the run happened on the closeout tip carrying the merged code
unchanged. Optional: say "against the merged code state (`3a9f24c`), rerun from
the closeout tip". Not gating.

**N2. Fixing the four older plans' headers is scope-adjacent to a PR #13
closeout, but defensibly placed and well-evidenced.** It broadens this PR from
"PR #13 plan + report" to five plans + index + report. The report is transparent
about it, frames it as the closeout stale-status scan (checklist 4.1), and each
edit is a one-line header backed by a real merged PR — so I read this as correct
scoping for a documentation-consistency pass rather than scope creep. Flagging
only so the human/driver consciously owns the slightly wider blast radius; no
change required.

**N3. Provenance label wording.** The Validation section labels the rerun
`driver-rerun`; the skill's canonical taxonomy is CI-backed / reviewer-rerun /
driver-reported / human acceptance. The meaning is unambiguous (the driver reran
the command set), so this is a wording nit, not an accuracy problem. This pass
adds reviewer-rerun provenance on top.

#### Overall judgment

Ready to resume closeout. No blocking issues. The report's delivery-state,
traceability, validation, mechanism-lifecycle, and stale-status-scan claims are
accurate and complete against repo state, and the older-plan header fixes are
correctly scoped and evidenced. N1-N3 are optional polish the driver may take or
leave; none change merge readiness, which remains the human's call at the
closeout gate.

#### Residual risks / validation provenance

- Validation provenance for this pass: reviewer-rerun (suite reproduced green in
  this worktree) plus CI-backed (the same command set passed on `main` at
  2026-06-06T19:27:51Z); delivery/merge facts confirmed against PR #13 metadata
  and the commit graph.
- Carried-forward and unchanged by this report: syntactic looseness and
  `--mode`-keyed backlog checking (documented and accepted in the plan), and the
  surviving remote feature branch (deletion is a human decision).
- Downstream submodule-bump PRs are owned by the adopting repos' workflows; this
  closeout verifies dispatch success only, as the report states.

### Driver response 1

Classification of reviewer pass 1 findings:

- N1 accepted. The Validation section now says the rerun ran from the closeout
  branch tip against the merged code state (`3a9f24c`), with the docs-only
  delta made explicit.
- N2 accepted as conscious ownership. The driver keeps the four older plan
  header fixes bundled in this closeout PR: they are one-line status edits
  caught by the same checklist-4.1 stale-status scan, each backed by its merged
  PR, and splitting them into a separate PR would duplicate review overhead for
  no risk reduction. The human can still reject the bundling at the merge gate.
- N3 accepted. The provenance label now uses the canonical `driver-reported`
  term instead of `driver-rerun`.

An earlier reviewer pass attempt was invalidated by the runner because the
reviewer deleted the thread-section placeholder comment while appending, which
the write-mode verification correctly rejected; the placeholder was removed in
`docs: drop review-threads placeholder before gate` and the gate was rerun
cleanly. Recorded here so the gate history in this PR is complete.

No blocking findings; closeout resumes. Merge readiness remains the human's
call.

# Scout Validation Provenance Plan

Status: draft for plan review
Branch: `feature/scout-validation-provenance-v2`
Worktree: `agent-protocols-scout-validation-provenance-v2`

## Context

Skynet Data write-enabled Scout cold-start testing exposed a protocol gap. The
run executed the expected validation commands, but the first generated
`SCOUT_REPORT.md` and `MANIFEST.md` only recorded setup-level provenance such
as `Setup: completed`, `Report skeleton created by Scout runner`, and
`Overlay parsed by Scout runner`.

That was not enough durable evidence for a write-enabled Scout run. The report
and manifest should record the final mechanical validation that makes the run
safe to review, especially:

- the `scout_runner.py check` command and result;
- the adopting repo backlog checker command and result when the run is
  write-enabled;
- any repo-local hygiene checks the driver uses as acceptance evidence, such as
  `git diff --check`, when they are part of the run handoff.

The immediate Data report was manually patched, but that is only a local fix.
The shared Scout protocol and runner should prevent this class of incomplete
artifact from passing again.

## Problem

`scout/scripts/scout_runner.py check` currently validates report headings,
enabled subskill sections, TODO placeholders, manifest headings, and dry-run
backlog immutability. It does not verify that the report and manifest record
final validation provenance.

As a result, a fresh agent can run validations correctly but leave the durable
Scout artifacts too weak for later review or closeout. This is most important
for write-enabled runs because they may update `docs/backlog.yml`.

## Goal

Make missing final validation provenance a mechanical Scout runner failure.

## Non-Goals

- Do not make the runner execute repo-specific backlog checks. The runner
  should validate the artifact records, not own each adopting repo's command.
- Do not hard-code one exact backlog checker command such as
  `uv run python scripts/check_backlog.py`; adopting repos may wrap the same
  checker differently.
- Do not decide whether Skynet Data `DATA-BL-0045` should remain. That is a
  separate human backlog decision in the Data repo.
- Do not change Scout candidate semantics, subskill scope, Vulture behavior, or
  report output locations.

## Proposed Design

1. Update `scout/SKILL.md`.
   - In the `## Workflow` step that says to run `scout_runner.py check` before
     handoff, state that the final report/manifest must record that validation
     before handoff.
   - In the `## Report Contract` block, require `SCOUT_REPORT.md`
     `Runner Validation` to record final validation provenance, not only setup.
   - In the same `## Report Contract` block, require `MANIFEST.md`
     `Validation` to mirror the final mechanical validation summary.
   - State that all modes must record the `scout_runner.py check` command and
     result.
   - State that write-enabled mode must also record the adopting repo backlog
     checker command and result.

2. Update `scout/scripts/scout_runner.py`.
   - Add a helper to extract section text from either report or manifest.
   - During `check`, inspect:
     - `SCOUT_REPORT.md` `## Runner Validation`;
     - `MANIFEST.md` `## Validation`.
   - Extract both sections strictly from their heading to the next same-level
     `##` heading. This prevents `MANIFEST.md` `## Validation` from matching
     later `## Backlog Write Mode` text such as "Write-enabled runs may modify
     backlog YAML."
   - Fail if either section lacks `scout_runner.py` and `check` provenance.
   - In `write-enabled` mode, also fail if either section lacks backlog checker
     provenance.
   - Scope token searches strictly to the extracted section text. Do not search
     the whole report or manifest.
   - Match provenance tokens case-insensitively so ordinary command/prose
     capitalization does not matter.
   - Generalize section extraction error labels so manifest failures say
     `MANIFEST.md`, not `SCOUT_REPORT.md`.
   - Define the required provenance tokens near `REPORT_HEADINGS`, for example
     runner tokens `scout_runner.py` + `check`, and write-enabled backlog token
     `backlog`, so future runner renames expose the coupling.
   - Keep the check intentionally syntactic. It should look for durable
     provenance text, not prove that the command actually ran.

3. Update `scout/tests/test_scout_runner.py`.
   - Add a negative test showing setup-only artifacts fail final check.
   - Add a negative test showing write-enabled artifacts fail when they record
     `scout_runner.py check` but omit backlog checker provenance.
   - Update positive setup/check tests so they simulate an agent appending
     final validation provenance before calling `cmd_check`.
   - Update every existing positive `cmd_check` path that relies on a setup
     skeleton:
     - `test_setup_and_check_report_artifacts`;
     - `test_dry_run_allows_backlog_dirty_before_setup_when_unchanged`;
     - `test_write_enabled_manifest_declares_write_mode`;
     - `test_check_rejects_dry_run_backlog_change`, if it still calls another
       positive setup/check helper internally.

## Backlog Checker Provenance Matching

Use a medium-strict rule:

- `scout_runner.py` and `check` must both appear in each final validation
  section. Matching is case-insensitive.
- In write-enabled mode, `backlog` must appear in each final validation
  section. Matching is case-insensitive.
- The section searched is only `SCOUT_REPORT.md` `## Runner Validation` or
  `MANIFEST.md` `## Validation`, bounded by the next same-level `##` heading.
  Later manifest text such as `## Backlog Write Mode` must not satisfy the
  validation provenance check.

This intentionally accepts variants such as:

- `python scripts/check_backlog.py`
- `uv run python scripts/check_backlog.py`
- `uv run --with pyyaml==6.0.3 python scripts/check_backlog.py`

It also avoids binding the shared runner to any one adopting repo's toolchain.

## Acceptance Criteria

- A dry-run Scout report/manifest with only setup provenance fails
  `scout_runner.py check`.
- A dry-run Scout report/manifest that records `scout_runner.py check` passes
  the new provenance check, assuming all existing structural checks pass.
- A write-enabled Scout report/manifest that records `scout_runner.py check`
  but omits backlog checker provenance fails `scout_runner.py check`.
- A write-enabled Scout report/manifest that records both `scout_runner.py
  check` and backlog checker provenance passes the new provenance check,
  assuming all existing structural checks pass.
- Existing dry-run backlog immutability, subskill section, TODO, manifest
  heading, and Vulture adapter tests keep passing.
- `scout/SKILL.md` and `scout/scripts/scout_runner.py` agree on the contract.

## Validation Plan

Run locally in the agent-protocols worktree:

```bash
python -m unittest discover -s scout/tests
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m compileall -q scout scripts structured-review tests
git diff --check
```

If the implementation touches only Scout files, `scout/tests` is the primary
functional check. The broader unittest/compileall checks guard shared repo
regressions before PR handoff.

## Review Gates

1. Plan review gate.
   - Use `structured-review/scripts/claude_structured_review.py` in
     `write-commit-to-plan` mode.
   - Type: `impl-plan`.
   - Artifact/thread file: this plan.
   - Do not implement until blocking plan-review threads are resolved or
     explicitly escalated.

2. Implementation review gate.
   - After implementation and local validation, run structured review with
     Type: `impl`.
   - Review should compare changed Scout protocol, runner, and tests against
     this accepted plan.
   - Do not close out until blocking implementation-review threads are resolved
     or explicitly escalated.

3. Closeout.
   - Confirm branch state, validation commands, PR status, and downstream
     adoption impact.
   - If merged, downstream Skynet V2/Data submodule bumps can happen through
     the existing submodule update mechanism.

## Risks

- The syntactic check may be too loose: a report could mention backlog without
  truly running the checker. This is acceptable for this slice because the
  runner is a mechanical artifact checker, not the executor of repo-local
  commands.
- The syntactic check may be too strict if a repo uses non-English or unusual
  phrasing. The protocol already expects command provenance, so requiring
  command-like text is acceptable.
- Existing agents may fail until they learn to append final validation
  provenance before calling `check`. That is the intended behavior.
- Mode spoofing remains possible: `scout_runner.py check` keys the
  write-enabled backlog requirement off the `--mode` flag rather than proving
  the manifest's recorded mode. This matches the existing runner interface and
  can be hardened later if it becomes noisy; this slice keeps scope on
  provenance completeness.

## Review Threads

<!-- Structured review threads go here. -->

### Reviewer pass 1 (impl-plan)

Human concern restated: make a write-enabled Scout run that recorded only
setup-level provenance fail mechanically, so the report/manifest carry the final
validation evidence a later review needs, without the shared runner owning any
one repo's backlog command.

Verification performed before judging:

- Confirmed the plan's factual claims against the code. The report skeleton's
  `## Runner Validation` is literally `- Setup: completed.` and the manifest
  skeleton's `## Validation` is `- Report skeleton created by Scout runner.` /
  `- Overlay parsed by Scout runner.` (`scout/scripts/scout_runner.py`,
  `report_skeleton` and `manifest_skeleton`). `cmd_check` validates headings,
  subskill subsections, TODO, manifest headings, and dry-run baseline only — no
  provenance. Claims accurate.
- Confirmed `## Runner Validation` and `## Validation` are the correct section
  names already enforced by `REPORT_HEADINGS` and the manifest heading list.
- Confirmed all validation-plan directories exist (`scout/tests`, `tests`,
  `structured-review/tests`, `scout`, `scripts`, `structured-review`), so the
  Validation Plan is runnable by the next agent.

#### Blocking

**B1. Pin the manifest `## Validation` section boundary and token case, or the
write-enabled `backlog` check can pass vacuously against the very skeleton it
must reject.**

This is the load-bearing detail for the task focus ("do acceptance criteria
catch the observed write-enabled gap?"). The new check works only if the
extracted `## Validation` text is correctly isolated.

In the manifest skeleton the `## Validation` section is immediately followed by
`## Backlog Write Mode`, whose body already contains "Backlog Write Mode",
"Write-enabled runs may modify backlog YAML", and "Backlog/report changes ...";
the `## Artifacts` table also contains "output-manifest check". If the new
helper extracts `## Validation` unbounded-to-EOF (or matches the `backlog` token
case-insensitively across the whole file), the write-enabled `backlog`
requirement is satisfied by the skeleton itself — so a setup-only write-enabled
run would PASS, which is exactly the failure this plan exists to prevent.

The existing `section_text` already bounds at the next same-level heading, but
the plan only says "Add a helper to extract section text from either report or
manifest" and does not pin: (a) the manifest `## Validation` section ends at the
next `##` heading (so `## Backlog Write Mode` is excluded), and (b) whether the
`scout_runner.py` / `check` / `backlog` token match is case-sensitive and
scoped strictly to the extracted section text. Please state both in Proposed
Design step 2 and in the Backlog Checker Provenance Matching rule. The negative
test (acceptance criterion 3) only guards this if the test artifact retains
`## Backlog Write Mode`; making the boundary explicit removes the coupling where
a too-loose extractor and a too-loose test could agree and ship the bug.

#### Non-blocking

**N1. Enumerate every existing positive `cmd_check` test that will break, not
just "positive setup/check tests."** After this change the raw skeleton fails
`check`, so four call sites need the provenance-append helper, not one:
`test_setup_and_check_report_artifacts` (dry-run),
`test_dry_run_allows_backlog_dirty_before_setup_when_unchanged` (dry-run),
`test_write_enabled_manifest_declares_write_mode` (write-enabled — must append
BOTH `scout_runner.py check` and backlog provenance), and
`test_check_rejects_dry_run_backlog_change`, which calls
`test_setup_and_check_report_artifacts` and would now error on the inner check
before reaching its own assertion. Listing these prevents surprise failures and
makes the "existing tests keep passing" acceptance criterion verifiable.

**N2. Generalizing `section_text` must fix its hard-coded error label.** It
currently raises `SCOUT_REPORT.md missing section: ...`. Reused for the manifest
it would mislabel a manifest problem as a report problem. Have the helper take
the artifact name (or message) so failures point at the right file.

**N3. Keep the required-provenance tokens as named constants.** The plan
hard-codes `scout_runner.py`, `check`, and `backlog`. Define them near
`REPORT_HEADINGS` so the contract is discoverable and so a future rename of the
runner script surfaces the coupling rather than silently weakening the check.
This satisfies the mechanism-lifecycle lens (who maintains it / what signals
staleness).

**N4. Name the specific `scout/SKILL.md` sections to edit.** Design step 1 says
"update SKILL.md" without saying where. The provenance requirement touches the
Report Contract block (the `Runner Validation` / manifest `Validation`
descriptions, around the `## Report Contract` section) and the run-loop step 5
("Run `scout_runner.py check` before handoff"). Pointing the implementer at the
exact sections keeps SKILL.md and the runner in agreement (acceptance criterion
6) without guessing.

#### Overall judgment

Ready for implementation once B1 is resolved (or explicitly escalated). The goal
is clear, non-goals are strong, the factual claims match the code, and the
runner/protocol boundary is appropriate and explicitly non-overfit: the
medium-strict `backlog` token rule and the refusal to hard-code one checker
command keep the shared runner repo-agnostic while still catching the observed
gap. The acceptance criteria do catch the Data write-enabled gap — provided B1's
section isolation is pinned down. N1–N4 are quality/specificity improvements,
not gates.

#### Residual risks / validation gaps

- Syntactic looseness is real and acknowledged by the plan: an agent can write
  the word "backlog" in prose without having run the checker. Accepted for this
  slice because the runner is an artifact checker, not an executor.
- Mode-spoofing: `check` keys the backlog requirement off the `--mode` flag, not
  the manifest's recorded `## Backlog Write Mode`. Running `check --mode dry-run`
  against a write-enabled run dir skips the new backlog requirement. This mirrors
  the existing dry-run baseline behavior, but the plan now gates more on it —
  worth recording as residual risk or hardening with an optional cross-check
  against the recorded mode.
- Validation provenance for this review: reviewer-inspected source and directory
  layout only; tests were not run (none exist yet for this change). Functional
  proof depends on the implementation-review gate executing the Validation Plan.

### Driver response 1

Accepted B1. The plan now requires section extraction to stop at the next
same-level `##` heading and requires provenance token searches to be scoped
strictly to the extracted `SCOUT_REPORT.md` `## Runner Validation` and
`MANIFEST.md` `## Validation` text. This prevents `## Backlog Write Mode` from
satisfying the write-enabled backlog-token requirement.

Accepted N1. The plan now names the existing positive `cmd_check` tests that
must receive simulated final validation provenance.

Accepted N2. The plan now requires manifest section extraction failures to name
`MANIFEST.md` rather than reusing the report error label.

Accepted N3. The plan now requires the provenance tokens to be named constants
near `REPORT_HEADINGS`.

Accepted N4. The plan now names the `scout/SKILL.md` `## Workflow` and
`## Report Contract` areas that need edits.

Accepted residual-risk note. The plan now records mode spoofing as out of scope
for this slice.

### Reviewer pass 2 (impl-plan re-review)

Re-reviewed after driver response 1. Scope of this pass: confirm B1 is resolved,
confirm readiness for implementation, and raise new blockers only if the
revision introduced a real implementation-risk gap.

Verification performed against current source (not just the prose):

- `scout/scripts/scout_runner.py` `manifest_skeleton` confirms the load-bearing
  hazard B1 named: the manifest `## Validation` section (`- Report skeleton
  created by Scout runner.` / `- Overlay parsed by Scout runner.`) is immediately
  followed by `## Backlog Write Mode`, whose body contains "Write-enabled runs
  may modify backlog YAML." and "Backlog/report changes ...". Unbounded
  extraction or whole-file token search would let that section satisfy the
  write-enabled `backlog` requirement against the very skeleton the check must
  reject.
- `section_text` already bounds at the next heading via its `next_level_prefix`
  argument and hard-codes the `SCOUT_REPORT.md missing section:` error label
  (the N2 finding is accurate).
- `REPORT_HEADINGS` exists and lists `## Runner Validation` last, so on the
  report side a `##`-bounded extraction runs to EOF — safe, since nothing
  follows it.
- `scout/SKILL.md` has `## Workflow` (step 5 is "Run `scout/scripts/scout_runner.py
  check` before handoff") and `## Report Contract` (with `Runner Validation`), so
  the N4 section pointers land on real headings.
- All four tests the plan now enumerates exist in `scout/tests/test_scout_runner.py`,
  and `test_check_rejects_dry_run_backlog_change` does call
  `test_setup_and_check_report_artifacts()` internally — so the N1 caveat is
  accurate and the "existing tests keep passing" criterion is now verifiable.

#### Blocking

None.

B1 is resolved. Proposed Design step 2 now requires extracting both sections
"strictly from their heading to the next same-level `##` heading" with the
explicit anti-leak rationale naming `## Backlog Write Mode`, requires token
searches "scoped strictly to the extracted section text" ("Do not search the
whole report or manifest"), and requires case-insensitive token matching. The
Backlog Checker Provenance Matching rule repeats both the section-boundary and
case rules. Together these close the vacuous-pass hole on the manifest side: a
setup-only write-enabled run can no longer satisfy the `backlog` token from
`## Backlog Write Mode`. The negative test (acceptance criterion 3) now genuinely
guards the boundary because it runs against the real `manifest_skeleton(mode=
"write-enabled", ...)`, which always emits `## Backlog Write Mode`; the design no
longer depends on the test artifact for correctness.

#### Non-blocking

No new findings. N1–N4 from pass 1 are all accepted and their pointers verified
accurate above. One optional implementation note (not a gate): the design says
"next same-level `##` heading", so the implementer should call `section_text`
with `"##"` as `next_level_prefix` for both `## Runner Validation` and
`## Validation` — not `"###"` as the existing subskill call does. This is already
implied by the wording; flagging only to prevent an accidental copy of the
subskill call convention.

#### Overall judgment

Ready for implementation. The goal, non-goals, assumptions, and acceptance
criteria are clear and specific; the Validation Plan is runnable by the next
agent; the sole blocking thread (B1) is resolved with the fix pinned in both the
design step and the matching rule; and the revision added specificity rather than
new mechanisms, so it introduced no new implementation-risk gap. The
runner/protocol boundary remains appropriately repo-agnostic.

#### Residual risks / validation gaps

- Syntactic looseness (an agent can write "backlog" / "check" in prose without
  having run the checker) remains, acknowledged and accepted for this slice.
- Mode-spoofing (`check` keys the backlog requirement off `--mode`, not the
  manifest's recorded `## Backlog Write Mode`) is now explicitly recorded as
  out-of-scope residual risk, consistent with pass 1.
- Validation provenance for this re-review: reviewer-inspected source
  (`scout/scripts/scout_runner.py`, `scout/SKILL.md`,
  `scout/tests/test_scout_runner.py`) and the plan diff for driver response 1;
  no tests were run (none exist yet for this change). Functional proof still
  depends on the implementation-review gate executing the Validation Plan.

### Reviewer pass 3 (impl)

Human concern restated: confirm the implemented change makes a write-enabled
Scout run that recorded only setup-level provenance fail mechanically, that B1's
manifest section-boundary risk is actually handled in code, that the tests cover
the observed Data write-enabled gap, and that the validation evidence is
sufficient.

Scope of this pass: compare the implementation in commit `c678f49`
(`scout/SKILL.md`, `scout/scripts/scout_runner.py`,
`scout/tests/test_scout_runner.py`) against the accepted plan and acceptance
criteria.

Verification performed (CI-backed unless noted):

- Ran the full Validation Plan in this worktree. `python -m unittest discover -s
  scout/tests` → 14 tests OK. `tests` → 15 OK. `structured-review/tests` → 41 OK.
  `python -m compileall -q scout scripts structured-review tests` → clean. `git
  diff --check` → clean. Worktree clean; impl commit `c678f49` touches only the
  three intended files (`scout/SKILL.md` +16, `scout/scripts/scout_runner.py`
  +27, `scout/tests/test_scout_runner.py` +73).
- B1 boundary, confirmed empirically against the real `manifest_skeleton(
  "write-enabled", ...)`: `section_text(manifest, "## Validation", "##",
  artifact="MANIFEST.md")` returns only `- Report skeleton created by Scout
  runner.` / `- Overlay parsed by Scout runner.` and excludes the immediately
  following `## Backlog Write Mode` body. The bounded extraction contains no
  `backlog` token; an unbounded-to-EOF extraction would. So the load-bearing
  vacuous-pass hole B1 named is closed in code.
- Catastrophic B1 case is doubly guarded: the report `## Runner Validation`
  skeleton is literally `- Setup: completed.`, which carries no `scout_runner.py`
  / `check` tokens and is the last `##` heading (nothing can leak into it). A
  setup-only write-enabled run therefore fails on the report side before the
  backlog rule is even reached — independent of manifest bounding.

Plan-to-implementation traceability (acceptance criteria):

- AC1 (dry-run setup-only fails) — Done. `test_check_requires_runner_validation_provenance`
  passes; report skeleton carries no provenance tokens.
- AC2 (dry-run recording `scout_runner.py check` passes) — Done.
  `test_setup_and_check_report_artifacts`,
  `test_dry_run_allows_backlog_dirty_before_setup_when_unchanged`.
- AC3 (write-enabled recording check but omitting backlog fails) — Done.
  `test_write_enabled_requires_backlog_checker_provenance` (see N1 on which side
  it actually exercises).
- AC4 (write-enabled recording both passes) — Done.
  `test_write_enabled_manifest_declares_write_mode`.
- AC5 (existing structural/immutability/Vulture tests keep passing) — Done; full
  suites green above.
- AC6 (`scout/SKILL.md` and runner agree) — Done. SKILL.md `## Workflow` step 5,
  `## Report Contract` (`Runner Validation` + manifest `Validation`), and
  `## Runner Boundary` now match runner enforcement: all modes record the
  `scout_runner.py check` command/result; write-enabled also records the repo
  backlog checker command/result.

Proposed Design step 2 items all present: section helper reused for both
artifacts with an `artifact` label (N2), `## Runner Validation` / `## Validation`
both extracted with `"##"` as the boundary (per pass-2 note), token search scoped
to the extracted section, case-insensitive matching via `contains_all_tokens`,
and named constants `RUNNER_CHECK_PROVENANCE_TOKENS` /
`WRITE_ENABLED_BACKLOG_PROVENANCE_TOKEN` beside `REPORT_HEADINGS` (N3).

#### Blocking

None. The implementation matches the accepted plan, every acceptance criterion is
met with concrete evidence, all Validation Plan commands pass, and B1's section
boundary is correctly handled in code.

#### Non-blocking

**N1. The B1 negative test exercises the report side, not the manifest boundary
it nominally guards.** In `require_validation_provenance` the report-side backlog
rule is checked before the manifest-side rule, and
`test_write_enabled_requires_backlog_checker_provenance` (via
`add_validation_provenance(include_backlog_check=False)`) feeds identical
backlog-less provenance to both artifacts. I confirmed empirically that the test
raises the same `SCOUT_REPORT.md ... repo backlog checker provenance` error
whether `section_text` is bounded or regressed to unbounded — so this test would
NOT catch a future regression of the manifest `## Validation` extractor to
unbounded. Pass 2's statement that "the negative test now genuinely guards the
boundary" holds for the report side and overall behavior, but not for the
manifest boundary specifically. Suggested hardening (non-gating, code is
correct): add one test where the report records full provenance including
`backlog` but the manifest `## Validation` records only `scout_runner.py check`
(no `backlog` within its bounds), and assert a `MANIFEST.md ... backlog checker`
error. That locks the manifest boundary directly; without it the manifest-side
isolation is correct but untested.

**N2. (observation, not a gate) Mode keying carried through as planned.**
`cmd_check` keys the write-enabled backlog requirement off `args.mode`, not the
manifest's recorded `## Backlog Write Mode`. This is the mode-spoofing residual
the plan explicitly scoped out; recording that it is unchanged in the
implementation.

#### Overall judgment

Ready for closeout. The accepted plan is implemented faithfully, B1 is resolved
in code (empirically verified), the observed Data write-enabled gap (setup-only
artifacts, and the narrower "recorded check but omitted backlog" case) is caught,
and all Validation Plan commands are green in this worktree. N1 is a test-robustness
improvement, not a gate, because the code is correct and the catastrophic
vacuous-pass case is independently impossible on the report side.

#### Residual risks / validation gaps

- Manifest-boundary regression guard is missing (N1): the manifest `## Validation`
  isolation is implemented correctly but not directly tested; a future unbounded
  regression there would be masked by the report-first short-circuit.
- Syntactic looseness (accepted by the plan), sharpened: the recorded
  `scout_runner.py check --run-dir <path>` line lives inside the searched
  section, so if an adopting repo's output/run-dir path ever contained the
  substring `backlog`, the write-enabled backlog requirement could be satisfied
  by the command line itself without a real backlog-checker line. Acceptable for
  this slice (artifact checker, not executor); worth a one-line awareness note if
  this ever feels noisy.
- Mode-spoofing (N2): `check` trusts `--mode` over the manifest's recorded mode;
  out of scope for this slice per the plan.
- Validation provenance for this review: CI-backed — reviewer reran the full
  Validation Plan (scout/tests 14, tests 15, structured-review/tests 41,
  compileall, `git diff --check`) plus targeted empirical checks of the
  `## Validation` boundary and the report-first check ordering against the real
  skeletons.

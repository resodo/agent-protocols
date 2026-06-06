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
   - Require `SCOUT_REPORT.md` `Runner Validation` to record final validation
     provenance, not only setup.
   - Require `MANIFEST.md` `Validation` to mirror the final mechanical
     validation summary.
   - State that all modes must record the `scout_runner.py check` command and
     result.
   - State that write-enabled mode must also record the adopting repo backlog
     checker command and result.

2. Update `scout/scripts/scout_runner.py`.
   - Add a helper to extract section text from either report or manifest.
   - During `check`, inspect:
     - `SCOUT_REPORT.md` `## Runner Validation`;
     - `MANIFEST.md` `## Validation`.
   - Fail if either section lacks `scout_runner.py` and `check` provenance.
   - In `write-enabled` mode, also fail if either section lacks backlog checker
     provenance.
   - Keep the check intentionally syntactic. It should look for durable
     provenance text, not prove that the command actually ran.

3. Update `scout/tests/test_scout_runner.py`.
   - Add a negative test showing setup-only artifacts fail final check.
   - Add a negative test showing write-enabled artifacts fail when they record
     `scout_runner.py check` but omit backlog checker provenance.
   - Update positive setup/check tests so they simulate an agent appending
     final validation provenance before calling `cmd_check`.

## Backlog Checker Provenance Matching

Use a medium-strict rule:

- `scout_runner.py` and `check` must both appear in each final validation
  section.
- In write-enabled mode, `backlog` must appear in each final validation
  section.

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

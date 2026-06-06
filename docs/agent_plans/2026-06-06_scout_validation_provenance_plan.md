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

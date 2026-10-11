---
name: release
description: "[release agent] Preloaded by the agent that ships a release; the master uses it when a release, a switch, or a scheduled post-release check is due. Generic skeleton: preconditions, pin a commit, baseline, install, switch, staged checks, failure policy, receipts. Commands and windows come from the project overlay."
---

# Release

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/release.md`: the commands, required flags and
   receipts for production changes, the observation windows the human
   approved, the rollback target rule, environments.

## Before

1. Permission: the brief names the release and cites its approval (the
   human's current-turn instruction, an active ledger entry, or a
   pre-authorization from `away-mode`), checked by the master (Delegated
   Execution). Irreversible steps (for example a migration without a
   downgrade) are named separately with their own approval. Anything the
   brief does not name stops the release agent. When the approval is a ledger
   entry, re-read that entry right before the switch and stop if it is no
   longer `active` or no longer covers the release.
2. Observation windows: use the windows the human approved for this kind of
   release. A new window, or changed criteria, is gate G10: ask.
3. Preconditions written in the plan are checked one by one and recorded.
4. Pin the exact commit. Record the rollback target.
5. Baseline: capture the health of the running system before switching (unit
   states, error rates, alerts already firing). If the baseline is already
   unhealthy for reasons outside this release, stop and report: the checks
   after the switch could not tell the difference.

## Switch

Install, switch, migrate only through the project's official commands with
their receipts. No manual shortcuts on production; if the official command is
blocked, stop and report.

## Checks

Run each staged check the overlay names (for example 30 minutes, 2 hours, next
day). Read content, not only plumbing: for model-facing changes, read the
first outputs. When a long window blocks a dependent, only the short check
gates it unless the overlay says otherwise.

## Failure Policy

- Reversible part failed: roll back first, then diagnose.
- Small, clear bug: fix through a PR with review and CI, re-release, rerun all
  checks.
- Anything unclear: stop and report; do not improvise on production.

## After

Report: what shipped (commit, receipts), each check's result with numbers,
anything skipped and why. Update the board.

## SAFETY Rules

- No production change without the official command, flags and receipt.
- No irreversible step without its own approval.

---
name: release
description: "[production operator] Preloaded by the agent that performs a named production change (a release, a configuration change or an ops action); the master uses it when such a change or a scheduled post-change check is due. Generic skeleton: permission, preconditions, baseline, the official command, staged checks, failure policy, receipts. Commands and windows come from the project overlay."
---

# Release (production changes)

The role is defined in `agents/release.md`. Every step below applies to every
named production change; where a step applies only to a version switch, it
says so.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/release.md`: the official commands, required flags
   and receipts for production changes, the observation windows the human
   approved, the rollback target rule, environments, and the checks for each
   kind of change.

## Before

1. Permission: the brief names the change, the official command to use and
   the receipt it must leave, and cites its permission
   (`decision-boundary/SKILL.md`, Delegated Execution). The operator does not
   choose among overlay commands itself. Irreversible steps (for example a migration without a
   downgrade) are named separately with their own approval. Anything the
   brief does not name stops the production operator.
2. Observation windows: use the windows the human approved for this kind of
   change. A new window, or changed criteria, is gate G10: ask.
3. Preconditions written in the plan are checked one by one and recorded.
4. Rollback target. A version switch: pin the exact commit and record the
   previous release as the target. A configuration or ops change: record the
   previous value, or the official command's documented undo.
5. Baseline: capture the health of the running system before the change (unit
   states, error rates, alerts already firing). If the baseline is already
   unhealthy for reasons outside this change, stop and report: the checks
   after the change could not tell the difference.

## Change

Install, switch, migrate, edit configuration or run an ops action only
through the project's official commands, with their receipts. No manual
shortcuts on production; if the official command is blocked, stop and report.

## Checks

Run each staged check the overlay names for this kind of change (for example
30 minutes, 2 hours, next day). For a configuration or ops change with no
named checks: one read-back of the changed value plus the health check the
brief names. Read content, not only plumbing: for model-facing changes, read
the first outputs. When a long window blocks a dependent, only the short check
gates it unless the approved schedule says otherwise.

Gate measurements (for example a latency gate against a baseline):

- the baseline is a measurement of the live release in the same time window,
  taken just before the switch, not an older number;
- measurements run in a quiet window announced in advance with its exact
  times, during which other lines run no heavy production queries;
- record the host load with each measurement; a run taken under abnormal load
  (the overlay sets the threshold) is void and retaken, not counted as a
  failure; if retakes stay void, measure in the next quiet slot.

## Failure Policy

- Reversible part failed: roll back first, then diagnose.
- Small, clear bug: fix through a PR with review and CI, change again, rerun
  all checks.
- Anything unclear: stop and report; do not improvise on production.

## After

Report to the master (check results to a coordinator when a coordinator
dispatched the checks): what changed (commit or value, receipts), each check's
result with numbers, anything skipped and why. The master updates the board.

## SAFETY Rules

- No production change without the official command, flags and receipt.
- No irreversible step without its own approval.
- Never run a production write command to look something up.

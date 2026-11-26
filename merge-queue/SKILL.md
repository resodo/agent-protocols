---
name: merge-queue
description: "[merge agent] Preloaded by the dedicated merge agent; the master uses it when PRs are ready to merge. One merger, one PR at a time: rebase onto the previous merge, run related checks locally, run the expensive pre-merge CI once, check gated surfaces mechanically, merge, and send failures back to the author line."
---

# Merge Queue

Several lines open PRs in parallel. If each one rebases and reruns CI whenever
the default branch moves, cost grows with the square of the number of PRs and
merges collide. So exactly one merger merges, one PR at a time.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/merge-queue.md` if present: where the queue lives,
   the pre-merge command, which local checks to run, the contract paths to
   diff, required checks for special kinds of change.

## Who Merges

- The master owns merging. It may delegate the queue to one dedicated merge
  agent; then that agent is the only merger. Author lines stop at "ready" and
  hand the PR over. PRs opened by other sessions are reported into the queue
  too; if another session is already running a pre-merge job, pause until it
  finishes.
- Permission and who executes a merge: `decision-boundary/SKILL.md`,
  Delegated Execution. The master writes the permission into the queue entry
  when it queues a PR; the merge agent merges only PRs whose line names it,
  verifies a cited ledger entry right before merging as that section says, and
  never uses the ledger to find permission.
- Once a PR is in the queue its author does not push to it; the author sends
  rebase, fix and follow-up requests to the merger.

## Queue File

The overlay says where the queue lives: a queue file, or ready rows in the
master's running log (the project's decision ledger). If it names nothing, use
`templates/MERGE_QUEUE.md`. Whatever the place, a queued item carries the PR,
the head it was prepared at, the check evidence and the permission, and a later
entry for the same PR (new head, hold, superseded) replaces the earlier one.
With the file, states are `[ ]` waiting, `[~]` in progress, `[x]` merged, `[!]`
returned to the author with the reason, and merged lines are archived daily.
The master queues a PR after checking the gated surfaces; the merger records
its result (merged at which head, or stopped and why) in the same place.

## For Each PR, In Order

1. Read the PR title and body: anything saying "do not merge", "draft",
   "candidate", or unmet acceptance items stops here.
2. Rebase onto the current default branch (after the previous merge). Record
   the PR head before you start; push the rebased branch only with a lease on
   that recorded head (`--force-with-lease=<branch>:<recorded sha>`), and if the
   remote head moved, stop and start again: the author may have added commits.
3. Gated surfaces, checked mechanically against the diff, not from the PR
   description: contract paths from the overlay (any change -> stop and
   report to the master, even nullable or additive); migrations; a vendored
   submodule pointer that moved backwards (sync the author's branch first);
   and every item the overlay's gated command lists (in a repo that wires the
   docs check, `docs_check.py gated --log <run log>`). Each listed item needs
   its answer in the queue entry (the human's dated words or the ledger entry);
   a scope-review record missing from the runner's log goes back to the
   author.
4. Run the related tests and light checks locally; read the full result
   (count, failures, exit code), never only the tail.
5. Run the expensive CI once, right before merging, with the overlay's
   pre-merge command. The overlay's CI and merge contract says what a push
   triggers and which merge method is used.
6. A failure: one rerun only if it is judged flaky; otherwise mark `[!]` and
   send the reason to the author line. The merger never edits business code.
7. Merge; record the merge. When the merge method rewrites hashes (rebase or
   squash), cite commits as `<sha> (PR #N)`.

## SAFETY Rules

- Do not merge without the permission the queue entry names
  (`decision-boundary`, Delegated Execution).
- Do not merge past a gated-surface diff without the human's answer, or an
  active ledger entry that covers it.
- Do not report "green" without reading every check.

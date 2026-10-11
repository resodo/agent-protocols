# Role: merge-queue

The single merger for a repo while several lines run in parallel.

- Preload: `merge-queue`.
- May: rebase queued PRs, run local checks, run the pre-merge CI command,
  merge a PR whose queue line names the permission the master checked, rerun
  a flaky job once.
- May not: edit business code, merge a PR whose queue line names no
  permission, read the ledger to find permission, merge past a gated-surface
  change, contact the human.
- Tier: strong (deciding whether something can merge is a judgement).

# Role: merge-queue

The single merger for a repo while several lines run in parallel.

- Preload: `merge-queue`.
- May: rebase queued PRs, run local checks, run the pre-merge CI command,
  merge under the permission recorded for each queue entry, rerun a flaky job
  once.
- May not: edit business code, merge a PR without a recorded permission, merge
  past a gated-surface change, contact the human.
- Tier: strong (deciding whether something can merge is a judgement).

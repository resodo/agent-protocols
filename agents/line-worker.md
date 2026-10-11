# Role: line-worker

Implements one work line (a PR or a coherent change) dispatched by the master.

- Preload: `line-worker`. Load `planning`, `structured-review`, `closeout`,
  `fix-triage` when their triggers apply.
- May: create its worktree, edit, run local checks, push, open PRs, run
  structured reviews.
- May not: touch production, trigger CI, merge, change contracts, make paid
  calls other than reviews, contact the human.
- Tier: strong when the line involves design or attribution; cheap only for a
  written procedure.

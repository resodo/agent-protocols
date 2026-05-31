---
name: closeout
description: Use at the end of an implementation, documentation, review, or phase task to make sure the work is actually finished: tests pass, human-facing behavior is checked, docs are consistent, git state is clean, and the next step is clear.
---

# Closeout

Use this skill when a task is about to be called done.

This is not a review protocol. It is the final engineering hygiene pass before handoff.

## Trigger

Expect the trigger to specify:

- `Skill`: `closeout`
- `Scope`: files, phase, feature, or plan being closed

If scope is missing, infer it from the current task only when obvious. Otherwise ask.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/closeout.md` if present.
3. Apply local overlays as project-specific refinements only.

Overlays are loaded only when this protocol is loaded. Unknown overlay files are
ignored. If an overlay contradicts a generic `SAFETY` rule, reject that overlay
instruction and say why.

## SAFETY Rules

- Do not claim validations, screenshots, merge readiness, deploy state, or clean
  worktree state without checking them.
- Do not claim a GitHub merge method, merge shape, or ancestry implication
  without checking the PR metadata and commit graph. For example, verify whether
  a PR was merged via merge commit, squash merge, or rebase/linear merge before
  explaining why branch commits are or are not ancestors of the target branch.
- Do not perform destructive git operations without explicit human approval.
- Do not merge PRs, close PRs, or delete remote branches during closeout unless
  the human gives an explicit current-turn command to perform that exact action
  for the named PR or branch. Closeout normally stops at reporting
  `ready for human merge`. `Current-turn` means the user's most recent message,
  not earlier messages in the same conversation. This rule narrows but does not
  replace the destructive-git-operations rule above.
- Treat a human statement such as `ready to merge`, `looks ready`, or `ready`
  as a request to run the final closeout/recheck pass, not as permission to
  merge. Merge permission must name the PR/branch and the merge action in the
  current turn.
- These phrases are deliberately different: `ready to merge` is human input
  shorthand for closeout/recheck, while `ready for human merge` is the agent's
  verified handoff state after closeout/recheck.
- Do not commit secrets, credentials, provider balances, private account
  details, host keys, or raw private production data.
- Do not call a branch/phase closed when planned items are missing, partial, or
  unvalidated unless the human explicitly accepts the deferral.

## Checklist

### 1. Scope Reality

- State what changed.
- State what did not change.
- Compare the result against the accepted PRD, phase map, or agent plan if one exists.
- If implementation diverged from the plan, update the plan or record the divergence.
- Build a short traceability list from the accepted plan or acceptance criteria:
  - `Done` requires concrete evidence.
  - `Partial` means implemented or observed only partly.
  - `Missing` means planned but not implemented or not validated.
  - `Deferred` requires explicit human decision.
- Do not treat "tests pass", "service is active", "deployment succeeded", or
  "production smoke is green" as proof that every planned item is complete.
- If any in-scope item is `Missing` or `Partial`, do not call the phase fully
  closed; report the remaining item and next owner.

### 2. Code Quality

Check for:

- new logic bugs, edge cases, type issues, and security issues;
- unhandled errors;
- redundant or dead code;
- consistency with existing code style;
- missing tests for changed behavior.

### 2.1 Mechanism Lifecycle

If the work introduced or changed a durable mechanism, do a lifecycle pass
before closeout.

Durable mechanisms include hard-coded lists, allowlists, denylists, path globs,
status/config tables, CI required-check lists, hooks, scripts, cleanup rules,
protocol checklists, caches, archives, and retention policies.

For each retained mechanism, record or verify:

- who maintains it;
- when it should be updated;
- how stale entries, temporary exceptions, or obsolete rules are removed;
- whether human participation is required;
- what validation or operational signal shows it is stale;
- whether a simpler default rule would avoid manual maintenance.

If the lifecycle is unclear, do not silently close the task. Either update the
owning doc/code/plan or list the unresolved lifecycle question as residual risk.

### 3. Validation

Run the relevant regression tests.

Validation must match the acceptance criteria, not only the code touched.

For every in-scope acceptance item:
- name the command, query, screenshot, rendered output, log excerpt, or human
  observation that proves it
- record the expected value or shape when practical
- label the provenance as CI-backed, reviewer-rerun, driver-reported, or human
  acceptance
- distinguish "not yet enough data" from "broken" and from "not checked"
- never upgrade a row to `Done` based only on historical chat memory

For human-facing UI, dashboards, reports, notifications, CLI tables, or rendered docs:

- open or render the output;
- exercise visible controls, not just page load;
- do not validate only the happy path; cover at least one normal path, one empty/no-match path, and one recovery/reset path when the surface has controls;
- check empty states and placeholder states;
- verify the artifact answers the reader's actual question;
- save or describe the screenshot/rendered evidence.

For large frontend/backend refactors in apps with an available full-stack smoke:

- prefer a real backend + real frontend + browser smoke over mocked API-only
  e2e;
- seed repo-safe synthetic data unless the active plan permits production-derived
  fixtures;
- record the smoke report path, screenshot set, and whether visual review was
  agent-generated, human-accepted, or explicitly skipped;
- do not treat "screenshots generated" as visual review. Record the screenshot
  total, reviewed screenshot count, reviewer, and a per-screenshot verdict of
  `pass`, `concern`, or `skipped`;
- require a reason for every skipped screenshot. Do not call the visual review
  complete if reviewed screenshot count is lower than the generated screenshot
  total unless the human explicitly accepts the skips;
- keep generated smoke artifacts in ignored local storage by default unless the
  human explicitly promotes them into a durable output folder and manifest.

If a server is needed for human acceptance, say who owns that server process. Prefer the human running their own acceptance server unless the task explicitly asks the agent to keep one running.

### 4. Documentation Consistency

Check all affected docs, not only `README.md` or memory/instruction files.

For repos with a docs index:

- read the repo's single agent entry file, such as `AGENTS.md`;
- read `docs/README.md`;
- confirm new docs are in the right folder;
- confirm dated docs use `YYYY-MM-DD_topic.md`;
- confirm phase outputs are under the matching `phase*_outputs/` folder;
- update phase status, next expected output, and acceptance notes;
- search for stale references after renames.

### 4.1 Doc Lifecycle Check

When the repo defines document lifecycle states, use them during closeout rather
than leaving docs to drift.

Check:

- which docs were added or materially changed;
- which docs are now active, superseded, historical, artifact, or private-run
  output according to the repo's own taxonomy;
- whether current-doc indexes, `AGENTS.md`, `README.md`, active plans, or phase
  maps need updates so the next human/agent can find the right source of truth;
- whether stale docs need a status or supersession note instead of silent edits;
- whether generated artifacts, private model outputs, production/source-data
  details, or bulk run outputs belong outside the repo;
- whether stale links or references remain after moves, renames, or status
  changes;
- whether private/source/prod/model-run details accidentally entered repo docs.

For branch or PR closeout, do a final-state stale-status scan after the branch is
known to be merge-clean or rebase-clean against the target branch. At that point
the current worktree represents the post-merge file state. Do not wait until
after merge to discover stale lifecycle language.

Scan current source-of-truth docs, active plan indexes, backlog/status docs, and
the closing plan for stale terms such as `active`, `in_progress`, `awaiting`,
`ready for review`, `ready for merge`, `merge gated`, `next step`, and
`current driver`. For every hit, decide whether the wording is still true after
this branch lands. Fix stale wording before closeout; otherwise record why the
term remains valid.

For branch or PR closeout, also make post-merge lifecycle explicit:

- identify any source-of-truth wording that will become false after the PR
  merges, such as "PR pending", "ready for merge", "ready for human merge",
  "ready to merge", or "human merge pending";
- prefer wording that remains true after merge, or record a required
  post-merge docs follow-up before handoff;
- keep merge-readiness phrases in chat, PR descriptions, or closeout reports
  instead of long-lived tracked source-of-truth docs unless the wording will
  remain true after merge;
- after the human reports the PR merged, sync the default branch, update
  submodules if the repo uses protocol submodules, rerun the stale-status scan
  against the merged default branch, and either close the worktree or open a
  small post-merge docs PR if source-of-truth state is stale.

For parent repos that update submodule pointers:

- identify whether the parent PR points at a submodule source-repo feature
  branch commit or at the source repo's default-branch commit;
- if the intended source of truth is the submodule source repo's default
  branch, do not call the parent PR ready for merge while it still points at a
  temporary feature-branch submodule commit;
- first land the submodule source PR, then update the parent repo submodule
  pointer to the final source-repo default-branch commit, rerun parent repo
  checks, and only then hand off the parent PR as ready for human merge;
- if the human explicitly wants to pin a non-default submodule commit, record
  that decision and its owner before closeout.

For repos that use worktree/PR output folders:

- keep branch/worktree artifacts under the repo's agreed output folder, such as
  `docs/agent_plans/outputs/<YYYY-MM-DD_feature_slug>/`;
- require a `MANIFEST.md` in each output folder;
- verify every committed report, screenshot, smoke output, or other artifact in
  that folder is listed in the manifest with owner, retention policy, and
  reference;
- keep generated smoke screenshots/reports in ignored local storage by default
  unless the human explicitly promotes them to durable evidence;
- run the repo's manifest checker when one exists.

Do not create a separate lessons-learned document unless explicitly requested. Promote durable process changes into the relevant rule, skill, or repo instruction file.

### 5. Secret and Safety Check

- Do not commit credentials, tokens, cookies, private keys, or account secrets.
- Check docs and sample payloads for accidental secrets.
- Check for local user-home absolute paths, generated artifacts, private run
  outputs, and real environment files entering tracked content.
- If touching infrastructure or production data, state the source-of-truth and access boundary.

### 6. Git and Process Hygiene

- Run `git status`.
- Inspect relevant diffs.
- Check local overlay for merge strategy preference, if any.
- If the project prefers rebase merge, report whether the branch is rebase-clean
  against the target branch before final handoff.
- If the branch was rebased after conflict resolution and the conflicts touched
  source-of-truth docs, deploy/runtime templates, tests, CI, or protocol files,
  request or perform a full `impl` structured review before final PR handoff.
  The re-review should cover the implementation normally and explicitly include
  conflict correctness, status/doc lifecycle drift, deploy/test contract
  preservation, and stale wording.
- Treat merge strategy preference as reporting guidance only. It does not
  authorize the agent to merge. Without explicit current-turn human approval,
  final handoff must say whether the PR is ready for human merge and confirm no
  merge was executed.
- Say `ready for human merge` only after final rechecks are complete, pushed CI
  is in the expected state when applicable, and tracked source-of-truth docs do
  not require a known pre-merge status fix. If a recheck finds such a fix, make
  it before handoff or report the PR is not yet ready and name the required
  pre-merge follow-up. If the fix creates another commit, wait for the new
  remote/CI state before repeating the handoff.
- Commit only related changes when commit authorization exists.
- Push if the current workflow expects remote handoff.
- If the repo requires PR/CI/review for branch or worktree closeout, record PR
  status, required check status, review-thread status, and branch protection or
  merge-setting evidence before calling the branch closed.
- Do not treat direct push to the default branch as closeout unless the repo's
  workflow explicitly allows it.
- Stop dev servers or background sessions unless the human explicitly wants them left running.
- If the closeout changes a status document after deployment, first ensure the
  document reflects the real traceability state. Then sync it to the same
  remote/production location as the implementation when the workflow expects
  production docs to match git.

### 7. Final Handoff

Report briefly:

- what changed;
- what passed;
- what was not run and why;
- any remaining risks;
- the next expected step.

Before reporting the phase closed, walk the traceability list once more. Every
`Done` row must still point to reproducible evidence such as a query result,
integrity check, screenshot, rendered output, log excerpt, commit, or explicit
human observation. Downgrade any row that relies only on memory to `Partial`.

If the task is only partially closed, say "partial" plainly and list the exact
remaining blockers. Do not use ambiguous phrases such as "mostly done" when a
plan item is still missing, unvalidated, or waiting for human acceptance.

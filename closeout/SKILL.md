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

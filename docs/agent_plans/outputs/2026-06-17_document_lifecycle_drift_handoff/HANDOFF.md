# Document Lifecycle Drift Handoff

Status: artifact
Owner: next driver
Date: 2026-06-17

## Project

- Repository: `agent-protocols`
- Remote: `origin` (`git@github.com:resodo/agent-protocols.git`)
- Handoff branch: `handoff/document-lifecycle-drift-20260617`
- Base commit at branch creation: `ed61c6a`
- Default branch at branch creation: `main`, aligned with `origin/main`

## Current Task Goal

Prepare the next Scout protocol change for a `document-lifecycle-drift`
subskill, but stop at repo-safe handoff. No new protocol feature work was
implemented in this handoff branch.

The proposed subskill should identify documentation whose lifecycle state,
currentness, routing, or status wording can mislead future agents or operators.
It should stay distinct from `document-structure`, which covers readability,
shape, navigation, and large-document decomposition.

## Completed Work

- Confirmed the repo entrypoint and documentation rules:
  - `AGENTS.md`
  - `README.md`
  - `docs/README.md`
  - `docs/CURRENT.md`
  - `docs/agent_plans/README.md`
- Loaded the `closeout` protocol for this handoff.
- Confirmed the default checkout was clean before creating the handoff branch.
- Created this repo-safe handoff artifact under `docs/agent_plans/outputs/`.
- Did not implement or edit the Scout protocol itself.

## Not Completed

- No implementation plan was written for `document-lifecycle-drift`.
- No structured plan review was run.
- No Scout reference, runner schema, tests, or current protocol map changes were
  made for the new subskill.
- No downstream Skyline V2 or Skyline Data overlays were changed.
- No cold-start validation was run for this new subskill.

## Current Decisions And Open Questions

Recommended defaults from the prior discussion:

- Use the subskill name `document-lifecycle-drift`.
- Keep it orthogonal to `document-structure`:
  - `document-structure`: document shape, length, navigation, readability.
  - `document-lifecycle-drift`: stale status, stale current routing, outdated
    instructions, historical docs that look current, backlog/doc state drift.
- Admit backlog candidates only when a document is likely to mislead current
  agent/operator decisions and has a clear remediation path.
- Keep weaker or provenance-only signals as report-only observations.
- Apply the active-feature suppression rule by default. Active feature docs
  should not be cleaned up early unless stale wording would cause a wrong
  current action.

Still worth confirming before implementation:

- Whether `document-lifecycle-drift` is the final name.
- Whether the candidate threshold above is strict enough to avoid noisy Scout
  output.

## Blockers, Bugs, And Risks

- No current implementation blocker is known.
- Residual tooling issue from previous cold-start work: `codex exec` with
  workspace-write sandbox blocked `git fetch` writes to `.git/FETCH_HEAD` in
  temporary clones, so prior cold-start Scout smoke used an ephemeral
  bypass-approvals/sandbox mode. This was not investigated in this handoff
  branch.
- Risk: without a strict candidate threshold, lifecycle drift could produce
  noisy findings against normal in-flight planning docs.
- Risk: if active feature docs are treated like stable docs, Scout may propose
  premature cleanup for intentionally changing work.

## Key Files And Entrypoints

- Agent entrypoint: `AGENTS.md`
- Repo overview: `README.md`
- Current protocol map: `docs/CURRENT.md`
- Docs lifecycle rules: `docs/README.md`
- Agent plan index: `docs/agent_plans/README.md`
- Scout protocol: `scout/SKILL.md`
- Existing Scout references:
  - `scout/references/script-lifecycle.md`
  - `scout/references/code-reachability-backend-python.md`
  - `scout/references/document-structure.md`
  - `scout/references/code-structure.md`
- Scout runner: `scout/scripts/scout_runner.py`
- Scout runner tests: `scout/tests/test_scout_runner.py`

## Commands And Validation Run

Discovery and safety commands run for this handoff:

```bash
pwd
git rev-parse --show-toplevel
git remote -v
git branch --show-current
git status --short --branch
git diff --stat
git worktree list
git log -1 --oneline --decorate
```

Observed state before the handoff branch:

- Branch: `main`
- Status: clean and aligned with `origin/main`
- Base commit: `ed61c6a`

Validation not run:

- No unit tests were run because this handoff branch only adds documentation and
  does not change protocol code, scripts, schemas, or tests.
- No structured review was run because this is a handoff artifact, not an
  implementation plan or protocol change.

## Local Or Private Artifacts Not Committed

- Prior cold-start Scout smoke outputs in temporary clone locations were not
  committed. They remain local execution artifacts and should not be treated as
  source-of-truth docs.
- No secrets, credentials, environment files, account details, private
  production logs, or large generated artifacts were committed.

## Background Processes

- No background services, dev servers, jobs, experiments, or model runs were
  started for this handoff.
- No background process needs to be stopped by the next driver.

## Suggested Next Steps

1. Start a normal feature worktree/branch for the Scout
   `document-lifecycle-drift` subskill.
2. Write an implementation plan under `docs/agent_plans/` and run the bundled
   structured-review runner as a plan review.
3. Implement only after the plan review gate is resolved.
4. Expected protocol changes:
   - add `scout/references/document-lifecycle-drift.md`;
   - update `scout/SKILL.md`;
   - update `scout/scripts/scout_runner.py` overlay/report validation;
   - update `scout/tests/test_scout_runner.py`;
   - update `README.md` and `docs/CURRENT.md` if references or protocol map
     entries change.
5. After the protocol PR merges, use separate downstream PRs for Skyline V2 and
   Skyline Data overlays, then run cold-start dry-run validation.

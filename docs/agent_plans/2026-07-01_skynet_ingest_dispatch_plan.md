# Skynet Ingest Dispatch Workflow Plan

Status: implementation plan, awaiting structured review
Date: 2026-07-01
Driver: Codex

## Context

Skynet Ingest now vendors `external/agent-protocols` and already has a target
repo workflow named `Update Agent Protocols Submodule`. That target workflow is
triggered by `repository_dispatch` event type `agent-protocols-updated` and uses
the target-repo secret `SKYNET_INGEST_AUTOMATION_TOKEN` to update the submodule
pointer and open a PR.

The missing source-repo side is an `agent-protocols` workflow that dispatches to
`MAGI-Systems-01/skynet-ingest` whenever `agent-protocols/main` changes. This
should match the existing organization pattern used by Skynet V2 and Skynet
Twitter: each target repo has an automation token in the target repo, and a
separate dispatch token in `resodo/agent-protocols`.

Current secret presence has been verified by name only:

- `MAGI-Systems-01/skynet-ingest`: `SKYNET_INGEST_AUTOMATION_TOKEN`
- `resodo/agent-protocols`: `SKYNET_INGEST_DISPATCH_TOKEN`

No token values, credentials, or private account details are in scope for this
plan or any repo artifact.

## Goal

Add a source-side GitHub Actions workflow in `resodo/agent-protocols` that sends
the standard `agent-protocols-updated` repository dispatch event to
`MAGI-Systems-01/skynet-ingest`.

## Non-Goals

- Do not change Skynet Ingest target-side workflow behavior.
- Do not rotate, create, print, or commit secrets.
- Do not add broad GitHub Actions permissions to the workflow.
- Do not live-trigger a dispatch from the feature branch unless the human
  explicitly asks for that operational smoke.
- Do not change protocol source files, skill mounts, or downstream submodule
  pointers in this PR.

## Implementation

1. Add `.github/workflows/dispatch-skynet-ingest.yml`.
2. Mirror the existing dispatch workflow structure:
   - trigger on `push` to `main`;
   - allow `workflow_dispatch`;
   - set top-level `permissions: {}`;
   - use `GH_TOKEN: ${{ secrets.SKYNET_INGEST_DISPATCH_TOKEN }}`;
   - dispatch to `MAGI-Systems-01/skynet-ingest`;
   - send event type `agent-protocols-updated`;
   - include `client_payload.repository` and `client_payload.sha`.
3. Keep naming aligned with existing workflows:
   - workflow name: `Dispatch Skynet Ingest Protocol Update`;
   - step name: `Dispatch Skynet Ingest update`;
   - env var: `SKYNET_INGEST_REPO`;
   - missing-secret message: `SKYNET_INGEST_DISPATCH_TOKEN is not configured.`

## Validation

Run from the `agent-protocols` worktree:

```bash
python scripts/check_backlog.py
python -m unittest discover -s tests
python -m unittest discover -s structured-review/tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout
```

Also validate the workflow file:

```bash
actionlint .github/workflows/dispatch-skynet-ingest.yml
```

If `actionlint` is unavailable locally, install or invoke it without committing
generated binaries or caches.

Before closeout, verify both required secret names still exist with `gh secret
list` and do not print secret values.

## Acceptance

- The new workflow is structurally consistent with the V2 and Twitter dispatch
  workflows.
- The workflow uses only `permissions: {}` and the dispatch token secret.
- The workflow targets `MAGI-Systems-01/skynet-ingest`.
- Local validation passes or any skipped command is explicitly reported.
- PR is opened in `resodo/agent-protocols` for human review/merge.
- Post-merge behavior is clear: the next push to `agent-protocols/main` should
  dispatch to Skynet Ingest, whose target workflow may open a submodule update
  PR only when the pinned submodule SHA changes.

## Risks

- The actual token permission cannot be proven from `gh secret list`; it can
  only be validated by a live workflow run. This plan avoids feature-branch live
  dispatch by default and leaves live validation to post-merge workflow behavior
  unless the human explicitly requests a smoke.
- If Skynet Ingest target workflow changes independently, this source workflow
  might dispatch successfully but target-side update behavior could differ.

## Review Threads

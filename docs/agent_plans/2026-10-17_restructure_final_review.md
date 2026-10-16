# Whole-repo review after the restructure (review request)

Document level: review request (no PR is opened from this file's findings
alone; blocking findings get fix PRs).

Status: active (2026-10-17).

## Why

The approved restructure decision (`2026-10-16_repo_restructure_decision.md`)
requires, after its five plans, a hard review of the **full resulting state**
(not the diffs) until it converges. Plans 1-4 merged: agent-protocols #45, #46,
#47; skynet-intern #1712; skynet-apps #44. Plan 5 (personal files and memory,
outside all repos) is done and is not reviewable here.

## What to review

1. This repo at this commit: every protocol, `agents/`, `agent-readiness/`,
   `README.md`, `AGENTS.md`, `docs/CURRENT.md`, `docs/README.md`.
2. skynet-intern, read-only, at the relative path `../../../skynet-intern/main/`
   from this worktree: `AGENTS.md`, every file in `.agent-protocols/`,
   `scripts/agent_protocols_guard.sh`, `scripts/ops/hooks/agent_role_reminder.py`,
   `docs/collaboration/worktree_feature_protocol.md`. Cite as `intern:<path>`.
3. skynet-apps, read-only, at `../../../skynet-apps/main/`: `AGENTS.md`, every
   file in `.agent-protocols/`, `scripts/agent_protocols_guard.sh`. Cite as
   `apps:<path>`.

## Questions

1. Did the restructure achieve the decision's target (sections 3-5): one role
   file per role with the same fields; one master definition; each protocol's
   reader and scope stated; each rule in one home with pointers elsewhere;
   core vs overlay vs personal correctly placed?
2. Contradictions or gaps introduced by the restructure: rules that now
   disagree, pointers to sections that do not exist or do not contain the
   rule, rules dropped in a move, a weakened `SAFETY` rule.
3. Remaining duplication or stale text (indexes, examples, overlays restating
   the core).
4. Role scenarios, each answered from the files only: a master taking over; a
   coordinator at a point of no return; a direct session told to merge while a
   master runs; a researcher told to read production; a worker whose brief
   cites an approved contract change; an agent typing a ledger entry; a
   production operator doing a configuration change; a line handing a PR to
   the merge queue and then wanting to fix a typo.

## Output

Findings by question, each with severity (blocking / should fix / note),
citations, and the smallest fix, deletion first. Say explicitly whether the
state has converged (no blocking findings).

## Review Threads

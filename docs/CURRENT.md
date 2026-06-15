# Current Protocol Map

Status: active source-of-truth map
Last updated: 2026-06-10

This file points humans and agents to the active protocol entrypoints. It does
not replace root `AGENTS.md`; agents should start there, then use this map to
avoid treating historical plans as current instructions.

## Current Anchors

- Agent entrypoint: `AGENTS.md`
- Repo overview: `README.md`
- Documentation rules: `docs/README.md`
- Protocol change plans and review artifacts: `docs/agent_plans/`
- Protocol-development backlog: `docs/backlog.yml`

## Current Protocols

- `structured-review/SKILL.md` - structured review for plans,
  implementations, optional closeout evidence reviews, and review-response
  passes. Repo-backed review gates default to the bundled runner when
  available, with cross-vendor Claude and Codex reviewer backends.
- `closeout/SKILL.md` - final hygiene checklist and delivery handoff after
  implementation, documentation, review, or phase work.
- `planning/SKILL.md` - discussion-to-plan workflow before implementation.
- `retrospective/SKILL.md` - evidence-based post-incident or post-closeout
  learning workflow.
- `backlog-maintenance/SKILL.md` - YAML backlog registry maintenance protocol.
  This repo dogfoods it through `docs/backlog.yml`.
- `scout/SKILL.md` - judgment-heavy repository discovery workflow for
  lifecycle, reachability, coverage, documentation, process, and
  maintainability findings that should become human-reviewed backlog
  candidates rather than CI failures.
- `agent-readiness/` - worktree guard contract and agent bootstrap template for
  downstream repos.

## Runner And References

- Structured-review runner:
  `structured-review/scripts/claude_structured_review.py`
- Runner-loaded structured-review references:
  `structured-review/references/review-lenses.md` and
  `structured-review/references/collaboration.md`
- Conditional UI review reference:
  `structured-review/references/ui-review.md`
- Scout runner:
  `scout/scripts/scout_runner.py`
- Scout references:
  `scout/references/script-lifecycle.md`,
  `scout/references/code-reachability-backend-python.md`,
  `scout/references/document-structure.md`, and
  `scout/references/code-structure.md`

The UI review reference is conditional. It is not part of the runner-loaded
required reference set unless a future accepted plan changes runner loading.

## Maintenance

Update this map during closeout when protocols, indexes, runner paths,
reference paths, or backlog ownership change.

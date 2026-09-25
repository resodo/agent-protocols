# Current Protocol Map

Status: active source-of-truth map
Last updated: 2026-09-25

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
  available, with Claude > Codex > Grok ordering excluding the coding agent,
  automatic missing-binary/exhausted-allowance fallback without per-provider
  permission, and explicit
  driver-owned normal/hard tier selection, rationale-required hard profiles,
  and recommendation-only mechanical complexity signals. Legacy auto safely
  selects normal with deprecation provenance. Normal/hard time limits are
  1800/3600 seconds. Claude uses Opus 5.5 at high for normal and Fable 5.1 at
  xhigh for hard; Codex uses GPT-6 Sol at high and GPT-6 Astra at xhigh. Grok
  uses 4.7 at medium/xhigh. Normal is default; hard is reserved by agent
  judgment for roughly the hardest 20% (major design/architecture or difficult
  bugs).
  Driver stop
  requests and guarded same-session recovery retain private per-attempt evidence.
  When acceptance depends on runnable behavior, Implementation Review readiness
  requires candidate-bound evidence that the intended changed behavior works;
  routine or documentation-only changes use readable scenarios or direct
  inspection, with explicit handling when access or cost prevents proof.
  Review responses are deletion-first: drivers ask whether deleting, rewording,
  or a known limitation resolves a finding before adding a mechanism, any new
  alert, counter, registry, config field, or script goes to the human,
  reviewers give the no-mechanism
  alternative, and passes are uncapped but stop on named stop-and-ask signals.
  Layer ownership is named only from a written repo definition; otherwise it is
  an escalation to the human. Fixes default to the long-term systemic fix; a
  wrong premise or a cause outside the change halts the loop for the human.
  Documents state their level: decision doc (an agent-facing source plus a
  readable brief in the same PR; approved only after the human reads the brief
  in full, then merged and split into plans; four-check review; written scope
  first, deferred items worded as candidates, human annotations on the brief
  committed verbatim first), plan (one PR), or implementation. Only the session
  that received a human approval records it.
- `closeout/SKILL.md` - final hygiene checklist and delivery handoff after
  implementation, documentation, review, or phase work, including verification
  that change-specific core-path evidence preceded review and merge.
- `planning/SKILL.md` - discussion-to-plan workflow before implementation, with
  bounded low-cost evidence for decision-changing uncertainties.
- `retrospective/SKILL.md` - evidence-based post-incident or post-closeout
  learning workflow.
- `backlog-maintenance/SKILL.md` - YAML backlog registry maintenance protocol.
  This repo dogfoods it through `docs/backlog.yml`.
- `readable-brief/SKILL.md` - turns a final, reviewed technical document into a
  brief for the human decision-maker: conclusion first, every term defined,
  process detail omitted, nothing to decide dropped or softened, ending with the
  points to confirm or reject. Required for decision docs, optional for other
  human-read documents. Reviewed once with the narrow fidelity-plus-readability
  lens; the consumer overlay supplies language, banned words, and delivery.
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
  `structured-review/references/collaboration.md`. `review-lenses.md` also
  holds the brief-only `Readable Brief: Fidelity And Readability` lens.
- Driver recovery operations: `structured-review/references/recovery.md`
  (not a runner-loaded review lens).
- Conditional UI review reference:
  `structured-review/references/ui-review.md`
- Scout runner:
  `scout/scripts/scout_runner.py`
- Scout references:
  `scout/references/script-lifecycle.md`,
  `scout/references/code-reachability-backend-python.md`,
  `scout/references/document-structure.md`,
  `scout/references/document-lifecycle-drift.md`, and
  `scout/references/code-structure.md`

The UI review reference is conditional. It is not part of the runner-loaded
required reference set unless a future accepted plan changes runner loading.

## Maintenance

Update this map during closeout when protocols, indexes, runner paths,
reference paths, or backlog ownership change.

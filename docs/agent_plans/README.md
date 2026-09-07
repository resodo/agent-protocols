# Agent Plans

This directory holds dated plans, review-thread records, implementation
responses, and closeout evidence for changes to this repo's protocols.

## Rules

- Use `YYYY-MM-DD_topic.md`.
- Keep review threads in the same plan artifact when the structured-review
  runner writes to the plan.
- Treat completed dated plans as historical records. Do not rewrite old reviewer
  or driver thread text just to modernize paths after a later file move.
- Update live indexes such as `README.md`, `AGENTS.md`, `docs/README.md`, and
  `docs/CURRENT.md` when a plan changes the repo's durable organization or
  protocol entrypoints.
- Review these rules during closeout documentation-consistency checks when
  plan or artifact handling changes.

## Current Records

- `2026-09-07_grok_reviewer_plan.md` - third reviewer backend, ordered credit
  fallback, no per-provider availability permission, rare-hard guidance, and
  real Grok dogfood/recovery evidence.

- `2026-08-07_evidence_discipline_rules_plan.md` - two `Shared Review Rules`
  bullets (a mechanism described with enforcing verbs is unverified until a
  sample it must catch has made it fail; an absence is not a fact until the
  presence case is shown), a `Guard Reach` lens in `review-lenses.md` carrying
  the reasoning and the execution-required clause for state claims, and two
  `closeout` bullets (contract verification is not acceptance after a deploy;
  read CI at the exact commit and name the excluded suites). Derived from a
  downstream session in which a re-run-safety finding was judged resolved by
  three independent review passes and went red on the first run of an execution
  harness. Registers `AP-BL-0007` and `AP-BL-0008` for the rules with no
  reachable home.

- `2026-06-04_claude_runner_plan.md` - Claude structured-review runner plan.
- `2026-06-05_structured_review_runner_default_refactor_plan.md` - runner
  default and structured-review refactor plan.
- `2026-06-05_review_closeout_boundary_plan.md` - review/closeout boundary and
  documentation organization plan.
- `2026-06-05_scout_skill_plan.md` - Scout discovery protocol plan.
- `2026-06-06_scout_validation_provenance_plan.md` - Scout validation
  provenance hardening plan.
- `2026-06-10_scout_validation_provenance_closeout.md` - closeout report for
  the Scout validation provenance work (PR #13).
- `2026-06-10_codex_reviewer_backend_plan.md` - Codex reviewer backend and
  cross-vendor default runner plan.
- `2026-06-10_canonical_protocol_source_plan.md` - canonical protocol source
  rule, guard freshness, and native skill mount plan.
- `2026-06-15_scout_structure_subskills_plan.md` - implementation plan for the
  `document-structure` and `code-structure` Scout subskills.
- `2026-06-16_scout_active_timeout_plan.md` - Scout active feature suppression
  and structured-review timeout discipline plan.
- `2026-06-17_document_lifecycle_drift_plan.md` - implementation plan for the
  `document-lifecycle-drift` Scout subskill.
- `2026-07-20_review_tier_model_matrix_plan.md` - historical implementation,
  review, and closeout record for merged PR #25, covering automatic reviewer
  tiers and the backend/model matrix.
- `2026-07-22_explicit_review_tier_ownership_plan.md` - implementation and
  review artifact for shared protocol PR #27, covering driver-owned tier
  selection, recommendation-only signals, and safe legacy-auto migration.
- `2026-07-22_explicit_review_tier_closeout.md` - closeout evidence for shared
  protocol PR #27, including traceability, validation, compatibility, and
  downstream submodule-bump handoff.

- `2026-09-06_review_resume_plan.md` - model/time-limit upgrade, driver stop,
  session recovery, independent reviews, and live dogfood evidence.

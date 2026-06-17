# Scout Document Lifecycle Drift Plan

Status: active implementation plan
Owner: driver
Date: 2026-06-17

## Goal

Add a Scout subskill named `document-lifecycle-drift` that helps agents find
current-facing documentation whose lifecycle state, routing, status wording, or
current-fact claims can mislead present agent/operator decisions.

The subskill is reference-driven. The Scout driver gathers evidence, interprets
whether current decisions are at risk, and classifies findings. The runner only
validates overlay shape and report/manifest shape.

## Context

Scout already has document and code structure references, script lifecycle, and
backend/Python code reachability. The next gap is documentation that is shaped
well enough to read but says the wrong thing about current state. Examples
include:

- stale "current" routing in entrypoints, current maps, runbooks, or indexes;
- historical plans that still look like active plans;
- completed work still described as pending;
- backlog state and current docs disagreeing in a way that changes next action;
- old runbooks that still read as executable current instructions.

The handoff branch
`handoff/document-lifecycle-drift-20260617` provided context only. It did not
write an implementation plan, run structured review, or change Scout files.

## Non-Goals

- Do not implement the subskill before this plan review gate is resolved.
- Do not make Scout a CI-style stale-document checker.
- Do not add runner commands that scan documents or infer drift automatically.
- Do not clean active feature docs merely because they are changing.
- Do not add or modify downstream Skyline V2 or Skyline Data overlays.
- Do not run downstream Scout dry-runs for Skyline V2 or Skyline Data in this
  PR.
- Do not write backlog candidates in this protocol PR.

## Accepted Design Defaults

- Use the subskill name `document-lifecycle-drift`.
- `document-structure` owns document shape, length, navigation, readability,
  source-of-truth duplication, and structural active/historical boundaries.
- `document-lifecycle-drift` owns whether docs express wrong current facts:
  stale status, stale current routing, historical docs that look current,
  completed work written as pending, backlog/docs state conflict, and stale
  runbooks that still look executable.
- Admit a backlog candidate only when a document can mislead current
  agent/operator decisions and there is a clear remediation path.
- Put weak signals, historical provenance, and normal active feature churn in
  report-only observations by default.
- Active feature docs are suppressed by default. Promote only stale wording that
  would cause a wrong current action.

## Boundary With Document Structure

Use `document-structure` when the problem is that a reader cannot efficiently
find, navigate, or maintain the right source of truth. Typical signals are
length, heading density, duplicated path references, overloaded current maps,
and unclear active/historical organization.

Use `document-lifecycle-drift` when the reader can find the document but the
document may cause a wrong current decision. Typical signals are status words
that no longer match source-of-truth state, "current" links that route to stale
instructions, historical plans without clear supersession, and runbooks whose
commands look current after their operational context changed.

If one document has both issues, classify the primary risk. Do not open
duplicate candidates for the same human decision. A structure report may note
possible factual drift as report-only and route it to this subskill; a lifecycle
drift report may note structural contributors without turning them into a
separate structure candidate.

## Candidate Threshold

Propose a backlog candidate only when all are true:

- the document or document cluster is entrypoint-routed, current-index-routed,
  operator-runbook-routed, active-doc-routed, or otherwise likely to be used in
  current work;
- evidence shows a lifecycle/currentness claim is false, contradictory, or
  ambiguous enough to affect current action;
- the likely reader is named, such as bootstrap agent, planning agent, closeout
  agent, reviewer, or human operator;
- the risk is a wrong decision, not just cosmetic stale language;
- a clear fix exists, such as add a supersession note, update current routing,
  retire an old runbook, align backlog/current docs, or move historical content;
- existing backlog items do not semantically cover the same decision.

Use report-only observation when:

- evidence is weak or the wrong action is not clear;
- the document is historical provenance and not routed as current;
- the stale wording is harmless after local context is read;
- active feature churn explains the mismatch;
- the next action would be speculative cleanup instead of a clear decision;
- the finding is useful context for a later Scout run but not candidate-worthy
  today.

Use ignored noise when the document is clearly archived/generated/private-run
output, has an explicit historical status, or contains stale wording only inside
quoted review threads or provenance that should not be rewritten.

## Active Feature Suppression

Apply Scout active feature suppression before proposing lifecycle drift
candidates. Positive active signals include a current plan, current-map entry,
active PR or worktree, explicit human statement, active backlog/progress entry,
recent acceptance or rollout notes, or multiple recent commits tied to the same
still-open feature.

For active feature docs, normal stale-looking status terms such as "pending",
"next", "in progress", or "awaiting review" are report-only by default. Promote
only when the wording is likely to cause an immediate wrong action, such as
following a retired runbook, editing the wrong source-of-truth doc, believing a
closed gate is still blocking, or ignoring an active safety/correctness/data
safety/production-risk/CI-blocking condition.

Suppression is deferral, not dismissal. Later Scout runs can re-evaluate the
same report-only observation after active signals fade.

## Overlay Schema

Add a new `subskills.document-lifecycle-drift` overlay mapping. No new global
overlay fields are needed.

Required fields:

- `entry_docs`: non-empty string list of agent/operator entrypoint docs.
- `current_docs`: non-empty string list of current maps, status docs, indexes,
  or runbooks whose current-state claims should be checked.
- `doc_roots`: non-empty string list of tracked document roots to inspect.

Optional fields:

- `archive_paths`: string list of historical, artifact, or provenance paths.
  When omitted, drivers should fall back to `repo_context.archive_paths`.
- `status_sources`: string list of backlog, roadmap, current-status, or plan
  files useful for checking current-state conflicts. The existing
  `repo_context.backlog_path` remains the default backlog source of truth.
- `runbook_roots`: string list of operator instruction roots when a repo keeps
  runbooks outside normal docs.
- `repo_notes`: string for repo-specific interpretation guidance.

No threshold fields are planned for v1. Lifecycle drift admission is not based
on line counts or term density; keyword and status-term searches are evidence
collection aids only.

Unknown fields should follow the runner's existing lenient subskill convention:
v1 validates known shape but does not fail future extension keys.

## Implementation Plan

1. Add `scout/references/document-lifecycle-drift.md`.
   - Define purpose, non-purpose, overlay fields, evidence loop, candidate
     unit, candidate admission, report-only/ignore rules, active feature
     suppression, and evidence standard.
   - Include examples of current-action risk without turning them into fixed
     mechanical rules.
   - State that backlog/docs state conflicts use the adopting repo's backlog
     source of truth; this repo's default is `docs/backlog.yml`.
2. Update `scout/SKILL.md`.
   - Add `document-lifecycle-drift` to the Subskills list.
   - Preserve the distinction from `document-structure`.
   - Preserve the runner boundary: no v1 automatic scans for document
     lifecycle drift.
3. Update `scout/scripts/scout_runner.py`.
   - Add the subskill reference mapping.
   - Validate the new overlay mapping and string-list fields listed above.
   - Ensure setup/check report skeletons include the subskill section when it
     is enabled.
   - Do not add scan commands, keyword scanners, drift inference, backlog
     semantic checks, or automatic candidate generation.
4. Update `scout/tests/test_scout_runner.py`.
   - Add an overlay fixture variant enabling `document-lifecycle-drift`.
   - Test valid schema acceptance.
   - Test required-field rejection for `entry_docs`, `current_docs`, and
     `doc_roots`.
   - Test optional field type validation for `archive_paths`,
     `status_sources`, `runbook_roots`, and `repo_notes`.
   - Test setup/check skeleton includes `### document-lifecycle-drift`.
   - Keep existing structure, reachability, vulture, dry-run, and
     write-enabled tests passing.
5. Update indexes.
   - Update `docs/CURRENT.md` Scout references to include the new reference.
   - Update root `README.md` only if the high-level Scout summary needs a
     wording adjustment; no routing change is expected.
   - Keep `docs/agent_plans/README.md` listing this plan as a current record.

## Validation

Run the focused Scout tests:

```bash
python -m pytest scout/tests/test_scout_runner.py
```

Run repository checks:

```bash
python -m pytest tests/test_skill_frontmatter.py
python -m pytest
git diff --check
python scripts/check_backlog.py
```

The runner tests validate overlay and report shape. The subskill behavior is
protocol prose, so validation also requires reading the edited
`document-lifecycle-drift` reference and Scout routing prose against this plan.

## Review Path

Before implementation, run the structured-review runner from this checkout:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree . \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/agent_plans/2026-06-17_document_lifecycle_drift_plan.md \
  --artifact docs/agent_plans/2026-06-17_document_lifecycle_drift_plan.md \
  --focus "Review the document-lifecycle-drift subskill boundary, candidate threshold, active feature suppression, overlay schema, runner boundary, scope exclusions, and validation plan." \
  --topic "Scout document lifecycle drift"
```

Use the default 900-second timeout for this small/medium plan review. Do not
start implementation until blocking reviewer feedback is resolved or explicitly
escalated to the human.

## Acceptance

- The new subskill reference makes lifecycle drift distinct from document
  structure.
- Candidate admission is strict enough to avoid noisy stale-word cleanup.
- Active feature docs are report-only by default unless stale wording would
  drive wrong current action.
- Runner changes are limited to reference lookup, overlay validation, and
  report shape validation.
- Tests cover valid and invalid overlay shape plus report skeleton inclusion.
- No downstream Skyline V2 or Skyline Data overlay or Scout output is changed
  in this PR.

## Review Threads

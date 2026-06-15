# Scout Structure Subskills Plan

Status: draft implementation plan
Owner: driver
Date: 2026-06-15

## Goal

Add two Scout subskills that find maintainability risks before lifecycle drift
or dead-code checks can be interpreted reliably:

- `document-structure` for agent/human readability of active document
  structures, indexes, and current-state maps.
- `code-structure` for active code modules or module clusters whose structure
  makes safe agent/human maintenance difficult.

The subskills are discovery protocols, not CI checks. Mechanical signals create
candidate pools only; the Scout driver must interpret evidence and classify
findings.

## Context

Existing Scout subskills cover script lifecycle and backend/Python code
reachability. Recent use in Skynet Data and Skynet V2 produced backlog
candidates for stale scripts, uncertain helper lifecycles, and dead or
test-only code surfaces. The next observed gap is different:

- long or overloaded current/index documents can make agents over-read
  historical context or misidentify the current source of truth;
- active code can be reachable and still too large or multi-role for safe
  targeted edits;
- frontend/TypeScript structure should be handled through the same
  `code-structure` subskill via a TypeScript/React adapter, rather than a
  separate subskill.

The first version should be reference-driven and agent-executed. Do not add
runner scan helpers yet; runner mechanics should validate overlay shape and
report skeletons only.

## Non-Goals

- Do not implement document lifecycle drift detection in this plan.
- Do not add a runner command that scans code or documents for structure
  metrics.
- Do not make line-count thresholds admission rules.
- Do not produce or modify Skynet Data or Skynet V2 Scout reports.
- Do not enable the new subskills in downstream repos in this change.
- Do not add frontend design critique, accessibility review, or visual quality
  judgment.

## Accepted Decisions

- Subskill names:
  - `document-structure`;
  - `code-structure`.
- `code-structure` is one subskill with language/framework adapters, not
  sub-subskills. V1 references define Python and TypeScript/React evidence
  obligations.
- Both v1 subskills are reference-driven. Agents run project-appropriate
  commands and record them in `SCOUT_REPORT.md`; the runner does not know or
  execute project toolchains.
- Candidate granularity:
  - documents: one document or one coherent document cluster;
  - code: one module or one coherent module cluster.
- Thresholds are overlay-configurable scan hints. Shared defaults are provided,
  but candidates require agent judgment.

## Implementation Plan

### 1. Add Document Structure Reference

Create `scout/references/document-structure.md`.

The reference must define:

- purpose and boundary;
- overlay fields:
  - required: `entry_docs`, `index_docs`, `doc_roots`;
  - optional: `archive_paths`, `thresholds`, `repo_notes`;
- default thresholds:
  - `index_review_lines: 400`;
  - `doc_review_lines: 800`;
  - `doc_large_lines: 1200`;
- required evidence loop:
  - read repo entry and docs placement rules;
  - identify entrypoint/current/index/active-plan/historical/artifact/backlog
    document classes;
  - collect tracked Markdown metrics for declared roots;
  - inspect current/index docs separately from largest dated plans;
  - compare duplicate path references across entry/current/index docs when
    useful;
  - search lifecycle terms and active/historical boundaries;
  - compare candidate-worthy findings against existing backlog items;
  - record commands and skipped evidence with reasons.
- candidate admission:
  - active or agent-routed doc/cluster;
  - mechanical signal exists;
  - concrete maintenance risk is proven;
  - clear restructuring next action exists;
  - no existing backlog item semantically covers the same decision.
- report-only and ignore rules for long but clearly historical docs, long but
  well-summarized active plans, and harmless duplicate references.

### 2. Add Code Structure Reference

Create `scout/references/code-structure.md`.

The reference must define:

- purpose and boundary;
- overlay fields:
  - required: `roots` with at least one non-empty adapter root list;
  - optional: `test_roots`, `active_contract_sources`, `thresholds`,
    `repo_notes`;
- default thresholds:
  - Python: `review_lines: 800`, `large_lines: 1000`,
    `script_review_lines: 600`;
  - TypeScript/React: `review_lines: 400`, `large_lines: 600`,
    `route_large_lines: 600`;
  - shared: `churn_since_days: 45`, `high_churn_commits: 6`;
- Python evidence obligations:
  - tracked files under declared roots;
  - line counts and top offenders;
  - AST or equivalent scan for functions/classes/methods/public symbols;
  - entrypoint hints such as FastAPI, Typer, argparse, and
    `if __name__ == "__main__"`;
  - dependency-category inspection for DB, HTTP/API, filesystem, metrics,
    provider/LLM, subprocess, and CLI boundaries;
  - tests/docs/backlog references;
  - recent git churn for top candidates.
- TypeScript/React evidence obligations:
  - tracked `.ts` / `.tsx` files under declared roots;
  - line counts and top route/component offenders;
  - component/function and hook counts where feasible;
  - route/page hints;
  - API/data shaping, feature flag, and interaction/state density hints;
  - frontend test/e2e/package-script references when present;
  - recent git churn for top candidates.
- candidate admission:
  - active code surface under declared roots;
  - mechanical signal exists;
  - concrete maintenance risk is proven;
  - clear restructuring next action exists;
  - no existing backlog item semantically covers the same decision.
- report-only and ignore rules for cohesive large modules, framework-heavy
  modules, generated files, migrations, schemas, typed data carriers, and
  test-only complexity without production-maintenance risk.

### 3. Update Scout Skill Routing

Update `scout/SKILL.md`:

- list `document-structure` and `code-structure` in the Subskills section;
- state that `code-structure` uses adapters inside one subskill section;
- clarify that the runner does not execute structure scans in v1;
- preserve the runner boundary that interpretation remains agent-owned.

### 4. Extend Overlay Validation

Update `scout/scripts/scout_runner.py`:

- add subskill reference mappings for:
  - `document-structure`;
  - `code-structure`.
- validate `document-structure` overlay:
  - `entry_docs`: non-empty string list;
  - `index_docs`: string list;
  - `doc_roots`: non-empty string list;
  - optional `archive_paths`: string list;
  - optional `thresholds`: mapping with positive integer values for known
    threshold fields;
  - optional `repo_notes`: string.
- validate `code-structure` overlay:
  - `roots`: mapping with at least one non-empty string-list adapter;
  - supported v1 adapters: `python`, `typescript_react`;
  - optional `test_roots`: mapping of string-list adapters;
  - optional `active_contract_sources`: string list;
  - optional `thresholds`: nested mapping with positive integer values for
    known adapter/shared threshold fields;
  - optional `repo_notes`: string.
- do not add scan commands.

### 5. Extend Tests

Update `scout/tests/test_scout_runner.py`:

- accepted overlay with all four subskills;
- `document-structure` rejects missing required fields and malformed
  thresholds;
- `code-structure` rejects missing roots, empty adapter root sets, unknown
  adapters, and malformed thresholds;
- setup/check skeleton includes the new subskill headings when enabled;
- existing vulture config tests still pass with `code-reachability`.

### 6. Update Indexes

Update:

- `README.md` only if the protocol summary needs to mention the expanded Scout
  scope;
- `docs/CURRENT.md` runner/reference map to include the two new references;
- `docs/agent_plans/README.md` with this plan record.

No root `AGENTS.md` change is expected unless routing changes.

## Validation

Run:

```bash
python -m pytest scout/tests/test_scout_runner.py
python -m pytest tests/test_skill_frontmatter.py
python -m pytest
```

Also run:

```bash
git diff --check
python scripts/check_backlog.py
```

## Review Path

Before implementation, run structured review on this plan:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree /Users/yibai/WorkSpace/agent-protocols-scout-structure \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/agent_plans/2026-06-15_scout_structure_subskills_plan.md \
  --artifact docs/agent_plans/2026-06-15_scout_structure_subskills_plan.md \
  --focus "Review subskill boundaries, overlay schema, runner scope, validation, and whether implementation requires guessing." \
  --topic "Scout structure subskills"
```

Implementation should wait until blocking review feedback is resolved or the
human explicitly accepts proceeding without that gate.

## Acceptance

- `document-structure` and `code-structure` references exist and define
  evidence loops, candidate admission, report-only, and ignore rules.
- `scout/SKILL.md` routes the new subskills without changing Scout's
  judgment-heavy boundary.
- Runner overlay validation accepts the new subskills and rejects malformed
  schemas.
- Runner setup/check skeletons include the new subskill sections when enabled.
- No runner scan helper is added.
- Tests and repo checks pass.

## Review Threads

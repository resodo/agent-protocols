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

`code-structure` intentionally uses in-subskill adapters while
`code-reachability` keeps frontend/TypeScript as a separate future extension:
structure findings share one admission rule across active code surfaces, while
reachability depends more heavily on language-specific static-analysis
false-positive classes.

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
- threshold defaults are scan hints, not admission rules, and the reference
  should say to revisit them when repo document norms change;
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
- threshold defaults are scan hints, not admission rules, and the reference
  should say to revisit them when repo code norms change;
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
  - `index_docs`: required string list, allowed to be empty;
  - `doc_roots`: non-empty string list;
  - optional `archive_paths`: string list;
  - optional `thresholds`: mapping whose known threshold fields, when present,
    have positive integer values. Unknown threshold keys are ignored in v1,
    matching the runner's existing lenient subskill-mapping convention;
  - optional `repo_notes`: string.
- validate `code-structure` overlay:
  - `roots`: mapping with at least one declared adapter, and every declared
    adapter root list must be non-empty. For example, declare
    `typescript_react` only when TypeScript/React roots should be scanned;
  - supported v1 adapters: `python`, `typescript_react`;
  - optional `test_roots`: mapping of string-list adapters using the same
    supported adapter keys as `roots`;
  - optional `active_contract_sources`: string list;
  - optional `thresholds`: nested mapping whose known adapter/shared threshold
    fields, when present, have positive integer values. Unknown threshold keys
    are ignored in v1, matching the runner's existing lenient
    subskill-mapping convention;
  - optional `repo_notes`: string.
- do not add scan commands.

### 5. Extend Tests

Update `scout/tests/test_scout_runner.py`:

- accepted overlay with all four subskills, using a separate overlay variant
  rather than changing the existing Slice 1 base fixture;
- `document-structure` rejects missing required fields and malformed
  thresholds;
- `code-structure` rejects missing roots, empty adapter root sets, unknown
  adapters, a mixed adapter map where any declared adapter has an empty root
  list, and malformed thresholds;
- setup/check skeleton includes the new subskill headings when enabled;
- existing vulture config tests still pass with `code-reachability`.

### 6. Update Indexes

Update:

- `README.md` only if the protocol summary needs to mention the expanded Scout
  scope;
- `docs/CURRENT.md` runner/reference map to include the two new references;
- `docs/agent_plans/README.md` is already updated by this draft plan. Do not
  add a duplicate record during implementation.

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

I've inspected the plan, the existing Scout runner, both existing subskill references, the test suite, the frontmatter test, and the docs the plan says it will touch. I have enough to review. Here is my reviewer pass.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

Restating the focus in one sentence: check whether the two new Scout subskills have clear boundaries, a precise overlay schema, a correctly-scoped runner change, executable validation, and whether an implementer could build this without guessing.

I read the plan against the actual code: `scout/scripts/scout_runner.py` (overlay validation flow, gated per-subskill blocks, generic report/check skeletons), `scout/references/script-lifecycle.md` and `scout/references/code-reachability-backend-python.md` (the two reference exemplars this plan mirrors), `scout/tests/test_scout_runner.py`, `tests/test_skill_frontmatter.py`, `scout/SKILL.md`, `docs/CURRENT.md`, and `docs/agent_plans/README.md`.

#### Blocking issues

**Thread B1 — code-structure `roots`: behavior on a partially-empty adapter map is underspecified (the one real guess).**

The plan gives three statements that do not pin down the same contract:
- Accepted Decisions: "required: `roots` with at least one non-empty adapter root list";
- Step 4 validation: "`roots`: mapping with at least one non-empty string-list adapter";
- Step 5 test: "`code-structure` rejects ... empty adapter root sets".

These leave the mixed case undecided. For `roots: {python: [], typescript_react: ["frontend/src"]}`, two implementations are both consistent with the wording:
- (a) every *declared* adapter must be non-empty, so this is rejected because `python` is empty;
- (b) the map only needs *at least one* non-empty adapter, so this is accepted.

The planned tests don't exercise the mixed case, so either implementation would pass them — which means the implementer silently fixes the public overlay contract by guessing, and a downstream overlay could be accepted or rejected depending on which they picked. This is exactly the "implementation requires guessing" risk the focus asks about, and it is a one-sentence fix in the plan. Please state explicitly which holds (I lean toward (a) "each declared adapter root list must be non-empty; declare only adapters you actually scan," mirroring how `production_roots`/`vulture.roots` are each required non-empty in code-reachability), and add the mixed-case overlay to the Step 5 reject/accept tests so the contract is encoded.

#### Non-blocking issues

**Thread N1 — threshold validation: define what "malformed" rejects, and use the existing leniency convention.**

Step 4 says thresholds carry "positive integer values for known threshold fields" (flat for `document-structure`: `index_review_lines`/`doc_review_lines`/`doc_large_lines`; nested for `code-structure` under `python`/`typescript_react`/`shared`). "Positive integer" makes a negative/non-int value clearly malformed, so the Step 5 "malformed thresholds" test is writable. What is left open is unknown-key handling: does an unknown threshold field or unknown threshold category (e.g. a typo `dox_review_lines`, or a `thresholds.rust` block) get rejected or ignored? The established runner convention is to validate known fields and not reject unknown keys inside subskill mappings (it does this for `script-lifecycle`/`code-reachability` today). Recommend the plan state "validate values of known threshold fields; unknown keys are ignored" (or, if you want typo protection, say so explicitly) and confirm the nested category keys are spelled `python`/`typescript_react`/`shared` to match the `roots` adapter keys. Not blocking — a competent implementer can follow precedent — but worth pinning so validator and test author agree.

**Thread N2 — `index_docs` "required" vs "allowed empty" wording.**

Step 1 lists `index_docs` under "required," while Step 4 validates it as a plain "string list" (not non-empty). That's the same shape as code-reachability's `test_roots` (required key, may be empty), which is fine — but the word "required" without "may be empty" reads as non-empty. Recommend matching the reference-doc convention used in `code-reachability-backend-python.md` ("Required ... list, allowed to be empty") so the implementer doesn't add an unintended `non_empty=True`.

**Thread N3 — Step 5 "accepted overlay with all four subskills" must not break the existing exact-list assertion.**

`test_validate_overlay_accepts_slice1_schema` asserts `enabled_subskills == ["script-lifecycle", "code-reachability"]` and is built from the shared `overlay()` helper. If the implementer enables all four subskills by editing that base helper, this test regresses. Recommend the plan say to add a separate overlay variant (or a dedicated fixture) for the four-subskill case rather than mutating the base `overlay()`, so the Slice-1 assertion and the new acceptance test coexist. Low risk (the breakage is obvious on first run) but cheap to call out.

**Thread N4 — code-structure `test_roots` adapter-key validation is unspecified.**

Step 4 calls `test_roots` "mapping of string-list adapters" but doesn't say whether its adapter keys are restricted to the supported `python`/`typescript_react` set the way `roots` is. Recommend stating it mirrors `roots`' adapter-key rule (or is intentionally unrestricted). Minor.

**Thread N5 — Step 6: the `docs/agent_plans/README.md` record already exists.**

`docs/agent_plans/README.md:36` already lists `2026-06-15_scout_structure_subskills_plan.md`. Step 6's "Update `docs/agent_plans/README.md` with this plan record" is therefore effectively already satisfied — the implementer should not add a duplicate. Also, root `README.md:16` has only a one-line Scout summary with no subskill enumeration, and `AGENTS.md` has no subskill/scout routing text, so the "only if needed" README change and "no AGENTS.md change" notes are correct as written. Just flagging so the closeout's docs-consistency check doesn't re-add an existing line.

**Thread N6 — threshold defaults are a maintenance surface; label them as hints in the references.**

The plan rightly makes line-count thresholds overlay-configurable scan hints, not admission rules (Non-Goals + Accepted Decisions). To satisfy the mechanism-lifecycle lens, recommend the two new references include a short note (as `code-reachability-backend-python.md` does for its false-positive defaults) that the default thresholds are interpretation hints to revisit when repo norms change, and that candidates always require agent judgment. This keeps the defaults from being read as silent thresholds later. Non-blocking.

**Thread N7 — record the rationale for the frontend-as-adapter divergence.**

`code-reachability` treats frontend/TypeScript as a *separate future subskill/extension*, while `code-structure` folds it into the *same subskill via a TypeScript/React adapter*. The Context section states this deliberately, so it is not a defect — but the two code subskills now diverge architecturally. A one-line rationale in `code-structure.md` (why structure uses an in-subskill adapter where reachability split frontend out) will prevent a future reader from treating it as an inconsistency. Non-blocking.

#### Overall judgment

The plan is close to ready and mostly does not require guessing. Strengths I confirmed against the code:
- Runner scope is correctly minimal. The report/check skeletons in `scout_runner.py` iterate `enabled_subskills` generically and apply the standard subskill subheadings, so the acceptance item "skeletons include the new subskill sections when enabled" is satisfied by existing code once overlay validation accepts the subskills — no skeleton code is needed, and the plan correctly does not ask for any. "Do not add scan commands" is consistent with the existing runner boundary.
- The change is additive and backward compatible: per-subskill validation is gated on `if "<subskill>" in enabled`, and `CORE_FIELDS`/existing overlays are untouched, so current overlays keep validating.
- Subskill boundaries are clear: document-structure (active index/current doc readability) vs code-structure (active over-large/multi-role code) vs code-reachability (dead/test-only code), with the candidate-admission "no existing backlog item semantically covers the same decision" rule handling cross-subskill overlap.
- Thresholds-as-hints (not admission rules) is a good answer to the mechanism-lifecycle lens.
- Reference authoring is well-anchored by two existing exemplars, so the prose content (evidence loop, admission, report-only/ignore) is low-guess.
- Validation commands are concrete and executable (`pytest` targets, `git diff --check`, `scripts/check_backlog.py` — all present), and the plan correctly avoids any merge-readiness claim, leaving that to closeout.

One blocking clarification (B1) and seven non-blocking tightenings. B1 is a genuine contract ambiguity in the `code-structure.roots` partial-empty case that should be resolved and test-encoded before implementation; the rest can be folded in by the driver or accepted with reason.

#### Residual risks / validation gaps

- The strongest residual risk is contract drift in the `code-structure` overlay (B1 + N1): if the validator's strictness isn't pinned, downstream overlays may be accepted/rejected inconsistently with intent, and the reject-case tests may encode the wrong contract. Resolving B1 and N1 closes this.
- No example `scout.yml` overlay is committed in this repo (overlays live downstream), so the only executable proof of the new schema is the inline test overlays in `test_scout_runner.py`. That is acceptable for a protocol repo, but it means the test fixtures are the de facto schema spec — another reason to make the accept/reject cases (especially the mixed-empty-adapter case) explicit.
- The reference prose (evidence loops, admission rules) is not mechanically validated; correctness there rests on reviewer reading at implementation-review time, not on tests. That is inherent to reference-driven subskills and matches the existing two references, so it is an accepted, not a new, risk.

No other blocking issues. Once B1 is resolved (and ideally N1/N3 folded in), this plan is ready for implementation.

### Driver response 1

Classification:

- B1: accepted. The plan now states that every declared `code-structure.roots`
  adapter must have a non-empty root list, and the tests must cover the mixed
  empty-adapter case.
- N1: accepted. The plan now states that known threshold fields require
  positive integer values and unknown threshold keys are ignored in v1,
  following the existing lenient subskill-mapping convention.
- N2: accepted. `document-structure.index_docs` is now explicitly a required
  list that may be empty.
- N3: accepted. The test plan now requires a separate all-four-subskills
  overlay variant instead of mutating the existing Slice 1 fixture.
- N4: accepted. `code-structure.test_roots` now mirrors the supported adapter
  key rule from `roots`.
- N5: accepted. Step 6 now says the plan record is already present and must not
  be duplicated during implementation.
- N6: accepted. Both reference sections now require a note that thresholds are
  scan hints to revisit as repo norms change, not admission rules.
- N7: accepted. The Context section now records why `code-structure` uses
  adapters while `code-reachability` keeps frontend reachability as a separate
  future extension.

Remaining risk: reference prose remains review-owned rather than mechanically
validated, which matches existing Scout references and is acceptable for this
plan.

# Scout Structure Subskills Plan

Status: implemented and reviewed
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
  - required: `roots` with at least one declared adapter, where every declared
    adapter root list is non-empty;
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

Verified against the runner code. Both grounding claims the revision relies on hold:

- **Lenient convention (N1):** `validate_overlay` (scout_runner.py:151-192) validates only known fields with `if "<key>" in mapping:` guards and never rejects unknown keys inside subskill mappings — so "unknown threshold keys are ignored in v1" is faithful to existing behavior.
- **Non-empty pattern (B1/N2):** `production_roots` and `vulture.roots` are each `non_empty=True` (lines 169, 182), while `test_roots` is required but may be empty (line 170). The plan's chosen contract — every declared `roots` adapter non-empty, `index_docs` required-but-empty-allowed — mirrors these exactly.

Here is my re-review.

---

### Reviewer pass 2 (impl-plan, claude reviewer)

Restating the focus in one sentence: confirm whether B1 (the `code-structure.roots` partial-empty contract ambiguity) is resolved by the driver's revision, and whether any remaining issue blocks implementation.

I read the diff `ce943cb..e8a8a04` for this plan, the revised plan body, the driver response classification, and re-checked the two grounding claims (lenient unknown-key handling; the non-empty-root precedent) against `scout/scripts/scout_runner.py:120-194`.

#### Blocking issues

None. B1 is resolved (see resolution below), and no new blocking issue was introduced by the revision.

#### Thread B1 — Resolved.

The contract is now pinned to option (a) and test-encoded, as recommended:
- Step 4 (validation) now reads "`roots`: mapping with at least one declared adapter, and every declared adapter root list must be non-empty," with the guidance "declare `typescript_react` only when TypeScript/React roots should be scanned." This is unambiguous and matches the `production_roots`/`vulture.roots` `non_empty=True` precedent.
- Step 5 (tests) now requires rejecting "a mixed adapter map where any declared adapter has an empty root list," so `{python: [], typescript_react: ["frontend/src"]}` is encoded as a reject case.

With the validator spec and the reject test both fixed to option (a), the implementer no longer has to guess the public overlay contract, and the de-facto schema (the test fixtures) now encodes intent. Resolved.

#### Non-blocking issues

**Thread N8 — Step 2 reference-content wording still describes the looser rule (residual of B1).**

B1 noted three locations that disagreed; the driver tightened two of them (Step 4 validation, Step 5 tests) to option (a) but left the third — Step 2's reference-doc content description (line 121) — as "required: `roots` with at least one non-empty adapter root list." Read literally, that phrasing is the weaker option (b): "at least one adapter is non-empty." Since overlay authors read the *reference*, not the validator code, a `code-structure.md` that copies this phrasing verbatim would teach a looser contract than the validator enforces, and a downstream author could write a partial-empty map expecting acceptance.

This does not reintroduce an implementation guess — Step 4 and Step 5 are authoritative and unambiguous, so the validator will be built correctly. It is a doc/validator consistency item: when writing `scout/references/code-structure.md` in Step 1/2, the `roots` field description should match Step 4 ("declare only the adapters you scan; every declared adapter root list must be non-empty"). Worth aligning at authoring time and confirming at implementation review; not a plan blocker.

**Threads N1–N7 — driver responses confirmed.**

All seven accepted revisions are present in the body and consistent with the runner:
- N1: thresholds now "known fields, when present, positive integer; unknown keys ignored" — matches the lenient `if key in mapping` convention. Malformed-threshold test remains writable (negative/non-int rejected).
- N2: `index_docs` now "required string list, allowed to be empty" — mirrors `test_roots`.
- N3: separate all-four-subskills overlay variant — protects the `test_validate_overlay_accepts_slice1_schema` exact-list assertion.
- N4: `test_roots` adapter keys mirror `roots`' supported set.
- N5: Step 6 now says the `docs/agent_plans/README.md` record exists and must not be duplicated.
- N6: both reference sections require a "thresholds are scan hints, revisit as norms change" note.
- N7: Context records the frontend-as-adapter vs reachability-as-separate-extension rationale.

#### Overall judgment

The plan is ready for implementation. B1, the one blocking ambiguity, is resolved with a pinned contract and an encoded reject test; the seven non-blocking tightenings were all folded in and check out against the runner. The single remaining item (N8) is a reference-prose consistency nit carried over from B1, explicitly non-blocking, to be closed when `code-structure.md` is authored and at implementation review. Per the readiness standard: goal, non-goals, assumptions, and acceptance are clear; validation commands are concrete and executable; and the previously blocking thread is resolved.

This is a plan-review conclusion (`ready for implementation`), not a merge-readiness handoff — final rechecks belong to closeout.

#### Residual risks / validation gaps

- N8 wording carryover: if the reference's `roots` description is copied from Step 2 verbatim, the published doc would describe a looser rule than the validator enforces. Low impact, closed by aligning the reference text; flag for the implementation-review docs-consistency pass.
- Reference prose (evidence loops, admission, report-only/ignore) remains review-owned rather than mechanically validated. The driver acknowledged this; it matches the existing two references and is an accepted, not new, risk.
- Test fixtures are the de-facto schema spec (no committed example `scout.yml` in this repo). Acceptable for a protocol repo; the now-explicit mixed-empty-adapter reject case mitigates the main drift risk.

No blocking issues remain. The plan is ready for implementation.

### Driver response 2

Classification:

- B1: resolved by reviewer confirmation.
- N8: accepted. The Step 2 `roots` reference-content wording now matches the
  validator/test contract: at least one adapter must be declared, and every
  declared adapter root list must be non-empty.

Remaining risk: implementation review should still confirm
`scout/references/code-structure.md` copies the stricter `roots` wording rather
than the earlier weaker phrasing.

I have everything I need. The implementation is complete and faithful to the accepted plan, all validation passes. Here is my implementation review thread to be appended.

---

### Reviewer pass 3 (impl, claude reviewer)

Restating the focus in one sentence: compare the committed implementation (`4910e8e scout: add structure subskill protocols`) against the accepted Scout structure subskills plan — references, runner overlay validation, tests, indexes, and validation evidence — and surface any blocker before closeout.

I reviewed the implementation diff (`4910e8e`) file by file against the plan body and the resolved review threads (B1, N1–N8), then ran the plan's full validation suite. The commit touches exactly the six files the plan named — `scout/references/document-structure.md`, `scout/references/code-structure.md`, `scout/SKILL.md`, `scout/scripts/scout_runner.py`, `scout/tests/test_scout_runner.py`, `docs/CURRENT.md` — and nothing else; `README.md` and `AGENTS.md` are untouched, matching Step 6's "only if needed" / "no AGENTS.md change" notes.

#### Blocking issues

None. The implementation matches the accepted plan, all five validation commands pass, and every resolved review thread is reflected in the committed code.

#### Plan-to-implementation traceability

| Plan item | Status | Evidence |
| --- | --- | --- |
| Step 1 — `document-structure.md` (purpose/boundary, overlay fields, default thresholds, hints note, evidence loop, admission, report-only/ignore) | Done | `scout/references/document-structure.md` — required `entry_docs`/`index_docs`/`doc_roots` (L19-24), optional fields (L26-30), thresholds 400/800/1200 (L32-36), hints note (L38-40), 8-step evidence loop (L42-58), admission (L84-95), report-only/ignore (L110-122) |
| Step 2 — `code-structure.md` (purpose/boundary, overlay fields, thresholds, Python + TS/React evidence, admission, report-only/ignore) | Done | `scout/references/code-structure.md` — purpose/boundary (L6-20), required `roots` + adapters (L24-33), optional fields (L34-41), thresholds (L43-55), hints note (L57-59), Python evidence (L81-94), TS/React evidence (L96-111), admission (L129-138), report-only/ignore (L155-167) |
| Step 3 — SKILL.md routing | Done | `scout/SKILL.md` — both subskills listed in Subskills section (L132-133), adapters-in-one-section note (L139-142), runner-does-not-scan-in-v1 note (L154-156) |
| Step 4 — overlay validation (option (a) `roots`, lenient thresholds, `test_roots` adapter keys) | Done | `scout_runner.py` — reference map (L24-27 of diff), `require_adapter_roots` rejects empty map/unknown adapter/empty declared root via `non_empty=True` (L122-131), `validate_adapter_string_lists` for `test_roots` (L134-139), `validate_code_structure_thresholds` nested by category (L142-146), `validate_known_thresholds` checks only known fields (L115-119); `document-structure`/`code-structure` blocks gated on `if "<subskill>" in enabled` (L243-279 of diff). No scan commands added. |
| Step 5 — tests (all-four variant, doc-structure rejects, code-structure rejects incl. mixed empty-adapter, skeleton headings) | Done | `test_scout_runner.py` — separate `overlay_with_structure_subskills` helper (not mutating base `overlay()`); 11 new tests incl. `test_code_structure_rejects_declared_empty_adapter_roots` (the B1 mixed case), unknown-adapter for `roots` and `test_roots`, malformed thresholds, empty-index allowed, and `### document-structure`/`### code-structure` skeleton assertions |
| Step 6 — indexes (CURRENT.md, no README/agent_plans duplication) | Done | `docs/CURRENT.md` reference map lists all four references; `docs/agent_plans/README.md` record count = 1 (no duplicate); root `README.md`/`AGENTS.md` unchanged |

Validation evidence (reviewer-rerun, this worktree):
- `python -m pytest scout/tests/test_scout_runner.py tests/test_skill_frontmatter.py` → 29 passed.
- `python -m pytest` → 105 passed.
- `git diff --check` → clean.
- `python scripts/check_backlog.py` → exit 0.
- `git status` → working tree clean.

Resolved-thread carry-through confirmed:
- **B1 / N8 (the one plan blocker and its prose residual):** the validator pins option (a) — `require_adapter_roots` requires a non-empty map, rejects unknown adapters, and applies `non_empty=True` per declared adapter — and `code-structure.md:26-27` now states "at least one declared adapter. Every declared adapter root list must be non-empty. Declare only adapters you actually scan," matching the validator rather than the earlier looser wording. The mixed case `{python: [], typescript_react: [...]}` is encoded as a reject test. Closed.
- **N1 (lenient thresholds):** `validate_known_thresholds` only validates listed fields; the accept fixture deliberately carries unknown keys (`future_threshold` inside `python`, an entire `future_adapter` category, `future_threshold` in document thresholds) and still validates, proving unknown-key leniency with positive evidence. The malformed-threshold tests prove known fields are checked (rejects `0` and `"many"`).
- **N2/N3/N4/N5/N6/N7:** `index_docs` required-but-may-be-empty (test present); separate all-four overlay variant protects the Slice-1 exact-list assertion; `test_roots` adapter keys restricted to the supported set (test present); no duplicate `agent_plans/README.md` record; both references carry the thresholds-are-hints note; `code-structure.md:16-20` records the frontend-as-adapter vs reachability-as-separate-extension rationale.

#### Non-blocking issues

**Thread N9 — `require_adapter_roots` return value is unused (trivial).**

`require_adapter_roots` builds and returns `parsed: dict[str, list[str]]` (scout_runner.py:126-131), but the only caller (`subskills.code-structure.roots`) discards the return value — validation is purely a side effect. This is harmless and mirrors `require_string_list`, which is likewise sometimes called for its raised-error side effect only; no behavior depends on it. Not worth a change on its own. If a future revision touches this function, the return type and `parsed` accumulation could be dropped to `-> None` for symmetry with the other `validate_*` helpers. No action required for closeout.

#### Overall judgment

The implementation is ready for closeout. It tracks the accepted plan item-for-item with concrete evidence, the runner change is correctly minimal and additive (per-subskill validation gated on `enabled`, `CORE_FIELDS` and existing overlays untouched, no scan helpers), the report/check skeletons surface the new subskill sections via the existing generic iteration (proven by `test_setup_and_check_report_artifacts_with_structure_subskills`), and the one prior blocker (B1) plus its prose residual (N8) are both closed in the committed code. All five plan validation commands pass on a clean worktree. The only open item (N9) is a cosmetic unused-return nit with no behavioral impact.

This is an implementation-review conclusion (`ready for closeout`), not a merge-readiness handoff — branch/PR, required CI checks, and final rechecks belong to closeout.

#### Residual risks / validation gaps

- Reference prose (evidence loops, admission, report-only/ignore) remains review-owned rather than mechanically validated. This was acknowledged at plan time, matches the two existing references, and I read both new references in full this pass; it is an accepted, not new, risk.
- Test fixtures remain the de-facto schema spec (no committed example `scout.yml` in this protocol repo, since overlays live downstream). Acceptable for a protocol repo, and the now-explicit mixed-empty-adapter reject case plus the unknown-key accept fixture mitigate the main drift risks.
- The subskills are intentionally not enabled in any downstream repo by this change (a stated non-goal), so there is no live-overlay or live-Scout-run evidence — only validation-level proof. That is the correct scope for this plan; first real-repo enablement is the place to confirm the evidence loops produce usable candidates.

No blocking issues. The implementation faithfully realizes the accepted plan and is ready for closeout.

---

人话总结：实现和已通过评审的计划完全对得上。两个新参考文档（document-structure、code-structure）、SKILL 路由、runner 的 overlay 校验、测试、索引（CURRENT.md）这六个文件都改对了，没有多动 README 或 AGENTS.md，计划记录也没重复添加。之前计划评审里唯一的阻塞点 B1（roots 里部分适配器为空时怎么处理）已经按"每个声明的适配器都必须非空"落实到校验代码，并有对应的拒绝测试;N1-N8 全部体现在代码里。我重新跑了计划要求的全部校验：单测 105 全过、`git diff --check` 干净、backlog 检查通过、工作区干净。没有阻塞问题，只有一个无关痛痒的小提示（一个校验函数的返回值没被用到，纯属多余，不影响行为）。结论：可以进入 closeout。注意这只是实现评审结论，分支/PR、CI、最终复查仍归 closeout 处理。

### Driver response 3

Classification:

- Implementation review: accepted. No blocking issues remain.
- N9: accepted as no-action. `require_adapter_roots` returning the parsed map is
  harmless and mirrors existing validation-helper style where callers may use a
  helper for raised-error side effects. It does not affect behavior or
  acceptance.

Validation provenance remains reviewer-rerun plus driver-reported local checks:
`python -m pytest scout/tests/test_scout_runner.py`, `python -m pytest
tests/test_skill_frontmatter.py`, `python -m pytest`, `git diff --check`, and
`python scripts/check_backlog.py` all passed in this worktree.

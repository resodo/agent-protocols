# Scout Document Lifecycle Drift Plan

Status: implemented
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

`current_docs` is deliberately distinct from
`document-structure.index_docs`: this subskill needs documents whose
current-state claims are in scope, not only navigational indexes. It is
required because at least one current-fact-bearing document is needed for a
lifecycle drift run. When a repo has no separate current map, list the relevant
entrypoint, status, or runbook document here rather than leaving it implicit.

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
2. Update `scout/references/document-structure.md`.
   - Replace the "future document-lifecycle drift subskill" wording with a
     cross-reference to the now-real `document-lifecycle-drift` subskill.
   - Keep `document-structure` focused on shape, navigation, and readability.
3. Update `scout/SKILL.md`.
   - Add `document-lifecycle-drift` to the Subskills list.
   - Preserve the distinction from `document-structure`.
   - Preserve the runner boundary: no v1 automatic scans for document
     lifecycle drift.
4. Update `scout/scripts/scout_runner.py`.
   - Add the subskill reference mapping.
   - Validate the new overlay mapping and string-list fields listed above.
   - Do not add subskill-specific report-skeleton logic. Verify the existing
     generic skeleton loop includes the subskill section after registration.
   - Do not add scan commands, keyword scanners, drift inference, backlog
     semantic checks, or automatic candidate generation.
5. Update `scout/tests/test_scout_runner.py`.
   - Add an overlay fixture variant enabling `document-lifecycle-drift`.
   - Test valid schema acceptance.
   - Test required-field rejection for `entry_docs`, `current_docs`, and
     `doc_roots`.
   - Test optional field type validation for `archive_paths`,
     `status_sources`, `runbook_roots`, and `repo_notes`.
   - Test that unknown extension keys on the new subskill mapping are accepted
     under the runner's lenient v1 convention.
   - Test setup/check skeleton includes `### document-lifecycle-drift`.
   - Keep existing structure, reachability, vulture, dry-run, and
     write-enabled tests passing.
6. Update indexes.
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

## Implementation Result

Implemented in this branch. The change adds the
`document-lifecycle-drift` Scout reference, wires it into Scout routing and
runner overlay validation, updates the document-structure cross-reference and
current protocol map, and extends Scout runner tests for valid schema,
invalid schema, lenient extension keys, and report skeleton inclusion.

Validation run after implementation:

```bash
uv run --with PyYAML --with pytest python -m pytest scout/tests/test_scout_runner.py
uv run --with PyYAML --with pytest python -m pytest tests/test_skill_frontmatter.py
uv run --with PyYAML --with pytest python -m pytest
git diff --check
uv run --with PyYAML python scripts/check_backlog.py
```

## Review Threads

I've verified the plan against the actual Scout runner, references, tests, and index files. I have enough to produce the review. Here is my complete review thread output.

---

### Reviewer pass 1 (impl-plan, claude reviewer)

**Human's concern (restated):** Confirm the `document-lifecycle-drift` plan is ready for implementation — specifically the subskill boundary, candidate threshold, active feature suppression, overlay schema, runner boundary, scope exclusions, and validation plan — so the implementer does not have to guess.

I inspected the artifacts the plan depends on before judging:
- `scout/SKILL.md` (subskill list, active feature suppression, runner boundary);
- `scout/references/document-structure.md` (sibling subskill and its forward reference to a "future" lifecycle subskill);
- `scout/scripts/scout_runner.py` (`SUBSKILL_REFERENCES`, `validate_overlay`, `report_skeleton`, `cmd_check`);
- `scout/tests/test_scout_runner.py` (overlay fixtures and rejection-test patterns);
- `docs/CURRENT.md`, `docs/agent_plans/README.md`, and confirmed `tests/test_skill_frontmatter.py` + `scripts/check_backlog.py` exist.

#### Blocking issues

None. The plan is implementable as written without guessing. The subskill name, reference path, required/optional overlay fields, runner-boundary exclusions, and validation commands are all concrete and match the current runner contract. The required-field rejection tests, lenient-extension convention, and report-skeleton inclusion are all consistent with how `document-structure` and `code-structure` are already wired (`scout/scripts/scout_runner.py:246-260`, the generic skeleton loop at `scout/scripts/scout_runner.py:341-344`, and the `### {subskill}` check at `scout/scripts/scout_runner.py:500-506`).

#### Non-blocking issues

**Thread 1 — `current_docs` field name diverges from the sibling `index_docs`, and is required-non-empty where `index_docs` is allowed-empty.**
The overlay schema (plan lines 134-138) names the second required field `current_docs` and requires it non-empty. The sibling `document-structure` subskill calls the analogous field `index_docs` and explicitly allows it to be empty (`scout/references/document-structure.md:22`, runner `scout/scripts/scout_runner.py:249`, test `test_document_structure_allows_empty_index_docs`). A repo enabling both subskills will declare two overlapping-but-differently-named lists (`index_docs` and `current_docs`), and `document-lifecycle-drift` will additionally *force* at least one entry where `document-structure` does not. This is explicitly specified, so it is not a guess-forcing ambiguity — but it is a deliberate divergence the driver should confirm consciously:
- Is the rename to `current_docs` intentional (semantic: "docs whose current-state claims are checked"), or should it reuse `index_docs` for overlay consistency?
- Should `current_docs` really be required-non-empty? A repo with `entry_docs` + `doc_roots` but no distinct current-map/runbook would be forced to point `current_docs` at an entry doc. An allowed-empty field with documented fallback to `entry_docs` would mirror `index_docs` and lower the adoption constraint. Requiring it is defensible (current-state claims are the core evidence here), but please make the choice on purpose, not by inheritance.
Recommend: add one sentence to the reference (plan step 1) recording why `current_docs` is a distinct, required field versus `document-structure.index_docs`.

**Thread 2 — Test plan omits a lenient unknown-extension-field assertion that the plan itself promises.**
Plan lines 155-156 state v1 "validates known shape but does not fail future extension keys," matching the runner's lenient pattern (it only checks named keys; unknown subskill keys are silently accepted — `scout/scripts/scout_runner.py:246-260`). The existing fixture proves this for `document-structure` via `"future_threshold": "ignored"` (`test_scout_runner.py:108`). The test list (plan step 4) does not include an equivalent lenient-extension assertion for `document-lifecycle-drift`. To lock in the documented convention and prevent a future regression to strict rejection, add an assertion that an unknown extension key on the new subskill mapping is accepted.

**Thread 3 — `document-structure.md` forward reference becomes stale on landing and is not in the edit list.**
`scout/references/document-structure.md:13-15` currently says stale current/historical state "belongs to a future document-lifecycle drift subskill." Once this subskill ships, that "future" wording is itself out-of-date routing — ironically the exact lifecycle drift this subskill exists to catch. Implementation steps 2 and 5 update `scout/SKILL.md`, `docs/CURRENT.md`, and (conditionally) `README.md`, but do not update `scout/references/document-structure.md`. Recommend adding it to the edit list so the cross-reference names the now-real subskill instead of "a future" one.

**Thread 4 — Step 3 bullet "Ensure setup/check report skeletons include the subskill section" risks redundant special-casing.**
The runner builds the `### {subskill}` section and its six subsections generically for every enabled subskill (`scout/scripts/scout_runner.py:341-344`; checked at `:500-506`). No per-subskill skeleton code is needed — registering the subskill in `SUBSKILL_REFERENCES` plus adding the overlay validation block is sufficient, and the skeleton inclusion then falls out for free (and is what the step-4 skeleton test will confirm). Recommend rewording step 3 so the implementer treats skeleton inclusion as an automatic consequence to *verify*, not new code to *add*, to avoid a needless special case.

#### Overall judgment

Ready for implementation. The boundary with `document-structure` is clean and was already anticipated by the sibling reference; the candidate threshold and report-only/ignore tiers are concrete and appropriately strict; the active feature suppression section correctly defers to and specializes the existing Scout suppression rule (`scout/SKILL.md:90-114`), including the same safety/correctness/data-safety/production-risk/CI-blocking bypass; the overlay schema matches the runner's lenient validation model and introduces no global fields; and the runner boundary firmly excludes scans, drift inference, and semantic backlog checks, consistent with `scout/SKILL.md:170-191`. Scope exclusions (no Skyline V2 / Skyline Data overlay or dry-run, no backlog writes in this PR) are explicit. The four non-blocking threads are refinements, not gates.

#### Residual risks and validation gaps

- **Prose acceptance is human-judged, not command-falsifiable.** Acceptance items like "makes lifecycle drift distinct" and "strict enough to avoid noisy stale-word cleanup" (plan lines 238-243) cannot be proven by a test; only the overlay/skeleton/test mechanics are mechanically falsifiable. The plan is honest about this (lines 213-215), and it is inherent to a reference-driven subskill — but the reviewer of the *implementation* will need to read the new reference against this plan's boundary and threshold sections, not rely on `pytest` alone. Flagging so the impl-review gate budgets for a prose read.
- **No in-repo overlay to dogfood.** `.agent-protocols/scout.yml` does not exist in this protocol repo, so the new overlay shape is exercised only through synthetic tempdir fixtures. This matches how the existing subskills are tested and is acceptable; noting it so no one assumes a live overlay validates the schema.
- **`status_sources` / `runbook_roots` are new manually-maintained path lists** (Mechanism Lifecycle lens). The plan handles their lifecycle reasonably by making them optional and adopting-repo-owned with documented fallbacks (`status_sources` → `repo_context.backlog_path`; `archive_paths` → `repo_context.archive_paths`, plan lines 142-148). Ensure the step-1 reference states these are adopting-repo-maintained so they do not silently rot in adopter overlays.

No blocking issues. Resolving Threads 1-4 would tighten consistency and lock in the plan's own stated conventions, but implementation may proceed; the driver owns accept/reject/defer on each thread per the structured-review protocol.

---

I did not write to any file or commit; per the runner contract the driver/runner appends this review under the thread file's `## Review Threads` section and creates the `structured-review:` commit. The above is my complete returned review.

### Driver response 1

Reviewer pass 1 had no blocking issues, so the plan gate is passed. I accepted
all four non-blocking refinements before implementation:

- Thread 1 accepted. The Overlay Schema section now explains why
  `current_docs` is distinct from `document-structure.index_docs`, why it is
  required, and how adopters should handle repos without a separate current
  map.
- Thread 2 accepted. The test plan now requires an assertion that unknown
  extension keys on the new subskill mapping are accepted.
- Thread 3 accepted. The implementation plan now includes
  `scout/references/document-structure.md` so its "future subskill" wording is
  updated when this subskill lands.
- Thread 4 accepted. The runner step now says to rely on and verify the
  existing generic skeleton loop, not add subskill-specific skeleton logic.

No re-review is required for these narrow accepted refinements because the
reviewer reported no blockers and judged the plan ready for implementation.
Per the human's current instruction, implementation still stops until the next
explicit implementation step.

I have everything I need. All artifacts inspected, all four accepted plan-review threads traced into the implementation, and validation independently re-run (31 Scout tests, 114 full-suite, `git diff --check` clean, backlog checker exit 0). Here is my complete review thread output.

---

### Reviewer pass 1 (impl, claude reviewer)

**Human's concern (restated):** Confirm the completed `document-lifecycle-drift` Scout subskill matches the accepted plan and its plan-review threads — subskill boundary, candidate threshold, active feature suppression, overlay schema validation, runner boundary, tests, docs/status consistency, and validation evidence — and decide whether it is ready for closeout or has blockers.

I inspected the implementation against the accepted plan (`docs/agent_plans/2026-06-17_document_lifecycle_drift_plan.md`) and the plan-review threads (Reviewer pass 1 + Driver response 1 in that file), then independently re-ran validation.

#### Plan-to-implementation traceability

| Plan item (Implementation Plan / Acceptance) | Status | Evidence |
| --- | --- | --- |
| 1. Add `scout/references/document-lifecycle-drift.md` (purpose, non-purpose, overlay fields, evidence loop, candidate unit, admission, report-only/ignore, active suppression, evidence standard) | Done | `scout/references/document-lifecycle-drift.md:1-170`; backlog source-of-truth stated `:107-108` |
| 2. Update `document-structure.md` to drop "future" wording, cross-reference real subskill, keep shape focus | Done | `scout/references/document-structure.md:12-14` ("belongs to the `document-lifecycle-drift` subskill"); no "future" wording remains |
| 3. Update `scout/SKILL.md` (subskill list, distinction, runner boundary no-scan) | Done | `scout/SKILL.md:159-160` (subskill list), `:182-183` (drift added to v1 no-scan list) |
| 4. Update `scout_runner.py` (reference map + overlay validation; no skeleton special-casing; no scans) | Done | `SUBSKILL_REFERENCES` `:26`; validation block `:263-275`; generic skeleton loop unchanged `:356-359` |
| 5. Tests: valid schema, required-field rejection, empty rejection, optional-field types, lenient extension key, skeleton inclusion | Done | `test_scout_runner.py` fixture `:147-164`; valid+extension `:208-218`; required `:245-253`; empty `:255-263`; optional types `:265-279`; skeleton `:359-383` |
| 6. Update indexes (`docs/CURRENT.md`, conditional `README.md`, `docs/agent_plans/README.md`) | Done | `docs/CURRENT.md:49-54`; `docs/agent_plans/README.md:39-40`; `README.md:16` unchanged (no routing change needed, matches plan) |
| Acceptance: lifecycle distinct from structure; admission strict; active docs report-only by default; runner limited to lookup/validation/shape; tests cover valid+invalid+skeleton; no Skyline V2/Data overlay or output changed | Met | Boundary bidirectional in both references; admission six-AND + report-only/ignore tiers; suppression `:110-118`; runner diff contains no scan/inference logic; no downstream overlay files touched |

**Accepted plan-review threads — all carried into implementation:**
- Thread 1 (current_docs distinct/required) — documented in reference `:25-29`; runner requires non-empty `:266`; tests cover required + empty rejection. ✓
- Thread 2 (lenient extension assertion) — fixture `future_extension` key `:162` + assertion `:218`; validation succeeds with the key present. ✓
- Thread 3 (document-structure forward reference) — updated, "future" wording removed. ✓
- Thread 4 (skeleton via generic loop, not special-casing) — no per-subskill skeleton code; inclusion proven by `test_setup_and_check_report_artifacts_with_document_lifecycle_drift`. ✓

#### Blocking issues

None. Every in-scope plan item is `Done` with concrete evidence, all four accepted plan-review threads are reflected in the code/tests, and validation passes on re-run. The work is implementable-as-planned and does not exceed the accepted scope.

#### Non-blocking issues

**Thread 1 — Cross-subskill tie-break from the plan's Boundary section is not captured verbatim in either reference.**
The accepted plan's "Boundary With Document Structure" (plan `:74-78`) states that when one document has both a structure and a lifecycle problem, the driver should "classify the primary risk" and "not open duplicate candidates for the same human decision," with each subskill allowed to note-and-route the other's concern. The shipped references implement the *scope split* correctly — `document-structure.md:131` routes "factual staleness rather than structure" to ignored noise, and `document-lifecycle-drift.md:153` routes "document shape, navigation, or readability" to ignored noise — and admission in both requires "no existing backlog item semantically covers the same decision." So duplicate candidates are largely prevented. But the explicit "classify the primary risk when a document has both issues" tie-break, and the softer "note as report-only and route to the sibling" disposition, are not literally present (the references use the harder "ignored noise" disposition for out-of-scope concerns). This is a prose refinement, not a correctness gap: the scope boundary and dedup intent both hold. Recommend (optional) adding one sentence to `document-lifecycle-drift.md` capturing the primary-risk tie-break for documents with both issues, so a Scout driver running both subskills has the plan's cross-routing guidance in the reference itself.

**Thread 2 — Lenient-extension assertion proves preservation, leans on the sibling test for rejection-avoidance.**
`test_validate_overlay_accepts_document_lifecycle_drift_schema` (`:208-218`) asserts the unknown `future_extension` key survives in the parsed result. Because `validate_overlay` returns the overlay unmodified, the substantive guarantee (validation does not *reject* the unknown key) is carried implicitly by the fact that the same test calls `validate_overlay` without expecting a raise. This is functionally sufficient and matches how `document-structure`'s `future_threshold` is tested, so it is consistent with repo convention — noting only that the assertion's strength is "key preserved," with "not rejected" implied by the surrounding successful call. No change required.

#### Overall judgment

**Ready for closeout.** The implementation faithfully matches the accepted plan and incorporates all four accepted plan-review threads. The subskill boundary with `document-structure` is clean and bidirectional; the candidate threshold is appropriately strict (six conjunctive admission conditions plus explicit report-only and ignored-noise tiers); active feature suppression correctly specializes the Scout-level rule, including the same safety/correctness/data-safety/production-risk/CI-blocking bypass (`document-lifecycle-drift.md:110-118` against `scout/SKILL.md:90-114`); the overlay schema validation adds only the planned required/optional fields with the lenient-extension convention and no global fields; and the runner boundary stays limited to reference lookup, overlay validation, and report-shape checks — no scans, drift inference, or semantic backlog checks were added (`scout/SKILL.md:182-183`). Docs/status are consistent: `docs/CURRENT.md` lists the new reference, the plans index lists the plan, the plan header reads `Status: implemented`, and `README.md` correctly needed no routing change. The two non-blocking threads are optional refinements, not gates.

#### Residual risks and validation gaps

- **Validation provenance (reviewer-rerun, strong).** I independently re-ran the plan's validation: `scout/tests/test_scout_runner.py` → 31 passed / 10 subtests; full `python -m pytest` → 114 passed / 22 subtests; `git diff --check` clean; `python scripts/check_backlog.py` → exit 0; worktree clean. This corroborates the plan's recorded Implementation Result.
- **Prose acceptance is human/reviewer-judged, not command-falsifiable.** Acceptance items like "makes lifecycle drift distinct" and "strict enough to avoid noisy stale-word cleanup" cannot be proven by `pytest`; only overlay/skeleton/test mechanics are mechanically falsifiable. I read the new reference prose against the plan's boundary and threshold sections and found it coherent and distinct — flagging that this judgment, not a test, backs those acceptance lines.
- **No in-repo overlay to dogfood.** `.agent-protocols/scout.yml` does not exist in this protocol repo, so the new overlay shape is exercised only through synthetic tempdir fixtures — same as the existing subskills, acceptable. Noting so no one assumes a live overlay validated the schema.
- **New manually-maintained path lists (`status_sources`, `runbook_roots`, `archive_paths`).** The reference now states these are adopting-repo-owned with documented fallbacks (`archive_paths` → `repo_context.archive_paths`; backlog default → `repo_context.backlog_path`) and should be updated when sources move/retire (`document-lifecycle-drift.md:33-41`), which resolves the Mechanism Lifecycle concern raised at plan review. The fallback semantics are reference prose for the driver, not runner-enforced — consistent with the reference-driven design.

No blocking issues. The implementation is ready for closeout; resolving the two non-blocking threads would tighten cross-subskill routing prose but is not required. Per the structured-review boundary, final merge-readiness belongs to closeout after its final rechecks (branch/PR, CI, human acceptance); this review concludes `ready for closeout`, not a merge handoff.

---

I did not write to any file or commit. Per the runner contract in `write-commit-to-plan` mode, the runner appends this review verbatim under the thread file's `## Review Threads` section and creates the `structured-review:` commit. The above is my complete returned review.

### Driver response 2

Reviewer pass 1 for implementation had no blocking issues and judged the work
ready for closeout. I accepted Thread 1 as a small prose tightening and updated
`scout/references/document-lifecycle-drift.md` to say that when one document
has both structure and lifecycle drift concerns, the Scout driver should
classify the primary risk, avoid duplicate candidates for the same human
decision, and route structural contributors to `document-structure` as
report-only context. Thread 2 required no code change because the successful
`validate_overlay` call with `future_extension` already proves unknown keys are
not rejected under the repo's existing test style.

Because the accepted refinement changes the implementation after review, I will
run an implementation re-review before closeout.

# Document Structure Subskill

Use this reference when `document-structure` is enabled in
`.agent-protocols/scout.yml`.

## Purpose

Find active or agent-routed document structures that make current context,
source-of-truth boundaries, or maintenance ownership hard for agents and humans
to understand.

This subskill does not judge whether the document's factual content is stale.
Stale active/current/historical state belongs to a future document-lifecycle
drift subskill. This subskill asks whether the document shape itself makes
maintenance risky.

## Overlay Fields

Required:

- `entry_docs`: non-empty list of repo entrypoint documents agents must read.
- `index_docs`: list of current maps or indexes, allowed to be empty.
- `doc_roots`: non-empty list of document roots to inspect.

Optional:

- `archive_paths`: paths whose documents are historical, artifact, or
  provenance context.
- `thresholds`: scan-hint threshold overrides.
- `repo_notes`: repo-specific interpretation notes.

Default thresholds:

- `index_review_lines: 400`
- `doc_review_lines: 800`
- `doc_large_lines: 1200`

Thresholds are scan hints, not admission rules. Revisit them when a repo's
document norms change. A document is not a candidate merely because it exceeds
a threshold.

## Evidence Loop

For each candidate-worthy document or coherent document cluster:

1. Read the repo entrypoint and document placement rules.
2. Classify relevant docs as entrypoint, current map, index, active plan,
   historical plan, artifact/report, backlog, or other local category.
3. Collect tracked Markdown metrics under `doc_roots`: line count, heading
   count, dense link/path references, and lifecycle-term density.
4. Inspect entry and index docs separately from the largest dated plans. A
   short current map can be higher risk than a very long historical plan.
5. Compare duplicated path references across entry/current/index docs when
   useful.
6. Look for unclear active/historical/provenance boundaries, index/provenance
   mixing, or source-of-truth duplication.
7. Compare candidate-worthy findings with existing backlog items.
8. Record commands and skipped evidence with reasons.

Useful tools are ordinary repo tools such as `git ls-files`, `wc`, `rg`, and
small one-off shell or Python snippets. Do not create a new maintained helper
script unless the logic is repeatable enough to own.

## Candidate Unit

One document or one coherent document cluster that needs one structural
decision.

Combine observations when:

- one index/current map and its companion index duplicate the same
  source-of-truth facts;
- several documents form one active navigation path whose boundary is unclear;
- the likely fix is one restructuring decision, such as splitting an index or
  adding a summary/status block.

Split observations when:

- different readers are affected by different document surfaces;
- one issue is an active source-of-truth problem and another is historical
  provenance organization;
- likely next actions differ.

## Candidate Admission

Propose a candidate only when all are true:

- the document or cluster is active, entrypoint-routed, current-index-routed, or
  otherwise likely to be read during normal agent work;
- a mechanical signal exists, such as size, heading/reference density,
  duplicate source references, lifecycle-term mixing, or index/provenance
  mixing;
- agent inspection proves a concrete maintenance risk;
- there is a clear restructuring next action;
- no existing backlog item semantically covers the same decision.

Apply the Scout active feature suppression rule before proposing document
structure cleanup candidates. Active implementation plans, review packets, and
rollout notes can be long or messy while they are carrying current work; that
is report-only by default until the phase stabilizes. Bypass suppression only
when the document structure is misleading agents today or the Scout-level
safety/correctness/data-safety/production-risk/CI-blocking/
explicit-human-direction override applies.

Concrete risks include:

- bootstrap over-read;
- unclear current/historical boundary;
- duplicated source-of-truth maintenance;
- active index documents carrying detailed provenance;
- long plans without a top status, current decision, or supersession pointer;
- cross-document navigation that forces unrelated history reads.

Good next actions include split an index, add an active/historical boundary,
move provenance into a historical section, add a status/summary block, create a
topic index, or clarify which document owns a fact.

## Report-Only Or Ignore

Use report-only when the structure is notable but the action is not yet clear,
when a long active document is readable enough but should be watched, or when
the document is carrying a clear or plausible active feature/rollout surface.

Use ignored noise when:

- a long document is clearly historical/provenance-only and not routed as
  active;
- a long active plan has clear status, summary, review threads, and closeout
  boundaries;
- duplicated references do not create source-of-truth ambiguity;
- the issue is factual staleness rather than structure.

## Evidence Standard

Each candidate proposal should cite:

- document path or cluster;
- active routing evidence;
- mechanical signals used only as candidate-pool evidence;
- the specific reader affected, such as bootstrap agent, planning agent,
  closeout agent, reviewer, or human operator;
- concrete maintenance risk;
- existing backlog overlap check;
- clear next decision/action.

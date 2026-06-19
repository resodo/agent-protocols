# Document Lifecycle Drift Subskill

Use this reference when `document-lifecycle-drift` is enabled in
`.agent-protocols/scout.yml`.

## Purpose

Find current-facing documents whose lifecycle state, routing, status wording,
or current-fact claims can mislead present agent/operator decisions.

This subskill does not judge document shape, length, navigation, or readability;
that belongs to `document-structure`. It also does not turn stale words into CI
failures. It asks whether a current reader could take a wrong action because a
document presents old, completed, superseded, or contradictory state as current.

## Overlay Fields

Required:

- `entry_docs`: non-empty list of agent/operator entrypoint documents.
- `current_docs`: non-empty list of current maps, status docs, indexes, or
  runbooks whose current-state claims should be checked.
- `doc_roots`: non-empty list of tracked document roots to inspect.

`current_docs` is deliberately distinct from
`document-structure.index_docs`. This subskill needs documents whose current
facts are in scope, not only navigational indexes. When a repo has no separate
current map, list the relevant entrypoint, status, or runbook document rather
than leaving the current-fact surface implicit.

Optional:

- `archive_paths`: historical, artifact, or provenance paths. When omitted,
  use `repo_context.archive_paths`.
- `status_sources`: backlog, roadmap, current-status, or active-plan files
  useful for checking current-state conflicts. The adopting repo owns this
  list; update it when source-of-truth status files move or are retired. The
  normal backlog source of truth is still `repo_context.backlog_path`.
- `runbook_roots`: operator instruction roots when runbooks live outside
  normal docs. The adopting repo owns this list and should update it when
  runbooks move or are retired.
- `repo_notes`: repo-specific interpretation notes.

There are no v1 threshold fields. Keyword, status-term, and date searches are
evidence collection aids, not candidate admission rules.

## Evidence Loop

For each candidate-worthy document or coherent document cluster:

1. Read the repo entrypoint, documentation placement rules, and current map.
2. Read overlay-declared `current_docs` before expanding into `doc_roots`.
3. Classify relevant docs as entrypoint, current map, status source, active
   plan, runbook, backlog, historical plan, artifact/report, archive, or other
   local category.
4. Search current-facing docs for status and routing terms such as `current`,
   `active`, `pending`, `next`, `in progress`, `awaiting`, `ready for review`,
   `ready for merge`, `blocked`, `superseded`, `closed`, and `deprecated`.
5. Compare suspicious claims against source-of-truth evidence, such as
   `repo_context.backlog_path`, overlay `status_sources`, `docs/CURRENT.md`,
   active plans, PR/worktree status when relevant, and nearby supersession
   notes.
6. Separate stale current claims from historical provenance that should remain
   untouched.
7. For candidate-worthy findings, inspect history with `git blame`, relevant
   commits, and related plans/docs when available to understand likely origin.
8. Compare candidate-worthy findings with existing backlog items.
9. Record commands, checked sources, and skipped evidence with reasons.

Useful tools are ordinary repo tools such as `rg`, `git ls-files`, `git log`,
`git blame`, `sed`, `wc`, and direct reads. Do not create a maintained helper
script unless the logic is repeatable enough to own.

## Candidate Unit

One document or one coherent document cluster that needs one lifecycle decision.

Combine observations when:

- one current map and companion status doc point to the same stale action;
- several runbooks share one supersession or retirement decision;
- one backlog/docs conflict has one clear source-of-truth alignment fix.

Split observations when:

- different readers would take different wrong actions;
- one issue is stale routing and another is stale status wording;
- likely next actions differ, such as update current routing versus retire a
  runbook.

## Candidate Admission

Propose a candidate only when all are true:

- the document or cluster is entrypoint-routed, current-index-routed,
  operator-runbook-routed, active-doc-routed, or otherwise likely to be used in
  current work;
- evidence shows a lifecycle/currentness claim is false, contradictory, or
  ambiguous enough to affect current action;
- the likely reader is named, such as bootstrap agent, planning agent, closeout
  agent, reviewer, or human operator;
- the risk is a wrong decision, not just cosmetic stale language;
- a clear fix exists, such as add a supersession note, update current routing,
  retire an old runbook, align backlog/current docs, or move historical content;
- no existing backlog item semantically covers the same decision.

Backlog/docs conflicts must use the adopting repo's backlog source of truth.
For this repo, that source is `docs/backlog.yml`.

Apply the Scout active feature suppression rule before proposing lifecycle
drift candidates. Active feature docs are report-only by default. Promote only
when stale wording is likely to cause an immediate wrong action, such as
following a retired runbook, editing the wrong source-of-truth document,
believing a closed gate is still blocking, or ignoring a safety, correctness,
data-safety, production-risk, or CI-blocking condition.

Suppression is deferral, not dismissal. Later Scout runs may re-evaluate the
same observation after active signals fade.

Concrete risks include:

- bootstrap agents reading a historical plan as the active plan;
- operators following a retired runbook;
- current maps routing agents to superseded instructions;
- completed work still presented as pending in source-of-truth docs;
- backlog and current docs disagreeing about the next action;
- merge, review, or closeout status text that remains current-facing after the
  gate has closed.

Good next actions include add a status/supersession note, update current
routing, align backlog/docs state, move historical content, retire a runbook,
or document that a current-facing instruction is still valid.

## Report-Only Or Ignore

Use report-only when evidence is useful but candidate admission is not met,
including when:

- evidence is weak or the wrong action is not clear;
- the document is historical provenance and not routed as current;
- stale wording is harmless after local context is read;
- active feature churn explains the mismatch;
- the next action would be speculative cleanup;
- the finding should be rechecked in a later Scout run after active signals
  fade.

Use ignored noise when:

- a document is clearly archived, generated, private-run output, or
  provenance-only;
- stale wording appears only inside quoted review threads or historical records
  that should not be rewritten;
- the issue is document shape, navigation, or readability rather than factual
  currentness;
- a supersession or status note already prevents wrong current action.

## Evidence Standard

Each candidate proposal should cite:

- document path or cluster;
- active/current routing evidence;
- the exact lifecycle/currentness claim at issue;
- source-of-truth evidence showing conflict or drift;
- the likely reader and wrong action risk;
- active feature suppression check;
- history provenance, such as introducing or last-status-change commit/plan,
  when practical;
- existing backlog overlap check;
- clear next decision/action.

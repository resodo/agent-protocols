---
name: scout
description: Use when a repo should be manually or periodically inspected for lifecycle, reachability, documentation, coverage, process, or maintainability issues and high-signal discoveries should be proposed as backlog candidates without treating judgment-heavy discovery as CI.
---

# Scout

Scout is a discovery protocol, not weak CI.

Use Scout when the user asks to audit, scout, periodically inspect, or discover
maintenance issues that need judgment and evidence synthesis. If a rule is
objective enough to return a stable true/false result, prefer CI or a repo
checker instead of Scout.

## Required Inputs

- Target repo root.
- Repo overlay at `.agent-protocols/scout.yml`.
- Backlog source of truth, normally `docs/backlog.yml`.
- Enabled subskills declared by the overlay.

## Workflow

1. Read the target repo entry files from `repo_context.entry_files`.
2. Read `.agent-protocols/scout.yml`.
3. Run `scout/scripts/scout_runner.py setup` to validate the overlay and create
   the run artifact skeleton.
4. For each enabled subskill, read the matching subskill reference, then run the
   subskill evidence loop:
   - collect initial context from the overlay;
   - inspect evidence and run/search tools where useful;
   - interpret evidence with subskill rules;
   - loop back for more evidence when the finding is not clear enough;
   - classify findings;
   - compare candidate-worthy findings with existing backlog items;
   - write the subskill report section.
5. Run `scout/scripts/scout_runner.py check` before handoff.
6. In dry-run mode, stop for human review before writing any backlog changes.

## Finding Classes

- `candidate proposal`: a candidate-worthy finding not semantically covered by
  an existing backlog item.
- `candidate refinement`: a finding that improves an existing
  `status: candidate` item without changing its core human decision.
- `related finding`: a finding that overlaps an existing item but needs a
  distinct decision or action.
- `report-only observation`: useful evidence that does not meet candidate
  admission rules.
- `ignored noise`: expected noise or accepted state.
- `inconclusive`: evidence is insufficient and further probing is not useful in
  the current run.

## Candidate Rules

Scout may propose or refine `status: candidate` items. It must not edit
`status: open` or `status: closed` items.

Candidate items use open-style backlog fields, with `refs` required so each
candidate links back to report evidence. Do not add Scout-specific fields such
as `scout`, `fingerprint`, `confidence`, `severity`, or `human_review`.

In dry-run mode, write proposed candidates only in `SCOUT_REPORT.md`. After
explicit human approval, use `backlog-maintenance/SKILL.md` to write or refine
candidate YAML.

Candidate granularity is one human decision or one coherent fix. Do not turn
raw tool findings, files, or line counts directly into backlog items.

## Report Contract

Each Scout run writes a directory under `report.output_root`, normally:

```text
docs/agent_plans/outputs/YYYY-MM-DD_scout_run/
  SCOUT_REPORT.md
  MANIFEST.md
```

`SCOUT_REPORT.md` must contain:

- `Run Metadata`
- `Executive Summary`
- `Proposed Backlog Changes`
- `Human Review Queue`
- `Subskill Results`
- `Tool Commands`
- `Runner Validation`

Use stable report anchors such as `candidate-proposal-001` and
`candidate-refinement-001`. Do not use hashes or fingerprints.

`MANIFEST.md` is an index, not a second report. It lists the primary artifact,
supporting artifacts or `None`, validation provenance, and backlog write mode.

## Subskills

Read only the references for enabled subskills:

- `script-lifecycle`: see `references/script-lifecycle.md`.
- `code-reachability` backend/Python Slice 1: see
  `references/code-reachability-backend-python.md`.

Subskills define domain scope, overlay fields, useful tools, evidence loops,
granularity, admission rules, and report/ignore rules. They do not define a
separate backlog lifecycle.

## Runner Boundary

The runner stabilizes mechanics:

- parse and validate overlay schema;
- create report and manifest skeletons;
- generate deterministic temporary tool adapters;
- check report/manifest headings and dry-run backlog protection.

The runner must not interpret tool output, decide whether a finding is true,
deduplicate candidates semantically, judge overlap with open/closed backlog
items, or replace the subskill evidence loop.

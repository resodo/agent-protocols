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
   - for candidate-worthy bug, legacy, lifecycle, or reachability findings,
     collect history provenance with `git blame`, relevant commits, and related
     historical plans/docs when available;
   - classify findings;
   - compare candidate-worthy findings with existing backlog items;
   - write the subskill report section.
5. Run `scout/scripts/scout_runner.py check` before handoff, and record that
   final validation command and result in both `SCOUT_REPORT.md` and
   `MANIFEST.md`.
6. In dry-run mode, stop for human review before writing any backlog changes.
7. In write-enabled mode, commit backlog/report changes separately per
   subskill after validation. Do not mix findings from multiple subskills in
   one Scout output commit unless the human explicitly requests a combined
   commit.

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

In write-enabled mode, each subskill gets its own backlog commit boundary:
write that subskill's candidate proposals/refinements, update the run report
and manifest for that subskill's write, run the repo backlog checker, then
commit only those changes before moving to the next subskill. Commit messages
should name the subskill, for example `scout: add script-lifecycle candidates`.

Candidate granularity is one human decision or one coherent fix. Do not turn
raw tool findings, files, or line counts directly into backlog items.

Candidate-worthy findings should explain both current state and likely origin.
When practical, cite the commit or plan that introduced or last changed the
surface, and say whether the finding is a new regression, planned residue, or
old debt that became visible through the current scan.

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

`Runner Validation` must record final validation provenance, not only setup.
At minimum, record the exact `scout_runner.py check` command used and its
result. In write-enabled mode, also record the adopting repo's backlog checker
command and result before handoff.

Use stable report anchors such as `candidate-proposal-001` and
`candidate-refinement-001`. Do not use hashes or fingerprints.

`MANIFEST.md` is an index, not a second report. It lists the primary artifact,
supporting artifacts or `None`, validation provenance, and backlog write mode.
Its `Validation` section must mirror the final mechanical validation summary:
the `scout_runner.py check` command/result, and in write-enabled mode the repo
backlog checker command/result. A manifest that only records skeleton creation
is incomplete.

## Subskills

Read only the references for enabled subskills:

- `script-lifecycle`: see `references/script-lifecycle.md`.
- `code-reachability` backend/Python Slice 1: see
  `references/code-reachability-backend-python.md`.
- `document-structure`: see `references/document-structure.md`.
- `code-structure`: see `references/code-structure.md`.

Subskills define domain scope, overlay fields, useful tools, evidence loops,
granularity, admission rules, and report/ignore rules. They do not define a
separate backlog lifecycle.

`code-structure` may use language/framework adapters inside the one subskill
section, such as Python and TypeScript/React. Adapters are evidence sources, not
sub-subskills, and the Scout report still uses one `### code-structure`
section.

## Runner Boundary

The runner stabilizes mechanics:

- parse and validate overlay schema;
- create report and manifest skeletons;
- generate deterministic temporary tool adapters;
- check report/manifest headings, final validation provenance, and dry-run
  backlog protection.

In v1, the runner does not execute `document-structure` or `code-structure`
scans. The driver runs project-appropriate commands, records them in
`SCOUT_REPORT.md`, and owns interpretation.

Backlog item field validation belongs to the repo backlog checker. The runner
may invoke or require that checker, but it must not maintain an independent
candidate field contract. Write-enabled runs must still follow
`backlog-maintenance/SKILL.md` and run the repo backlog checker before handoff.

The runner must not interpret tool output, decide whether a finding is true,
deduplicate candidates semantically, judge overlap with open/closed backlog
items, or replace the subskill evidence loop.

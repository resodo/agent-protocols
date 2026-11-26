---
name: scout
description: "[scout executor] Use when a repo should be manually or periodically inspected for lifecycle, reachability, coverage, process, or maintainability issues and high-signal discoveries should be proposed as todo-tracker items without treating judgment-heavy discovery as CI."
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
- The project's todo tracker, as named in `.agent-protocols/context.md`.
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
   - compare candidate-worthy findings with existing todo-tracker items;
   - write the subskill report section.
5. Run `scout/scripts/scout_runner.py check` before handoff, and record that
   final validation command and result in both `SCOUT_REPORT.md` and
   `MANIFEST.md`.
6. In dry-run mode, stop for human review before opening, editing, or
   commenting on any todo-tracker item.
7. In write-enabled mode, open the subskill's tracker items after validation
   and record each one in `MANIFEST.md` (`Tracker Write Mode`, `Opened tracker
   items:`). Commit report changes separately per subskill unless the human
   explicitly requests a combined commit.

## Finding Classes

- `candidate proposal`: a candidate-worthy finding not semantically covered by
  an existing todo-tracker item.
- `candidate refinement`: new evidence for an existing tracker item that does
  not change its core human decision.
- `related finding`: a finding that overlaps an existing item but needs a
  distinct decision or action.
- `report-only observation`: useful evidence that does not meet candidate
  admission rules.
- `ignored noise`: expected noise or accepted state.
- `inconclusive`: evidence is insufficient and further probing is not useful in
  the current run.

## Candidate Rules

A candidate proposal is a proposed new item for the project's todo tracker:
a title, why it matters, the next decision, and a link back to its report
anchor. A candidate refinement is a proposed comment on an existing item.
Scout never closes, re-scopes, or reprioritizes an existing item.

In dry-run mode, write proposals only in `SCOUT_REPORT.md`; the human decides
which become tracker items. In write-enabled mode, Scout opens the items and
posts the comments itself, one subskill at a time, and lists each one (link
and report anchor) in `MANIFEST.md` under `Opened tracker items:`.

Candidate granularity is one human decision or one coherent fix. Do not turn
raw tool findings, files, or line counts directly into tracker items.

Candidate-worthy findings should explain both current state and likely origin.
When practical, cite the commit or plan that introduced or last changed the
surface, and say whether the finding is a new regression, planned residue, or
old debt that became visible through the current scan.

### Active Feature Suppression

Do not propose cleanup, refactor, dead-helper, stale-payload, or structure
candidates for an active feature surface by default.

An active feature surface is maintained code, docs, scripts, or configuration
that is currently being built, stabilized, rolled out, or acceptance-tested. It
is different from ordinary active/in-use code: maintained and stable code can
still produce Scout candidates, while actively-being-built feature work usually
should not.

Positive activity signals include a current plan, current-map entry, active PR
or worktree, explicit human statement, active tracker item or progress entry, recent
acceptance or rollout notes, or multiple recent commits tied to the same
still-open feature. Churn alone is not enough to prove active feature status,
but plausible unresolved activity is enough to suppress cleanup candidates.

When active feature status is clear or plausible, classify cleanup/refactor/
dead-helper findings as `report-only observation` and name the active owner,
plan, tracker item, or uncertainty when known. Later Scout runs may re-evaluate
the same observation after active signals fade.

Only bypass this suppression when the finding is about safety, correctness,
data safety, production risk, CI-blocking failure, or explicit human direction
to review that active feature surface for immediate action.

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
- `Proposed Todo Changes`
- `Human Review Queue`
- `Subskill Results`
- `Tool Commands`
- `Runner Validation`

`Runner Validation` must record final validation provenance, not only setup.
At minimum, record the exact `scout_runner.py check` command used and its
result.

Use stable report anchors such as `candidate-proposal-001` and
`candidate-refinement-001`. Do not use hashes or fingerprints.

`MANIFEST.md` is an index, not a second report. It lists the primary artifact,
supporting artifacts or `None`, validation provenance, and tracker write mode.
Its `Validation` section must mirror the final mechanical validation summary:
the `scout_runner.py check` command/result. A manifest that only records skeleton creation
is incomplete.

## Subskills

Read only the references for enabled subskills:

- `script-lifecycle`: see `references/script-lifecycle.md`.
- `code-reachability` backend/Python Slice 1: see
  `references/code-reachability-backend-python.md`.
- `code-structure`: see `references/code-structure.md`.

Scout has no documentation subskills. In a repo that wires the docs check,
the doc watcher reads each merge for rules and docs it made wrong
(`doc-watcher`); other document discovery is retired.

Subskills define domain scope, overlay fields, useful tools, evidence loops,
granularity, admission rules, and report/ignore rules. They do not define a
separate tracker lifecycle.

`code-structure` may use language/framework adapters inside the one subskill
section, such as Python and TypeScript/React. Adapters are evidence sources, not
sub-subskills, and the Scout report still uses one `### code-structure`
section.

## Runner Boundary

The runner stabilizes mechanics:

- parse and validate overlay schema;
- create report and manifest skeletons;
- generate deterministic temporary tool adapters;
- reject the retired `repo_context.backlog_path` overlay key;
- check report/manifest headings, final validation provenance, and, in
  write-enabled mode, that the manifest has the `Opened tracker items:` line.
  The runner does not check that line's contents; the driver checks that it
  lists every item the run opened or commented on.

In v1, the runner does not execute `code-structure` scans. The driver runs
project-appropriate commands, records them in `SCOUT_REPORT.md`, and owns
interpretation.

The runner never reads or writes the todo tracker; the driver does, and a
dry-run's promise to leave the tracker untouched is the driver's to keep.

The runner must not interpret tool output, decide whether a finding is true,
deduplicate candidates semantically, judge overlap with existing tracker
items, or replace the subskill evidence loop.

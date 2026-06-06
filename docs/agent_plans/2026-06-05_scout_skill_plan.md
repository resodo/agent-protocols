# Scout Skill Plan

Status: draft plan / decisions captured / pending structured review
Date: 2026-06-05

## Context

This plan captures the current design discussion for a new shared Scout
protocol. The immediate trigger came from Skynet V2 backlog item V2-BL-0072,
which started as an audit of active scripts, code, and docs for lifecycle and
regression ownership.

During discussion, the scope changed. The project owner does not want this work
to be a one-off cleanup pass that depends on a single agent's memory. The more
durable need is a reusable Scout workflow that can periodically or manually
inspect a project, find likely maintenance, documentation, code, process, and
coverage issues, and turn high-signal discoveries into backlog candidates.

The distinction from CI is central:

- CI should own objective, stable true/false checks that can block a merge.
- Scout should own discovery work where judgment, context, and evidence
  synthesis matter.
- Scout should not be treated as weak CI. If a rule is objective enough on day
  one, it should go directly into CI instead of being routed through Scout.

The first implementation should be conservative. It should establish the shared
workflow, candidate lifecycle, and first few subskills, then improve through
repeated runs.

## Historical Inputs From Skynet V2

The Skynet V2 backlog shows that agent-discovered work is broader than script
lifecycle cleanup. Current examples include:

- regression coverage gaps, such as broader service/API/CLI tests, Postgres
  query coverage, full-stack smoke data, and narrow viewport coverage;
- legacy and semantic debt, such as SQLite policy cleanup, future hooks,
  materialized summaries, dormant lifecycle semantics, and ambiguous field
  names;
- production and ops follow-ups, such as provider incidents, scrape fragment
  ownership, deploy/runtime contracts, dashboards, alerts, and runbooks;
- process and protocol issues, such as worktree discipline, stale protocol
  paths, closeout/review boundaries, and transcript-backend gaps;
- model and evaluation debt, such as prompt/model experiments, routing
  evaluation, lookup sufficiency, and one-off evaluation scripts;
- product acceptance evidence gaps, such as missing real error-state
  screenshots or missing viewport coverage.

Scout should be designed from these historical backlog patterns, not from a
fixed list of static-analysis tools.

## Working Model

Scout is a shared top-level skill with internal subskills.

The main Scout skill owns:

- repo bootstrap and overlay loading;
- subskill orchestration;
- report creation;
- semantic comparison against existing backlog items;
- candidate creation and candidate refinement.

Each subskill owns one domain lens. A subskill may be mostly text
instructions, may call ordinary repository tools, or may eventually bundle a
deterministic helper. Scripts are optional. Most useful Scout work is expected
to involve judgment and evidence synthesis rather than pure machine checks.

Each subskill follows an evidence loop, not a one-pass detector pipeline:

1. collect initial context from the shared protocol and repo overlay;
2. inspect evidence and run/search tools where useful;
3. interpret the evidence using domain-specific rules;
4. return to context collection or tool use if the evidence is insufficient;
5. classify findings as candidate-worthy, report-only, ignored, or explicitly
   inconclusive;
6. apply the shared backlog interaction rules for this subskill's findings;
7. write this subskill's section in the run report.

The initial orchestration should be a per-subskill mini-pipeline with an
explicit inner evidence loop:

```text
agent invokes the Scout runner once to validate overlay config and create the
run report skeleton

for each enabled subskill:
    load subskill protocol and overlay config
    while evidence is insufficient and useful context/tools remain:
        collect or read more context
        run/search tools where useful
        interpret the new evidence under the subskill rules
        decide whether more evidence is needed
    classify findings as candidate-worthy, report-only, ignored, or inconclusive
    compare candidate-worthy findings with backlog
    propose candidate backlog items when justified; write/refine only when the
        run mode allows backlog changes
    write the subskill report section

agent invokes the Scout runner again to check report/backlog mechanics before
handoff
```

The first implementation should not split the pipeline into global detect,
global interpret, and global reconcile phases. Keeping interpretation inside
the subskill should make the system easier to extend.

Consistency is a core requirement. The main Scout skill should define the
standard run pipeline, finding classes, backlog interaction rules, report
sections, and minimum evidence expectations. Subskills should fill in
domain-specific scope, useful inputs, tool guidance, candidate/report/ignore
rules, and granularity overrides. They should not invent their own backlog
lifecycle behavior or report categories.

## Overlay And Runner Model

Scout should distinguish shared protocol behavior from repo-local configuration.

Shared Scout owns:

- the top-level workflow;
- finding classes;
- backlog interaction rules;
- report structure;
- subskill contracts;
- generic subskill reasoning rules.

The repo overlay owns:

- enabled subskills and their order;
- concrete script roots, active docs, source-of-truth docs, archive paths, and
  entrypoint declarations;
- repo-specific exceptions and known manual entrypoints;
- local validation commands and report output location.

The current preference is a single YAML overlay:

```text
.agent-protocols/scout.yml
```

The YAML should include both stable machine-readable config and prose fields for
repo-specific judgment rules. The runner reads only documented config fields.
The agent reads the whole file, including prose notes. This avoids a
`scout.yml` / `scout.md` source-of-truth split in v1.

All repo and subskill overlay configuration should live in this one file. The
file should stay namespaced so shared context and subskill-specific rules do not
blur together:

```yaml
version: 1

enabled_subskills:
  - script-lifecycle
  - code-reachability

report:
  output_root: docs/agent_plans/outputs

repo_context:
  entry_files:
    - AGENTS.md
  backlog_path: docs/backlog.yml
  active_docs:
    - README.md
    - docs/README.md
    - docs/CURRENT.md
  archive_paths:
    - docs/agent_plans/outputs

subskills:
  script-lifecycle:
    script_roots:
      - scripts
    script_entrypoint_sources:
      - README.md
      - docs/CURRENT.md
      - docs/agent_plans
      - .github/workflows
      - backend/pyproject.toml
      - frontend/package.json
    known_manual_entrypoints:
      - scripts/agent_protocols_guard.sh
    historical_script_contexts:
      - docs/agent_plans/outputs
    repo_notes: >
      Scripts tied to historical experiment provenance should prefer archive
      discussion over direct deletion.

  code-reachability:
    python:
      production_roots:
        - backend/app
        - scripts
      test_roots:
        - backend/tests
      active_contract_sources:
        - README.md
        - docs/CURRENT.md
        - docs/agent_plans
        - backend/pyproject.toml
      dynamic_entrypoint_sources:
        - backend/pyproject.toml
        - backend/app/main.py
        - backend/app/api
        - backend/app/cli.py
      known_false_positive_classes:
        - FastAPI route handlers
        - Typer commands
        - Pydantic models and fields
        - SQLAlchemy mapped fields
        - validators and decorated hooks
        - Alembic/migration/runtime entrypoints
        - pytest fixtures/helpers
      vulture:
        roots:
          - backend/app
          - scripts
        min_confidence: 60
        ignore_decorators:
          - "@app.get"
          - "@app.post"
          - "@app.put"
          - "@app.patch"
          - "@app.delete"
          - "@router.get"
          - "@router.post"
          - "@router.put"
          - "@router.patch"
          - "@router.delete"
          - "@app.command"
          - "@app.callback"
          - "@field_validator"
          - "@model_validator"
        ignore_names:
          - cls
          - model_config
    repo_notes: >
      Treat test-only production helpers as seam-lifecycle questions, not
      immediate deletion candidates.
```

The important v1 direction is one overlay file with clear namespaces, not
parallel YAML and Markdown sources of truth.

Core overlay fields should be strict. Current agreed core fields:

- `version`
- `enabled_subskills`
- `report.output_root`
- `repo_context.entry_files`
- `repo_context.backlog_path`
- `repo_context.active_docs`
- `repo_context.archive_paths`

`enabled_subskills` must be non-empty. The repo context list fields should be
present even when empty.

Subskill overlay sections should stay lightweight. The only shared base field in
v1 is `repo_notes`. Path fields, entrypoint declarations, and other config are
subskill-specific and must be declared by the corresponding subskill protocol.
This avoids fake uniformity and prevents generic include/exclude path fields
from becoming confusing second sources of truth.

For `script-lifecycle`, `script_roots` and `script_entrypoint_sources` are
required and should be non-empty for an enabled run. `known_manual_entrypoints`
is optional and defaults to an empty list. `historical_script_contexts` is
optional and defaults to `repo_context.archive_paths`.

For backend/Python `code-reachability`, `python.production_roots` is required
and non-empty. `python.test_roots`, `python.active_contract_sources`, and
`python.dynamic_entrypoint_sources` are required fields but may be empty lists
in repos that lack those concepts. `python.known_false_positive_classes` is
optional and extends the shared defaults. `python.vulture.roots` is required and
non-empty when Vulture is enabled. `python.vulture.min_confidence` defaults to
60. `python.vulture.ignore_decorators` and `python.vulture.ignore_names` are
optional lists defaulting to empty lists.

`python.production_roots` and `python.vulture.roots` are intentionally separate.
Production roots define semantic scope; Vulture roots define the concrete tool
scan. They may match, but they do not have to.

Scout should also include a lightweight runner script for deterministic
orchestration. The runner should not replace the agent's judgment or try to
make LLM-based findings deterministic. Its job is to stabilize the mechanical
parts:

- load and validate the overlay config;
- resolve enabled subskills and order;
- create the run directory, report skeleton, and manifest skeleton;
- print or record the current subskill step;
- validate that candidate writes use allowed backlog statuses and required
  fields;
- verify generated tool adapter files are deterministic when they are used;
- check report and manifest completeness before handoff.

Runner v1 hard checks should include:

1. Overlay parse and schema checks for `version`, `enabled_subskills`,
   `report.output_root`, `repo_context.entry_files`,
   `repo_context.backlog_path`, `repo_context.active_docs`, and
   `repo_context.archive_paths`. List fields may be empty when the subskill
   allows that, but the fields should exist.
2. Enabled subskill checks: every enabled subskill must have a shared subskill
   protocol, and subskill-specific required overlay fields must be present.
3. Run artifact setup: create a stable run directory and skeleton
   `SCOUT_REPORT.md` / `MANIFEST.md` with fixed headings and run mode.
4. Backlog mechanics: locate and parse the configured backlog YAML; in dry-run
   mode, verify the backlog file was not modified; when backlog writes are
   allowed, verify candidate status and required fields.
5. Generated tool adapters: when a temporary native config is generated from
   overlay data, verify canonical output for identical overlay input and keep it
   outside the repo unless explicitly configured otherwise.
6. Report completeness: every enabled subskill must have a section with
   context/tools used, findings classification, proposed candidates or `None`,
   report-only observations or `None`, ignored noise or `None`, and
   inconclusive items or `None`; no TODO placeholders should remain.
7. Manifest completeness: primary artifact, supporting artifacts or `None`,
   validation provenance, and backlog write mode must be present.

Runner v1 must not interpret tool output, decide whether a finding is true,
deduplicate candidates semantically, judge overlap with open/closed backlog
items, write final conclusions, or replace the agent/subskill evidence loop.

When a tool needs a native config file that would otherwise become long-lived
repo clutter, the overlay remains the source of truth and the runner may emit a
temporary adapter file. Those generated files must be canonical: stable field
order, stable list ordering when order is not semantically meaningful, stable
quoting/formatting, and identical output for identical overlay input. For
example, Skynet V2's `code-reachability` overlay may declare Vulture ignore
decorators/names in YAML, while the runner writes a temporary TOML config for
the Vulture invocation and removes it after the run.

The agent still performs the domain reading, tool use, interpretation, and
candidate wording under the shared Scout protocol.

## Decisions So Far

### One Top-Level Skill

Decision: Scout v1 uses one top-level shared `scout` skill. Domain-specific
checks are implemented as internal subskill protocol files, not standalone
Codex skills.

Reason: Scout's most important shared behavior is the backlog candidate memory
and run report. Making every subskill a standalone skill would duplicate
schema, reconcile, and reporting rules too early.

Possible future: a subskill may later become a standalone skill if it has clear
independent trigger value and does not duplicate Scout's core memory contract.

### Candidate Is A Backlog Status

Decision: `candidate` is a first-class backlog lifecycle state in the same
`docs/backlog.yml` registry used for `open` and `closed` items.

Candidate items use the normal backlog ID sequence, such as `V2-BL-0073`.

Reason: The project owner wants one durable YAML memory, not a parallel inbox or
temporary Scout database. A candidate is an early backlog state awaiting human
review, not an ephemeral cache entry.

Valid lifecycle paths:

```text
candidate -> open -> closed
candidate -> closed
```

Human review owns candidate promotion or closure.

### No Scout-Specific Backlog Metadata In V1

Decision: Candidate items use the same fields as normal open items:

- `id`
- `status`
- `priority`
- `kind`
- `title`
- `why`
- `next`
- `done_when`
- `refs`

Scout v1 should not add dedicated fields such as `scout`, `fingerprint`,
`confidence`, `severity`, or `human_review`.

Reason: Backlog entries should remain simple and human-maintainable. Evidence,
detectors, subskill names, and interpretation details belong in the linked
Scout run report, not in a complex per-item schema.

Semantic comparison is preferred over artificial fingerprints. Scout findings
are often judgment-based, and a fingerprint can create false stability or false
matches.

### Candidate Refinement Is Allowed

Decision: Scout may create or refine `status: candidate` items. Scout must not
edit `open` or `closed` items.

If a finding overlaps an existing `open` or `closed` item, Scout should express
the incremental part separately and reference the existing item in the report or
new candidate.

Reason: A candidate has not yet been human-reviewed and can reasonably be
clarified by later Scout runs. An open or closed item has already entered
human-owned backlog lifecycle and should not be rewritten by Scout.

The refinement rules should stay simple. Do not add a complicated provenance or
supersession model in v1.

After a dry-run, approved Scout proposals should be written through the
backlog-maintenance protocol, not by the Scout runner. Scout owns discovery,
evidence, and proposal wording. Backlog-maintenance owns long-lived backlog
mutation, ID sequencing, required fields, and status semantics. The runner may
perform mechanical checks, but it must not author backlog items from report
content.

Because `candidate` is a new backlog status, the shared backlog-maintenance
protocol must be updated in the same implementation scope. It should define:

- `candidate` as a human-unreviewed backlog proposal;
- allowed fields, matching normal backlog items;
- the transition expectation that a human may later accept it into `open`,
  close/cancel it, or leave it pending;
- that Scout-proposed candidates should link back to a Scout report anchor in
  `refs`;
- that no Scout-specific metadata fields are required.

### Scout Report Carries Evidence

Decision: Each Scout run should produce a Markdown report. Backlog candidates
link to that report through `refs`.

The report should carry:

- which subskills ran;
- important evidence;
- raw tool outputs or summaries when relevant;
- interpretation notes;
- new candidates created;
- existing candidates refined;
- findings that were report-only or ignored with rationale.

Reason: The report is the right place for detailed evidence. The backlog item
should remain a concise action record.

For Skynet V2 adoption, each Scout run should write a dedicated output
directory under the repo-configured `report.output_root`, for example:

```text
docs/agent_plans/outputs/YYYY-MM-DD_scout_run/
  SCOUT_REPORT.md
  MANIFEST.md
```

If multiple runs happen on the same date, use a stable suffix such as
`YYYY-MM-DD_scout_run_2`. `SCOUT_REPORT.md` is the primary evidence artifact.
It should include run metadata, summary, proposed backlog changes, subskill
results, tool commands or summaries, ignored noise, inconclusive items, and a
human review queue. Proposed candidates should have stable anchors so approved
backlog items can link back to the exact report section through `refs`.

`SCOUT_REPORT.md` v1 should use these required top-level headings:

```markdown
# Scout Report

## Run Metadata
## Executive Summary
## Proposed Backlog Changes
## Human Review Queue
## Subskill Results
## Tool Commands
## Runner Validation
```

`Run Metadata` must record repo, branch/worktree, date, mode, overlay path,
enabled subskills, backlog path, and report output directory. `Executive
Summary` should record counts and a short run-level summary, not long evidence.

`Proposed Backlog Changes` should contain `Candidate Proposals` and `Candidate
Refinements`. Each proposal/refinement must include proposed title, target
backlog action, `why`, `next`, `done_when`, evidence summary, refs considered,
subskill, and status if approved. These are proposals, not already-written
backlog entries.

`Human Review Queue` should list the concrete decisions needed from the human,
such as approving or rejecting specific proposal anchors. `Subskill Results`
must include one section per enabled subskill. Each subskill section should use
fixed subsections for context/tools used, candidate proposals, candidate
refinements, report-only observations, ignored noise, and inconclusive items.
If a subsection has no entries, write `None.` rather than leaving it blank.

Report anchors should be simple and stable within the report:

- `candidate-proposal-001`
- `candidate-refinement-001`
- `report-only-001`
- `ignored-noise-001`
- `inconclusive-001`

Number anchors by report order from `001`. Do not use hashes or fingerprints.
If a title changes during report editing, keep the anchor stable.

`Tool Commands` should record actual commands run. Do not preserve full raw tool
output by default. Summarize long outputs in the report; inline raw output only
when it is short and materially important. Extra raw-output artifacts are
allowed only when the run intentionally keeps them, and they must be listed in
`MANIFEST.md`.

`MANIFEST.md` is mandatory for Skynet V2 adoption but should stay thin. It is
an output-directory index, not a second report. It should list:

- primary artifact;
- supporting artifacts, or `None`;
- validation provenance, including runner skeleton/checks used;
- backlog write mode, such as dry-run with no `docs/backlog.yml` changes;
- notes that candidate proposals require explicit human approval before
  backlog writes.

The manifest must not duplicate the report body. First-run supporting artifacts
default to `None` unless the run intentionally keeps additional files.

### Candidate Granularity

Decision: A Scout candidate backlog item should represent one human decision or
one coherent fix. Raw observations, raw tool findings, files, or line counts do
not map directly to backlog items.

Use these questions to choose the candidate boundary:

1. Can a human review and decide the item as one unit?
2. Can the work plausibly be completed as one coherent change?
3. Does the evidence point to the same underlying issue rather than merely the
   same tool output?

If the answer is no, split the candidate. If several observations share one
root decision or fix, combine them.

Each subskill may define a more specific default unit. That default can override
the global heuristic only by making candidate boundaries clearer, not by
mapping every raw observation directly into backlog.

### Main Skill Backlog Interaction

Decision: The main Scout skill owns finding classes and backlog interaction
rules. Subskills decide whether a domain finding is candidate-worthy,
report-only, or ignored, but they do not define separate backlog lifecycle
behavior.

Finding classes:

- `candidate proposal`: a candidate-worthy finding that is not semantically
  covered by an existing backlog item.
- `candidate refinement`: a candidate-worthy finding that improves or broadens
  an existing `status: candidate` item without changing its core human
  decision.
- `related finding`: a finding that overlaps an existing backlog item but is not
  the same human decision or coherent fix.
- `report-only observation`: a useful observation that does not meet candidate
  admission rules.
- `ignored noise`: expected noise or intentionally accepted state.

Backlog interaction rules:

- In dry-run mode, Scout must not write backlog changes. It records proposed
  candidate creations/refinements in the run report for human approval.
- If an existing `status: candidate` item represents the same human decision,
  Scout may refine that candidate.
- If an existing `status: open` item represents the same human decision, Scout
  must not edit it; the run report should mark the finding as already covered.
- If an existing `status: closed` item represents the same human decision, Scout
  must not reopen it; the run report should record the match for human
  attention if the issue appears to recur.
- If a finding overlaps an existing item but adds a distinct decision or action,
  Scout may propose a new candidate and describe the relationship in the run
  report.
- Scout must not automatically promote, close, cancel, reopen, or delete backlog
  items.

The first Skynet V2 adoption run should use dry-run mode. It may include
proposed candidate creations/refinements in the report, but it must not modify
`docs/backlog.yml` until a human explicitly approves specific proposals. This
lets Slice 1 validate report quality, candidate granularity, and backlog
mechanics before writing to long-lived backlog memory.

Because the first run is dry-run, v1 should not add a fixed candidate volume
limit yet. The first report should preserve enough proposed candidates and
report-only observations to let a human judge whether admission rules are too
loose, too strict, or badly grouped. A soft per-subskill limit can be added
later if the first dry-run shows backlog-flood risk.

## Candidate Versus CI

When a subskill identifies an objective true/false rule, the plan should prefer
CI or a repo checker over Scout.

Examples of CI-like checks:

- schema validation;
- generated artifact drift;
- static formatting/linting;
- secret scanning;
- deterministic import smoke;
- objective registry consistency.

Examples of Scout-like checks:

- whether a script still has lifecycle value;
- whether an active doc is stale or conflicts with another source of truth;
- whether a test protects a real production path or only a test seam;
- whether coverage gaps are meaningful enough to schedule;
- whether a one-off experiment should be archived, replaced, or kept active;
- whether a protocol/process failure pattern suggests backlog work.

Scout may discover that a new CI check should exist, but that is a candidate
finding. Scout should not keep re-running a mature objective rule as if it were
judgment work.

## Slice 1 Scope

This plan is for Slice 1 / Scout MVP only. It records the full Scout subskill
map for context, but it does not plan the remaining subskills as future slices.
Deferred subskills should be tracked as backlog follow-ups instead.

The Scout subskill map currently has eleven subskills:

1. `script-lifecycle`
2. `docs-lifecycle`
3. `code-reachability`
4. `regression-coverage`
5. `protocol-drift`
6. `ops-drift`
7. `product-acceptance`
8. `model-eval-debt`
9. `security-privacy-boundary`
10. `bug-risk`
11. `maintainability-refactor`

`frontend-runtime-review` is not a separate canonical subskill in this map. It
can be considered later as a specialization of `product-acceptance` if the
product/UI review workflow needs to split.

### Slice 1: Scout MVP

In-scope subskills:

1. `script-lifecycle`
2. `code-reachability` for backend/Python only

Reason: these two cover different behavior and tool-use patterns. Script
lifecycle exercises active artifact ownership, manual entrypoints,
historical/provenance interpretation, and archive/delete/keep decisions.
Backend code reachability exercises repository search, Python static-analysis
noise, dynamic entrypoints, test-only references, public contracts, and
false-positive control. Together they should reveal whether the overlay schema,
runner, evidence loop, report structure, candidate granularity, and backlog
interaction rules are sufficient without adding the frontend/TypeScript tool
surface to the first implementation.

Slice 1 should not try to cover every Scout domain. Its acceptance should focus
on whether the Scout meta-framework works.

### Deferred Backlog Follow-Ups

Before Slice 1 closes, create or update explicit backlog follow-ups for the
remaining planned Scout subskills:

1. `docs-lifecycle`;
2. `regression-coverage`;
3. `protocol-drift`;
4. `ops-drift`;
5. `product-acceptance`;
6. `model-eval-debt`;
7. `security-privacy-boundary`;
8. `bug-risk`;
9. `maintainability-refactor`.

Also create a separate follow-up for extending `code-reachability` to
frontend/TypeScript, including Knip configuration, package/script entrypoint
handling, exported type/component interpretation, and at least one Skynet V2
frontend dry-run. This is an extension of the existing subskill, not a new
canonical Scout subskill in the v1 map.

Each follow-up should state that adding the subskill means defining overlay
fields, granularity, evidence loop, candidate/report/ignore rules, report
evidence standard, and at least one adoption run or dry-run on Skynet V2. These
are deferred backlog items, not part of the Slice 1 implementation plan.

## Subskill Design Notes

### `script-lifecycle`

Purpose: find active helper scripts whose lifecycle, ownership, maintenance
coverage, or retirement path is unclear.

The shared protocol must not assume that every repo uses a `scripts/`
directory. Concrete script roots and entrypoint sources come from the repo
overlay.

Required overlay fields:

- `script_roots`: active helper/script roots to inspect.
- `script_entrypoint_sources`: files or directories that declare active script
  entrypoints, such as CI workflows, README commands, package manifests,
  Makefiles, deploy docs, or runbooks.

Optional overlay fields:

- `known_manual_entrypoints`: scripts known to be manual entrypoints, so lack
  of CI usage alone is not suspicious.
- `historical_script_contexts`: paths whose script references are mainly
  provenance or historical context. Defaults to `repo_context.archive_paths`
  when omitted.
- `repo_notes`: repo-specific interpretation notes.

Candidate unit: one script or one coherent script group that needs one
lifecycle decision.

Combine observations when:

- a runner and helper belong to the same workflow or experiment;
- several scripts belong to one incident cleanup or one migration;
- the likely decision is shared, such as archive together, keep together, or
  replace together.

Split observations when:

- scripts have different purposes, owners, or runtime contexts;
- one issue is production/deploy safety and another is historical provenance;
- the likely next actions differ, such as adding validation for one script and
  archiving another.

Evidence loop:

1. Confirm the script or script group is under an overlay-declared active script
   root.
2. Check overlay-declared entrypoint sources.
3. Search active docs and current source-of-truth docs.
4. Distinguish active references from historical/provenance-only references.
5. Check whether CI, import smoke, syntax checks, or docs own the script.
6. Look for duplicate or superseded active paths.
7. Look for retired paths, stale commands, legacy services, or obsolete
   dependencies.
8. If evidence is still insufficient, keep the finding report-only or
   inconclusive instead of creating a candidate.

Candidate admission rule: create or refine a candidate only when all are true:

- the script is in an active script context;
- lifecycle is unclear, contradicted, or weakly maintained;
- ambiguity creates concrete maintenance, safety, provenance, or review-cost
  risk;
- the next human decision or action is clear.

Candidate-worthy patterns:

- one-off incident or experiment script still lives in an active script root;
- active manual/deploy script lacks validation or a documented contract;
- script generates important artifacts but has no drift check or validation
  path;
- script references retired paths, configs, services, or policies;
- script duplicates a superseded active path;
- historical-provenance script may need archive treatment, but direct deletion
  would harm reproducibility.

Report-only patterns:

- the script looks mildly suspicious but evidence is incomplete;
- a small local helper has a clear manual purpose and no concrete risk;
- historical references exist but current placement may still be acceptable;
- the issue is naming or comment polish rather than lifecycle ownership;
- existing backlog mostly covers the issue but not enough to justify editing it.

Ignore patterns:

- CI, README, package manifests, or runbooks clearly own the script;
- the script is a declared manual entrypoint and no concrete risk is found;
- the path is historical/archive/vendor/generated rather than active script
  context;
- an existing open or closed backlog item fully covers the lifecycle issue.

Candidate/refinement report evidence should include:

- script path or paths;
- active entrypoint evidence or lack of it;
- active-doc references or historical-only references;
- maintenance and validation evidence;
- lifecycle risk;
- recommended next decision or action.

### `docs-lifecycle`

Purpose: identify active docs that are stale, duplicative, conflicting, too
long to maintain, or occupying active-doc space without current purpose.

Likely inputs:

- `README.md`;
- `docs/CURRENT.md`;
- `docs/README.md`;
- active agent plans;
- active collaboration/protocol docs;
- dated outputs and historical docs.

Candidate-worthy examples:

- active docs disagree on current source of truth;
- dated historical docs are still treated as active instructions;
- active docs describe old runtime/deployment behavior;
- active docs are too broad or redundant and should be consolidated or archived.

### `code-reachability`

Purpose: identify code that appears dead, test-only, compatibility-only, or
misleadingly exported, while avoiding raw static-analysis noise.

Likely inputs:

- static search with `rg`;
- language-aware tools when available;
- mature dead-code or export-analysis tools configured through the repo overlay
  when they provide useful candidate pools;
- package/entrypoint declarations;
- tests and monkeypatch usage;
- docs and public contracts.

Candidate-worthy examples:

- production code is only referenced by tests;
- a compatibility shim has no current documented compatibility need;
- in the deferred frontend extension, an exported type/component is not actually
  part of a public contract;
- a helper is unreferenced and not a dynamic entrypoint.

Raw dead-code tool output is not enough by itself.

For Skynet V2 Slice 1, this subskill is backend/Python only:

- Python: use Vulture only as a noisy candidate-pool generator. Configure it
  through overlay fields such as `vulture_min_confidence`,
  `vulture_ignore_decorators`, and `vulture_ignore_names`; if Vulture requires a
  TOML config, have the runner generate a deterministic temporary adapter file
  from those fields.

Backend/Python candidate admission requires semantic confirmation after the
tool signal. A raw Vulture finding, low reference count, single reference, or
test-only reference is never enough on its own. Before proposing a candidate,
the agent must read the definition context, search production references, test
references, docs references, and config/entrypoint references, and rule out
known dynamic or framework-driven usage.

Default false-positive classes include FastAPI route handlers, Typer commands,
Pydantic models and fields, SQLAlchemy mapped fields, validators/decorated
hooks, dynamically imported modules, Alembic/migration/runtime entrypoints,
pytest fixtures/helpers, and actively documented compatibility shims. These
should be ignored or kept report-only unless additional evidence shows a real
lifecycle problem.

Only-referenced-by-tests is candidate-worthy only when the definition is under
production roots and the investigation cannot find production wiring, dynamic
entrypoint usage, or active public-contract justification. The proposed action
should ask whether to remove the code, wire or document the intended production
seam, or convert the logic into explicit test-only support. It should not simply
assert that test-only production code is dead.

A backend reachability candidate must end with a clear next human
decision/action. If the action is unclear, keep the finding report-only.

Frontend/TypeScript reachability is deferred to a separate backlog follow-up.
The likely mature tool there is Knip, but the follow-up should define package
metadata, entry/project roots, exported type/component interpretation, and known
false-positive handling before adopting it.

Do not introduce obscure or immature reachability tools in v1 just because they
promise entrypoint graph analysis. If the remaining evidence requires judgment,
Scout should do the judgment explicitly instead of hiding it inside an unstable
tool.

### `regression-coverage`

Purpose: identify meaningful regression gaps that are too contextual for raw
coverage percentage thresholds.

Likely inputs:

- test suites;
- CI workflow;
- README validation commands;
- recent plan acceptance criteria;
- runtime entrypoints;
- coverage tools if useful.

Candidate-worthy examples:

- production-critical path lacks tests and is not covered by CI smoke;
- README or closeout says a validation matters but CI does not run it;
- tests patch a seam that production does not use;
- known backlog/plan risk remains uncovered.

Raw low coverage is not enough by itself.

## Remaining Implementation Details

The core product and protocol decisions are captured above. The remaining
items are implementation details that can be finalized during the shared
`agent-protocols` PR or explicitly deferred before structured review closes:

1. Runner command interface: whether setup/check/finalize are separate commands
   or one command with subcommands, and where deterministic adapter hashes are
   recorded.
2. Markdown templates and checks: exact `SCOUT_REPORT.md` / `MANIFEST.md`
   template text and how runner checks required sections without becoming
   brittle about ordinary prose edits.
3. Backlog-maintenance examples: exact `candidate` wording, validation
   examples, and approved-refinement mechanics now that Scout owns the semantic
   proposal while backlog-maintenance owns YAML mutation.
4. Subskill document template: exact required sections for each subskill doc,
   including purpose, shared scope, overlay fields, useful tools, granularity,
   candidate/report/ignore rules, and evidence standard.
5. Candidate volume control: intentionally deferred until after the first
   dry-run report shows whether admission rules create backlog-flood risk.

The following decisions are no longer open: one YAML overlay, Slice 1
backend/Python-only `code-reachability`, first-run dry-run mode, approved
candidate writes through backlog-maintenance, and shared protocol PR before
Skynet V2 adoption.

## Acceptance Criteria

The shared `agent-protocols` PR should be accepted only if:

- `scout/SKILL.md` defines the orchestration loop, finding classes, backlog
  interaction rules, dry-run behavior, report structure, and runner boundary.
- Slice 1 subskill docs exist for `script-lifecycle` and backend/Python
  `code-reachability`, with overlay fields, evidence loops, granularity,
  candidate/report/ignore rules, and admission standards.
- `backlog-maintenance` defines `candidate` status using the normal backlog
  fields, no Scout-specific metadata, and examples for approved Scout proposal
  writes/refinements.
- The runner validates overlay schema, enabled subskills, report/manifest
  skeletons, backlog mechanics, dry-run no-backlog-write behavior, and
  deterministic generated tool adapters.
- Runner tests or equivalent validation cover overlay parsing, report skeleton
  generation, dry-run backlog protection, candidate field validation, and
  deterministic Vulture TOML adapter generation.

The Skynet V2 adoption PR should be accepted only if:

- it consumes the shared protocol through a submodule pointer update, without
  unpublished local changes under `external/agent-protocols`;
- `.agent-protocols/scout.yml` enables `script-lifecycle` and backend/Python
  `code-reachability` with the agreed Slice 1 overlay fields;
- `scripts/check_backlog.py` accepts `status: candidate` with the same fields
  as open items;
- the first Scout run produces a dry-run output directory with
  `SCOUT_REPORT.md` and `MANIFEST.md`;
- no backlog candidates are written unless the human explicitly approves
  specific report proposals;
- follow-up backlog items are created for the nine deferred Scout subskills and
  the frontend/TypeScript `code-reachability` extension.

## Proposed Implementation Scope

The implementation should include:

1. In the `agent-protocols` source repo, add shared `scout/SKILL.md`.
2. In the `agent-protocols` source repo, add internal Scout subskill docs for
   Slice 1: `script-lifecycle` and
   backend/Python `code-reachability`.
3. In the `agent-protocols` source repo, update shared
   `backlog-maintenance/SKILL.md` to define `candidate` status and lifecycle in
   simple terms.
4. In the `agent-protocols` source repo, add or update shared backlog
   validation tests if shared protocol repo schema changes.
5. In the `agent-protocols` source repo, add a lightweight Scout runner for
   config validation, report skeletons, and mechanical backlog/report checks.
6. Merge the shared `agent-protocols` PR first.
7. In Skynet V2, consume the shared change through a submodule pointer update.
8. Add Skynet V2 Scout overlay config/prose files in the adopting repo.
9. Update Skynet V2 `scripts/check_backlog.py` to allow `candidate`.
10. Produce a first Scout run report in Skynet V2 in dry-run mode.
11. After explicit human approval, optionally create or refine a small number of
    high-signal candidate backlog items from that report through
    backlog-maintenance.
12. Add explicit backlog follow-up items for the nine deferred Scout subskills
    and the frontend/TypeScript `code-reachability` extension so remaining
    planned work does not disappear after Slice 1.

PR order is a hard boundary: shared Scout behavior must land in
`agent-protocols` first. Skynet V2 adoption must consume it through a submodule
pointer update plus repo-local overlay/adoption changes. Do not merge a Skynet
V2 adoption PR while `external/agent-protocols` contains unpublished local
protocol changes.

Out of scope for first implementation:

- solving all findings discovered by Scout;
- periodic scheduling;
- converting Scout to CI;
- large-scale code or documentation cleanup;
- heavy per-finding metadata or fingerprinting;
- a separate candidate inbox outside `docs/backlog.yml`.

## Review Notes

This file is a draft implementation plan pending structured review. Before
implementation starts, the remaining implementation-detail questions above
should be resolved or explicitly deferred, and the plan should receive the
normal structured-review treatment for protocol changes.

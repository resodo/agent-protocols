---
name: backlog-maintenance
description: Use when adding, updating, closing, querying, migrating, or defining backlog items in a repo that uses docs/backlog.yml as its source of truth. This protocol keeps deferred work separate from active work, standardizes backlog IDs and lifecycle states, and defines the minimum YAML schema and CI checks agents must follow.
---

# Backlog Maintenance

Use this protocol when the user asks to:

- add or record something in backlog;
- mark a backlog item completed, cancelled, transferred, or otherwise closed;
- answer what backlog items are highest priority;
- migrate a backlog document into `docs/backlog.yml`;
- change backlog schema, allowed work kinds, or backlog maintenance rules.

This protocol does not cover active feature execution. Active work belongs in
the active plan, worktree, PR, review, and closeout. Backlog tracks deferred
work that should not be forgotten.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/backlog-maintenance.md` if present.
3. Apply local overlays as project-specific refinements only.

Overlays may define the repo's `id_prefix`, default `kinds`, CI command, or
repo-specific priority examples. They must not weaken the generic `SAFETY`
rules.

## SAFETY Rules

- Do not add active work to backlog merely because it is important. If work is
  already owned by an active plan, worktree, PR, review, or closeout, update
  that active artifact instead.
- Do not let a P0 production/data/core-alert bug remain a passive backlog note.
  Escalate it to active incident/bugfix planning unless the human explicitly
  defers it or an external blocker prevents action.
- Do not create duplicate backlog items. Search current open and closed items
  first; update an existing item when it covers the same deferred work.
- Do not encode secrets, credentials, private account details, host keys, raw
  private production data, or provider balances in backlog items.
- Do not hand-edit an active `docs/backlog.md` when the repo uses
  `docs/backlog.yml`. The YAML registry is the source of truth.

## Source Of Truth

Each adopting repo has one backlog registry:

```text
docs/backlog.yml
```

Do not generate or maintain a parallel active Markdown backlog. A repo may keep
dated historical notes, but active backlog state lives in YAML.

## Schema

Top-level shape:

```yaml
version: 1
repo: example-org/example-repo
id_prefix: EXAMPLE-BL
kinds:
  - bug
  - feature
  - ops
  - debt
  - research
  - process
items: []
```

Open item:

```yaml
items:
  - id: EXAMPLE-BL-0001
    status: open
    priority: P1
    kind: ops
    title: Full observability source-of-truth follow-up
    why: >
      Alerts now use a registry, but dashboards and scrape config may still
      define the same operational meaning in multiple places.
    next: >
      Compare dashboard panels, scrape fragments, and alert registry entries
      to find duplicated operational meanings.
    done_when: >
      Dashboards, scrape targets, alert thresholds, and shared runtime
      contracts have one documented source of truth, or remaining manual
      surfaces are explicitly justified.
    refs:
      - docs/example_plan.md
```

Open item with staged active work:

```yaml
items:
  - id: EXAMPLE-BL-0003
    status: open
    priority: P1
    kind: debt
    title: Retire legacy deployment assumptions from docs
    why: >
      Some active docs still describe an older deployment model and can mislead
      agents during production work.
    next: >
      Continue from the active documentation cleanup PR, then rescan entrypoint
      docs for stale deployment assumptions.
    done_when: >
      Active entrypoint docs describe the current deployment model, and any
      historical notes are clearly marked historical.
    active_refs:
      - docs/2026-06-03_docs_cleanup_plan.md
      - https://github.com/example-org/example-repo/pull/12
    progress:
      - 2026-06-03: README and agent entrypoint updated; runbook scan remains.
    cross_repo:
      - repo: example-org/platform-repo
        note: Update only if shared deployment runtime wording changes.
```

Candidate item:

```yaml
items:
  - id: EXAMPLE-BL-0004
    status: candidate
    priority: P2
    kind: debt
    title: Decide whether to retire stale helper scripts
    why: >
      A Scout dry-run found scripts that appear to have no active entrypoint,
      but the finding still needs human review before becoming open backlog.
    next: >
      Review the linked Scout evidence, then accept the item into open backlog,
      close it as cancelled, or leave it pending with updated rationale.
    done_when: >
      The helper scripts are either assigned active lifecycle ownership,
      removed or archived, or explicitly kept with a documented reason.
    refs:
      - docs/agent_plans/outputs/2026-06-06_scout_run/SCOUT_REPORT.md#candidate-proposal-001
```

Closed item:

```yaml
items:
  - id: EXAMPLE-BL-0002
    status: closed
    priority: P1
    kind: ops
    title: Alert-level source-of-truth migration
    resolution: completed
    closed_at: 2026-06-03
    outcome: >
      Actionable alerts now route through Prometheus/Alertmanager, and direct
      critical notification paths are forbidden by CI.
    refs:
      - docs/example_closeout.md
```

## IDs

- IDs are per-repo stable backlog identifiers.
- Format is `<id_prefix>-NNNN`, for example `EXAMPLE-BL-0001` or
  `SERVICE-BL-0007`.
- All deferred work uses the same ID sequence. Do not create separate bug,
  feature, or ops numbering.
- Never reuse an ID, even after the item closes.
- New ID = highest number in `items`, plus one.
- If work moves to another repo, close the old item with
  `resolution: transferred`; the target repo assigns its own new ID.

## Status

`status` is an item attribute, not a top-level grouping:

- `candidate`: human-unreviewed backlog proposal awaiting accept/close/pending
  review.
- `open`: deferred work still exists.
- `closed`: this backlog item is no longer open.

Do not use `in_progress` as a status. Work that is currently being carried by a
plan or PR remains `status: open` until the backlog item is fully closed. Use
optional `active_refs` and `progress` to record staged work.

Candidate items use open-style fields, but `refs` is required so the proposal
links to its review evidence. A human may later accept a candidate into
`status: open`, close it as cancelled/completed/transferred, or leave it
pending for later review. Do not add Scout-specific metadata fields such as
`scout`, `fingerprint`, `confidence`, `severity`, or `human_review`; put
evidence in the linked report.

## Priority

Priority is an item attribute used to order open work:

- `P0`: production safety, data safety, core alerting, or core runtime risk.
  P0 should usually become active work immediately.
- `P1`: important deferred work that should be scheduled, but short-term
  deferral does not immediately endanger production or core behavior.
- `P2`: cleanup, optimization, naming, static-analysis, cost, or long-term
  maintainability work.

When uncertain, do not choose P0. Use P1 and explain the risk in `why`.

## Kind

`kind` is a single-select work mode, not a tag list:

- `bug`: known behavior is wrong; next work is reproduce, fix, and verify.
- `feature`: new capability or product/user-facing improvement.
- `ops`: monitoring, alerting, deployment, backup, reliability, security
  boundary, or production operation.
- `debt`: legacy, naming, refactor, documentation slimming, or static checks.
- `research`: the answer is unknown; next work is investigation and decision.
- `process`: human/agent collaboration workflow, review, closeout, CI policy,
  protocol, or backlog maintenance itself.

If no kind fits, do not invent one casually. Treat adding a kind as a schema
change: update `kinds`, update validation, explain why existing kinds are
insufficient, and consider whether sibling repos using this protocol need the
same change.

## Closed Lifecycle

Closed items use one resolution:

- `completed`: the deferred work is done.
- `cancelled`: the work is intentionally not done, no longer relevant, or
  superseded by another approach.
- `transferred`: the work moved out of backlog tracking, such as into an active
  plan/PR or another repo's backlog.

Closed items must explain the specific outcome in `outcome` and link supporting
context in `refs`. Do not add specialized closure-specific fields; keep the
explanation in `outcome`.

## Required Fields

Open item fields:

- `id`
- `status`
- `priority`
- `kind`
- `title`
- `why`
- `next`
- `done_when`

Candidate item fields:

- `id`
- `status`
- `priority`
- `kind`
- `title`
- `why`
- `next`
- `done_when`
- `refs`

Optional open item fields:

- `refs`: list of related plans, PRs, docs, issues, or reports.
- `cross_repo`: list of `{repo, note}` objects for dependent repo pointers.
- `trigger`: plain-language condition for when to revisit the item.
- `blocked_by`: list of blockers, each as a string or `{ref, note}` object.
- `active_refs`: list of active plans, PRs, or branches currently carrying part
  of the work.
- `progress`: dated plain-language milestone strings for staged work.

Closed item fields:

- `id`
- `status`
- `priority`
- `kind`
- `title`
- `resolution`
- `closed_at`
- `outcome`
- `refs`

## Add Or Update Workflow

When the user asks to record backlog work:

1. Decide whether the work is active or deferred. Active work does not enter
   backlog.
2. Decide which repo should track the work. Default tracking repo is the
   current repo; use `cross_repo` only when another repo must know or act.
3. Search `items` for related open and closed items.
4. If a related open item exists, update it instead of adding a duplicate.
5. If no item exists, set `status: open`, choose one `priority`, choose one
   `kind`, allocate the next ID, and write `why`, `next`, and `done_when`.
6. Run the repo's backlog validation command.

## Candidate Workflow

Use `status: candidate` only when a human-unreviewed proposal should remain in
the durable backlog registry before acceptance. Scout may propose candidate
items in a run report; after explicit human approval, backlog-maintenance owns
the YAML write.

When adding an approved candidate:

1. Search existing `candidate`, `open`, and `closed` items for semantic overlap.
2. Allocate the next normal backlog ID.
3. Set `status: candidate`.
4. Choose a valid `priority` and `kind`.
5. Write concise `why`, `next`, and `done_when`.
6. Set `refs` to the evidence source, such as a Scout report anchor.
7. Run the repo's backlog validation command.

When refining an approved Scout finding into an existing candidate:

1. Confirm the existing item is still `status: candidate`.
2. Keep the existing `id`, `status`, `priority`, `kind`, and `title` unless the
   title is materially misleading.
3. Update `why`, `next`, or `done_when` only when the new evidence clarifies the
   same human decision or coherent fix.
4. Append the new Scout report anchor to `refs` instead of replacing prior
   evidence.
5. Run the repo's backlog validation command.

Do not promote, close, cancel, reopen, or delete candidates automatically.
Human review owns lifecycle transitions.

## Close Workflow

When closing a backlog item:

1. Confirm the item is actually complete, cancelled, or transferred.
2. Set `status: closed`.
3. Remove open-only fields that are no longer useful, or leave them only if
   they preserve important context.
4. Set `resolution`, `closed_at`, `outcome`, and `refs`.
5. Keep the original `id`, `kind`, `priority`, and `title` unless the title was
   materially misleading.
6. Run the repo's backlog validation command.

## Query Workflow

When answering backlog questions:

1. Read `docs/backlog.yml`.
2. For "highest priority", filter `status: open` and summarize `P0`, then
   `P1`, then `P2`.
3. For kind-specific questions, filter by `kind`.
4. Explain items in plain language using `why`, `next`, and `done_when`.
5. Do not require the human to read YAML unless they ask for raw entries.

## CI Expectations

Repos adopting this protocol should run a backlog check in CI. Hard checks:

- YAML parses.
- top-level `version`, `repo`, `id_prefix`, `kinds`, and `items` exist.
- every ID matches `id_prefix` and is unique across `items`.
- every item has `status`, `priority`, `kind`, `title`, and `id`.
- `status` is `candidate`, `open`, or `closed`.
- `priority` is `P0`, `P1`, or `P2`.
- open items have required open fields.
- candidate items have required candidate fields, including `refs`.
- closed items have required closed fields.
- `kind` is in `kinds`.
- `resolution` is one of `completed`, `cancelled`, or `transferred`.
- `closed_at` is an ISO date (`YYYY-MM-DD`).
- no active `docs/backlog.md` exists.

Semantic quality remains review-owned, not CI-owned: priority choice, kind
choice, and whether `why`/`next`/`done_when` are useful require human or
structured review judgment.

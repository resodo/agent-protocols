# Docs

This folder contains repo-facing documentation for the shared agent protocols.

Agents should enter through root `AGENTS.md`, then use this file for document
placement and naming.

## Structure

- `CURRENT.md` - active source-of-truth map for protocol entrypoints, indexes,
  and current maintenance notes.
- `agent_plans/` - dated plans, review-thread artifacts, implementation
  records, and closeout evidence for protocol changes.
- `backlog.yml` - this repo's protocol-development backlog. Use
  `backlog-maintenance/SKILL.md` before adding, updating, closing, or querying
  items.

Protocol packages live at the repo root, such as `structured-review/` and
`closeout/`. Those directories should contain executable or reusable protocol
material, not dated worktree artifacts.

## Naming

Use a date prefix for plans, reviews, reports, and execution records:

```text
YYYY-MM-DD_topic.md
```

Exceptions:

- `README.md`;
- `CURRENT.md`;
- `backlog.yml`;
- long-lived protocol files such as `SKILL.md`, `references/*.md`, templates,
  scripts, and tests.

## Lifecycle

Docs may be current instructions, historical provenance, or execution
artifacts. Use explicit status notes instead of relying on file age.

- `active` - current source of truth or current implementation driver.
- `historical` - completed provenance record; do not use as active instruction
  unless a current index points to it.
- `artifact` - execution evidence such as review threads, closeout reports, or
  validation records.

Dated plans moved into `agent_plans/` are historical records. Do not rewrite
old reviewer or driver thread text just to modernize paths after a later file
move; update live indexes and protocol references instead.

## Maintenance

When protocols are added, renamed, retired, or moved, update:

- root `README.md`;
- root `AGENTS.md` if agent routing changes;
- `docs/CURRENT.md`;
- this file when placement or lifecycle rules change;
- `docs/agent_plans/README.md` when plan/artifact handling changes;
- `docs/backlog.yml` when backlog ownership changes.

These index checks are part of closeout documentation consistency.

# Protocol Backlog

## Purpose

Track follow-up work for this repo's shared protocols without bloating
`SKILL.md` files.

`SKILL.md` should stay focused on current stable protocol behavior. This
backlog captures work that is real, agreed, and not yet fully designed.

This is not an adopting-repo `docs/backlog.yml` registry. Do not migrate it to
YAML unless a future accepted plan explicitly adopts that workflow for this
repo.

## Open items

### 1. Self-evolution protocol

Define:
- when a missed review gap should be written down
- who writes it
- where it is stored
- when a lesson stays in a log vs gets promoted into `SKILL.md`

### 2. Global canonical source

Decide:
- where the canonical global `structured-review` project should live
- how Codex and Claude should read the same source
- whether wrappers, symlinks, or copy-sync are needed

### 3. Agent-specific wrappers

After the canonical source is stable, decide:
- Codex global skill wrapper shape
- Claude global skill / command wrapper shape
- how much wrapper text is needed vs direct file reading

### 4. Real-plan dogfooding

Run the protocol on real artifacts and record friction points without adding project-specific details to this public backlog.

### 5. Optional examples and evolution logs

The `references/` directory now contains required protocol references loaded by
the Claude runner. If v1 usage proves they are needed, add optional files for:

- evolution logs;
- examples;
- unusual review cases that should not bloat `SKILL.md`.

Do not create a second general checklist that duplicates
`references/review-lenses.md`.

## Rule for this backlog

Only add items that are:
- clearly real
- not yet fully designed
- better tracked outside `SKILL.md`

Do not turn this file into a long incident log.

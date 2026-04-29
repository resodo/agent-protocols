# structured-review backlog

## Purpose

Track follow-up work for the `structured-review` protocol without bloating `SKILL.md`.

`SKILL.md` should stay focused on the current stable v1 protocol.
This backlog captures work that is real, agreed, and not yet fully designed.

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

### 5. Optional references

If v1 usage proves they are needed, add:
- `references/evolution-log.md`
- `references/review-checklist.md`
- `references/examples.md`

## Rule for this backlog

Only add items that are:
- clearly real
- not yet fully designed
- better tracked outside `SKILL.md`

Do not turn this file into a long incident log.

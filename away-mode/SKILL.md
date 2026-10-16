---
name: away-mode
description: "[master] A master procedure (role: agents/master.md). Use when the human says they are leaving, going to sleep or going offline, and again when they return. Collect pre-authorizations before they go, keep lines moving within standing grants and those pre-authorizations while they are away, and hand over a per-change ledger when they are back."
---

# Away Mode

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/away-mode.md` if present: the categories used in the
   per-change ledger, any project rule for unattended operation.

## Before The Human Leaves

List the gated steps likely to come up while they are away (a release whose
preconditions will be met later, a ramp step, a paid run, a cleanup). For each,
write a pre-authorization with `templates/preauthorization.md`:

- trigger: the exact condition that must hold;
- action: what will be done, with which command and receipt;
- failure handling: roll back if possible; a small clear bug goes through PR,
  review and CI and is retried; anything unclear stops;
- budget cap;
- expiry: when the pre-authorization lapses unused.

Send them in one message, one line each, so the human can approve them all at
once or strike some. Record the answer in the project ledger as dated
temporary entries, and copy the active ones into the session handoff file.

## While Away

- Do only what standing grants and the approved pre-authorizations cover.
  Everything else that needs the human goes into the queue; other lines keep
  moving.
- Keep a per-change ledger as changes happen, not at the end.
- Expired pre-authorizations are not used.

## When The Human Returns

Deliver the per-change ledger before anything else: for every change, why,
how, how to undo it, a self-review (too large? a mechanism added for a small
problem?), and its category. It stays in the queue until the human has read
it. Then the normal report.

## SAFETY Rules

- A pre-authorization never covers a step it does not name.
- Never stretch a pre-authorization past its expiry or budget.

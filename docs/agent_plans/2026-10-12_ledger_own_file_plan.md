# Plan: the authority ledger gets its own master-only file

Document level: plan (one PR in agent-protocols; a follow-up PR in each
consumer that embeds the core).

Decision source: per master relay (2026-10-12), pending record by the master
session. A work-line agent reported that following `decision-boundary` made it
read `.agent-protocols/decision-boundary.md`, which also holds the authority
ledger, so it read the whole ledger; that contradicts "only the master reads
the ledger".

## Change

- The ledger moves to `.agent-protocols/authority-ledger.md`, read only by the
  master (plus the single cited entry under Delegated Execution).
  `.agent-protocols/decision-boundary.md` keeps what every role should read:
  the project's gate checks and the settled-decision list.
- `decision-boundary/CORE.md`: the ledger path in "The rule" becomes
  `.agent-protocols/authority-ledger.md`. Consumers copy the changed core in
  their bump PR (the guard enforces it).
- `decision-boundary/SKILL.md` Local Overlay: step 2 reads
  `decision-boundary.md` (all roles: gate checks, settled decisions); step 3,
  master only, reads `authority-ledger.md`. Every other mention of the ledger
  path in this protocol uses the new file.
- `closeout/SKILL.md`, `planning/SKILL.md`, `structured-review/SKILL.md`: the
  ledger path changes to `.agent-protocols/authority-ledger.md`.
- `line-worker` needs no change: it never points at the ledger; it reads
  `context.md` and `line-worker.md`, and the core.

No new mechanism; the guard and its check script are unchanged (they compare
the core block, whose text changes).

## Validation

- `python -m unittest discover tests`.
- `grep -rn "decision-boundary.md"` outside `docs/agent_plans` shows only the
  gate-check overlay meaning; the ledger is referenced only as
  `authority-ledger.md`.
- Consumer (skynet-intern) follow-up: move the ledger sections into
  `.agent-protocols/authority-ledger.md`, update references in its overlays
  and `AGENTS.md`, copy the new core; guard passes.

## Review Threads

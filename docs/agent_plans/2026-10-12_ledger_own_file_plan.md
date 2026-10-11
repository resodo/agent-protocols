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
- Read-only role-boundary inspection in the consumer (no new script):
  1. the shared `decision-boundary.md` contains only gate checks and settled
     decisions (grep for ledger entry ids `L1`..`L13` and "Authority Ledger"
     finds nothing);
  2. trace what a work line loads: start a dispatched-worker session in the
     consumer (Claude, with its normal settings and the `line-worker`
     preload) on a small read-only task that touches a gate, and check its
     tool-call trace: it may read `decision-boundary.md`, it must not read
     `authority-ledger.md`;
  3. trace a delegated merge-agent session given a queue line that cites
     `L1`: its trace shows a read of `authority-ledger.md` right before the
     (dry, no-push) merge step, and its answer quotes only L1.
  Results are recorded in the consumer PR.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

**Blocking issues**

**Thread 1 — Validation does not yet prove the role boundary.** The reported problem is that a work-line agent read the whole authority ledger while following `decision-boundary`. The plan covers every explicit old ledger-path reference I found in the active protocols, but its proposed tests, grep, and core guard would not show whether a non-master role still loads ledger content through a consumer’s `AGENTS.md`, context, or overlays. Add a read-only inspection scenario for each affected consumer: confirm the shared `decision-boundary.md` contains only gate checks and settled decisions; trace what a work-line agent loads; and confirm a delegated agent re-reads only its cited entry immediately before acting. This needs no new script.

**Non-blocking issues**

None.

**Overall judgment**

The file split and protocol edits are concrete and preserve Delegated Execution’s single-entry rule. The plan is ready for implementation once validation covers the behavior it is meant to fix.

**Residual risks or validation gaps**

The consumer checks will occur in the follow-up PRs. No tests were run during this read-only plan review.

### Driver response to pass 1

- Thread 1, accepted. Validation adds a read-only role-boundary inspection in
  the consumer: grep that the shared file has no ledger content; a traced
  worker session that must not read the ledger file; a traced delegated
  merge-agent session that re-reads only the cited entry. No script added.

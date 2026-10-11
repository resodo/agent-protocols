# Plan: delegated agents look up one ledger row, not the file

Document level: plan (one PR in agent-protocols).

Decision source: consumer validation of #43 (skynet-intern, 2026-10-12). A
traced delegated merge-agent session, preloaded with `merge-queue`, opened
the whole `.agent-protocols/authority-ledger.md` to re-check L1, because
`merge-queue`, `release`, `closeout` and the core say "re-read that entry"
while only `decision-boundary` says how (a line-level lookup).

## Change (text only)

Use the same wording everywhere a delegated agent checks its cited entry:
"look up only that entry: a line-level search for its id (the row starting
with `| L1 |`) in `.agent-protocols/authority-ledger.md`; never open the whole
file". Files: `merge-queue/SKILL.md`, `release/SKILL.md`, `closeout/SKILL.md`,
`decision-boundary/CORE.md` (the dispatched-agent bullet).

## Validation

Unit tests; then in skynet-intern rerun the traced delegated merge-agent
session: exactly one lookup in the ledger file, a line-level search whose
result is only the L1 row.

## Review Threads

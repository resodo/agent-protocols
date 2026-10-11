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

### Reviewer pass 1 (impl, codex reviewer)

The human’s concern is that a delegated agent opened the whole authority ledger when it needed to check only its cited row. I inspected the plan, all four changed files, and `decision-boundary/SKILL.md`’s Delegated Execution rule.

#### Blocking issues

**Thread B1 — Preserve the active-status check in the resident core.** `decision-boundary/CORE.md:19` now permits a line-level lookup right before acting, but the edit removed its instruction to check that the entry is still active. Delegated Execution requires the agent to stop when the entry is inactive or no longer covers the action. State both checks in the core bullet.

**Thread B2 — Make `L1` clearly an example.** `merge-queue/SKILL.md:32` says to search for the cited ID, then identifies the row as `| L1 |` without “for example.” A queue line citing another ID could be read as an instruction to search for L1. Use the cited ID as the rule and label L1 as an example, as `decision-boundary/SKILL.md` does.

**Thread B3 — Record the planned validation outcome.** The plan calls for unit tests and a traced delegated merge-agent rerun showing one line-level lookup returning only the L1 row. The reviewed artifact records neither result. Provide that candidate-bound evidence, or record the validation as incomplete with an owner and next action.

#### Non-blocking issues

The plan and implementation being in one commit does **not** itself block this small text change. There was no separately accepted plan; I used the committed plan as the acceptance list. The four files received the intended text edits, with B1 and B2 leaving two of them partial. I found no new mechanism.

#### Overall judgment

The wording is not yet ready for closeout. Resolve B1 and B2, then establish the validation result in B3.

#### Residual risks and validation gaps

Direct inspection confirms that the edits direct agents toward a line-level lookup. It cannot establish whether a delegated merge agent follows that instruction in the traced scenario; that result remains unverified in the review record.

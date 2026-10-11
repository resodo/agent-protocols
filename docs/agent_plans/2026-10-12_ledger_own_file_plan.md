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
- Delegated Execution in `decision-boundary/SKILL.md`: the re-read is a
  line-level lookup of the cited entry id in `authority-ledger.md` (for
  example a search for the row that starts with `| L1 |`), not a read of the
  whole file.
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
  1. static: the shared `decision-boundary.md`, `AGENTS.md` (core block and
     other text), `context.md`, the `line-worker` overlay, the role wrappers
     and the SubagentStart hook text contain no ledger content (grep for
     entry ids `| L1 |`..`| L13 |`, "Authority Ledger", and verbatim grant
     quotes finds nothing);
  2. traced worker: a dispatched-worker session in the consumer (normal
     settings, `line-worker` preloaded) on a small read-only task that touches
     a gate; its trace shows at least one known file read (the trace captures
     reads) and no read or search of `authority-ledger.md`;
  3. traced delegated merge agent: given a queue line citing `L1`, its trace
     shows exactly one lookup in `authority-ledger.md`, a line-level search
     for `| L1 |`, and the tool result returned only that row.
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

### Reviewer pass 2 (impl-plan, codex reviewer)

**Blocking issues**

**Thread 1 remains open — the validation does not yet prove the role boundary.** The original concern is that a work-line agent saw the whole authority ledger. A tool-call trace showing no read of `authority-ledger.md` cannot rule out ledger content supplied through `AGENTS.md`, context, or a preload. Inspect those startup materials as well as the trace, and show that the trace captures at least one known file read. For the delegated agent, an answer quoting only L1 does not show that it read only L1; verify the content returned by the file-read call. These checks need no new script.

**Non-blocking issues**

None.

**Overall judgment**

The revised plan improves validation, but Thread 1 remains blocking. It is not yet ready for implementation.

**Residual risks or validation gaps**

The consumer checks remain planned for the follow-up PR. No tests were run during this read-only plan review.

### Driver response to pass 2

- Thread 1, accepted. Static inspection now covers every startup material
  (AGENTS.md, context, line-worker overlay, wrappers, hook text); the worker
  trace must show at least one known read; the delegated re-read becomes a
  line-level lookup of the cited entry (protocol text changes accordingly),
  and the check verifies the tool result contained only that row.

### Reviewer pass 3 (impl-plan, codex reviewer)

**Blocking issues**

None. Thread 1 is resolved. The revised plan checks startup materials for ledger content, confirms the worker trace captures file reads, and verifies that the delegated lookup returns only the cited row.

**Non-blocking issues**

None.

**Overall judgment**

The plan is ready for implementation.

**Residual risks or validation gaps**

The role-boundary checks remain planned for the consumer PR. No tests were run during this read-only plan review.

### Reviewer pass 1 (impl, codex reviewer)

**Blocking issues**

None.

**Non-blocking issues**

None.

**Overall judgment**

The original concern was that a work-line agent could read the whole authority ledger while loading the shared decision-boundary overlay. The implementation matches the accepted plan:

- **Done:** All tracked ledger-path references point to `.agent-protocols/authority-ledger.md`. The sole remaining `decision-boundary.md` reference identifies the shared gate-check and settled-decision overlay.
- **Done:** Local Overlay gives every role the shared overlay and reserves the ledger file for the master, subject to the cited-entry exception.
- **Done:** Delegated Execution specifies a line-level lookup of the cited entry.
- **Done:** `CORE.md` changes only the ledger path. The diff adds no mechanism.

Direct inspection supports readiness for closeout of this repository’s implementation.

**Residual risks or validation gaps**

I did not run the test suite: it invokes a protocol guard script, which this review was instructed not to run. Consumer startup and agent-trace checks remain for the consumer PR, as the plan specifies.

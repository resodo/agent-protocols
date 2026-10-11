<!-- agent-protocols:decision-boundary-core v1 (source: external/agent-protocols/decision-boundary/CORE.md; keep verbatim) -->
## Decision boundary (resident core)

- **Your role.** Master: the human named you master in this session. Direct session: the human gave you a task without naming you master. Dispatched agent: another agent started you. Act within your role.
- **The rule.** Gates decide whether a step needs the human. The project's authority ledger (`.agent-protocols/decision-boundary.md`) lists the gated steps the human has handed to the master. Only the master reads the ledger.
- **Gates.** Does this step:
  - G1 become impossible to undo losslessly within minutes (deleting data, irreversible migrations, messages sent)?
  - G2 spend money beyond an approved budget, or open a new paid channel?
  - G3 speak for the human or the team to an outside party (tickets, quota requests, forms, email, other teams)? Approving the action is not approving the wording.
  - G4 change a contract's shape (API endpoint or field, schema/DDL, cross-repo interface, shared infrastructure)?
  - G5 move which layer is responsible for what?
  - G6 change what users see or what the product means?
  - G7 add a standing mechanism (alert, counter, registry, config field, guard, approval step)?
  - G8 touch permissions, credentials or security, or work around a denial?
  - G9 contradict a decision the human already made?
  - G10 set or change an observation window, its criteria, a rollback condition, or the rollout pace?
- **Master.** A gated step the ledger does not cover: ask the human, one question at a time, with a recommendation. Anything else: decide, keep a receipt and a way to undo, and report it afterwards.
- **Direct session.** A gated step: ask the human. Never use the ledger.
- **Dispatched agent.** Any gate, growing scope, a cause outside your scope, a conflict with an earlier decision, or anything that needs the human: stop and report to whoever dispatched you. Never contact the human, never consult the ledger, never record a human approval yourself.
- **Never ask, when no gate is hit:** read-only investigation (just do it); anything already answered (search the record first and cite it); hypothetical contingencies; implementation detail.
- **Permission denied:** stop and report. Never try another route to the same thing.
- **More:** examples, the grey zone, the escalation format and the ledger rules are in the `decision-boundary` protocol.
<!-- /agent-protocols:decision-boundary-core -->

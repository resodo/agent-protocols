# Role: master

The single definition of the master. Other protocols point here; none of them
defines the master again.

- **Who.** The session the human named master in this session. A session that
  was not named master in this session is not the master, even if an earlier
  session was. There is one master per project at a time.
- **Owns.** The board, the queue of items waiting on the human and the
  settled-decisions list (it is their only writer); dispatching and watching
  every line; merge and release permission and their delegation
  (`decision-boundary`, Delegated Execution); the go or no-go at every point of
  no return; all conversation with the human.
- **May decide.** Steps that hit no gate, gated steps the project ledger hands
  to it, and the defaults in `decision-boundary` ("What The Master Decides By
  Default"). Its authority over project governance (for example approving a
  pipeline's proposals) comes only from ledger grants; without a grant it is
  not a governance layer.
- **Coordinates, does not implement lines.** It decides, dispatches, merges and
  releases or delegates them, and does small checks and fixes itself. Every
  implementation line goes to a worker, so the sweep keeps every line moving
  while the human is away.
- **Stops at.** A gated step the ledger does not cover: ask the human
  (`decision-boundary`, Escalation Format). A denial: stop and report it.
- **Reports to.** The human, in the shape the human's master preferences give.
- **Preloads.** `decision-boundary`, `master-board`, `dispatch`,
  `session-handoff`, `away-mode`, their project overlays, the project ledger,
  and the human's master-preferences file named in the user-level
  instructions (read only by the master).

## Taking over

When the human names a new master, the earlier master session stops
coordinating from that turn: it starts nothing new, takes no gated step, and
writes its open items into the handoff file (`session-handoff`). The new master
runs the cold start; running agents report to it once it has re-dispatched or
parked them.

## Shared state

The master alone writes the board, the queue and the settled list. Each line
writes only its own status file. Production operators, coordinators and other
lines report results to the master, which updates the board. Who may type a
ledger entry: `decision-boundary`, Authority Ledger.

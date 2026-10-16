# Roles

Every agent has two roles at once:

- an **authority role**, which sets what it may decide and whom it asks at a
  gate: master, direct session, or dispatched agent (resident core in
  `decision-boundary/CORE.md`; long form in `decision-boundary`);
- a **task role**, which sets its work and its output: one of the files below.

Author, driver and reviewer are responsibilities for one artifact
(`structured-review`, `closeout`). Any role can hold them and they grant
nothing.

| Role | Authority role | Reports to | File |
|---|---|---|---|
| master | master | the human | `master.md` |
| direct session | direct session | the human | resident core only |
| coordinator | dispatched agent | the master | this file, "Coordinator" |
| line worker | dispatched agent | whoever dispatched it | `line-worker.md` |
| researcher | dispatched agent | whoever dispatched it | `researcher.md` |
| merge agent | dispatched agent | the master | `merge-queue.md` |
| production operator | dispatched agent | the master (check results to a coordinator that dispatched the checks) | `release.md` |
| visual QA | dispatched agent | whoever dispatched it | `visual-qa.md` |

Each role file states who the role is, what it owns, what it may decide,
where it stops, whom it reports to, and what it preloads.

## Coordinator

A dispatched agent that runs one multi-PR program for the master and may
dispatch its own workers (`dispatch`).

- Owns: the program's plan, its workers and their briefs, the program's
  go/no-go checklist.
- May decide: engineering choices inside the program, which worker does what.
- Stops at: every gate. It never grants or widens a gate for its workers. A
  point of no return, a switch, a merge, or any step the ledger covers is
  asked of the master as a message, and counts only after the master answers;
  without an answer it re-sends and never waits silently (`dispatch`).
- Cannot pass on a delegated execution it received; the master delegates
  each gated action to the agent that performs it.
- Reports to: the master. Its workers report to it, never to the master or
  the human directly. The one exception: a production operator always reports
  to the master and sends only the results of checks the coordinator
  dispatched to the coordinator as well.
- Preloads: `line-worker`, `dispatch`.

## Wrappers

A consumer repo adds a thin wrapper per coding agent that points here (see
`agent-readiness/capabilities.md`, "role definition"):

- Claude Code: `.claude/agents/<name>.md` with `skills:` listing the preloaded
  protocols and a body that says "follow external/agent-protocols/agents/<name>.md".
- Codex: `.codex/agents/<name>.toml` with `developer_instructions` saying the same.
- Grok Build: `.grok/roles/<name>.toml` with `prompt_file` pointing at
  `external/agent-protocols/agents/<name>.md`.

When a coding agent has no role definitions, paste the role text into the
dispatch brief. The master is a session role and needs no wrapper.

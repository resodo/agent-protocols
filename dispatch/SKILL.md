---
name: dispatch
description: "[master, coordinator] A master procedure (role: agents/master.md); a coordinator (agents/README.md) uses it for its own workers. Use when about to spawn a subagent, when an agent notification arrives, when an agent stalls or reports a denial, and when resuming an old plan or PR. Covers the dispatch brief, choosing a model tier, watchdogs and nudges, returned work, relaying human decisions, and keeping every line moving."
---

# Dispatch

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/dispatch.md` if present (project briefing extras,
   concurrency limits that are project-specific).

Model names, cost limits and concurrency caps that follow the human's
subscription live in the user-level instruction file.

Capabilities used (see `agent-readiness/capabilities.md` for each coding
agent's feature or fallback): spawn subagent, role definition, message a
running agent, watchdog, subagent-start injection.

## Before Dispatching

- Search the record for decisions that touch the task; put them in the brief
  with sources.
- Resuming an old plan, parked line or old PR: first write "premise then vs
  state now". If the premise changed, bring the difference back to the human
  instead of executing the old plan.
- Decide parallel or serial: parallel only when files and deploy surfaces do
  not overlap or the work is read-only; anything touching a shared surface
  merges in order.
- Pick the role definition from `agents/` if one fits (worker, researcher,
  merge, release, visual QA).

## The Brief

Use `templates/brief.md`. It always contains: the objective, the output
format, the sources and tools to use, the boundaries, the decisions already
made (with sources), how to report back, and "if a permission is denied, stop
and report; never work around it". State in one line which parts are the
human's decisions and which are your engineering elaboration (the agent may
challenge the latter with evidence).

## Model Tier

Ask "what is the hardest judgement in this task?". Any real judgement (design,
attribution, resolving conflicts, deciding whether something can merge,
verifying identities) -> the strong tier. Only mechanical execution under a
written procedure (collect receipts, run a checklist, update status) -> the
cheap tier. Pass the rule and the cost facts to the agent. An agent that
dispatches its own workers is a coordinator (`agents/README.md`): it follows
this protocol for them, stays inside its own brief, and cannot pass a gated
permission on. Concrete model names are in the user-level
file.

## After Dispatching

- In the same turn, start a watchdog (`references/watchdog.md`).
- Record the line on the board with a link to its `STATUS.md`.
- A verbal "someone will do it in parallel" becomes a tracked task now, or it
  does not exist.
- A discovered improvement to a design or plan is written into that document
  now, by a cheap agent if needed, with its date and source.

## When An Agent Reports

- Done: read its result against the brief before relaying; check claims that
  matter (PR exists, tests ran, files changed). Relay to the human in the
  human's language.
- Denied: do not do the denied thing yourself; tell the human that it was
  denied and what was attempted.
- Returned work (failed review, failed merge): send it back to the author line
  with the reason; the reviewer or merger does not fix business code.
- Tail work (post-merge cleanup, CI babysitting, doc sync) goes to a
  cheap-tier agent so the master stays on the main line.

## Keeping Lines Moving

Every approval gets its next step dispatched in the same turn. A line that
stops is either moved forward or written down with the real blocker, who owns
it, and the condition that restarts it. A blocker that is the human's decision
is stated as such in the queue.

## Relaying To The Human

Text meant for the human to copy to someone else goes between clear separator
lines. Outside the separators, talk to the human.

## SAFETY Rules

- Do not give a dispatched agent production access, merge rights or CI
  triggers unless its role definition says so.
- Do not ask an agent to record a human approval; an agent may type a
  `proposed` ledger entry that you then check (`decision-boundary`, Authority
  Ledger).
- Do not let a dispatched agent talk to the human directly.

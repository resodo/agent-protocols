---
name: session-handoff
description: "[master] A master procedure (role: agents/master.md). Use when this session is about to end or its context is nearly full, and at the start of a new session in which the human named you master (cold start). Write a one-page handoff of what dies with the session; on cold start, load the state, verify it live, and re-dispatch or park every line."
---

# Session Handoff

Timers and in-session promises die with the session; subagents may or may
not (the cold start checks). The board, the queue and line STATUS files
survive. The handoff file carries only what would otherwise be lost.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/session-handoff.md` if present: where the state
   files live.

## Writing The Handoff

Write the handoff file in the state directory from `templates/SESSION_HANDOFF.md`
(one page; overwrite the previous handoff, do not append history):

- lines that were running: worktree or branch, STATUS path, where it stopped,
  next step, model tier;
- promises made to the human that are not yet kept;
- active pre-authorizations (trigger, action, failure handling, budget,
  expiry);
- timers and observation windows with their due times;
- production actions in flight: locks, commands, receipt ids;
- lessons learned this session that are not yet in a protocol, overlay or
  ledger, with a proposed home.

Write it whenever the context is getting full, not only at the very end.

## Cold Start (new master)

1. Confirm the human named you master in this session (`agents/master.md`).
   If not, you are not. From this turn the earlier master session stops
   coordinating.
2. Load `decision-boundary`, `master-board`, `dispatch` (re-dispatching lines
   follows it; model tiers are in the human's master preferences), this
   protocol, and their overlays.
3. Read the handoff file, then the board, then the queue.
4. Verify live state instead of trusting files: open PRs and the merge queue,
   one production line (read-only), each line's worktree and STATUS, and
   whether the earlier master session and its agents are still running. A
   line whose agent is confirmed stopped is re-dispatched or parked with a
   trigger. A line whose agent still runs, or whose state you cannot tell, is
   parked: never start a second agent on it. Take it over only once the agent
   can be reached through a documented route (the "message a running agent"
   capability from a session that owns it, or the earlier master session
   relaying) and acknowledges the handoff. Gated delegations are re-issued
   only after this check: for a stopped line when it is re-dispatched, for a
   live line after its agent acknowledged the handoff.
5. Before resuming any old plan, write "premise then vs state now".
6. Start the scheduled sweep now, in this turn, with the "scheduled sweep"
   capability (see the capability map; for example a 30-minute timer that runs
   the `master-board` sweep). This step is not optional: if the capability is
   missing in this session, say so in the first report and use the fallback.
   Then run the daily actions.
7. First report: the human's report format, what is waiting on him, and what
   happened to each line (re-dispatched, parked with trigger, done).

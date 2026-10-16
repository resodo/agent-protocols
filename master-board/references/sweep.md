# Sweep

A sweep checks every line for anything that is not moving, whoever's fault it
is. Check live state; do not answer from files alone.

Start from the list of agents running now (the "spawn subagent" capability's
listing), not from the PR list. Write one line per work line: running,
waiting until a stated time, waiting on which PR or question, or idle with
work available; dispatch every idle line that has work. A round that dispatches
nothing can say why each idle line truly has nothing to do.

For each item found, say why it is stuck and what unblocks it, then act:
dispatch, nudge, fix, park with a trigger, or add to the queue. Any stated
estimate (a merge, a check, a reply) that has passed is chased now.

1. Every work line on the board: is someone working on it now? If not, is the
   reason written down with a trigger? An approved plan that nobody started
   is stuck.
2. Every running agent: did its output grow since the last sweep? A silent
   agent gets the nudge in `dispatch/references/watchdog.md`.
3. Open pull requests: red checks, conflicts, a stale base, drafts nobody owns,
   PRs opened by other sessions that are not in the merge queue.
4. Runs and jobs: failed or partly failed runs, retries that never happened.
5. Self-imposed waits: observation windows or "wait until tomorrow" that block
   a dependent although the short check already passed.
6. Designs or follow-ups that were promised but nobody is drafting; verbal
   delegations ("X will do it in parallel") that never became a task.
7. Everything waiting on the human: is it in the queue, with its trigger?
8. Commitments made to the human ("I will tell you in the morning", "after
   the screenshot") that are due.
9. Parked or suspended items from earlier sessions (board, handoff file,
   project overlay) whose trigger has fired.
10. Project-specific daily actions from the overlay.

When the scheduled sweep finds nothing, it says nothing to the human.

# Watchdog

Notifications arrive only when an agent stops on purpose. An agent that was
killed, waits on something that never fires, or thinks silently sends nothing.

- Start a watchdog in the same turn as the dispatch. Watch whether the agent's
  output (transcript or log file) grows; never read its content for this.
- No growth for about 15 minutes: nudge it. Wording: "Check the next
  precondition yourself and continue; do not wait for a notification. If you
  are blocked from outside, report the exact blocker."
- Before nudging, check whether it is waiting on a long external job (a review
  runner, a CI run) whose own output is growing; then leave it.
- Emit events only when the state flips (stalled / recovered), not every tick.
- Stop the watchdog when the agent finishes; kill an old watchdog before
  starting a new one for the same purpose.
- A crashed agent can often be resumed from its transcript with a message
  (see the "message a running agent" capability).

---
name: master-board
description: "[master] A master procedure (role: agents/master.md). Use when state changes and must be recorded, when the human asks for progress or what is stuck or what can still move, when the scheduled sweep fires, and before any status report. Keeps the board (current lines, settled decisions, production line) and the queue of items waiting on the human, and runs the full sweep."
---

# Master Board

The master keeps two local markdown files. They are the source of truth for
"where is everything"; any delivery page is a copy (see
`agent-readiness/capabilities.md`).

- **Board** (`templates/BOARD.md`): the goal, the route, one table of current
  work lines, settled decisions (newest first), one production line.
- **Queue** (`templates/QUEUE.md`): only items waiting on the human. Each item
  says what he must decide and what triggers it.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/master-board.md` if present: file locations, daily
   fixed actions, project items every report must carry.

## Keeping The Files

- Update the board when something changes, in the same turn, not at the end of
  the session.
- The queue holds only open items. When the human answers, move the answer to
  the board's settled list in the same turn (date, his words, scope) and
  delete the queue item. If the answer grants authority, record it in the
  project ledger (`decision-boundary`).
- The board has one current table of lines. When a table is replaced, move the
  old one to an archive file next to the board; do not stack tables.
- Line status lives in each line's `STATUS.md` (`line-worker` template); the
  board links to it and carries one line per work line.
- Size rule: if the queue no longer fits on one screen or the board's current
  section no longer fits on two, archive before adding.
- Record rejections as carefully as approvals.

## Reports

Every reply to the human ends with what is waiting on him, or says plainly
that nothing is. The full report shape (sections, language) comes from the
human's user-level instructions; the project overlay may add required items.
Before saying anything is done or ready, check it (PR title and acceptance
section, CI in full, the actual state), and list what was not verified.

## Sweep

A master session keeps a scheduled sweep running from its first turn (see the
"scheduled sweep" capability; timers that expire are restarted). Run
`references/sweep.md` when the scheduled sweep fires, when the human asks what is stuck or what can move, and
before the first report of a session. Answer from the sweep, never from the
queue file alone.

## SAFETY Rules

- Do not report from memory or from the queue alone; check the live state.
- Do not leave an answered item in the queue or an unanswered one out of it.
- Do not put secrets or private production data in these files.

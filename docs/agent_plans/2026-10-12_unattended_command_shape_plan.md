# Plan: command shapes that do not stall unattended sessions

Document level: plan (one PR in agent-protocols).

Decision source: per master relay (2026-10-12), pending record by the master
session. The human reported that a memory-cleanup command raised the platform
confirmation "Dangerous rm on possibly-empty variable"; a prompt like that
stalls a session while he is away.

## Change

Add one rule to `line-worker` ("While Working") and one line to `dispatch`
("The Brief" hard rules template):

- Write commands so they never need a platform confirmation: delete only by
  literal path or with guarded expansions (`"${dir:?}"/"${name:?}"`), never a
  bare variable in `rm`; one command does one thing; for many deletions, a
  script that lists literal paths. If a confirmation prompt appears anyway,
  stop and report the command instead of retrying variants.

No new mechanism; text only. The capability map is unchanged.

## Validation

`python -m unittest discover tests` passes; grep shows the rule in both files.

## Review Threads

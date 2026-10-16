# Plan: line STATUS records the agent, its model tier and its dispatcher

Document level: plan (one small PR).

Source: the cold-start exercise after the restructure (2026-10-17) found that
a new master could not re-dispatch lines at the right tier because no STATUS
file recorded it; the master approved adding the field (per master relay,
2026-10-17).

## Scope

- `line-worker/templates/STATUS.md`: one header line, "Agent: <id> - model
  tier: <strong | cheap> (<model name>) - dispatched by: <master |
  coordinator NAME>".
- `line-worker/SKILL.md` STATUS.md section names the three fields and why.

## Validation

- `python -m unittest discover -s tests`.
- Reading check: `session-handoff` cold start step 4 (each line's STATUS) can
  now pick the tier from the STATUS file.

## Review Threads

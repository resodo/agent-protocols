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

### Reviewer pass 1 (impl, codex reviewer)

The concern was that a new master needs each line’s model tier to re-dispatch it correctly after a cold start.

**Blocking issues:** None.

**Non-blocking issues:** None.

**Overall judgment:** Ready for closeout. The plan’s two implementation items are done: `line-worker/templates/STATUS.md` records the agent ID, model tier, model name, and dispatcher; `line-worker/SKILL.md` tells agents to keep those details current and explains their use. The change adds no mechanism beyond the template field and its instruction. Direct inspection and `git diff --check` passed.

**Residual validation gap:** Live STATUS files were unavailable for inspection, so adoption by existing lines is unverified. The planned unittest command was not run because `python` is unavailable in this environment; this text-only change was assessed by direct inspection.

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

### Reviewer pass 1 (impl, codex reviewer)

The human’s concern is that a deletion command can trigger a platform confirmation and stall an unattended session. I inspected the plan and both edited protocol files. The guidance appears in `line-worker/SKILL.md` and `dispatch/templates/brief.md`; no new mechanism was added.

#### Blocking issues

**Thread B1 — Correct the shell quoting in the guarded path example.** In `docs/agent_plans/2026-10-12_unattended_command_shape_plan.md:16` and `line-worker/SKILL.md:48`, the inline example contains `\"${dir:?}\"/\"${name:?}\"`. Those backslashes make the quote characters literal rather than quoting the expansions. A read-only shell probe with `dir="alpha beta"` produced a path containing literal quotes in zsh and two arguments in Bash. Change the example to `"${dir:?}"/"${name:?}"`. The brief at `dispatch/templates/brief.md:12` should also say *quoted* guarded expansions so its shorter instruction preserves the same rule.

#### Non-blocking issues

**Thread N1 — Avoid promising that a command will never prompt.** The platform may still request confirmation for a literal or guarded path. The existing instruction to stop and report if that happens is sound; wording such as “avoid preventable confirmations” would describe the rule more accurately. The suggestion to use a script for many deletions also deserves care so it is not read as a way around a platform prompt.

#### Overall judgment

The locations and text-only scope match the plan. The shell example must be corrected before this implementation is ready for closeout.

#### Residual risks and validation gaps

Direct inspection confirms both placement and the quoting defect. The shell probe confirms its effect. The plan reports that `python -m unittest discover tests` passed, but this read-only review did not rerun it.

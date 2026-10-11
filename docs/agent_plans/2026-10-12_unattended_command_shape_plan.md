# Plan: command shapes that do not stall unattended sessions

Document level: plan (one PR in agent-protocols).

Decision source: per master relay (2026-10-12), pending record by the master
session. The human reported that a memory-cleanup command raised the platform
confirmation "Dangerous rm on possibly-empty variable"; a prompt like that
stalls a session while he is away.

## Change

Add one rule to `line-worker` ("While Working") and one line to `dispatch`
("The Brief" hard rules template):

- Avoid preventable platform confirmations: delete only by literal path or
  with quoted guarded expansions (`"${dir:?}"/"${name:?}"`), never a
  bare variable in `rm`; one command does one thing; for many deletions, list
  the literal paths (a script is for clarity, never to get around a prompt). If a confirmation prompt appears anyway,
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

### Driver response to pass 1

- B1: the files contain no backslashes (`grep -c '\\"' line-worker/SKILL.md`
  returns 0); the example is `"${dir:?}"/"${name:?}"`. The escaping the
  reviewer saw comes from how the text was quoted for the review prompt. The
  brief now says "quoted" guarded expansions.
- N1, accepted: "avoid preventable platform confirmations"; a script lists
  literal paths for clarity, never to get around a prompt.

### Reviewer pass 2 (impl, codex reviewer)

The human’s concern is that a deletion command could trigger a platform confirmation and stall an unattended session. I re-reviewed B1 and N1 against the committed files.

#### Blocking issues

None.

- **Thread B1 — Resolved.** The examples in `docs/agent_plans/2026-10-12_unattended_command_shape_plan.md:16` and `line-worker/SKILL.md:48` contain zero backslash bytes and use `"${dir:?}"/"${name:?}"`. The brief also specifies quoted guarded expansions. Read-only Bash and zsh probes produced one path when both variables contained spaces. The earlier finding came from prompt escaping, not the committed files.
- **Thread N1 — Resolved in the implementation.** `line-worker/SKILL.md` and `dispatch/templates/brief.md` now say “Avoid preventable platform confirmations.” The line-worker rule says a script is for clarity and never a way around a prompt.

#### Non-blocking issues

- The plan body at `docs/agent_plans/2026-10-12_unattended_command_shape_plan.md:15` still says commands should “never need” confirmation and retains the older script wording. Align it with the accepted wording in the driver response so the plan body reflects the implemented rule.

#### Overall judgment

There are no blocking issues. The implementation is ready for closeout.

#### Residual risks and validation gaps

A platform may still prompt for a literal or guarded path; both instructions say to stop and report if it does. This pass verified the committed bytes, wording, and shell quoting directly. I did not rerun the driver-reported full test suite.

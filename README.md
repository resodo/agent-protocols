# Agent Protocols

Reusable local protocols for human-agent and multi-agent software work.

## Protocols

- `structured-review/` - structured review for high-level plans, implementation plans, and completed implementation validation.
- `closeout/` - final hygiene checklist before handing off completed work.

## Usage

Point an agent at the relevant `SKILL.md` file and provide the requested role, artifact, and type.

Example:

```text
Please read ~/.agent-protocols/structured-review/SKILL.md
Role: reviewer
Artifact: docs/some_plan.md
Type: impl-plan
```

For implementation closeout:

```text
Please read ~/.agent-protocols/closeout/SKILL.md
Scope: current implementation task
```

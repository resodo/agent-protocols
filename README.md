# Agent Protocols

Reusable local protocols for human-agent and multi-agent software work.

## Protocols

- `structured-review/` - structured review for high-level plans, implementation plans, and completed implementation validation.
- `closeout/` - final hygiene checklist before handing off completed work.
- `planning/` - discussion-to-plan workflow before implementation starts.
- `retrospective/` - evidence-based post-incident or post-closeout learning workflow.
- `backlog-maintenance/` - YAML backlog registry maintenance for deferred work, including add/update/close/read operations and CI schema expectations.

## Guidance

- `agent-readiness/` - worktree guard contract and `AGENTS.md` bootstrap template for keeping project coordinates and shared protocol availability explicit.

## Local Overlays

Protocols are reusable. Project-specific policy belongs in the repo being worked
on, under:

```text
.agent-protocols/context.md
.agent-protocols/<protocol-name>.md
```

When a protocol is loaded inside a repo:

1. Read the generic protocol from this directory.
2. Read `.agent-protocols/context.md` if present.
3. Read `.agent-protocols/<protocol-name>.md` if present.

Overlays are loaded only for the protocol being used. Unknown overlay files are
ignored. A project overlay may be more specific than the generic protocol, but
must not override a generic `SAFETY` rule.

`SAFETY` rules may appear at H2 or H3 depending on a protocol's internal
structure. The heading text is the contract; overlays must not weaken those
rules.

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

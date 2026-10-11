# Role definitions

Vendor-neutral definitions of the specialist subagents a master dispatches.
Each file says what the role is for, which protocols it preloads, what it may
and may not do, and its suggested tier. A consumer repo adds a thin wrapper per
coding agent that points here (see `agent-readiness/capabilities.md`, "role
definition"):

- Claude Code: `.claude/agents/<name>.md` with `skills:` listing the preloaded
  protocols and a body that says "follow external/agent-protocols/agents/<name>.md".
- Codex: `.codex/agents/<name>.toml` with `developer_instructions` saying the same.
- Grok Build: `.grok/agents/<name>.md`.

When a coding agent has no role definitions, paste the role text into the
dispatch brief.

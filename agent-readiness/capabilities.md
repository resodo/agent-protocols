# Capability Map

Protocols name **capabilities**, never one vendor's tool. This map says how
each coding agent provides a capability and what to do when it does not.

Status words: **documented** = read in the vendor's documentation;
**observed** = seen in a local install (CLI help or config) only;
**unverified** = not checked. **Only `documented` counts as support**; for an
`observed` or `unverified` cell, use the fallback column. Update this file when
a vendor ships or changes a capability; keep the protocol text unchanged.

Sources checked on 2026-10-11: Claude Code docs (skills, sub-agents, hooks,
memory at code.claude.com/docs/en/...); Codex docs (developers.openai.com/codex/skills,
learn.chatgpt.com/docs/hooks, learn.chatgpt.com/docs/agent-configuration/subagents);
Grok Build user guide shipped with the CLI (`~/.grok/docs/user-guide/`,
chapters 08 skills, 10 hooks, 12 project rules, 14 headless, 16 subagents,
20 background tasks).

## Support statement

The protocols are supported for Claude Code, Codex and Grok Build as far as
this map marks `documented`. OpenCode is not supported. Essential
capabilities:

- project instructions and reading files: required, no fallback;
- spawn subagent and message a running agent: documented for all three;
  fallbacks below;
- scheduled sweep: documented for Grok Build only (observed for Claude Code,
  unverified for Codex); elsewhere use the fallback, and the sweep may run
  late;
- session-start and subagent-start injection: optional; the resident core in
  `AGENTS.md` and the brief template carry the same rules.

When an essential capability is missing and its fallback cannot run, the
workflow that needs it is unsupported for that agent.

Evidence keys: CC-skills = code.claude.com/docs/en/skills; CC-sub =
code.claude.com/docs/en/sub-agents; CC-hooks = code.claude.com/docs/en/hooks;
CC-mem = code.claude.com/docs/en/memory; CX-skills =
developers.openai.com/codex/skills; CX-hooks = learn.chatgpt.com/docs/hooks;
CX-sub = learn.chatgpt.com/docs/agent-configuration/subagents; CX-agents =
learn.chatgpt.com/docs/agent-configuration/agents-md; GK-nn = Grok
Build user guide chapter nn (`~/.grok/docs/user-guide/`). A cell without a
key is `observed` or `unverified` and does not count as support.

| Capability | Meaning in protocols | Claude Code | Codex | Grok Build | Fallback when missing |
|---|---|---|---|---|---|
| on-demand protocol | description always listed, body loaded when used | skills in `.claude/skills/` (documented, CC-skills) | skills in `.agents/skills/`; name, description, path listed, `SKILL.md` read when used (documented, CX-skills) | skills; also scans `.claude/skills/` and `.agents/skills/` (documented, GK-08) | the repo `AGENTS.md` routes "before X, read `external/agent-protocols/X/SKILL.md`" |
| project instructions | always-loaded project text | `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists; otherwise import it with `@AGENTS.md` (documented, CC-mem) | `AGENTS.md` from the project root down to the working directory (documented, CX-agents) | `AGENTS.md`, also `CLAUDE.md` files (documented, GK-12) | none: required |
| user-level instructions | the human's personal preferences | `~/.claude/CLAUDE.md` (documented, CC-mem) | `~/.codex/AGENTS.md` (or `AGENTS.override.md` there; documented, CX-agents) | reads `~/.claude/CLAUDE.md` with Claude compatibility on (documented, GK-12) | keep one source and generate the other copy |
| spawn subagent | start a worker with its own context | Agent tool (documented, CC-sub) | sub-agent threads (documented, CX-sub) | built-in agent types and custom roles (documented, GK-16) | a separate CLI session started with the brief as its prompt; results exchanged through files |
| role definition | a specialist with preloaded protocols and tool limits | `.claude/agents/<name>.md`, `skills:` preloads full bodies (documented, CC-sub) | `.codex/agents/<name>.toml`, `developer_instructions`, `skills.config` (documented, CX-sub) | `.grok/roles/<name>.toml` with `description`, `default_capability_mode`, `prompt_file` (documented, GK-16) | paste the neutral role text from `agents/<name>.md` into the brief |
| message a running agent | nudge or add instructions to a live worker | SendMessage (documented, CC-sub) | the parent routes follow-up instructions to sub-agent threads (documented, CX-sub) | `send_subagent_message`, steer or queue (documented, GK-16) | the worker reads `lines/<line>/INBOX.md` after each step |
| scheduled sweep | run the sweep on a timer | session cron or `/loop` (observed) | unverified | `/loop` and scheduler (documented, GK-20) | an OS timer (launchd, cron) that sends the sweep prompt; otherwise a sweep on every agent notification, which may run late |
| watchdog | notice a stalled worker | a monitor on the worker's output file size (observed) | unverified | `monitor` tool (documented, GK-20) | check whether output files grow; never read their content to decide |
| session-start injection | short text added when a session starts or after compaction | SessionStart hook, matchers include `compact`; stdout becomes context (documented, CC-hooks) | SessionStart hook; stdout added as developer context; PreCompact/PostCompact exist (documented, CX-hooks) | SessionStart (not for subagents), PreCompact/PostCompact (documented, GK-10); whether output reaches the model is unverified | the resident core in `AGENTS.md` tells the agent what to load first |
| subagent-start injection | short text added to every new worker | SubagentStart `additionalContext` (documented, CC-hooks) | SubagentStart event exists (documented, CX-hooks); injection unverified | SubagentStart event exists (documented, GK-10); injection unverified | the brief template starts with the worker hard rules |
| delivery page | a finished page for the human to read or approve | Artifact (observed) | unverified | unverified | repo markdown or the PR description; the local or repo file is always the source of truth, any page is a copy |
| structured review | plan and implementation review | `structured-review` runner, Claude backend | same runner, Codex backend | same runner, Grok backend | — |
| ask the human | a question that needs reading first | plain text | plain text | plain text | — |

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
- scheduled sweep: documented for Claude Code and Grok Build, unverified for
  Codex; with the fallback, the sweep may run late;
- session-start and subagent-start injection: optional; the resident core in
  `AGENTS.md` and the brief template carry the same rules.

When an essential capability is missing and its fallback cannot run, the
workflow that needs it is unsupported for that agent.

| Capability | Meaning in protocols | Claude Code | Codex | Grok Build | Fallback when missing |
|---|---|---|---|---|---|
| on-demand protocol | a protocol whose description is always listed and whose body loads when used | skills in `.claude/skills/` (documented) | skills in `.agents/skills/`; name, description and path listed up front, `SKILL.md` read when used (documented) | skills; also scans `.claude/skills/` and `.agents/skills/` (documented) | the repo `AGENTS.md` routes "before X, read `external/agent-protocols/X/SKILL.md`" |
| project instructions | always-loaded project text | `CLAUDE.md`; reads `AGENTS.md` when no `CLAUDE.md` exists (documented) | `AGENTS.md` | `AGENTS.md`, also `CLAUDE.md` and `~/.claude/CLAUDE.md` (documented) | none needed: every agent reads `AGENTS.md` |
| user-level instructions | the human's personal preferences | `~/.claude/CLAUDE.md` | `~/.codex/AGENTS.md` | reads `~/.claude/CLAUDE.md` (documented) | keep one source and generate the other copy |
| spawn subagent | start a worker with its own context | Agent tool (documented) | sub-agent threads; custom roles in `.codex/agents/*.toml` (documented) | built-in and `.grok/agents/*.md` (documented) | start a separate CLI session for the worker; exchange files |
| role definition | a specialist with preloaded protocols and tool limits | `.claude/agents/<name>.md`, `skills:` preloads full bodies (documented) | `.codex/agents/<name>.toml`, `developer_instructions`, `skills.config` (documented) | `.grok/agents/<name>.md` (documented) | paste the neutral role text from `agents/<name>.md` into the dispatch brief |
| message a running agent | nudge or add instructions to a live worker | SendMessage (documented) | parent routes follow-up instructions to sub-agent threads (documented); `codex queue` for an existing session (observed) | `send_subagent_message`, steer or queue (documented) | the worker reads `lines/<line>/INBOX.md` after each step |
| scheduled sweep | run the sweep on a timer | CronCreate or `/loop`; session-scoped, expires after 7 days (documented) | unverified | `/loop` and scheduler (documented) | an OS timer (launchd, cron) that sends the sweep prompt; otherwise sweep on every agent notification |
| watchdog | notice a stalled worker | Monitor on the worker's output file size | watch the session log size | `monitor` tool (documented) | check whether output files grow; never read their content to decide |
| session-start injection | short text added when a session starts or after compaction | SessionStart hook, matchers include `compact`; stdout becomes context (documented) | SessionStart hook; stdout "added as extra developer context"; PreCompact/PostCompact exist (documented) | SessionStart (not for subagents), PreCompact/PostCompact (documented); whether output reaches the model is unverified | the resident core in `AGENTS.md` tells the agent to read the handoff file first |
| subagent-start injection | short text added to every new worker | SubagentStart `additionalContext` (documented) | SubagentStart (documented; injection details unverified) | SubagentStart (documented; injection details unverified) | the dispatch brief template starts with the worker hard rules |
| delivery page | a finished page for the human to read or approve | Artifact (observed) | none (unverified); PR page or repo markdown | none (unverified) | repo markdown or the PR description. The local or repo file is always the source of truth; any page is a copy |
| structured review | plan and implementation review | `structured-review` runner (Claude, Codex or Grok backend) | same runner | same runner | — |
| ask the human | a question that needs reading first | plain text (pop-up forms can hide the explanation) | plain text | plain text | — |

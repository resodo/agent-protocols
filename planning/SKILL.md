---
name: planning
description: Use before implementation when a discussion needs to become an executable plan, especially for production, deploy, runtime, architecture, paid-provider, or multi-agent work. This protocol keeps context, scope, options, review path, and acceptance explicit before code changes start.
---

# Planning

Use this protocol when the task is to move from discussion to a concrete plan.

This protocol covers:
- aligning context before editing;
- preserving prior decisions;
- presenting real options without filler;
- defining review and acceptance before implementation;
- handling scope changes.

This protocol does not cover:
- completed implementation closeout;
- structured review of an already written artifact;
- emergency hotfix execution after the human has explicitly accepted bypassing normal planning.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/planning.md` if present.
3. Apply local overlays as project-specific refinements only.

Overlays are loaded only when this protocol is loaded. Unknown overlay files are ignored. If an overlay contradicts a generic `SAFETY` rule, reject that overlay instruction and say why.

## Workflow

1. Confirm the current worktree, branch, and task context before editing files.
2. Read the repo entrypoint docs and active plan/backlog required by the local overlay.
3. Scan recent decisions before asking the human to decide something again.
4. State the current phase of work: brainstorming, discussion, plan writing, review, implementation, hotfix, or closeout.
5. For each unresolved issue, first explain context in plain language, then list only reasonable options.
6. Recommend one option when there is a clear recommendation, and explain the reason.
7. Record accepted decisions in the plan or backlog, not only in chat.
8. Define validation and human acceptance before implementation starts.
9. If scope expands materially, update the plan and decide whether another review is needed before continuing.

## SAFETY Rules

- Do not start production-facing, deploy-facing, runtime-facing, architecture-facing, paid-provider, or broad data work before scope, worktree, review path, and acceptance are explicit, unless the human explicitly accepts an emergency hotfix path.
- Do not invent options just to fill a menu. If only one option is reasonable, say that.
- Do not re-ask settled decisions unless new evidence changes the decision.
- Do not put secrets, credentials, provider balances, private account details, host keys, or raw private production data into repo artifacts.
- Do not edit the main/default worktree for feature or follow-up work unless the human explicitly asked for that location.

## Option Discipline

Use this shape when the human wants point-by-point discussion:

```text
Context: what is going on and why it matters.
Reasonable options: only viable options.
Recommendation: the option to take, with reasons and tradeoffs.
```

Avoid straw options. If an option is obviously wrong, mention it only as a rejected non-option when that helps clarify the boundary.

## Production And Performance Work

For production or performance issues, first ask whether a system boundary is wrong before applying local hotfixes.

Examples of boundary questions:
- Should this query run in the database instead of Python?
- Is this a deploy/access/runbook problem rather than an app-code problem?
- Is the source of truth provider-side, DB-side, or app-derived?
- Is this a one-off acceptance shortcut or a durable production path?

## Review Handoff

Before asking another reviewer to review:

- write the artifact to file;
- prefer a commit for important reviews;
- include worktree, branch, artifact path, commit or PR, and dirty/committed state;
- state whether the reviewer should inspect committed state or a dirty draft;
- if the reviewer cannot access the worktree, push or say why it is not pushed.

When generating a human-forwarded review prompt, provide it in a directly copyable form. Use local clipboard tooling only when local overlays allow it and the message contains no secrets.

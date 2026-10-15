# Whole-repo structure audit (review request)

Document level: review request for a decision doc (no PR is opened from this
file; its findings feed the restructure decision doc).

Status: active (2026-10-16).

## Why

The human said on 2026-10-16 (relayed by the master; per master relay,
pending record): the repo still feels like "one big tangle": who is which
role, how the master role is defined, and what each scope is, are unclear.
He asked for an independent, hard review of the **complete current repo
state**, not of a recent diff, before any restructuring.

This review is the input to a restructure decision doc. Nothing is changed in
this pass.

## What to review

Review the repository as it stands at this commit, every file that carries
rules, plus one consumer overlay that shows how the core is used:

1. This repo (core): `README.md`, `AGENTS.md`, `docs/README.md`,
   `docs/CURRENT.md`, `docs/agent_plans/README.md`, and every protocol
   directory: `decision-boundary/` (including `CORE.md`), `master-board/`,
   `dispatch/`, `line-worker/`, `merge-queue/`, `release/`, `visual-qa/`,
   `away-mode/`, `session-handoff/`, `fix-triage/`, `planning/`,
   `structured-review/` (the `SKILL.md` and its `references/`; the runner script
   only where its text states rules), `closeout/`, `readable-brief/`,
   `retrospective/`, `backlog-maintenance/`, `scout/` (the `SKILL.md`),
   `agent-readiness/`, and `agents/`.
2. One consumer overlay, read-only, at the relative path
   `../../../skynet-intern/main/` from this worktree: its `AGENTS.md`
   (sections "Decision boundary (resident core)", "Master Session",
   "CI Triggering and Merging") and every file in its `.agent-protocols/`
   directory, including `authority-ledger.md` and `context.md`. Cite these
   as `overlay:<file>` (for example `overlay:dispatch.md`), never with an
   absolute path.

Dated plans under `docs/agent_plans/` are provenance, not instructions; read
them only to check whether a rule's history explains a conflict.

## Questions

Answer each with concrete file and section citations.

1. **Roles.** List every role the repo defines or implies (master, direct
   session, dispatched agent, line worker, researcher, merge agent, release
   agent, visual QA, driver, reviewer, author, and any role that exists in
   practice but has no definition, such as an agent dispatched by the master
   that itself dispatches and coordinates other agents). For each: where it
   is defined, what it may and may not do, whom it reports to. Flag roles that
   are defined in more than one place, defined inconsistently, or used but
   never defined.
2. **The master role.** Is there one place that defines what the master is,
   what it owns, what it may decide, and what it must not do? List every
   place that states part of the master's duties or powers. Is the set
   complete and consistent? What is missing?
3. **Scope boundaries.** For each protocol, what does it claim as its scope
   (its description line and body)? Where do two protocols claim the same
   thing? Where does a protocol reach into another's scope? Are the three
   families (development lifecycle: planning, structured-review, closeout,
   readable-brief, retrospective, backlog-maintenance, scout; multi-agent
   operation: decision-boundary, master-board, dispatch, line-worker,
   merge-queue, release, visual-qa, away-mode, session-handoff, fix-triage;
   guidance: agent-readiness, agents) clearly separated, and does a reader
   know which one to load?
4. **Single source of truth per rule.** Find rules stated in more than one
   place (core vs core, core vs overlay, overlay vs consumer `AGENTS.md`).
   Examples to check, not an exhaustive list: merge permission; the
   ledger-entry line-level lookup; "only the session that heard an approval
   records it"; deletion first and premise before fix; command shape that
   avoids platform confirmations; reviewer model and tier names. For each:
   which copy should be the source, and which copies should become pointers
   or be deleted.
5. **Conflicts.** Rules that contradict each other, or an overlay that
   weakens a core `SAFETY` rule, or a consumer document that contradicts the
   overlay or the core.
6. **Layering.** Is each item in the right layer: core (true for any project
   and any coding agent), project overlay (names this project's paths,
   scripts, numbers, business terms, or this human's grants for this project),
   or the human's personal preferences (true for him in any project; these
   live in a user-level file outside both repos)? Flag personal preferences
   that sit in the core or in an overlay, and project details in the core.
7. **Orphans and stale text.** Files, sections or references that nothing
   routes to, paths that no longer exist, retired mechanisms still described,
   indexes (`README.md`, `docs/CURRENT.md`) that are out of date or restate
   protocol bodies instead of pointing at them.
8. **Size and progressive disclosure.** Which always-loaded text (resident
   core, descriptions, consumer `AGENTS.md` sections) carries detail that only
   one role needs? Which protocol bodies are too long for what they do?

## Output

Group findings by the eight questions. For each finding: severity (blocking
for the restructure / should fix / note), the exact citations, what is wrong,
and the smallest correct fix, deletion first (would deleting, merging or
pointing resolve it before adding anything?). End with a short proposal for a
target structure: the role list with one owner file each, where the master
role is defined, and where each family of rules lives. Do not propose new
standing mechanisms unless deleting or merging cannot solve the problem.

## Review Threads

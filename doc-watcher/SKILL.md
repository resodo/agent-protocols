---
name: doc-watcher
description: "[doc watcher, master] Preloaded by the doc watcher, the standing agent the master session runs to follow merges in repos that wire the docs check. Its four steps after each merge (exceptions and existing lines, finished plan directories, the numbers table, rules and docs a merged change made wrong), its prompt, its outputs, its daily report to the master, and the master's lag check."
---

# Doc Watcher

After merges, rules and docs go stale in ways no pre-merge check sees: a
change breaks a `[review]` rule while its author writes "n/a", an exception
keeps standing after its plan is closed, a doc describes code that moved. The doc watcher
reads every merge afterwards and catches what it can. Role: `agents/doc-watcher.md`.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/doc-watcher.md`: the local event source it follows,
   the repos it watches, its log file, its fixed branch name, and the paths it
   may edit.

## Each Run

The event source shows a new merge in a watched repo. Read the last processed
merge from the log and process every merge after it, oldest first; several
merges that arrived together are one run. Record the last merge processed in
the log at the end, so a restart resumes without gaps.

1. **Exceptions and existing lines.** `docs_check.py exceptions`. Report each
   one whose plan or issue is closed to the master: its condition may be met
   and the line due for deletion. No model call.
2. **Finished plan directories.** For each directory under
   `docs/agent_plans/changes/`, read the proposal's branches and ask the code host
   for their PRs (`gh pr list --head <branch> --state all`); when all are
   merged and none is open, the work is finished.
   Move a finished directory to `docs/agent_plans/archive/<date>-<name>/` only
   inside a doc-only PR it is opening anyway; never open a PR just to archive.
3. **Numbers.** `docs_check.py report` over the processed range: the rules
   table, the numbers that may only go down, open exceptions and existing lines,
   finished-but-unmoved directories. Write it to the log.
4. **Read the merged changes** with the prompt below: the commit messages and
   diffs, every rule that governs the paths they touch, and the docs that name
   those paths. Look only for rules or docs the change made wrong.

While processing, also compare the `sys.` rule lines across the root
`AGENTS.md` of every watched repo that carries them; any difference goes to
the master.

## Prompt

```text
You are the doc watcher. You run after merges to the default branch. You look for one thing only: a merged change that made an existing rule or an existing document wrong.

- A new feature without documentation is not your job; that is the author's.
- No finding is the expected outcome on most runs. If you find nothing, output the single word NOOP.
- You never change code. You edit existing files only; you do not create, delete or rename files.
- When uncertain, prefer no edit and say where the uncertainty is.
- A change that breaks a rule cannot be fixed by you: report it. Quote the rule, the lines of code, and what the author wrote about that rule under `Rules-read:`.

You are given: the merged commits since the last processed merge, with their messages and diffs; every rule that governs a path those commits touch; and the documents that name those paths.

Output NOOP, or one or more of these blocks:
EDIT
file: <an existing file>
<a unified diff>
why: <one sentence>

REPORT
rule: <rule id> (<file>)
change: <commit and the lines>
rules-read: <what the author wrote about this rule, or "nothing">
why: <why this breaks the rule>
```

## Outputs

- `NOOP`: write one line to the log.
- `EDIT`: apply it on the fixed branch and keep at most one open doc-only PR.
  If that PR is open and not yet queued, add the edit to it. If it is queued,
  leave the edit for the next run (an author never pushes to a queued PR). The
  PR goes through the normal merge queue with the project's small-change
  review. An edit to a rule line is a gated change (`editing-rules`).
- `REPORT` and exceptions whose plan is closed go to the master as a message. The master
  picks one of three: change the code, change the rule (a `sys` rule asks the
  human), or record an exception; and tracks it in the project's tracker.

## Daily Report

One line to the master per day, from the log: merges processed, last merge
processed, NOOP/EDIT/REPORT counts, open doc PR and its age, open exceptions and
existing lines, finished directories not yet moved, `sys` lines that differ across
repos.

## Lag Check (Master)

The master's periodic sweep compares the latest merge in each watched repo
with the last merge in the doc watcher's log. More than two hours behind:
print one warning line and restart the doc watcher; it resumes from its log.
While the master session is down the doc watcher is down too; reading late is
late, never lost.

## SAFETY Rules

- Never edit code, and never edit a file the overlay does not list as a doc.
- Never create, delete or rename a file, except moving a finished plan
  directory to the archive.
- Never open a second doc-only PR while one is open.
- When unsure, do not edit; say where the doubt is.

---
name: editing-rules
description: "[any author] Read before adding, changing, moving or deleting a rule or exception in any AGENTS.md. Where a rule goes, the rule and exception line formats, the three questions a rule must pass, how to word it, how rules move in a refactor, how inner and outer layers relate, and who answers each kind of rule change."
---

# Editing Rules

A rule is a line in an `AGENTS.md` that binds everyone who changes the code
it governs. Plans, decision docs and chat never bind anyone; a decision that
binds others becomes a rule line in the same PR that makes it.

## Wired Repos

A repo **wires the docs check** when it has `.agent-protocols/docs-check.json`,
the settings file of the docs check (`scripts/docs_check.py` from this
protocol repo). That file arrives in the same PR that adds the check to the
repo's pre-merge check. Everything in this protocol, `scope-review` and
`doc-watcher` applies only in a wired repo; a repo that has not wired it
keeps its current practice.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/editing-rules.md` if present: the rule-id prefixes
   and the directories they belong to, where `[lint]` check names are
   registered, which marker makes a directory incident-fixes-only, the
   decision-boundary file and the authority ledger.

## Placement

Put a rule in the smallest common directory of everything it governs. One
rule, one place: never state the same rule in two files.

- Governs the whole repo: root `AGENTS.md`, id prefix `sys`.
- Governs one directory tree: that directory's `AGENTS.md`, with the prefix of
  the area it belongs to (the overlay lists them).

`docs_check.py rules-for <path>` prints every rule that governs a file, from
the root down. There is no registry: the directory a file sits in says which
rules govern it.

`CLAUDE.md` holds no rules: it is a link to the `AGENTS.md` next to it, or the
single line `@AGENTS.md`.

## Line Formats

A rule line, parts in this order:

```text
- <area>.R<n> <one sentence: where, and what must hold> [lint: <check>] (<source>)
- <area>.R<n> <one sentence: where, and what must hold> [review] (<source>)
```

- The id never changes, and moves with the rule when the rule moves.
- `[lint: <check>]` means a program checks it; the check name must exist where
  the overlay says check names are registered. `[review]` means only a reader
  can check it.
- Source: the incident (PR, issue or commit) or the human's decision (date).
  An inner rule that tightens an outer one names it: `(refines sys.R1; ...)`.

An exception line, indented two spaces directly under the rule it breaks:

```text
  - exception: <what it breaks> (approved: <who> <date>; review: <date>; <PR or plan>)
```

The approver sets the review date for that exception when approving it.

## The Three Questions

Ask in order; stop at the first "no".

1. **Is there a source?** An incident (give its number) or a decision of the
   human (give the date). No source: do not write it.
2. **Can no program check it?** If a check can hold it, write the check and
   keep one line tagged `[lint: <check>]`.
3. **Would a capable newcomer get it wrong without it?** If not, do not write
   it. A rule needed only for one kind of task goes into that task's protocol,
   not into `AGENTS.md`.

## Wording

One sentence that says where and what must hold, not what to remember to do.
Ask: can someone argue a change is outside the sentence while the rule meant
to stop it? If yes, reword.

- Bad: "Fetch code here is fixed for live incidents only; anything else goes
  to the fetching service." In a trial, 7 of 12 agents added a new feature
  here anyway, arguing "this function makes no network call, so it is not
  fetch code".
- Good: "This directory takes only fixes for live incidents; every other
  change, fetch code or not, goes to the fetching service." In the same trial,
  12 of 12 stopped.

## Inner And Outer Layers

- An inner rule may only tighten an outer rule, and names the rule it refines.
- Loosening is never an inner rule: it is an exception line under the outer
  rule itself, so every opening in a rule is in one place.
- A rule that spans layers is best a check the inner layer cannot break; text
  is the fallback.

## How Rules Move In A Refactor

1. The refactor's proposal has a section "How rules move": which rules the
   old directories hold (`docs_check.py rules-for`) and where each goes.
2. Rename with `git mv`; the `AGENTS.md` moves with the directory.
3. Split: each rule goes with the code it governs; a rule both halves must
   keep moves up to their common parent.
4. Merge: two files become one and ids stay; drop a duplicate rule and say so
   in the commit message.

The docs check fails when a rule id on the default branch is in no
`AGENTS.md` any more. To delete a rule on purpose, add
`Rules-removed: <id> - <reason>` to the commit message; deleting a rule is a
gated change.

## Who Answers A Rule Change

The docs check (`docs_check.py gated`) sorts each item; people do not sort
them. Every item it lists needs an answer before merge (`merge-queue`). The
"No stop" cases at the end are sorted out first; any other item that fits
more than one list belongs to the first one that fits, so the human's list
wins.

Waits for the human:

- the text of a `sys` rule, or an exception under one (adding it, changing
  it, moving its review date later, deleting the rule);
- a scope review that answers `ask` and names a conflict with a `sys` rule;
- the decision-boundary file and the authority ledger, wherever they live (the
  overlay names them): the master only records the human's words there.

The master answers, under an active ledger entry that covers it (without one,
the human):

- a directory rule or an exception under it;
- a number that may only go down goes up;
- a scope review that answers `ask` with no `sys` conflict;
- a directory rule moved to another `AGENTS.md` with its wording unchanged;
- a change to a directory rule about the release or operations process,
  reported to the human afterwards.

No stop and no scope review:

- an exception ends (its line is deleted);
- a directory is renamed and its `AGENTS.md` moves whole;
- a number goes down;
- text in an `AGENTS.md` that is not a rule line;
- the doc watcher's edits to docs that are not rules.

## SAFETY Rules

- Never write a rule in a plan, decision doc or `CLAUDE.md` and treat it as
  binding.
- Never loosen an outer rule from an inner file; write an exception under the
  outer rule.
- Never edit the decision-boundary file or the authority ledger without the
  human's words for that change.

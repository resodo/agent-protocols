---
name: scope-review
description: "[any author, merge agent] Use in a repo that wires the docs check when the check says a change needs a scope review: a new proposal, a changed rule or exception, a number that may only go down going up, or a change in an incident-fixes-only directory. The proposal's five sections, how to run the reviewer, the record format, the four verdicts, what the program checks, and the reviewer prompt."
---

# Scope Review

Before work starts, a separate reviewer reads a one-page proposal and the
rules that govern the paths it will touch, and judges ownership and scope. It
sees no code and none of the author's reasoning, and it may only cut, move or
name a conflict. Applies in a repo that wires the docs check (`editing-rules`,
Wired Repos).

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/scope-review.md` if present: the reviewer model and
   the placement-questions file.
3. The program's settings are in `.agent-protocols/docs-check.json`; the run
   log is the environment variable `SCOPE_REVIEW_LOG`, or else that file's
   `scope_review.log`.

## When It Is Required

The program decides (`docs_check.py scope`), from four signals:

1. a new proposal under `docs/agent_plans/changes/`;
2. any rule or exception changed, or a rule moved to another file;
3. a number that may only go down goes up (`Raises:` in a commit message);
4. a change under a directory marked incident-fixes-only.

Ending an exception, renaming a directory whose `AGENTS.md` moves whole, and a
number going down do not trigger it. A change with no plan directory that the
check stops writes the proposal then; it is no longer a small change. A real
live-incident fix still gets the review; there is no "ship first, review
later" path.

## The Proposal

`docs/agent_plans/changes/<name>/proposal.md`, one page, five sections:

1. **Branch**: every branch the work will use (the doc watcher archives the
   directory when all of them are merged).
2. **Intent**: what is broken today, with one real incident or number.
3. **Scope**: the smallest version that fixes it.
4. **Touches** (heading `## Touches`; the runner parses it): the files or directories it will touch.
5. **Rule changes**: which rules or exceptions it adds, changes or moves, or
   "none". A refactor adds "How rules move" (`editing-rules`).

## Running It

```text
scope-review/run_scope_review.py <name>
```

`<name>` is the change directory's name, not a file path; the runner reads
`<name>/proposal.md` under the repo's changes directory and exits with an error
if it is missing. It starts a fresh model session with no tools and a clean
configuration, and gives it four things: `reviewer_prompt.md`, the
proposal, the rules that govern the proposal's paths (from
`docs_check.py rules-for`, with their rows from `docs_check.py report`), and
the overlay's placement questions. It writes `scope-review.md` next to the
proposal and appends the record's fingerprint to the run log (Local
Overlay, step 3). Commit both files with the change. Never write or edit a record by
hand.

## The Record

```text
---
verdict: go | cut | ask | no
reviewer: <model>
run_id: <run id>
proposal_sha: <fingerprint of the proposal as reviewed>
---
- <rule id>: holds | n/a | conflict. <one sentence>
Owner: <a rule id or a placement-question line>
Cut: <what to take out, or "nothing">
Question: <one question; only when the verdict is ask>
```

One line per governing rule, in the order given.

## Verdicts

- `go`: passes.
- `cut`: does not pass. Take the listed parts out of the proposal and run the
  review again; a new session reads the changed proposal from scratch. Only a
  later `go` passes.
- `ask`: passes the check; the merge agent stops until the question is
  answered by whoever `editing-rules` (Who Answers A Rule Change) names. When
  the record also lists cuts, the answer says cut or keep for each.
- `no`: does not pass.

## What The Program Checks

Before merge, `docs_check.py scope`:

1. a record exists when a signal requires one;
2. the verdict passes (above);
3. the proposal has not changed since the review (`proposal_sha`);
4. every rule that governs a path the PR actually touches has a line, so a
   change that grows into new directories needs a new review;
5. the proposal sits next to the record.

At merge, `docs_check.py gated --log <run log>` lists each gated item and who
answers it, and flags a record whose fingerprint is not in the runner's log
(send it back to the author).

## Reviewer Prompt

The runner sends `reviewer_prompt.md` (next to this file; the only copy) verbatim, then
the proposal, the rules and the placement questions.

In `reviewer_prompt.md`, the sentence "You may say only ... never propose adding anything" is the
human's decision; changing it needs the human.

## What It Cannot Guarantee

- The reviewer has no tools and takes the proposal's facts as given.
- After an `ask` answered "cut", no program checks that the code was cut.

## SAFETY Rules

- Never write, edit or copy a `scope-review.md` by hand.
- Never change a proposal after its review without running the review again.
- Never merge on `cut` or `no`.

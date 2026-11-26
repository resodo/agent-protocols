# Development-docs mechanism: protocol text

Status: active implementation plan
Branch: `doc-mechanism-protocols`

## What and why

The human approved a development-docs mechanism and chose to switch every
consuming repo over at once (no pilot). Its parts:

- Rules live in `AGENTS.md` files, one rule in one place, in the smallest
  directory that contains everything it governs, in a fixed line format that a
  program can read (`<area>.R<n> ... [lint: <check>] | [review] (<source>)`),
  with exceptions written directly under the rule they break.
- A docs check (`scripts/docs_check.py`) runs on every PR in a repo that wires
  it: rule format, ids, paths, numbers that may only go down, the `Rules-read:`
  block in the branch's commit messages, and whether a scope review is needed.
- A scope reviewer reads a one-page proposal and the rules that govern its
  paths before work starts, and may say only delete, move, or which rule
  conflicts. Its record is committed with the change and checked by the
  program.
- Gated rule changes fall into three piles: wait for the human, the master
  answers under an active ledger entry, or no stop.
- A standing doc watcher, run by the master session, follows merges and keeps
  rules and docs from going stale; it edits docs only and reports code-vs-rule
  problems to the master.

This PR writes the protocol text only. The check script and the scope-review
runner are a separate PR by another worker; this text names them
(`scripts/docs_check.py`, `scope-review/run_scope_review.py`) and states their
interface. Consumer overlays (paths, models, event file, tracker) are separate
consumer PRs.

## Files

New:

- `agents/scope-reviewer.md`, `agents/doc-watcher.md` - the two roles.
- `scope-review/SKILL.md` - when required, proposal, record, verdicts, what the
  program checks, the reviewer prompt.
- `editing-rules/SKILL.md` - read before changing any `AGENTS.md`: placement,
  formats, the three questions, wording, refactors, inner and outer layers, who
  answers.
- `doc-watcher/SKILL.md` - the four steps, the prompt, outputs, daily report,
  lag check.

Changed:

- `agents/README.md` - two rows.
- `planning/SKILL.md` - step 2 (proposal and scope review), step 10 (binding
  decisions only in the owning `AGENTS.md`; the rest to the project tracker),
  a "How rules move" section.
- `closeout/SKILL.md` 4.1 - in a wired repo the docs check replaces the
  doc-status checks; submodule pointer and artifact parts stay.
- `line-worker/SKILL.md` - `Rules-read:` block; scope review first when the
  check asks.
- `merge-queue/SKILL.md` - step 3 also covers what the overlay's gated command
  lists; the safety rule accepts an active ledger entry that covers it.
- `agents/master.md` - answers gated items handed to it, marks the human's
  statements daily, receives the doc watcher's reports.
- `structured-review/SKILL.md` - a plan with a scope-review record cites it for
  ownership.
- `scout/` - remove `document-structure` and `document-lifecycle-drift`:
  delete `scout/references/document-structure.md` and
  `scout/references/document-lifecycle-drift.md`; drop their entries and
  validation from `scout/scripts/scout_runner.py`; drop their tests from
  `scout/tests/test_scout_runner.py` and add one test that an overlay still
  enabling a retired subskill fails with a clear message; update
  `scout/SKILL.md`.
- Indexes: `README.md`, `docs/CURRENT.md`, `docs/agent_plans/README.md`.

Unchanged: `dispatch/`, `release/`, `master-board/`.

## Interface For The Companion PR

The new protocol files are the contract the check and runner PR implements:

- Opt-in: a repo wires the check when it has `.agent-protocols/docs-check.json`
  (`editing-rules`, Wired Repos).
- Rule and exception line formats, `Rules-read:`, `Raises:` and
  `Rules-removed:` commit-message lines (`editing-rules`, `line-worker`).
- Proposal at `docs/agent_plans/changes/<name>/proposal.md`, record
  `scope-review.md` next to it, record format, verdicts, the five checks, the
  four signals, the run log and `gated --log` (`scope-review`).
- Who answers each gated item (`editing-rules`, Who Answers A Rule Change).

Compact contract (the protocol files state the same):

- Opt-in: the presence of `.agent-protocols/docs-check.json`, which arrives
  in the same consumer PR that wires the check. One place for agents and the
  program.
- Rule line: `- <area>.R<n> <sentence> [lint: <check>] (<source>)` or
  `... [review] (<source>)`. Exception line, two spaces under its rule:
  `- exception: <what> (approved: <who> <date>; review: <date>; <PR or plan>)`.
- Commit messages in base..HEAD (the check reads them all): a `Rules-read:` block with one line
  per `[review]` rule governing a touched path, `- <id>: applies; <how>` or
  `- <id>: n/a; <why>`; `Raises: <name> <old> -> <new> - <reason>`;
  `Rules-removed: <id> - <reason>`. Missing lines fail the check.
- Scope-review signals: a new `docs/agent_plans/changes/<name>/proposal.md`; a
  rule or exception changed, or moved to another file; a declared `Raises:`; a
  change under an incident-fixes-only directory. Not signals: an exception
  line deleted, a directory renamed with its `AGENTS.md` whole, a number going
  down.
- Record `scope-review.md` next to the proposal: front matter `verdict`
  (`go|cut|ask|no`), `reviewer`, `run_id`, `proposal_sha`; one
  `- <id>: holds|n/a|conflict. <sentence>` line per governing rule; `Owner:`,
  `Cut:`, and `Question:` when `ask`.
- The five checks, each a failure with a message saying what to do: record
  absent when a signal fires; verdict `cut` or `no`; `proposal_sha` does not
  match; a governing rule of a touched path has no line; no proposal next to
  the record. `ask` passes the check and is listed by `gated`.
- `gated --log <run log>`: one line per gated item with who answers it (the
  human, or the master under a ledger entry), and a line for a record whose
  fingerprint is not in the log.
- Settings: `.agent-protocols/docs-check.json`; run log from env
  `SCOPE_REVIEW_LOG`, else the config's `scope_review.log`.
- Runner: `scope-review/run_scope_review.py <proposal.md>` (Python, testable
  with a fake model command) writes the record and appends its fingerprint
  to the run log; it sends the fenced
  prompt under "Reviewer Prompt" in `scope-review/SKILL.md` verbatim.

Negative cases (a required record that is absent, a changed proposal, a
missing `Rules-read:` line) are tests in that PR, not here.

## Rollout Order

1. This PR merges. A consumer pinned at an older commit is unaffected: its
   pointer does not move.
2. The check and runner PR merges in this repo.
3. Each consumer's bump PR, in one PR: moves the pointer, adds skill mounts
   for `scope-review`, `editing-rules`, `doc-watcher`, adds role wrappers,
   drops the two retired Scout subskills from its `scout.yml`, and adds the
   overlays that wire the check. Its own CI proves the migrated case.
4. The consumer PR that adds the check to its pre-merge gate merges only after
   that repo's first rules are written and the master has told running lines.

## What Replaces The Two Scout Subskills

The human's design retires both; nothing is kept in Scout.

- Lifecycle drift (current docs that a change made wrong): the doc watcher's
  step 4 after every merge, instead of a periodic scan.
- Stale paths, `CLAUDE.md` holding rules, plans outside `changes/`, the plan
  index growing: the docs check on every PR.
- Plan status words (`active`, `ready for merge`): no longer tracked; a plan
  binds no one, and finished plan directories are archived by the doc watcher.
- Intentionally retired, with no replacement: periodic discovery of older
  misleading claims in current maps, status documents and runbooks that no
  recent merge touched; source-of-truth duplication and unclear current versus
  historical boundaries between documents; navigation structure and doc size
  thresholds. Rules have one home by construction (`editing-rules`), and the
  only size numbers kept are the docs check's "may only go down" numbers. A
  one-off sweep of existing docs, if wanted, is a separate task.

A repo that does not wire the check loses both subskills with no replacement.
That is the human's choice to switch every repo at once.

## Recording The Human's Words

`master-board` keeps the same-turn rule for answers to the master's questions.
The daily marking in `agents/master.md` is a second pass over everything the
human said, to catch statements that should become rules; it does not replace
the same-turn record. `master-board` stays unchanged.

## Compatibility

Every new duty applies only "in a repo whose overlay wires the docs check"
(defined once in `editing-rules`). A repo that has not wired it keeps today's
behavior, except Scout: an overlay that still enables one of the two removed
subskills fails setup with "enabled subskill has no shared protocol:
<name>" until its bump PR drops them (step 3 above).

## Validation

- Structured review: plan review and implementation review, Codex normal.
- CI on GitHub (scout tests change). No local test runs.
- Read every changed line, and grep the diff for personal names, emails, company and product names, hostnames
  and machine paths before commit.

## Acceptance

The coordinator reads the PR; the master decides the merge. Consumers adopt it
through submodule bumps with their overlays.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

The concern is whether this protocol change can be implemented and adopted without breaking consumers or silently retiring useful document checks.

#### Blocking issues

1. **Consumer rollout can break an unwired repo.** `Compatibility` says an overlay retaining either removed Scout subskill will fail setup, while the consumer overlays and check implementation are separate PRs. Specify the merge order and require each consumer bump to wire the docs check, remove the retired Scout entries, and add the new skill mounts together. Validate both an unchanged pinned consumer and a migrated consumer.

2. **The companion check and reviewer interface is too vague to implement consistently.** The plan names two programs but does not define the overlay opt-in field, proposal and record locations, `Rules-read:` format, or the check’s pass and failure cases. Add a compact interface contract or cite an agreed artifact that defines these details. Include a negative case that proves a required scope-review record is rejected when absent.

3. **The Scout replacement does not account for both retired scopes.** `document-structure` finds navigation and source-of-truth structure problems; `document-lifecycle-drift` checks current claims against status sources. A watcher that follows merges may miss either class. State which checks the watcher retains and which are intentionally retired. If coverage is meant to remain, define how the watcher inspects it; retaining the Scout subskills until migration is the simpler fallback, at the cost of temporary overlap.

4. **The file list conflicts with the existing recording rule.** The planned daily recording in `agents/master.md` conflicts with `master-board/SKILL.md`, which requires recording human answers in the same turn, yet `master-board/` is listed as unchanged. Preserve the same-turn rule in the new text, or explicitly include and justify a change to its owner.

#### Non-blocking issue

- Name the specific `scout/` files to edit or remove in the file list. For privacy validation, inspect the changed text as well as running targeted searches: a grep alone cannot establish that every personal or private organization name has been caught. The current plan contains no apparent private hostname or machine path.

#### Overall judgment

**Not ready for implementation** until the four blocking issues are resolved.

#### Validation gap

No tests were run in this read-only review. The implementation should use the configured CI checks for Scout changes and demonstrate the consumer compatibility cases above.

#### Driver reply to pass 1

1. Added "Rollout Order": pinned consumers are unaffected; each consumer bump
   does pointer, mounts, wrappers, Scout overlay and check overlays in one PR,
   and its CI proves the migrated case.
2. Added "Interface For The Companion PR": the new protocol files are the
   contract and the section lists where each part is defined. The negative
   cases are tests of the check PR, which owns the program.
3. Added "What Replaces The Two Scout Subskills": what the doc watcher and the
   check take over, and what is retired on purpose (navigation structure and
   size thresholds), per the human's design.
4. Added "Recording The Human's Words": the same-turn rule stays; the daily
   marking is an extra pass, so `master-board` does not change.
- Non-blocking: named the Scout files; validation now reads every changed line
  as well as grepping.

### Reviewer pass 2 (impl-plan, codex reviewer)

The human’s concern is whether these protocols can be implemented and adopted without breaking consumers or silently losing useful document checks.

#### Blocking issues

1. **Pass 1 thread 2 remains open: the companion interface still requires design choices.** “Interface For The Companion PR” points to protocol files this PR has yet to write. It does not specify the opt-in field, `Rules-read:` syntax, the five checks, the four signals, or record failure behavior, and it cites no existing approved contract for them. Add a compact contract to the plan or cite an agreed artifact so the protocol author can write those files without guessing. Keep the absent-record negative case in the companion PR’s validation requirements.

2. **Pass 1 thread 3 remains open: part of the retired Scout coverage is unaccounted for.** The watcher is assigned current docs made wrong by a merge, while `scout/references/document-lifecycle-drift.md` also covers older misleading claims in current maps, status documents, and runbooks. `scout/references/document-structure.md` covers source-of-truth duplication and unclear current versus historical boundaries beyond navigation and size. State whether those discovery duties are intentionally retired. Recording that loss is the simpler option; retaining detection would require a defined inspection duty and ongoing maintenance.

#### Resolved threads

- **Pass 1 thread 1 — Resolved.** The plan now orders the shared PRs before consumer bumps and requires each bump to carry the pointer, mounts, Scout removal, and check overlays together. An unchanged pinned consumer keeps its existing pointer; the migrated case is assigned to consumer CI.
- **Pass 1 thread 4 — Resolved.** “Recording The Human’s Words” preserves `master-board`’s same-turn rule and makes daily marking an additional pass.

#### Non-blocking issues

None.

#### Overall judgment

**Not ready for implementation** while threads 2 and 3 remain open.

#### Validation gap

This read-only review ran no tests. The companion PR should exercise the specified negative cases, including a required scope-review record being absent; consumer CI should prove the migrated configuration.

#### Driver reply to pass 2

1. Added a compact contract under "Interface For The Companion PR": opt-in
   field, line formats, commit-message lines, signals and non-signals, record
   format, the five checks and their failure behavior, `gated`, and the
   runner's prompt source.
2. "What Replaces The Two Scout Subskills" now lists the retired discovery
   duties explicitly: older misleading claims that no merge touched,
   source-of-truth duplication, current versus historical boundaries,
   navigation and size. They are retired on purpose.

### Reviewer pass 3 (impl-plan, codex reviewer)

The concern is whether the protocol and companion check can be implemented from the same interface without guessing, while making the retired Scout coverage explicit.

#### Blocking issue

1. **Pass 1 thread 2 remains open in one respect.** The compact contract specifies the rule, record, and failure formats, but its “opt-in field” still says only that `.agent-protocols/context.md` *names* the docs-check command. It gives no literal field name or syntax for the companion check to read. Specify that declaration in the plan; a single example line would suffice.

#### Resolved thread

- **Pass 1 thread 3 — Resolved.** “What Replaces The Two Scout Subskills” now explicitly lists the discovery duties retired without replacement, including older misleading claims, source-of-truth duplication, and unclear current versus historical boundaries.

#### Non-blocking issues

None.

#### Overall judgment

**Not ready for implementation** until the opt-in declaration is specified. Thread 3 is closed; thread 2 remains open only for that interface detail.

#### Validation gap

This read-only review ran no tests. The companion PR should test that a required scope-review record is rejected when absent; consumer CI should verify the migrated configuration.

#### Driver reply to pass 3

1. The opt-in is now a literal line, `- Docs check: \`<command>\`` in
   `.agent-protocols/context.md`, with an example; `editing-rules` states the
   same line.

### Reviewer pass 4 (impl-plan, codex reviewer)

#### Blocking issues

None.

#### Resolved thread

- **Pass 1 thread 2 — Resolved.** The plan now specifies the literal `- Docs check:` declaration in `.agent-protocols/context.md` and gives an example command. The remaining interface detail identified in pass 3 is closed.

#### Overall judgment

**Ready for implementation.** All blocking review threads are closed.

#### Validation gap

This read-only review ran no tests. The companion PR should test rejection of an absent required scope-review record; consumer CI should verify the migrated configuration.

### Reviewer pass 1 (impl, codex reviewer)

The concern is whether the new document protocols match the accepted plan, remain conditional for wired repos, and preserve the stated Scout and approval boundaries.

#### Blocking issues

1. **Gated rule changes have conflicting owners.** In `editing-rules/SKILL.md`, a `sys` rule change waits for the human, while an unchanged rule move and a release or operations process rule change are assigned to the master. A `sys` release rule could match both lists. State that the human-owned category takes precedence, and limit the master-owned move and process cases accordingly.

2. **New duties reach repos that have not wired the check.** `editing-rules/SKILL.md` tells unwired repos to follow the new placement and format rules, and `planning/SKILL.md` applies “How Rules Move” without a wired-repo condition. The plan says every new duty is conditional. Restrict those instructions to wired repos.

3. **Scout’s replacement claim contradicts the plan.** `scout/SKILL.md` says the doc watcher follows documentation structure and drift after each merge. The accepted plan explicitly retires older-document discovery and structure checks without replacement. Describe only the watcher’s actual after-merge duty.

4. **The new reviewer prompt contains product names.** `scope-review/SKILL.md` lines 122–124 name external products, contrary to the stated public-repo constraint. The questions can remain without those labels.

#### Non-blocking issues

None.

#### Plan traceability

| In-scope item | Status | Evidence |
| --- | --- | --- |
| New protocols and role files | Partial | Files are present; the ownership and wired-repo conflicts above remain. |
| Integrations with existing protocols | Partial | Planned edits are present; `planning/SKILL.md` needs the wired-repo condition. |
| Scout retirement and test changes | Partial | Runner and test edits match the planned removal; `scout/SKILL.md` misstates replacement coverage. |
| Index updates | Done | Planned indexes include the new protocols and remove the retired Scout references. |
| Check, runner, and consumer rollout | Deferred | Assigned by the accepted plan to separate PRs. |

#### Overall judgment

**Not ready for closeout** until the four blocking issues are resolved.

#### Residual risks and validation gaps

No local tests were run, as instructed. No CI result was supplied. CI should run `python -m unittest discover -s scout/tests`, including the retired-subskill rejection test.

#### Driver reply to impl pass 1

1. `editing-rules`: an item that fits several lists belongs to the first, so
   the human's list wins; the master's "moved" and "release or operations"
   items are limited to directory rules.
2. `editing-rules` now applies only in a wired repo (unwired repos keep their
   current practice); `planning` "How Rules Move" is conditional too.
3. `scout/SKILL.md` now names only the watcher's after-merge duty and says
   other document discovery is retired.
4. The reviewer prompt drops the source labels; the three questions stay.

### Reviewer pass 2 (impl, codex reviewer)

The concern is whether the protocols follow the accepted plan, apply only in wired repos, and preserve the agreed Scout and approval boundaries.

#### Blocking issue

1. **The new precedence rule overrides two “no stop” cases.** `editing-rules/SKILL.md` says the first matching list wins, but its master-owned list includes any directory rule or exception under one. Deleting an expired directory-rule exception therefore requires a master answer, despite the later “No stop” entry. Renaming a directory with its `AGENTS.md` has the same conflict. The plan and `scope-review/SKILL.md` explicitly exclude both from review signals. Narrow the master-owned entries or state that these two exclusions are classified before the gated lists.

#### Resolved threads from impl pass 1

- **Thread 1 — Resolved for the reported `sys` conflict.** Human-owned changes take precedence, and the move and release-process entries now specify directory rules.
- **Thread 2 — Resolved.** `editing-rules` and planning’s “How Rules Move” section now apply only in wired repos.
- **Thread 3 — Resolved.** Scout now describes only the watcher’s after-merge duty and states that other document discovery is retired.
- **Thread 4 — Resolved.** The reviewer prompt retains the three questions and removes the product labels.

#### Non-blocking issues

None.

#### Plan traceability

| In-scope item | Status | Evidence |
| --- | --- | --- |
| New protocols and role files | Partial | Present; the new precedence rule has the conflict above. |
| Integrations with existing protocols | Done | The planning condition and relevant role and workflow edits are present. |
| Scout retirement and test changes | Partial | Removal and a rejection test are present; no execution result was supplied. |
| Index updates | Done | The planned indexes include the new protocols and retirement. |
| Check, runner, and consumer rollout | Deferred | Assigned to separate PRs by the accepted plan. |

#### Overall judgment

**Not ready for closeout** until the precedence conflict is resolved.

#### Residual risks and validation gaps

This read-only review ran no tests, as instructed. No CI result was supplied. CI should run `python -m unittest discover -s scout/tests` and report the retired-subskill rejection test result.

#### Driver reply to impl pass 2

1. `editing-rules`: the "No stop" cases (an exception ending, a directory
   renamed with its `AGENTS.md` whole, and the rest) are sorted out first;
   only then does the first matching list win.

### Reviewer pass 3 (impl, codex reviewer)

#### Blocking issues

None. The precedence thread is resolved: `editing-rules/SKILL.md` now classifies “No stop” cases before applying the human and master lists. Deleting an ended exception and renaming a directory with its `AGENTS.md` whole therefore bypass those lists. The changed lines introduce no new blocking issue.

#### Resolved thread

- **Impl pass 2 precedence thread — Resolved.**

#### Overall judgment

**Ready for closeout on the reviewed change.** The worktree is clean.

#### Residual validation gap

No CI result was supplied, and this read-only review ran no tests. Closeout should obtain the result of `python -m unittest discover -s scout/tests`, including the retired-subskill rejection test.

#### Driver note after impl review

Aligned with the companion PR: runner `scope-review/run_scope_review.py`;
settings `.agent-protocols/docs-check.json`, whose presence is the opt-in
(replacing the `- Docs check:` line in `context.md`); run log from env
`SCOPE_REVIEW_LOG` or the config's `scope_review.log`; `Rules-read:` read from
every commit in base..HEAD.

### Reviewer pass 4 (impl, codex reviewer)

The concern is whether the branch consistently uses the revised companion interface and keeps public-repo content private.

#### Blocking issues

None. The active plan and protocol text use `scope-review/run_scope_review.py`, opt in through `.agent-protocols/docs-check.json`, select the run log from `SCOPE_REVIEW_LOG` or `scope_review.log`, and specify reading `Rules-read:` from every commit in `base..HEAD`. The old `context.md` opt-in appears only in preserved historical review threads. No `.sh` runner reference or new private detail was found in the branch diff.

#### Non-blocking issues

None.

#### Plan traceability

| In-scope item | Status | Evidence |
| --- | --- | --- |
| Companion interface edits | Done | The active plan, `editing-rules/SKILL.md`, `scope-review/SKILL.md`, `line-worker/SKILL.md`, and `docs/CURRENT.md` agree on the revised interface. |
| Protocols, integrations, Scout retirement, and indexes | Done by inspection | The planned files and edits are present in the branch diff. |
| Scout test execution | Partial | The rejection test is present; no CI result was supplied. |
| Check, runner, and consumer rollout | Deferred | The plan assigns these to separate PRs. |

#### Overall judgment

**Ready for closeout on the reviewed change.** This is not a merge-readiness judgment.

#### Residual validation gap

This read-only review ran no tests. Closeout should obtain the CI result for `python -m unittest discover -s scout/tests`, including the retired-subskill rejection test.

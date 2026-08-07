# Evidence Discipline Rules For Review And Closeout

Status: plan, review pass 1 resolved; ready for implementation
Owner: `feature/evidence-discipline-rules`
Worktree: `../agent-protocols-evidence-discipline`
Base: `origin/main` @ `cba0229`
Created: 2026-08-07

## Source

A 14-hour multi-agent session in a downstream project (`skynet-intern`,
2026-08-06/07: ~17 PRs merged, one production deploy, one production acceptance,
one six-hour GitHub Actions outage) produced a retrospective. Its findings were
classified `General` / `Project-specific` / `Hybrid` per
`retrospective/SKILL.md`. The project-specific half is landing in that repo as
two CI checks, overlay rules, and backlog items. This plan lands the general
half here.

The downstream retrospective and its routing table live at
`docs/collaboration/2026-08-07_session_retrospective_zh.md` in that project. This
plan does not depend on it; each rule below is justified from its own failure.

**Evidence reach, stated plainly.** A reviewer working from this repository
cannot verify any of the failures below — they happened in another repository,
and this one has no access to it. Every item is therefore reported at the
strength its own record supports: items 1-5 are recorded in commit messages,
plan bodies, or workflow files in the downstream repository and can be checked
by anyone with that checkout; item 6 is a driver report with a correction noted
inline; item 7 was re-derived in this repository during this review pass. If any
characterization is wrong, the rule derived from it inherits the error, and
nothing here would catch that.

## The Failures These Rules Come From

Reducible to two questions nobody asked: *has this detector ever been shown to
fire?* and *which commit is this evidence about?*

1. **The strongest case, and the reason rule A has two clauses.** A deploy-helper
   change carried a blocking review finding about whether re-running the switch
   phase could leave the rollback pointer equal to the live pointer — the exact
   state the rollback path is specified to refuse. **Three independent review
   passes judged that finding resolved.** Later, to close a different finding,
   the driver built the thing all three passes had recorded as an unclosable
   residual: a harness that renders each phase and *executes* it against
   throwaway repositories with the privileged commands stubbed. Running it turned
   that finding red immediately. The cause was that one side of the guard's
   comparison had been resolved through a symlink-resolving read while the other
   was the operator's raw string, so the branch the entire protection turns on
   was taken only for paths that happen to resolve to themselves. The same run
   surfaced two more defects, one of them introduced by the fix to the first. The
   driver's own conclusion: the first two were not the kind of defect reading
   finds. Two of the three would have reached production.
2. A test asserting that a trial path and the production path produce identical
   output opened by asserting the target had no custom configuration — the one
   condition under which the two paths could not diverge. The only test
   guaranteeing the property covered only the case that could not violate it.
3. A test enforcing "this disclosure must be removed everywhere at once" keyed on
   a backlog ID string that also appeared in an unrelated inventory line and an
   archived review thread. Deleting the real disclosure left it green. The
   driver's own summary: enforcement was verified to exist, not to reach.
4. A CI gate forbidding in-place repository mutation matched a bare command name
   and would have passed on the exact incident it was written for, because the
   real invocation carried an intervening flag.
5. A reported "14 checks green" covered the parent commit, not the tip that added
   the test being reviewed. Caught only on a later review pass.
6. A monitoring predicate built on a relative-time file test, whose empty output
   was read as "nothing has been written". Re-checked on the same machine while
   writing this plan: the expression is not portable and is wrong under both
   implementations on that `PATH` — one rejects it as an unparseable timestamp,
   the other accepts it and matches everything. Neither behavior is the one the
   predicate assumed, and the predicate had never been run against a known-fresh
   file to find out. The precise failing mode at the time is a driver report; the
   non-portability is reproducible.
7. A registry checker that reports duplicate entries but is silent when a rebase
   deletes one. Three entries were lost in one night; one reached the default
   branch. **This repository has the same gap**: review pass 1 found that
   `AP-BL-0006`, which this plan had claimed as free, is already allocated on an
   unmerged branch. Re-derived here: `git log origin/main` says `AP-BL-0005` is
   the maximum, and a scan of every remote branch says `AP-BL-0006` is taken.
   The check that "confirmed" the ID was free could not see the branch that took
   it.

The common shape: the mechanism was believed because it was passing, and passing
was the only state it had ever been observed in. Item 1 is the strongest form —
there the mechanism was believed because *three reviews said so*, and no
execution existed to disagree.

## Rules To Add

Deliberately small: three bullets in two `SKILL.md` files, and two expanded
lenses in the already-required `structured-review` reference. Rationale lives in
the reference; `SKILL.md` keeps one imperative line each, matching the existing
bullet shape in those sections.

### `structured-review/SKILL.md`, `Shared Review Rules`

- Treat a mechanism described with enforcing verbs — enforces, prevents,
  guarantees, blocks, makes impossible — as unverified until a sample it must
  catch has been observed making it fail; record an unverified guard as a
  blocking issue or as a named residual risk rather than endorsing its passing
  state.
- Before treating an absence as a fact — no output, no match, no change, no
  error, no alert — require the positive control that shows the presence case is
  observable.

The `Reviewer Role` bullet proposed in the first draft is **dropped**. It said
the same thing to the same reader in the same file, and `Reviewer Role` already
carries "checks whether validation is strong enough", of which this is a
specialization.

### `structured-review/references/review-lenses.md`

A new lens, placed after `Validation First`, carrying the reasoning and the
second clause that failure 1 justifies:

- a check that has only ever been observed passing carries no information about
  what it would catch;
- ask which sample was used, from which direction, and what was observed —
  "the tests pass" is the claim under examination, not evidence for it;
- for claims that an action cannot happen in a given state — idempotency, state
  machines, rollback and recovery protection, re-run safety — reading and review
  do not constitute evidence. Require a test that executes the transition and
  observes the result. A finding of this class can be judged resolved by several
  independent review passes and still be false;
- a validator that constrains form is not a validator of meaning. Passing a
  character or shape constraint says nothing about whether the value is safe to
  act on.

Two sentences are added to the existing `Sample Data Before Endorsement` lens
pointing at the negative-evidence rule, so the two do not drift: the same
standard applies to a tool's silence as to a schema's existence.

### `closeout/SKILL.md`, `3. Validation`

Placed immediately above the existing `For human-facing UI, dashboards, ...`
block, so that block reads as its elaboration:

- For work that has been deployed, contract, schema, migration, and health
  verification establish wiring only. Accept a human-facing flow only after one
  real interaction through the deployed path, performed after the deploy, and
  record what was exercised, what came back, and the provenance label. The human
  may perform it and the label is then `human acceptance`. If the deployed path
  is unreachable from the agent's environment, record the item `Partial` with a
  named owner instead of accepting it.

This reuses the provenance vocabulary already defined a few lines above it
(`CI-backed`, `reviewer-rerun`, `driver-reported`, `human acceptance`) rather
than inventing a second one, and it satisfies `retrospective/SKILL.md`'s
`Action Feasibility` rule by naming the fallback when the agent cannot reach the
deployed path.

### `closeout/SKILL.md`, `6. Git and Process Hygiene`

- Read CI status at the exact commit being handed off and record that commit.
  "The branch is green" is a claim about some commit; name which one, and say so
  when a later commit is not covered. Also name any suite excluded from the
  default run or configured not to block, so its silence is not read as a pass.

## Rules Deliberately Not Added

- **A liveness/watchdog rule.** The source session rewrote a stall detector 19
  times; every version until the last measured something correlated with
  progress rather than progress itself, so "unchanged" meant both "dead" and
  "busy on one long step". The generalizable core is already covered by the
  negative-evidence rule above. The remainder — alert on "no legitimate reason
  to be idle" rather than on "signal unchanged" — belongs to whatever surface is
  loaded when a driver decides how to monitor subagents. No `SKILL.md` is loaded
  then. The one always-loaded surface in the consumption model is the consuming
  repo's `AGENTS.md`, whose shape this repo owns through
  `agent-readiness/agents-bootstrap-template.md` — considered and rejected,
  because that template's own `Principles` say the bootstrap establishes
  coordinates and does not solve the next task. Per `Rule Economy` and
  `retrospective/SKILL.md`'s "if the right owner is unclear, say why and create a
  bounded follow-up instead of inventing a mechanism", this becomes a backlog
  item rather than a new protocol directory.
- **An identifier-discipline rule** ("read a flag, selector, path, pattern, or
  run ID's definition before putting it in a command whose result you will act
  on"). The claim in the first draft — that no reviewer or checklist is present
  at the moment the command is typed — was too broad, and review pass 1 was
  right that failure 4 in the list above is a counter-example: a wrong pattern
  that reached a committed CI gate is reachable by review, and rule A already
  reaches it. The genuinely unreachable subset is the typed-and-gone kind: a
  command-line flag that does not exist, a page selector guessed from a rendered
  screenshot, a "latest run" query that returns a different workflow's run.
  Those leave no artifact for anyone to review. Narrowed to that subset and
  deferred.
- **An implausible-measurement rule** ("if a number implies an impossible
  conclusion, suspect the measurement before acting on it"). Same reasoning:
  the session's instance — a misparsed timestamp implying a job had run 8.6
  hours under a 6-hour platform kill limit, which led to cancelling a healthy
  job — happened during execution, not during review or closeout. Backlog item,
  grouped with the identifier rule; both belong to a possible future
  execution-discipline surface, and inventing that surface for two bullets is not
  justified yet.

## Change Set

| Path | Change |
| --- | --- |
| `structured-review/SKILL.md` | two bullets in `Shared Review Rules` |
| `structured-review/references/review-lenses.md` | one new lens after `Validation First`; two cross-reference sentences in `Sample Data Before Endorsement` |
| `closeout/SKILL.md` | one bullet in `3. Validation` above the human-facing block, one in `6. Git and Process Hygiene` |
| `docs/backlog.yml` | register `AP-BL-0007`, `AP-BL-0008` |
| `docs/CURRENT.md` | no change expected; neither protocol's description in that map becomes false |
| `docs/agent_plans/README.md` | index this plan |

**Backlog IDs.** `origin/main` is at `AP-BL-0005`, but `AP-BL-0006` is already
allocated to a different open item on the unmerged branch
`origin/codex/backlog-structured-review-runner-false-failure`. Taking `0006`
here would collide at merge time on whichever branch lands second. This branch
therefore takes `AP-BL-0007` and `AP-BL-0008`, chosen by scanning every remote
branch rather than `origin/main` alone. Checked for overlap per
`backlog-maintenance/SKILL.md`: `AP-BL-0001` (protocol self-evolution workflow)
and `AP-BL-0004` (dogfood structured review) are adjacent but distinct.

Both items are `kind: process`, `status: open`:

- `AP-BL-0007`, P2 — no protocol surface is loaded at the moment an agent types
  a command or reads a measurement, so the identifier and implausible-measurement
  rules have no reachable home. `done_when`: either an execution-discipline
  surface exists and carries them, or the item closes as `cancelled` with the
  reason that no such surface is worth its maintenance cost.
- `AP-BL-0008`, P2 — subagent liveness monitoring has no owning protocol; the
  "alert on no legitimate reason to be idle" rule has nowhere to live.
  `done_when`: same shape — an owning surface exists, or the item closes as
  `cancelled` with the reason recorded.

## Acceptance

- The three `SKILL.md` bullets read as operating instructions: each is one
  imperative line a reviewer or closeout driver can act on without reading this
  plan or the reference.
- No rule can be satisfied by an assertion or by asking. Rule A names a state
  (observed failing) and a consequence (blocking issue or named residual risk);
  the negative-evidence rule names a positive control; the deploy-acceptance rule
  names a recorded interaction with a provenance label and a `Partial` fallback;
  the CI rule names a commit.
- No duplication, within a file or across files: the `Reviewer Role` bullet is
  dropped, the rationale sits only in `review-lenses.md`, and
  `Sample Data Before Endorsement` cross-references the negative-evidence rule
  rather than restating it.
- `python scripts/check_backlog.py` passes — that is the shape floor only. The
  real acceptance for the two new items is implementation-review judgment on
  whether `why` / `next` / `done_when` are useful, which that script explicitly
  does not check.
- **Lifecycle.** These rules are durable protocol checklist entries and fall
  under `Skill Self-Evolution`'s prune clause. The staleness signal is a rule
  that never triggers: if a year of reviews produces no finding under rule A, or
  no closeout ever records a `Partial` for an unreachable deployed path, that is
  the signal to merge or delete it rather than to keep it. `AP-BL-0004` already
  watches this repo for the drift of turning one session's friction into
  permanent protocol text; these four rules are in its scope.
- Not part of this change's acceptance: whether the downstream project's overlay
  clauses are consistent with these rules. Nothing in this repository can check
  that. It moves to the downstream follow-up described under Review Path.

## Review Path

- Plan review: `structured-review`, `Type: other-plan`, `normal` tier. This is a
  skill self-evolution change, so per `Skill Self-Evolution` it is treated as a
  plan-revision pass with explicit reviewer and driver roles. **Pass 1 complete;
  three blocking threads, all accepted.**
- Implementation review after the edits land on the branch.
- Closeout, then PR handoff. This agent does not merge.

Downstream sequencing: the consuming project pins this repo as a submodule and
its closeout overlay forbids handing off a parent PR that points at a feature
branch here. The downstream PR therefore does **not** move its submodule
pointer; the bump is a separate follow-up after this PR merges, tracked in that
project's backlog, and that follow-up owns checking the overlay clauses against
the rules landed here.

## Review Threads

_None yet._

I've inspected the plan, both target skills, the required references, the backlog registry and its validator, CI, and the branch/remote state. Here is the complete review thread.

---

### Reviewer pass 1 (other-plan, claude reviewer)

Driver's concern, restated: are these four rules real operating instructions that add something the existing protocols don't already say, is the "not added" section honest, and are the backlog IDs right?

Verified before judging: base is `origin/main` @ `cba0229` (confirmed), artifact committed at `d1812e4`, branch not pushed (confirmed — no `origin` ref contains it), worktree clean. `docs/backlog.yml` is unchanged from `origin/main` on this branch. I read `structured-review/SKILL.md`, `closeout/SKILL.md`, both required references, `retrospective/SKILL.md`, `backlog-maintenance/SKILL.md`, `scripts/check_backlog.py`, `.github/workflows/ci.yml`, and the repo indexes. I did not read the downstream `skynet-intern` retrospective or its overlay — no access from this worktree — so every claim in `## Source` and `## The Failures These Rules Come From` is taken as given and is not independently verified. The plan says it does not depend on that document, which is the right call.

### Reviewer pass 1 (impl, codex reviewer)

Driver concern, restated: verify that the four evidence-discipline rules landed exactly as accepted, require evidence rather than mere asking, avoid duplicated guidance, and register useful deferred backlog decisions.

Verified: `db4e43c` descends from `origin/main @ cba0229`; the worktree is clean and the branch is unpushed. I reviewed the accepted pass-1 response and all requested artifacts.

## Blocking issues

None.

## Non-blocking issues

### Thread 1: Plan text miscounts the implemented operating bullets

`docs/agent_plans/2026-08-07_evidence_discipline_rules_plan.md:90` and `:230` say there are “three” `SKILL.md` bullets, but the accepted response and landed implementation contain four: two in `structured-review/SKILL.md` and two in `closeout/SKILL.md`. Correct this count, and update the plan status from “ready for implementation” during the driver’s next plan-thread response.

## Overall judgment

Ready for closeout.

Traceability is complete:

| Accepted item | Result |
| --- | --- |
| Guard must have an observed failing sample; otherwise block or name residual risk | Done in `structured-review/SKILL.md:253` |
| Absence requires an observable positive control | Done in `structured-review/SKILL.md:257` |
| Guard rationale, failure shapes, state-transition execution requirement, and form-vs-meaning distinction | Done in `structured-review/references/review-lenses.md:21` |
| Prevent drift with the negative-evidence cross-reference | Done in `structured-review/references/review-lenses.md:152` |
| Post-deploy human-facing acceptance evidence, human owner, and `Partial` fallback | Done in `closeout/SKILL.md:172` |
| CI status pinned to the handoff commit | Done in `closeout/SKILL.md:326` |
| `AP-BL-0007` and `AP-BL-0008` | Done in `docs/backlog.yml:102` and `:138` |

The four rules no longer reduce to asking alone: the first requires an observed failing sample, the second an observable positive control, the third a recorded deployed-path interaction and provenance, and the fourth the exact recorded commit. They remain reviewer-operated controls rather than executable enforcement, which is an inherent residual limitation, not a mismatch with the accepted scope.

`Guard Reach` is a useful specialization of `Validation First` and `Mechanism Lifecycle`, not a duplicate: it tests a guard’s discriminatory reach across both durable and non-durable mechanisms. The short `SKILL.md` bullets supply operating decisions; the reference holds rationale and examples. The closeout deploy rule is correctly positioned as a prerequisite to the UI checks below it, not a duplicate. Its `Partial` fallback is consistent with the existing traceability-status vocabulary, while provenance remains one of the four labels defined immediately above.

Both backlog items meet the open-item schema, use valid `P2`/`process` fields, include references, and have real closure decisions—either establish an owning execution/monitoring surface or explicitly cancel with rationale—rather than aspirational completion statements.

## Residual risks and validation gaps

- The downstream-session facts remain driver-reported and cannot be independently verified from this repository, as the plan already discloses.
- Reviewer-rerun validation passed: `git diff --check cba0229...db4e43c`, `python scripts/check_backlog.py`, 18 general tests, 87 structured-review tests, 31 Scout tests, and compilation of `structured-review` and `scout`.
- No remote CI run covers unpushed `db4e43c`; closeout should report that provenance plainly.

## Blocking issues

### Thread 1: Rule A can be satisfied by asking, which is the failure it exists to prevent

Plan lines 63-66. The rule's verb is "ask for the sample that made it fail and the observed failure." A reviewer satisfies "ask for X" by asking, whether or not X arrives. The rule states no consequence for the case that matters most — the artifact says a guard enforces something, the reviewer asks, and the answer is "it has always been green." Nothing in the bullet tells the reviewer what to do then.

This directly contradicts the plan's own acceptance criterion at lines 142-143: "No rule in this change could be satisfied by an assertion alone — each names an artifact the agent must produce." Rule A names an artifact the reviewer must *request*, not one the reviewer must *receive* before endorsing.

Note that the `Reviewer Role` bullet at line 74 is already the stronger formulation — "checks whether each claimed guard **has been shown** to fail on a sample it must catch." That is a state check, not a speech act. The cheapest fix collapses this thread and Thread 4 together: give the `Shared Review Rules` bullet the state-check verb and a stated consequence (for example: treat a guard with no observed failure as unverified and record it as a blocking issue or a named residual risk), and then drop the redundant `Reviewer Role` bullet.

### Thread 2: Rule C names an event, not an artifact, and names nobody to perform it

Plan lines 80-82. Two problems in one bullet.

First, artifact. "Acceptance of a human-facing flow requires one real interaction through the deployed path" — an interaction is an event that leaves no trace unless the rule says what to record. Compare the other three rules, which name a sample, a positive control, and a commit SHA. `closeout/SKILL.md:163-170` already has the machinery this bullet should reuse: name the command/screenshot/log excerpt/human observation that proves the item, record the expected shape, and label provenance as CI-backed, reviewer-rerun, driver-reported, or human acceptance. As drafted, Rule C is the one bullet in this change that a closeout driver can mark `Done` from memory — which is what `closeout/SKILL.md:344` already tries to prevent.

Second, feasibility and ownership. The rule says the interaction is required but not who performs it or what happens when the agent cannot reach the deployed path (no credentials, no browser, human-owned environment). This repo's own `retrospective/SKILL.md:132-142` (`Action Feasibility`) says not to record a control that requires capabilities the agent does not have, and to route to the earliest executable point instead. `closeout/SKILL.md:198` already handles the analogous case for acceptance servers by naming the owner. Rule C should say the interaction may be human-performed with `human acceptance` provenance, and that unavailable access is recorded as `Partial` with a named owner rather than skipped silently.

Fix: add the recorded evidence (what was done, what came back, provenance label) and the performer/fallback to the bullet, or state that both are inherited from the existing §3 provenance block and place the bullet so that inheritance is visible (see Thread 6).

### Thread 3: `AP-BL-0006` is already claimed by a live unmerged branch

Plan lines 131-133 state that `origin/main` is at `AP-BL-0005` and this branch takes `AP-BL-0006` and `AP-BL-0007`. The first half is correct. The conclusion is not safe: `origin/codex/backlog-structured-review-runner-false-failure` (`dd41581`, 2026-06-13) already allocates `AP-BL-0006` in `docs/backlog.yml` to a different item — "Fix structured-review runner false failure after committing review text", P1 bug. That branch is not an ancestor of `origin/main`; it is still pending.

`backlog-maintenance/SKILL.md:174` says "Never reuse an ID, even after the item closes." Whichever branch merges second either collides or silently renumbers. `scripts/check_backlog.py:105` enforces uniqueness within the file, so a textual merge that keeps both entries fails CI — a loud failure, but at merge time, on someone else's branch. The plan should state the resolution now: take `0007`/`0008`, or record that the codex branch is abandoned and this branch reclaims `0006`, or state that final IDs are assigned at rebase time by whoever merges second. Any of the three is fine; asserting `origin/main` is the only claimant is not, and the check that "confirms" it is `git log origin/main` — a green signal with no reach, which is the shape this plan is about.

Two smaller items in the same cluster, since they land in the same file:

- The plan specifies only parenthetical titles for the two items. `backlog-maintenance/SKILL.md:246-255` requires `id`, `status`, `priority`, `kind`, `title`, `why`, `next`, `done_when` for open items. The implementing agent will invent `priority`, `kind`, and all three prose fields. Stating `kind: process`, a priority, and the shape of `done_when` (for both items the honest `done_when` is a decision — the surface exists, or the item closes as `cancelled`) costs two lines here and removes the guessing.
- Acceptance criterion 4, "`docs/backlog.yml` validates" (line 144), is `python scripts/check_backlog.py` (`.github/workflows/ci.yml:27-28`). That check validates shape only. `backlog-maintenance/SKILL.md:378-380` says out loud that priority choice, kind choice, and whether `why`/`next`/`done_when` are useful are review-owned, not CI-owned. Citing that check as the acceptance for these two items is a passing check that carries no information about what the plan actually cares about. Name the human/impl-review judgment as the real acceptance, with the script as the shape floor.

Also worth recording in the plan: `backlog-maintenance/SKILL.md:300` requires searching existing items for overlap. I checked — `AP-BL-0001` (protocol self-evolution workflow) and `AP-BL-0004` (dogfood structured review) are adjacent but not duplicates of either new item. Say that you checked.

## Non-blocking issues

### Thread 4: the `Reviewer Role` bullet duplicates the new `Shared Review Rules` bullet in the same file

`Shared Review Rules` (`structured-review/SKILL.md:246`) is not role-gated; `Reviewer Role` (`:271`) is. A reviewer therefore reads both. Plan line 74 restates plan lines 63-66 for the same reader, and both are specializations of the existing `:280` "checks whether validation is strong enough." That is a three-way overlap in one file, against `Skill Self-Evolution`'s "periodically prune, merge, or shorten rules that overlap." Acceptance criterion 2 (line 140) claims "nothing is duplicated between them," which reads as file-to-file; the duplication here is within one file. Recommend merging into the single `Shared Review Rules` bullet as described in Thread 1, and widening acceptance criterion 2 to cover within-file duplication.

### Thread 5: altitude — the rationale sentences belong in `review-lenses.md`, and that reference is already runner-loaded

The plan says "no new reference file" (line 57) and treats that as the minimal option. But the choice is not "SKILL.md bullet vs. new reference" — `structured-review/references/review-lenses.md` already exists, is listed as required at `structured-review/SKILL.md:40-46`, and is loaded into every runner-driven reviewer prompt. Putting the expanded form there loses no reach at all.

Concretely: the second sentence of each structured-review bullet is explanation, not instruction — "A check that has only ever been observed passing carries no information about what it would catch" and "A tool that fails quietly needs one positive control before its silence means anything." Every existing `Shared Review Rules` bullet is one imperative line. Two four-line bullets roughly double that section. Rule B in particular has an obvious home next to `Sample Data Before Endorsement` in `review-lenses.md`, which already says "treat 'the field exists' as insufficient evidence that it is usable" — Rule B is the general case of that.

The asymmetry is worth naming in the plan: `closeout/` has no references directory, so its two bullets must stay in `SKILL.md`; `structured-review/` does, so its bullets have a cheaper home. Either split accordingly, or state why you rejected the split.

### Thread 6: Rule C's placement relative to the existing human-facing block

`closeout/SKILL.md:172-179` already requires opening/rendering the output, exercising visible controls rather than page load, covering normal / empty / recovery paths, and saving the evidence. `closeout/SKILL.md:121-124` already says "deployment succeeded" and "production smoke is green" are not proof of completeness.

What Rule C genuinely adds — and it is real — is that the interaction must go *through the deployed path*, *after the deploy*, and that contract/schema/migration/health checks establish wiring only. The existing UI bullets can all be satisfied on a local server before deploy. But the plan says "In `3. Validation`" without saying where, and a reader landing on two overlapping demands has to reconcile them. Recommend placing Rule C immediately above the "For human-facing UI..." block so that block reads as its elaboration, and say so in the plan.

### Thread 7: `Rules Deliberately Not Added` is honest, with one overstated claim and one imprecise premise

Overall this section is the strongest part of the artifact and I do not read it as avoiding work. It gives reasons rather than gestures, it routes to backlog exactly as `retrospective/SKILL.md:117` prescribes ("if the right owner is unclear, say why and create a bounded follow-up instead of inventing a mechanism"), and the liveness and measurement exclusions each cite a concrete instance. Two corrections:

- The identifier-discipline exclusion (lines 105-111) claims seven instances and cites none, while every other failure in the document is described concretely. A reader cannot check the load-bearing claim that "neither a reviewer nor a closeout checklist is present at the moment the command is typed." More pointedly, failure 3 in this plan's own list (lines 37-39 — a CI gate matching a bare command name, defeated by an intervening flag) looks like a member of that class, and it is a *committed artifact*: a reviewer reading that gate could have asked for the sample that makes it fire, which is precisely Rule A. So "cannot reach" is overstated for at least part of the cluster. Either cite one or two of the seven and show they are unreachable, or narrow the claim to the subset that is genuinely typed-and-gone.
- "no skill is loaded at that moment" (lines 99-100, 109-111) is accurate for skills under this repo's consumption model — skill mounts are cataloged at startup and bodies load on invocation, per `AP-BL-0003`'s recorded outcome and `README.md` Canonical Source. But the repo is not without an always-loaded surface: consuming repos carry their own `AGENTS.md` and `.agent-protocols/context.md`, and this repo owns the template that shapes the first of those (`agent-readiness/agents-bootstrap-template.md`). That template's own `Principles` say "Keep startup small. The bootstrap establishes coordinates; it does not solve the next task" — which is a good reason to reject it as a home, but the plan should say it considered and rejected it rather than saying no home exists. One sentence.

### Thread 8: acceptance criterion 5 is not checkable from this repo

Line 145-146: "The downstream project's overlay clauses are more specific than these rules and do not contradict them." No overlay file is named, no repo path is given, and nothing in this worktree can verify it. As written it is an acceptance row that can only be marked `Done` by assertion. Either name the overlay files and who checks them with what provenance, or move it out of this change's acceptance into the downstream follow-up you already describe at lines 156-160.

### Thread 9: no lifecycle statement for the four new rules

`references/review-lenses.md` (`Mechanism Lifecycle`) lists "protocol checklists" as a durable mechanism and asks for the staleness signal and the removal path. These four rules are derived from one session, and this repo already carries `AP-BL-0004` to watch for exactly the drift of turning real-artifact friction into protocol text. `Skill Self-Evolution` covers pruning in general, so the owning mechanism exists — but one line in the plan saying these rules are subject to that prune rule, and what "this rule never triggers" would look like, closes the lens cheaply.

## Overall judgment

Not ready for implementation as drafted. Three blocking threads, all with small fixes; none requires rethinking the approach.

The approach is right and the artifact is well above average for this repo: goal is clear, the non-goals section is genuinely good, the rule text is verbatim so implementation needs almost no guessing, the change set is complete (I checked — `README.md`, `docs/README.md`, and `AGENTS.md` do not require updates under their own maintenance rules, and the `docs/CURRENT.md` "only if stale" conditional is correct, since neither protocol's description in that map turns false), and the downstream submodule sequencing at lines 156-160 matches `closeout/SKILL.md:260-271` rather than contradicting it.

On the driver's specific questions:

1. Rules B and D are clean additions. Rule B's nearest neighbors are `Sample Data Before Endorsement` in `review-lenses.md` and closeout's "distinguish 'not yet enough data' from 'broken' and from 'not checked'"; it generalizes both and adds the positive control, which neither has. Rule D is the strongest of the four — `closeout/SKILL.md:313` says "pushed CI is in the expected state" but pins no commit, and the SAFETY bullet at `:82` forbids claiming without checking but says nothing about checking the wrong commit. Rule A overlaps `Check what proves success, who can verify it, and what would falsify it` less than it appears: that bullet is about falsifying the artifact's success claim, Rule A is about the discriminating power of a detector. Different question, worth having. Rule C overlaps the existing UI bullets more than the others and needs the placement fix, but "after the deploy, through the deployed path, and wiring checks are only wiring" is not said anywhere today.
2. Honest judgment, not avoidance — with the two corrections in Thread 7.
3. Two of four are satisfiable without producing evidence: Rule A (Thread 1) and Rule C (Thread 2). Rules B and D name an artifact.
4. It stays a checklist in shape, but the structured-review half pushes explanation into `SKILL.md` when a runner-loaded reference is already available at no cost to reach (Thread 5).
5. ID arithmetic is right against `origin/main` and wrong against reality (Thread 3); the item bodies are under-specified against the required-field list.

## Residual risks and validation gaps

- Everything about the source session is unverified from here. If any of the six failures is mischaracterized, the rule derived from it inherits the error, and nothing in this repo would catch that.
- Four rules from one session is real bloat pressure on two files that are already long. `Rule Economy` in `retrospective/SKILL.md:125-130` and the prune clause in `Skill Self-Evolution` both point the same way; the driver owns that call, and Threads 4 and 5 are where it gets exercised.
- If Rule B stays in `SKILL.md` while `Sample Data Before Endorsement` stays in `review-lenses.md`, the two will drift. Whichever placement wins, the other should cross-reference rather than restate.
- Rule D's third clause ("name any suite excluded from the default run or configured not to block") has no instance in this repo to validate against — `.github/workflows/ci.yml` is a single job in which every step blocks. The clause will first be exercised downstream, unreviewed here.
- Branch is unpushed, so no CI has run against `d1812e4`. Nothing on this branch touches code, so that is expected rather than a gap — but per Rule D's own logic, note that "CI is green" for this work currently refers to `cba0229`, not to the tip.

---

### Driver response to reviewer pass 1

All three blocking threads **accepted**. Non-blocking threads 4 through 9 all
accepted. Thread 3's factual claim was re-derived here before acting on it.

**Thread 1 — accepted.** Rule A was satisfiable by asking, which is the failure
it exists to prevent, and it contradicted this plan's own acceptance criterion.
Rewritten as a state check with a stated consequence: treat the mechanism as
unverified until a sample it must catch has been observed making it fail, and
record an unverified guard as a blocking issue or a named residual risk. The
`Reviewer Role` bullet is **dropped** rather than kept, per the reviewer's
"cheapest fix" — it said the same thing to the same reader in the same file.

**Thread 2 — accepted, both halves.** Rule C now names the artifact (what was
exercised, what came back, and a provenance label drawn from the vocabulary
already defined a few lines above it in the same section) and the performer and
fallback (the human may perform it, label `human acceptance`; an unreachable
deployed path is recorded `Partial` with a named owner rather than skipped). The
`Action Feasibility` point was the right lens — a control the agent cannot
execute has to name who can.

**Thread 3 — accepted, and verified independently before acting.**
`origin/codex/backlog-structured-review-runner-false-failure` does allocate
`AP-BL-0006` to a different open P1 bug. I re-derived it by scanning every remote
ref rather than trusting the finding: `origin/main` maximum is `AP-BL-0005`, and
that branch is the only ref carrying `0006`. This branch now takes `AP-BL-0007`
and `AP-BL-0008`. Both items are specified with `kind`, priority, and the shape
of `done_when` so the implementing agent invents nothing, and the overlap check
against `AP-BL-0001` and `AP-BL-0004` is recorded. Acceptance criterion 4 no
longer cites the shape checker as if it validated judgment; it names the checker
as a floor and implementation-review judgment as the real acceptance.

Worth naming plainly: this is the same failure the downstream retrospective is
about, committed inside the plan that routes its lesson — an ID confirmed free by
a command that could not see the branch that took it. It is now failure 7 in the
list below, cited as re-derived here rather than reported from elsewhere.

**Thread 4 — accepted.** Covered by dropping the `Reviewer Role` bullet.
Acceptance criterion 3 now says "within a file or across files".

**Thread 5 — accepted, and it was the better option.** The rationale sentences
move to `structured-review/references/review-lenses.md`, which is already in the
required-reference set and already loaded into every runner-driven reviewer
prompt, so nothing loses reach. `SKILL.md` keeps one imperative line per rule,
matching the existing bullet shape. The asymmetry is now stated: `closeout/` has
no references directory, so its two bullets stay in `SKILL.md`. Two
cross-reference sentences go into `Sample Data Before Endorsement` so it and the
negative-evidence rule do not drift, per the reviewer's residual risk 3.

**Thread 6 — accepted.** Rule C is placed immediately above the
`For human-facing UI, ...` block so that block reads as its elaboration, and the
plan says so.

**Thread 7 — accepted, both corrections.** The identifier-discipline exclusion
was overstated: failure 4 in the list is a committed CI gate, reachable by
review, and rule A already reaches it. The claim is narrowed to the
typed-and-gone subset that leaves no artifact — a flag that does not exist, a
selector guessed from a screenshot, a "latest run" query returning a different
workflow's run — and the examples are given. The "no loaded surface" premise now
records that the consuming repo's `AGENTS.md` was considered and rejected, with
the reason drawn from the bootstrap template's own `Principles`.

**Thread 8 — accepted.** The overlay-consistency criterion cannot be checked from
this repository and has been moved out of acceptance into the downstream
follow-up, which now explicitly owns it.

**Thread 9 — accepted.** Acceptance gains a lifecycle row: these rules fall under
`Skill Self-Evolution`'s prune clause, the staleness signal is a rule that never
triggers, and `AP-BL-0004` already watches this repo for exactly this drift.

**New material that arrived during this review pass.** The downstream session
produced one more case after the plan was committed, and it is now failure 1 —
the strongest of the set. A blocking finding about re-run safety was judged
resolved by **three independent review passes**, then went red on the first run
of an execution harness that all three passes had recorded as an unclosable
residual. This is materially stronger than failures 2 through 4: those were
checks written wrong, and a careful reader could have caught each. This one is
the case where no executable check existed and careful review repeatedly
concluded there was no problem. It adds a second clause to the new lens — for
claims that an action cannot happen in a given state (idempotency, state
machines, rollback and recovery protection, re-run safety), reading and review do
not constitute evidence; require a test that executes the transition — and a
fourth clause about form validation not being meaning validation, from the same
pass.

**On residual risk 1 in the review** (nothing about the source session is
verifiable from this repository): accepted and now stated in the artifact itself
under `Source`, with per-item strength labels rather than a uniform claim. One
item was corrected as a direct result: the monitoring-predicate failure was
re-checked on the machine in question while writing this response, and the
original characterization was imprecise. The corrected version is in failure 6.

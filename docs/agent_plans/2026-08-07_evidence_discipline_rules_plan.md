# Evidence Discipline Rules For Review And Closeout

Status: plan, awaiting plan review
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

## The Failures These Rules Come From

Four distinct incidents in one session, all reducible to two questions nobody
asked: *has this detector ever been shown to fire?* and *which commit is this
evidence about?*

1. A test asserting that a trial path and the production path produce identical
   output opened by asserting the target had no custom configuration — the one
   condition under which the two paths could not diverge. The only test
   guaranteeing the property covered only the case that could not violate it.
2. A test enforcing "this disclosure must be removed everywhere at once" keyed on
   a backlog ID string that also appeared in an unrelated inventory line and an
   archived review thread. Deleting the real disclosure left it green. The
   driver's own summary: enforcement was verified to exist, not to reach.
3. A CI gate forbidding in-place repository mutation matched a bare command name
   and would have passed on the exact incident it was written for, because the
   real invocation carried an intervening flag.
4. A reported "14 checks green" covered the parent commit, not the tip that
   added the test being reviewed. Caught only on a later review pass.

Two supporting failures share the second question's root:

5. A monitoring predicate using a relative-time file test that silently matches
   nothing on the host platform, read as "nothing was written".
6. A registry checker that reports duplicate entries but is silent when a rebase
   deletes one. Three entries were lost in one night; one reached the default
   branch.

The common shape: the mechanism was believed because it was passing, and passing
was the only state it had ever been observed in.

## Rules To Add

Deliberately small. Four bullets across two existing skills, no new skill, no new
reference file, no script.

### `structured-review/SKILL.md`

In `Shared Review Rules`:

- When an artifact says a mechanism enforces, prevents, guarantees, blocks, or
  makes something impossible, ask for the sample that made it fail and the
  observed failure. A check that has only ever been observed passing carries no
  information about what it would catch.
- Before treating an absence as a fact — no output, no match, no change, no
  error, no alert — establish that the presence case is observable. A tool that
  fails quietly needs one positive control before its silence means anything.

In `Reviewer Role`, add to the reviewer's list:

- checks whether each claimed guard has been shown to fail on a sample it must
  catch.

### `closeout/SKILL.md`

In `3. Validation`:

- For work that has been deployed, contract, schema, migration, and health
  verification establish wiring only. Acceptance of a human-facing flow requires
  one real interaction through the deployed path, performed after the deploy.

In `6. Git and Process Hygiene`:

- Read CI status at the exact commit being handed off and record that commit.
  "The branch is green" is a claim about some commit; name which one, and say so
  when a later commit is not covered. Also name any suite that is excluded from
  the default run or configured not to block, so its silence is not read as a
  pass.

## Rules Deliberately Not Added

- **A liveness/watchdog rule.** The source session rewrote a stall detector 19
  times; every version until the last measured something correlated with
  progress rather than progress itself, so "unchanged" meant both "dead" and
  "busy on one long step". The generalizable core is already covered by the
  negative-evidence bullet above. The remainder — alert on "no legitimate reason
  to be idle" rather than on "signal unchanged" — belongs to whatever skill is
  loaded when a driver decides how to monitor subagents, and no such skill
  exists. Per this repo's own `Rule Economy` and the retrospective protocol's
  "if the right owner is unclear, say why and create a bounded follow-up instead
  of inventing a mechanism", this becomes a backlog item rather than a new
  protocol directory.
- **An identifier-discipline rule** ("read a flag, selector, path, pattern, or
  run ID's definition before putting it in a command whose result you will act
  on"). Seven instances in one session, and it is real, but it is a working
  habit rather than a review or closeout gate: neither a reviewer nor a closeout
  checklist is present at the moment the command is typed. Adding it to a skill
  that is not loaded then would be a rule that cannot reach — the exact failure
  this plan is about. Backlog item.
- **An implausible-measurement rule** ("if a number implies an impossible
  conclusion, suspect the measurement before acting on it"). Same reasoning:
  the session's instance — a misparsed timestamp implying a job had run 8.6
  hours under a 6-hour platform kill limit, which led to cancelling a healthy
  job — happened during execution, not during review or closeout. The
  negative-evidence bullet does not cover it. Backlog item, grouped with the
  identifier rule; both belong to a possible future execution-discipline surface,
  and inventing that surface for three bullets is not justified yet.

## Change Set

| Path | Change |
| --- | --- |
| `structured-review/SKILL.md` | two bullets in `Shared Review Rules`, one in `Reviewer Role` |
| `closeout/SKILL.md` | one bullet in `3. Validation`, one in `6. Git and Process Hygiene` |
| `docs/backlog.yml` | register the two deferred rule clusters |
| `docs/CURRENT.md` | only if a description becomes stale |
| `docs/agent_plans/README.md` | index this plan |

Backlog IDs: `origin/main` is at `AP-BL-0005`; this branch takes `AP-BL-0006`
(execution-discipline surface: identifier and measurement rules have no loaded
home) and `AP-BL-0007` (subagent liveness monitoring has no owning protocol).

## Acceptance

- The four rules read as operating instructions, not as narrative. Each is one
  sentence a reviewer or closeout driver can act on without reading this plan.
- `structured-review/SKILL.md` and `closeout/SKILL.md` stay short checklists per
  the `Skill Self-Evolution` rule; nothing is duplicated between them.
- No rule in this change could be satisfied by an assertion alone — each names
  an artifact the agent must produce (a failing sample, a positive control, an
  interaction, a commit SHA).
- `docs/backlog.yml` validates.
- The downstream project's overlay clauses are more specific than these rules
  and do not contradict them.

## Review Path

- Plan review: `structured-review`, `Type: other-plan`, `normal` tier. This is a
  skill self-evolution change, so per `Skill Self-Evolution` it is treated as a
  plan-revision pass with explicit reviewer and driver roles.
- Implementation review after the edits land on the branch.
- Closeout, then PR handoff. This agent does not merge.

Downstream sequencing: the consuming project pins this repo as a submodule and
its closeout overlay forbids handing off a parent PR that points at a feature
branch here. The downstream PR therefore does **not** move its submodule
pointer; the bump is a separate follow-up after this PR merges, tracked in that
project's backlog.

## Review Threads

_None yet._

I've inspected the plan, both target skills, the required references, the backlog registry and its validator, CI, and the branch/remote state. Here is the complete review thread.

---

### Reviewer pass 1 (other-plan, claude reviewer)

Driver's concern, restated: are these four rules real operating instructions that add something the existing protocols don't already say, is the "not added" section honest, and are the backlog IDs right?

Verified before judging: base is `origin/main` @ `cba0229` (confirmed), artifact committed at `d1812e4`, branch not pushed (confirmed — no `origin` ref contains it), worktree clean. `docs/backlog.yml` is unchanged from `origin/main` on this branch. I read `structured-review/SKILL.md`, `closeout/SKILL.md`, both required references, `retrospective/SKILL.md`, `backlog-maintenance/SKILL.md`, `scripts/check_backlog.py`, `.github/workflows/ci.yml`, and the repo indexes. I did not read the downstream `skynet-intern` retrospective or its overlay — no access from this worktree — so every claim in `## Source` and `## The Failures These Rules Come From` is taken as given and is not independently verified. The plan says it does not depend on that document, which is the right call.

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

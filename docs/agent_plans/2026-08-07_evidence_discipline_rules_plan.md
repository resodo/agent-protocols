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

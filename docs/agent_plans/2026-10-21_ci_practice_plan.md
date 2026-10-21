# Plan: a shared CI practice protocol

Document level: plan (one small PR).

Source: resodo, 2026-10-21 (relayed by the master), approved writing the
organization's CI practice into agent-protocols: two-tier triggers
(pull-request and default-branch pushes light; full suite on a release
candidate and nightly), release gate on the exact SHA, runner choice by
measurement with a target wall time, caching, flaky-test policy, cost
tracking. Evidence: Thesis Room's CI work the same day (two-tier triggers,
a light-only `application` gate that a release check misread as a full result,
the separate `full-gate`, one-box runs measured on several machine types,
load-sensitive tests found when parallelism rose).

## Scope

- `ci-practice/SKILL.md` (new): the generic rules only. Project numbers
  (target wall times, runner labels, measured costs, cost line, flaky list
  location) go to each consumer's `.agent-protocols/ci-practice.md`.
- `README.md` and `docs/CURRENT.md`: list the new protocol (AGENTS.md rule for
  adding a protocol).

Not in scope: consumer overlays and submodule bumps (rollout after merge, per
AGENTS.md "Rollout To Consumers").

## Validation

- `python3 -m unittest discover -s tests` (frontmatter is strict YAML).
- Reading check against the 2026-10-21 Thesis case: the light gate reporting on
  push runs and the release check keying on it would violate "Two Tiers"
  (gate on its own events) and "Release Gate" (key on the full gate's check).
  A green nightly run and a red candidate run on the same SHA: "Release Gate"
  refuses, because only the candidate run counts.
- Reading check against `merge-queue`: a project whose overlay requires an
  expensive pre-merge run keeps it ("Two Tiers", pre-merge run).

## Review Threads

### Reviewer pass 1 (impl, codex reviewer)

The requested protocol should keep project-specific choices in overlays while making the full-suite release check unambiguous.

#### Blocking issues

**Thread 1 — Identify the candidate run, not just its SHA.** `ci-practice/SKILL.md:38-43` requires a successful `full-gate` check on the release SHA, but the same SHA can have both a green nightly run and a red candidate run. A check selected only by name and SHA could accept the nightly result despite the failed candidate. Require the release check to verify the candidate run’s identity, head SHA, and `full-gate` result. Add this case to the plan’s reading check.

**Thread 2 — Preserve the pre-merge CI gate.** `ci-practice/SKILL.md:21-23` names only release-candidate dispatch and nightly scheduling for the full tier. `merge-queue/SKILL.md:54-56` also requires expensive CI immediately before each merge. State how that pre-merge run fits the two tiers so adopting this protocol cannot omit the existing gate.

**Thread 3 — Move unapproved operating choices out of the generic rule.** `ci-practice/SKILL.md:61-62,81-83,92-98` mandates a one-command runner rollback, a two-failure/two-week threshold, a monthly budget alert, and experiment spend caps. The plan approves the policy areas but places project numbers in overlays; the alert is also a new standing mechanism. Keep the general expectations here and put thresholds and chosen mechanisms in project overlays, or record the additional human decision.

#### Non-blocking issues

None.

#### Overall judgment

**Not ready for closeout.** The new protocol, plan, and both required index updates are present. Direct inspection supports the frontmatter and index changes; the three protocol items above remain partial.

#### Residual risks and validation gaps

Ruby parsed the frontmatter and `git diff --check` passed. The plan’s specified Python test command could not run here because PyYAML is unavailable; the driver should run it in the configured test environment. The worktree was clean at review time.

### Driver response to reviewer pass 1

1. Accepted. "Release Gate" now identifies the candidate run by id, requires
   its head SHA to equal the candidate and its full gate to have succeeded,
   and says no other run on the SHA stands in. Reading check added.
2. Accepted. "Two Tiers" keeps the merge-queue overlay's pre-merge run as its
   own trigger on the exact head being merged. Reading check added.
3. Accepted. The rollback command, flaky threshold, spend alert and
   experiment limit are now named by the overlay or set by the human; the
   protocol keeps only the general expectation.

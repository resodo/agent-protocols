---
name: ci-practice
description: "[repo maintainer, any author changing CI] Use before adding or changing a repository's CI workflow, its triggers, its runners, its caches, its release gate, or a test that CI keeps failing intermittently. Two-tier triggers, a release gate on the exact SHA, runners chosen by measurement against a target wall time, caches keyed by lock files, a flaky-test policy, and cost tracking."
---

# CI Practice

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/ci-practice.md` if present: the project's target
   wall times, runner pools and labels, measured numbers, cost line, release
   check command, flaky-test list and threshold, runner rollback command, and
   the spend alert it uses.

## Two Tiers

- **Light tier:** every pull request push and every push to the default
  branch. Only checks that finish in a few minutes on a small runner: policy
  tests, contracts, lint, types, build, unit tests. A newer push to the same
  pull request cancels its older run.
- **Full tier:** the whole suite, run on a manual dispatch for a release
  candidate and on a nightly schedule on the default branch. Full runs are
  never cancelled or replaced by a newer run.
- **Pre-merge run:** where the project's merge-queue overlay requires an
  expensive CI run right before each merge (`merge-queue`), that run stays; it
  runs the full suite on the exact head being merged and is not replaced by
  the nightly run. Two tiers only take the full suite off ordinary pushes.
- A default-branch push does not run the full suite: a burst of merges would
  pay for one full run per commit. If the project wants the full suite on
  every merge, it records that decision and its cost in its overlay.
- Each tier reports through its own final gate job, and each gate exists only
  on its own events. A light gate must not report on a full run, and a full
  gate must not exist on a light run, so a green light result can never be read
  as a full result.
- The full gate passes only when every job it requires succeeded. A required
  job that was skipped fails it; when the suite can run in more than one
  place (for example hosted jobs or one large self-hosted job), the gate reads
  the same switch the jobs read and requires the selected side.

## Release Gate

- A release names one exact commit SHA and one full run dispatched for it
  (the candidate run). The release check reads that run by its id and requires
  its head SHA to equal the candidate SHA and its full-gate job to have
  succeeded. Another run on the same SHA (a green nightly, an earlier attempt)
  never stands in for a red or missing candidate run.
- The release check keys on the full gate's result in that run, not on the
  workflow's overall conclusion and not on the light gate.
- A red nightly run is fixed forward; it does not block a release whose own
  candidate run is green, but the next candidate includes the fix.

## Choosing Runners

- Start from a target wall time for the full tier (for example 10 minutes,
  stretch 5) and the expected run count per day, written in the overlay.
- Measure before choosing: run the real suite on two or three candidate
  setups (machine size, CPU family, one large machine versus several small
  ones, spot versus on-demand) and record wall time, per-job time, CPU and
  memory peak, failures and cost per run. Use the cheapest setup that meets
  the target with its failures understood.
- Count the whole run: boot, image or dependency fetch, and the slowest job,
  not only test time.
- Parallel jobs on one machine need their own ports and databases; give each
  its own container or network namespace rather than editing tests to share.
- Do not run untrusted code (pull requests from forks, unreviewed branches)
  on self-hosted runners that hold credentials. Keep the light tier on hosted
  runners unless the overlay records why not.
- Every switch to a new runner has a written rollback that returns the jobs
  to the previous runners; the overlay names it.
- Third-party runner services get repository access; adding one is a human
  decision recorded in the overlay.

## Caching

- Cache dependencies by a hash of exactly the inputs that decide them (lock
  files, the image definition, tool versions). An unchanged lock reuses the
  cache; a changed one rebuilds once.
- A cache never carries secrets: credentials reach an install step through the
  CI secret mechanism (for example a build secret mount), never a cached layer.
- Measure what a cold install costs; if it is a large share of the run, the
  cache is part of the runner choice, not an afterthought.

## Flaky Tests

- A test that fails intermittently on the default branch's full runs is
  recorded in the project's flaky-test list with the test name, date and run
  link the first time it is seen.
- When a test reaches the overlay's threshold of intermittent failures, the
  owner fixes the test or removes it from the required set with a written
  restore date. No automatic retry of failed tests to hide them; a manual
  re-run of a failed job is recorded with its reason.
- Before moving the suite to a new runner or raising parallelism, run it
  there several times and fix what newly fails. Load-sensitive timing in a
  test is a test bug: wait on a condition with a bound, never on a fixed
  sleep or an assumption that work already finished.

## Cost Tracking

- Tag every self-hosted CI resource so its spend can be filtered; the overlay
  names how spend reaches a human (for example a budget alert).
- Per repository, keep track of full runs, runner minutes per run, and spend.
  When a repository's CI exceeds the overlay's cost line, revisit triggers and
  runner choice before adding capacity.
- Runner experiments run under a spend limit the human set, with their own
  tag, and end with every resource removed.

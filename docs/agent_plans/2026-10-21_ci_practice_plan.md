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

## Review Threads

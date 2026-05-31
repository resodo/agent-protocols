# Worktree Protocol Guard

This guidance is for repos that vendor these shared protocols through a
project-local submodule such as `external/agent-protocols`.

## Purpose

A feature worktree can be created before the shared protocol submodule is
initialized. If an agent then cannot find planning, review, or closeout
protocols, it may silently skip the workflow.

The guard prevents that failure by making protocol availability a worktree setup
check, not a memory test.

## Boundary

The executable guard must live in the consumer repo, not only inside this shared
protocol repo. The failure case is that the submodule may be missing or empty,
so a script that exists only inside the submodule cannot be the first line of
defense.

This repo defines the contract. Consumer repos own:

- the local script, hook, or worktree setup step;
- the canonical required protocol list for that repo;
- the point in their worktree creation flow where the guard runs.

Division of labor: the worktree guard proves required protocol files are
available; the repo bootstrap receipt proves the agent has established repo
coordinates, ownership, and production/access posture. Neither should silently
cover for the other.

## Declaration

A consumer repo declares that it vendors shared protocols by either:

- tracking `external/agent-protocols` in `.gitmodules`; or
- explicitly naming the vendored path in its repo entrypoint or worktree
  protocol.

The guard should use that local declaration instead of assuming every repo has
the same submodule layout.

## Baseline Checks

For Skynet-style repos, the baseline required lifecycle protocols are:

```text
planning
structured-review
closeout
```

The baseline checks are:

```bash
git submodule update --init --recursive external/agent-protocols
test -f external/agent-protocols/planning/SKILL.md
test -f external/agent-protocols/structured-review/SKILL.md
test -f external/agent-protocols/closeout/SKILL.md
```

Consumer repos may require additional protocols, such as `retrospective`, when
their own lifecycle requires them. Add those to the consumer repo's local guard
list, not to scattered docs.

## Failure Semantics

The guard must fail loudly when required protocols cannot be made available.

On failure, an agent must not:

- continue by skipping planning, review, or closeout;
- fall back to user-home absolute paths;
- claim the workflow is available without checking the files;
- modify production state.

The expected remediation is to initialize the submodule or fix the consumer
repo's vendored protocol declaration.

## Consumer Script Shape

This is a shell sketch, not a required filename:

```bash
#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

protocol_path="external/agent-protocols"
required_protocols=(planning structured-review closeout)

git submodule update --init --recursive "$protocol_path"

for protocol in "${required_protocols[@]}"; do
  skill="$protocol_path/$protocol/SKILL.md"
  if [[ ! -f "$skill" ]]; then
    echo "missing required agent protocol: $skill" >&2
    exit 1
  fi
done
```

The consumer repo should treat `required_protocols` as the executable source of
truth for that repo. Other docs should point to the guard instead of repeating
the list. In the script sketch above, the `required_protocols` array is the
canonical example source; the prose and `test -f` lines illustrate the same
baseline, not a separate list to maintain.

## Validation

When adopting this guard in a consumer repo, validate both cases in a temporary
or otherwise non-destructive setup:

1. Initialized pass case: the guard initializes or verifies the vendored
   protocols and exits successfully.
2. Missing-submodule fail case: with `external/agent-protocols` unavailable or
   missing required files, the guard exits non-zero before the agent starts
   feature work.

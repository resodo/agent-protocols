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

- the local script, hook, or worktree setup step, usually under `scripts/` or
  `tools/`;
- the canonical required protocol list for that repo;
- the point in their worktree creation flow where the guard runs.

Do not use a `.agent-protocols/` overlay as the first-line guard. Overlays are
loaded after an agent has already found the shared protocol workflow; they do
not protect the earlier failure mode where the vendored protocol submodule is
missing.

Division of labor: the worktree guard proves required protocol files are
available, fresh, and mounted; the repo bootstrap receipt proves the agent has
established repo coordinates, ownership, and production/access posture.
Neither should silently cover for the other.

## Declaration

A consumer repo declares that it vendors shared protocols by either:

- tracking `external/agent-protocols` in `.gitmodules`; or
- explicitly naming the vendored path in its repo entrypoint or worktree
  protocol.

The guard should use that local declaration instead of assuming every repo has
the same submodule layout.

## Freshness

Availability checks alone cannot catch a stale clone: a checkout that is
clean on `main` can still sit weeks behind `origin/main`, especially when
the same human works across multiple machines. Freshness is part of the
guard contract and is checked mechanically at the moment of use, never
assumed:

- Before creating a feature worktree, run `git fetch origin` in the parent
  clone and base the new worktree on `origin/<default-branch>`, never on a
  possibly stale local branch:

  ```bash
  git fetch origin
  git worktree add ../repo-feature -b feature/topic origin/main
  ```

- If the fetch fails (offline, auth, remote unavailable), stop and report
  the blocker. Do not start feature work against an unverified base.
- After the worktree exists, materialize the vendored protocols at their
  pinned version with `git submodule update --init --recursive`.

## Native Skill Mounts

Consumer repos commit symlinks that mount the vendored protocols into each
agent's documented project-level skill discovery path:

```text
.claude/skills/<protocol> -> ../../external/agent-protocols/<protocol>
.agents/skills/<protocol> -> ../../external/agent-protocols/<protocol>
```

`.claude/skills/` is Claude Code's project skill path; `.agents/skills/`
is Codex's documented repository skill path. Claude Code does not scan
`.agents/skills`, so both mount directories are required. Mount every
vendored protocol that ships a `SKILL.md`. Do not copy protocol content
into mount directories; symlinks only.

The links resolve only after the submodule is materialized, so the guard
verifies them: each mount entry must be a symlink resolving to a readable
`SKILL.md`. A dangling mount means the submodule step was skipped or the
mount target moved; fail loudly.

## Ordering And Fallback

Run the guard before the agent enters the worktree: create the worktree,
run the guard inside it, and only then start or attach the agent there.
Claude Code entering through `--add-dir` or a fresh session loads the
worktree's mounted skills at that moment; Codex catalogs skills only at
session start, so launch it inside the worktree after the guard.

After entry the agent self-checks that the protocol skills are cataloged.
When they are not - wrong ordering, or an agent without dynamic skill
loading - the deterministic fallback is reading the protocol `SKILL.md`
files directly from the vendored submodule path. Native cataloging is a
convenience layer; direct file reading is the floor. Repo `AGENTS.md`
keeps the guard step and the repo's obligations (which gates are mandatory
when); it does not need path-navigation text for skills the mounts already
surface.

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

Downstream adoption should be checked in the consumer repo. A typical consumer
repo check should verify that:

- the local guard script exists;
- the worktree feature flow calls the guard after creating or entering a
  feature worktree;
- the repo entrypoint points agents to the guard instead of asking them to rely
  on memory;
- the guard uses one local required-protocol list.

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

if ! git fetch origin; then
  echo "git fetch origin failed; refusing to start feature work on an unverified base" >&2
  exit 1
fi

git submodule update --init --recursive "$protocol_path"

for protocol in "${required_protocols[@]}"; do
  skill="$protocol_path/$protocol/SKILL.md"
  if [[ ! -f "$skill" ]]; then
    echo "missing required agent protocol: $skill" >&2
    exit 1
  fi
  for mount in ".claude/skills/$protocol" ".agents/skills/$protocol"; do
    if [[ ! -L "$mount" || ! -f "$mount/SKILL.md" ]]; then
      echo "broken or missing protocol skill mount: $mount" >&2
      exit 1
    fi
  done
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
3. Fetch-failure case: with the origin unreachable, the guard exits non-zero
   instead of proceeding against an unverified base.
4. Mount fail case: with a dangling or missing skill-mount symlink, the guard
   exits non-zero.

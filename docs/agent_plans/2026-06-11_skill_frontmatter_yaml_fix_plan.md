# Skill Frontmatter YAML Fix Plan

Status: historical - implemented and merged via PR #17 (2026-06-11)

## Human Concern

During a 2026-06-11 structured-review run in skynet-v2, the Codex reviewer
logged:

```text
failed to load skill <PATH>/external/agent-protocols/closeout/SKILL.md:
invalid YAML: mapping values are not allowed in this context at line 2 column 130
```

Since the canonical-source adoption, consumer repos mount these skills
natively into Claude Code (`.claude/skills/`) and Codex (`.agents/skills/`),
so SKILL.md frontmatter is load-bearing: a skill whose frontmatter fails
strict YAML parsing silently drops out of Codex's catalog. Codex sessions in
consumer repos currently run without the closeout skill and only a log line
records why.

## Root Cause

`closeout/SKILL.md` line 2 carries an unquoted `description` value containing
a colon followed by a space ("...actually finished: tests pass, ..."). In
strict YAML an unquoted scalar cannot contain `: `; lenient loaders (Claude
Code) accept it, strict loaders (Codex CLI 0.139) reject the document.

A strict `yaml.safe_load` scan of all six `*/SKILL.md` frontmatters confirms
closeout is the only failing file.

## Goal

- `closeout/SKILL.md` loads in strict YAML parsers, restoring native closeout
  skill cataloging for Codex sessions in all consumer repos.
- Frontmatter validity becomes regression-proof for every protocol skill in
  this repo, so a future description edit cannot silently break skill loading
  for one vendor again.

## Scope

1. Quote the `description` value in `closeout/SKILL.md` frontmatter. No
   wording change; quoting only.
2. Add `tests/test_skill_frontmatter.py`: for every `*/SKILL.md` in the repo
   root, extract the frontmatter block and assert that it parses with
   `yaml.safe_load`, that `name` and `description` keys exist and are
   non-empty strings, and that `name` matches the protocol directory name.
   The existing CI step `python -m unittest discover -s tests` picks it up
   with no workflow change. PyYAML is already a CI dependency.

## Non-Goals

- No rewording of any skill description beyond adding quotes.
- No changes to other protocols, references, scripts, or the runner.
- No consumer-repo changes: skynet-v2 and skynet-data receive the fix
  through the existing repository_dispatch submodule-bump automation.

## Validation

- New test fails on the current tree (closeout frontmatter) and passes after
  the quoting fix - demonstrated in the implementation evidence.
- `python -m unittest discover -s tests` green locally and in CI.
- `python scripts/check_backlog.py` untouched and green.
- Direct Codex skill-load verification is environment-dependent; the strict
  `yaml.safe_load` test is the agreed proxy for "Codex can parse it", since
  the observed Codex error is a YAML parse failure.

## Acceptance

- All six `*/SKILL.md` frontmatters parse under strict YAML.
- CI green on the PR.
- The regression test exists and runs in the default CI test discovery.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

Human concern: `closeout/SKILL.md` has frontmatter that strict YAML parsing rejects, causing Codex skill discovery to drop the closeout skill in consumer repos.

#### Blocking issues

No blocking issues.

#### Non-blocking issues

No non-blocking issues requiring a plan revision.

#### Overall judgment

Ready for implementation. The plan is narrowly scoped, identifies the exact failing field in `closeout/SKILL.md`, and keeps the implementation to a quote-only metadata fix plus a regression test in `tests/test_skill_frontmatter.py`.

I checked the repo-visible assumptions behind the plan:

- The branch is `feature/skill-frontmatter-yaml-fix`, based on `origin/main` at `c2fc951`, with a clean worktree and one plan commit ahead.
- There are exactly six root protocol skill files matching `*/SKILL.md`.
- `.github/workflows/ci.yml` installs `PyYAML` and runs `python -m unittest discover -s tests`, so the proposed test will run in existing CI without workflow changes.
- A current strict `yaml.safe_load` scan fails only on `closeout/SKILL.md` with the same `mapping values are not allowed here` class of YAML error.
- Existing root tests currently pass, so the new failure will be attributable to the planned regression test and frontmatter state.

Implementation should not require guessing. The file to edit, the allowed edit shape, the test location, the path glob, the required assertions, and the validation commands are all specified.

#### Residual risks or validation gaps

The direct Codex skill-load check remains environment-dependent, but the plan explicitly calls out `yaml.safe_load` as the agreed proxy because the observed Codex failure is a YAML parse failure. That is sufficient for this bug fix plan.

During implementation, the evidence should include both the pre-fix failing frontmatter check or failing new test and the post-fix passing `python -m unittest discover -s tests` run.

### Reviewer pass 2 (impl, codex reviewer)

Human concern: strict YAML parsing rejected `closeout/SKILL.md` frontmatter, causing Codex skill discovery to omit the closeout skill.

#### Blocking issues

No blocking issues.

#### Non-blocking issues

No non-blocking issues.

#### Overall judgment

Ready for closeout. The implementation matches the accepted plan exactly:

- Done: `closeout/SKILL.md` quotes the existing `description` value only. The word diff shows no wording change beyond adding opening and closing quotes.
- Done: `tests/test_skill_frontmatter.py` was added and scans every root `*/SKILL.md`, strict-parses the frontmatter with `yaml.safe_load`, requires non-empty string `name` and `description`, and requires `name` to match the protocol directory.
- Done: The test would catch the original bug. I reproduced the parent-version strict YAML failure for `closeout/SKILL.md` at line 2, column 130, and the new test exercises that same parser path.
- Done: Existing CI discovery picks up the new test through `.github/workflows/ci.yml` via `python -m unittest discover -s tests`.

Reviewer-rerun validation passed:

- `python -B -m unittest discover -s tests`: 18 tests passed.
- `python -B -m unittest discover -s structured-review/tests`: 61 tests passed.
- `python -B -m unittest discover -s scout/tests`: 15 tests passed.
- `python -B scripts/check_backlog.py`: passed.
- In-memory syntax compile for Python files under `structured-review` and `scout`: 4 files compiled.

Branch/process checks:

- Worktree is clean.
- Branch is `feature/skill-frontmatter-yaml-fix`, ahead of `origin/main` by 3 commits.
- Touched repo-visible files contain no local user-home absolute paths; the only secret-related scan hits are existing safety-rule text in `closeout/SKILL.md`.

#### Residual risks or validation gaps

Remote PR CI status was not checked in this reviewer pass. The exact bytecode-writing `python -m compileall -q structured-review scout` command remains driver-reported; I used a no-write in-memory compile check for the reviewer rerun.

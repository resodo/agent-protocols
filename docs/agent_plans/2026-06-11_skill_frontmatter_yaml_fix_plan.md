# Skill Frontmatter YAML Fix Plan

Status: active - plan review pending

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

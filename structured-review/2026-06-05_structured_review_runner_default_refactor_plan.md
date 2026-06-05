# Structured Review Runner Default Refactor Plan

Status: Draft for structured review
Owner: driver
Date: 2026-06-05

## Human Concern

Repo-backed review gates should default to `claude -p` through the shared
runner. The current skill still carries older human-forwarded review patterns,
including action menus and human shorthand, which makes agents treat the runner
as optional and leaves the driver responsibility under-emphasized.

## Goal

Refactor `structured-review` so the shared protocol clearly says:

- for repo-backed Plan Review, Plan Re-review, Implementation Review, and
  Implementation Re-review, the driver defaults to invoking the bundled Claude
  runner when it is available;
- `write-commit-to-plan` is the default for normal plan/implementation
  artifacts that have `## Review Threads`;
- `print-review` is the fallback for artifacts where appending review threads
  would pollute a durable reference artifact;
- the driver, not the reviewer, owns the decision after reviewer output:
  adopt, reject, defer, or pause and escalate to the human before editing;
- human shorthand and old reviewer action menus are removed, not retained as
  fallback paths.

## Non-Goals

- Do not change runner mechanics or Claude CLI flags in this PR.
- Do not update downstream `skynet-data` or `skynet-v2` submodule pointers in
  this PR.
- Do not add project-specific overlay policy to the shared protocol.
- Do not weaken the existing validation, source-of-truth, lifecycle, UI, or
  branch hygiene review lenses.

## Proposed Shape

1. Keep `structured-review/SKILL.md` as the short operating protocol.
   - Trigger and role requirements.
   - Default Claude runner rule.
   - Mode selection.
   - Driver decision checkpoint after reviewer output.
   - Thread/commit boundary summary.
   - Readiness standard.

2. Move detailed review lenses out of `SKILL.md` into direct references:
   - `structured-review/references/review-lenses.md`
   - `structured-review/references/collaboration.md`

3. Remove obsolete interaction mechanics from `SKILL.md`.
   - Delete `Human Shorthand` entirely.
   - Delete the post-review "offer action menu" rule entirely.
   - Remove the generic `Human Input Rule` menu mechanics from this skill unless
     a concise final-authority statement is still needed.

4. Strengthen the driver checkpoint.
   - Before modifying artifacts or implementation after a Claude review, the
     driver must classify reviewer findings as accepted, rejected, deferred, or
     escalation-needed.
   - The driver must pause for human discussion before editing when a finding
     changes scope, contradicts human direction, changes risk tolerance, or
     exposes an ambiguous tradeoff.
   - The driver closeout summary must distinguish Claude suggestions, driver
     decisions, human decisions, remaining risks, and validation provenance.

5. Update repo docs/tests only as needed.
   - Keep runner tests unchanged unless the refactor affects documented paths.
   - Add or update lightweight text checks if useful, but do not create a large
     doc-testing framework.

## Acceptance Criteria

- `structured-review/SKILL.md` states that repo-backed review gates default to
  the bundled Claude runner when available.
- `SKILL.md` no longer contains `Human Shorthand`, `[O]`, `[H]`, `[V]`, `[R]`,
  `[X]`, or the "Write review comments into the artifact and commit" action
  menu.
- `SKILL.md` makes the driver post-review decision checkpoint prominent and
  concrete.
- Detailed review lenses remain available through direct references linked from
  `SKILL.md`.
- Existing runner tests and compile checks pass:

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
git diff --check
```

## Review Threads

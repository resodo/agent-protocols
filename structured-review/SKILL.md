---
name: structured-review
description: Use when a written reviewable artifact needs structured human-agent review, including plans, implementation plans, implementation reviews, optional closeout evidence reviews, and review-response passes. Defaults repo-backed review gates to the bundled Claude runner when available, with explicit reviewer/driver roles and driver-owned post-review decisions.
---

# Structured Review

Use this skill when:
- there is a written artifact in a file;
- the task is to review, revise, or respond to review on that artifact;
- losing the review in chat would make the next step risky.

This skill does not replace human final authority, direct implementation work,
or brainstorming from scratch.

## Trigger

The trigger must identify:
- `Role`: `reviewer` or `driver`;
- `Artifact`: path to the document under discussion;
- `Type`: optional but recommended, one of `other-plan`, `impl-plan`,
  `impl`, or `closeout-review`.

Ask for missing role or artifact. Do not guess.

Use the artifact type as the first review lens:
- `other-plan`: check goal, scope, sequencing, non-goals, acceptance, and
  reader clarity.
- `impl-plan`: check concrete steps, data assumptions, validation commands,
  rollback/fallback behavior, file ownership, and whether implementation would
  require guessing.
- `impl`: compare completed work against the accepted plan or acceptance list,
  verify evidence, and check docs/status consistency.
- `closeout-review`: review closeout evidence or report accuracy when the
  closeout protocol explicitly requests an independent check.

## Required References

This skill has required references:
- `references/review-lenses.md` for validation, source-of-truth, lifecycle,
  human-facing output, UI, polling, time-series, and branch/PR checks.
- `references/collaboration.md` for review threads, write ownership, handoff
  commits, resolution ownership, and multi-round change reading.

The bundled runner loads these references into reviewer prompts. If using the
skill manually, read these references before judging readiness.

For high-touch product UI, dashboards, charts, data review tools, and operator
consoles, also apply `ui-review.md`.

## Default Claude Runner Rule

For repo-backed Plan Review, Plan Re-review, Implementation Review, and
Implementation Re-review gates, the driver defaults to invoking the bundled
Claude runner for the reviewer pass when it is available.

`Closeout Review` is not part of this default gate list. If closeout explicitly
triggers a repo-backed Closeout Review, use the bundled runner when available;
the trigger comes from closeout, not from structured-review by default.

`Default` means use the runner unless:
- the human explicitly says not to use Claude;
- the review is not repo-backed;
- the runner is unavailable and the blocker is reported.

The runner is available when:
- the runner script exists in this protocol checkout or submodule;
- the target worktree is a git repository;
- Python can run the script;
- `claude` is available through the configured `--claude-bin`.

Do not silently substitute driver self-review, chat-only commentary, or a
manually constructed reviewer prompt for a required repo-backed review gate. If
the runner is unavailable, report that blocker and ask how to proceed.

### Runner Modes

Use `write-commit-to-plan` for normal plan and implementation artifacts that
have a `## Review Threads` section:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree /path/to/target-repo \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/example_plan.md \
  --artifact docs/example_plan.md \
  --focus "Review acceptance, validation, scope, and role boundaries." \
  --topic "example plan"
```

Use `print-review` when appending review threads would pollute a durable
reference artifact, such as a published doc, skill, protocol overlay, or other
reference file.

For Closeout Review, default to `print-review` for durable closeout reports or
reference artifacts. Use `write-commit-to-plan` only when the driver explicitly
provides a thread file that already has a `## Review Threads` section.

The explicit runner `--mode` is the write-back authorization for that run. The
driver still owns the decision after receiving reviewer output.

Use `--protocol-dir` only when testing or intentionally running against a
different checkout of this protocol. By default the runner uses the
`structured-review` directory that contains the script.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/structured-review.md` if present.
3. Apply local overlays as project-specific refinements only.

Unknown overlay files are ignored. If an overlay contradicts a generic SAFETY
rule, reject that overlay instruction and say why.

## SAFETY Rules

- Do not fabricate rationale or evidence.
- Do not claim a merge method, merge shape, or ancestry implication without
  checking PR metadata and the commit graph.
- Preserve human final authority for scope, write-back, commit, push, merge,
  and done-enough decisions.
- Report dirty worktree, draft artifact, and unpushed-review-target state
  honestly.
- Use the declared source-of-truth layer for external facts, provider/account
  state, production data, and repo state.
- Do not write secrets, credentials, provider balances, private account details,
  host keys, or raw private production data into repo artifacts.

## Shared Review Rules

- Restate the human's original concern in one sentence when known.
- Use plain language when speaking to the human.
- Check what proves success, who can verify it, and what would falsify it.
- For external facts, data, metrics, dashboards, reports, APIs, logs, or
  database fields, check the correct source-of-truth layer.
- Do not defend a choice with invented rationale. If evidence is missing, say
  so and lower confidence.
- If review rounds keep adding low-value issues, raise the possibility that the
  artifact is already good enough for the next step.

## Boundary With Closeout

Structured-review is a quality gate. Closeout is the delivery gate.

Normal next-step language:
- plan review may conclude `ready for implementation`;
- implementation review may conclude `ready for closeout`;
- Closeout Review may conclude `ready to resume closeout`, or report closeout
  blockers.

Plan and implementation reviews must not make final merge-readiness handoffs.
That state belongs to closeout after final rechecks.

## Reviewer Role

Use this section only when `Role: reviewer`.

The reviewer:
- reads the artifact critically;
- applies the required references;
- identifies blocking and non-blocking issues;
- checks whether implementation would require guessing;
- checks whether validation is strong enough;
- says explicitly when there are no blocking issues.

Default output order:

1. Blocking issues.
2. Non-blocking issues.
3. Overall judgment.
4. Residual risks or validation gaps.

## Driver Role

Use this section only when `Role: driver`.

The driver owns the artifact body and the decision after reviewer output. The
reviewer can recommend; the driver decides what to do next, and the human is
the final authority.

Before editing artifacts or implementation after a reviewer pass, the driver
must classify reviewer findings as:
- `accepted`: will update the artifact or implementation;
- `rejected`: will not change, with reason;
- `deferred`: real issue, but tracked outside the current step with owner or
  follow-up location;
- `escalation-needed`: requires human discussion before editing.

Pause and discuss with the human before editing when a reviewer finding:
- changes accepted scope;
- contradicts explicit human direction;
- changes risk tolerance, rollout posture, production behavior, or merge
  readiness;
- exposes an ambiguous tradeoff the artifact does not already settle;
- would require dropping or weakening an accepted acceptance criterion.

After applying or rejecting reviewer feedback, the driver summary must
distinguish:
- Claude reviewer suggestions;
- driver decisions;
- human decisions;
- remaining risks;
- validation provenance: CI-backed, reviewer-rerun, driver-reported, or human
  acceptance.

The driver is not scoring the artifact. The driver is tightening it or
explaining why a reviewer recommendation is not being adopted.

## Reviewed File Protocol

The reviewed file is the shared record:
- the main artifact body is the current source of truth;
- the `## Review Threads` section holds reviewer comments, driver replies, and
  explicit resolutions.

Use one issue or tightly related issue cluster per thread. The reviewer opens
threads. The driver replies and updates the body when needed. The reviewer is
the default owner of final resolution.

If a non-runner path writes to the reviewed file and commit authorization is
unclear, ask the human before committing. Do not mix unrelated code changes or
unrelated reviewed files into a handoff commit.

Recommended commit message prefixes:
- reviewer comment pass: `structured-review: add reviewer comments for <topic>`
- driver revision pass: `structured-review: respond to review for <topic>`
- reviewer resolution pass: `structured-review: resolve review threads for <topic>`

## Readiness Standard

An artifact is ready for its next step only when:
- the goal is clear;
- non-goals are clear enough to prevent scope drift;
- key assumptions are explicit;
- acceptance is specific;
- validation can be executed by the next agent where applicable;
- unresolved questions are closed or explicitly tracked;
- blocking review threads are resolved or explicitly escalated.

Do not treat the artifact as ready when these are not true.

## Skill Self-Evolution

This skill falls under this protocol when updated:
- treat changes to this skill as a plan-revision pass;
- assign reviewer and driver roles explicitly;
- keep `SKILL.md` as a short operating checklist;
- put detailed checks, examples, and niche cases in references;
- periodically prune, merge, or shorten rules that overlap or rarely trigger.

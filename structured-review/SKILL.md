---
name: structured-review
description: Use when a written reviewable artifact needs structured human-agent review, including high-level plans, implementation plans, and completed implementation validation. This skill standardizes explicit roles (`reviewer` or `driver`), plain-language discussion, validation-first scrutiny, and comment-based convergence.
---

# Structured Review

Use this skill when:
- there is already a written artifact in a file
- the current task is to review, revise, or respond to review on that artifact
- the artifact is important enough that chat-only feedback would be too easy to lose

This skill covers:
- reviewing high-level plans, implementation plans, and implementation closeout reports
- replying to review as the driver
- deciding whether the artifact is ready for its next step
- writing review comments back after human approval

This skill does not cover:
- brainstorming from scratch
- implementing code directly
- replacing final human acceptance

## Trigger

Expect the trigger to specify:
- `Skill`: `structured-review`
- `Role`: `reviewer` or `driver`
- `Artifact`: file path to the document under discussion
- `Type`: optional but recommended, one of `other-plan`, `impl-plan`, or `impl`

The trigger does not need to follow a rigid template.
Natural-language triggering is fine as long as it clearly includes those three pieces of information.

Canonical template:

```text
Use skill: structured-review
Role: reviewer
Artifact: docs/some_artifact.md
Type: impl-plan
```

or

```text
Use skill: structured-review
Role: driver
Artifact: docs/some_artifact.md
Type: impl
```

Natural-language examples:

```text
Use structured-review as reviewer and look at docs/some_artifact.md.
```

```text
Use the structured-review skill. You are the driver. The artifact is docs/some_artifact.md.
```

If `Artifact` or `Plan` is missing, ask for it. Do not guess.
If `Role` is missing, ask for it. Do not guess.

## Review Types

Use the artifact type to choose the review lens.

- `other-plan`: high-level planning artifacts such as PRD-lite docs, phase maps, workflow proposals, architecture notes, and research plans. Check goal, scope, phase boundaries, sequencing, non-goals, acceptance, and whether the artifact is understandable to its intended readers. Do not demand implementation detail unless it affects scope or feasibility.
- `impl-plan`: executable implementation plans for coding agents. Check concrete steps, data assumptions, validation commands, rollback/fallback behavior, file ownership, and whether an implementing agent would need to guess.
- `impl`: completed implementation review. Check code against the accepted plan and PRD, run or inspect tests, validate human-facing behavior by operating the real rendered output, and check docs/status consistency.

When type is omitted, infer the likely lens from the file path and title, but state the inference explicitly.

## Shared Protocol

These rules apply to both `reviewer` and `driver`.

### Core Goal

The goal is not to make the artifact sound polished.
The goal is to make the next step safe without guessing.

### Human Concern Anchor Rule

At the start of a review or driver handoff, restate the human's original concern in one sentence when it is known.

Use this as an anchor, not a new approval gate:
- if the artifact's internal goals drift away from the human's concern, call that out
- do not turn every technical review into a full product requirements debate
- if the original concern is unclear, ask the human instead of inventing it

### Plain-Language Rule

When speaking to the human:
- default to plain language
- explain jargon the first time it appears
- do not hide weak reasoning behind compressed technical wording
- if the reason is weak or unknown, say so directly

### Validation-First Rule

An artifact is not ready if acceptance is vague.

Always check:
- what exactly proves success
- whether the implementing agent can verify that by itself
- what artifact, query, command, screenshot, or test will be used
- what result would falsify the artifact

For artifacts involving external facts, data, metrics, dashboards, reports, APIs, logs, or database fields, also check:
- whether the required data actually exists and is usable
- whether the correct source-of-truth layer is being used
- whether different representations are being confused

### Human-Facing Output Rule

For human-facing outputs, query/API success is not sufficient validation.

Human-facing outputs include:
- dashboards and Grafana panels
- reports and daily summaries
- notification bodies
- CLI tables
- UI screens
- rendered docs or charts

For these outputs, always check:
- who reads it
- what question the reader is trying to answer
- what the output looks like under current real data
- how empty data, missing series, zero values, `NaN`, and low-volume data render
- what artifact proves the rendered output is usable, such as a screenshot, copied output, or explicit rendered example

For UI implementation review specifically:
- page load is not enough
- do not validate only the happy path; exercise at least one normal path, one empty/no-match path, and one recovery/reset path when the UI has controls
- visible controls must be exercised, including search, filters, navigation, detail pages, and empty-result states
- if a filter option has no matching sample data, verify that it returns an intentional empty state and that `all` or reset restores the data
- placeholder stages must be understandable to a human reader
- compare the implemented UI against any prototype only at the agreed fidelity level; do not treat an early skeleton as a failed high-fidelity design unless the plan promised fidelity
- clarify who owns any dev server used for human acceptance, so the agent does not silently leave or kill a server the human depends on

When grouping multiple outputs into one surface, justify the grouping by reader scenario:
- who reads the combined surface
- when they read it
- what decision or question the grouping helps answer

Maintainer-side convenience, such as one fewer file, one fewer panel, or one fewer directory, is not sufficient justification by itself.

Treat "the query returns `success`", "the API returned 200", or "the SQL parses" as insufficient. The artifact should define the reader-facing acceptance artifact whenever feasible.

### Sample-Data-Before-Endorsement Rule

For any artifact item that depends on a field, table, API response field, log record, metric, or other live data source:
- do not endorse it based only on schema, docs, or naming
- check sample live data before endorsing the item
- treat "the field exists" as insufficient evidence that the field is usable
- treat "the raw field exists" as insufficient evidence that raw should be used
- when both raw and enriched or corrected variants exist, default to enriched or corrected unless there is a reason to prefer raw

When appropriate, the artifact should reference the sample evidence or the validation step that will check it.

### External Resource Source-of-Truth Rule

For artifacts involving third-party quota, billing, rate limits, usage budgets, API availability, external account state, or service-side counters, internal application metrics are not automatically the source of truth.

Always check:
- who owns the authoritative number
- whether an API, dashboard, invoice, admin page, or provider-side response exposes that number
- whether the artifact's metric is authoritative, derived, sampled, or only a proxy
- what conversion factor connects internal events to external units, if any
- whether that conversion factor is validated or merely guessed

If both external truth and internal estimates exist, prefer a reconciliation design:
- show external truth
- show internal estimate
- show drift only when both sides cover the same scope

Do not endorse alert thresholds or budget projections based on internal counters alone unless the artifact explains why no external source exists or why the internal counter is equivalent.

### Plan-to-Implementation Traceability Rule

For `Type: impl` reviews, passing tests and healthy production smoke are not
enough.

The reviewer must compare the completed work against the accepted plan, PRD, or
acceptance list item by item:
- mark each in-scope item as `Done`, `Partial`, `Missing`, or `Deferred`
- require concrete evidence for `Done`
- treat an empty evidence cell, chat memory, or "looks fine" as insufficient
- treat every planned-but-unimplemented item as `Missing` unless the human
  explicitly defers it
- call out any status doc that says or implies completion while rows are still
  missing or partial

If no accepted plan or acceptance list exists, say that directly and create a
minimal traceability list before judging the implementation complete.

### Polling Safety Rule

For any artifact that periodically calls an external API or service, check polling safety before accepting the interval.

The artifact should define:
- the polling interval
- whether the endpoint itself costs money, quota, credits, tokens, or rate-limit budget
- whether the endpoint has documented or observed rate limits
- whether multiple processes could poll redundantly
- what backoff or disable behavior happens after failures
- whether a controlled live check has proven the polling call is safe

If cost or rate-limit behavior is unknown, default to treating the endpoint as expensive until proven otherwise. An artifact must not daemonize frequent polling of an unknown-cost endpoint without first validating that the polling itself will not exhaust or distort the resource being measured.

### Time-Series Semantics Rule

For artifacts using Prometheus, Grafana, or other time-series systems, check that metric type and query semantics match.

Always check:
- counters are used for monotonically increasing event counts
- gauges are used for current snapshots
- `rate()` / `increase()` are only used on counters or on values with explicitly handled reset/decrease semantics
- snapshot gauges are not treated as consumption counters without a poller-computed monotonic delta
- low-volume business events use human-scale units such as per-hour or per-day when per-second rates are unreadable
- missing series and zero events are handled intentionally, not left as confusing empty panels

If an artifact derives consumption from periodic snapshots, it must define reset handling. For example, if a provider-side `used` snapshot decreases because a quota pool resets, the artifact should not treat that decrease as negative consumption.

### No-Made-Up-Rationale Rule

Do not defend a choice with invented rationale.

If a reason was assumed but never validated:
- say that clearly
- downgrade the confidence
- ask for evidence or artifact revision

### Comment-Thread Rule

The artifact file is the shared record.

Default behavior:
- discuss with the human first
- write comments back only after approval
- prefer comment-based convergence over silent rewrites

Unless explicitly asked otherwise, do not silently change the main artifact body during review discussion.

### Human as Final Authority

Reviewer and driver propose. The human decides.

The human is the final authority on:
- scope decisions
- priority tradeoffs between reviewer and driver positions
- when an artifact is "done enough" to stop iterating
- whether a concern is over-engineering relative to the task

If reviewer and driver disagree and neither side yields, explicitly escalate to the human instead of forcing through a unilateral outcome.

### Human Input Rule

Human shorthand and raw chat text are part of the conversation protocol, not the artifact file by default.

When human input is needed, the agent must present a short numbered decision menu in plain text. If the runtime supports a native choice UI, use it; otherwise fall back to the numbered text menu. The menu should include the recommended option first when there is a clear recommendation, and it should always allow free-form human reply.

The menu's numbers are the only numbers the human should need to reply with. Do not put competing internal option numbers such as `Option 1`, `Option 2`, or `Option 3` inside the menu labels. If the artifact already uses numbered option names, rewrite them into plain action labels for the human menu.

Bad:

```text
1. Option 3 (recommended): Do not write a stub
2. Option 1: Add a cache table
3. Option 2: Write a stub row
```

Good:

```text
1. Do not write a stub (recommended): simplest; retry only if referenced again.
2. Add a 404 cache table: more precise, but adds a table.
3. Write a deleted stub row: most complex; needs placeholder fields and reader skip rules.
```

Example:

```text
Need a decision:

1. Write this back to the review thread (recommended)
2. Keep it only in chat for now
3. Drop this concern

You can also reply in your own words.
```

Do not rely on shorthand tags as the main human interface. Shorthand is optional, not required.

Do not copy the human's raw shorthand or raw wording into the artifact unless explicitly asked.

If the human makes a strong decision that affects the artifact, the current agent may summarize it in artifact-friendly form.

Prefer summarized decisions such as:
- a scope decision
- a hard constraint
- an explicit approval or rejection of a proposal

Do not preserve the human's raw chat text unless that exact wording is itself important.

### Reviewed File Collaboration Protocol

The shared reviewed file has two different functions:

1. **Main artifact body**
   - the current source of truth
   - updated by the driver after convergence on accepted changes

2. **Review threads**
   - appended near the end of the file
   - used for reviewer comments, driver replies, and explicit resolutions

Default collaboration rules:
- one issue or one tightly related issue cluster per thread
- reviewer writes comments into review threads
- driver replies inside those threads and updates the main body separately
- reviewer decides whether a thread is resolved
- each mature thread should end with an explicit resolution written by the reviewer

Resolution examples:
- `Resolved. Artifact body updated in §4.`
- `Resolved by human decision. Keep current scope; no further change.`
- `Superseded by later rewrite in §7.`

### Write Ownership Rule

Only one agent should be the active writer for a reviewed artifact at a time.

Default ownership:
- during review pass: reviewer writes comment threads
- during revision pass: driver writes thread replies and artifact-body updates

Avoid simultaneous edits to the same artifact file by both reviewer and driver.

### Handoff Commit Protocol

Structured review depends on clear git boundaries. After an agent writes to a reviewed file, that agent must run `git status` and inspect the relevant diff before handing off.

Default behavior after reviewed-file edits:
- if the human has already authorized commits for this review session, create a small commit for the artifact change
- if commit authorization is unclear, ask with a numbered decision menu before committing
- if the human chooses not to commit, explicitly say the artifact changes are left uncommitted

Recommended commit message format:
- reviewer comment pass: `structured-review: add reviewer comments for <artifact topic>`
- driver revision pass: `structured-review: respond to review for <artifact topic>`
- reviewer resolution pass: `structured-review: resolve review threads for <artifact topic>`

Do not mix unrelated code changes or unrelated reviewed files into a handoff commit. If the worktree already has unrelated changes, mention them and commit only the relevant file when authorized.

### Resolution Ownership Rule

The reviewer is the default owner of final resolution.

Default lifecycle:
- reviewer opens the thread
- driver replies and updates the artifact body if needed
- reviewer checks the reply and the updated body
- reviewer writes the final resolution when satisfied

A thread is not considered closed until the reviewer writes resolution.

The driver may suggest that a thread is ready to close, but does not finalize resolution by default.

The driver may explicitly mark a thread as ready for reviewer closure after replying and updating the artifact body.

### Change-Reading Rule

When revisiting an artifact that has already gone through one or more review rounds:
- inspect recent diff or history first
- use `git diff -- <artifact>` to find uncommitted changes
- use `git log -1 -- <artifact>` or recent history to find the last committed handoff
- read changed sections before expanding to the full file
- read the newest review-thread additions before re-reading the whole artifact

This is required for multi-round review work.
The current artifact file remains the source of truth.

## Reviewer Role

Use this section only when `Role: reviewer`.

### Reviewer Responsibilities

The reviewer:
- reads the artifact critically
- identifies blocking and non-blocking issues
- checks whether implementation would require guessing
- checks whether validation is strong enough
- discusses findings with the human first
- writes comments back only after approval

### What the Reviewer Must Look For

Actively look for:
- missing or weak acceptance criteria
- vague implementation rules that different agents could interpret differently
- assumptions that were never validated
- wrong source-of-truth layer
- claimed completion that only proves service health, not plan completion
- planned work that disappeared into implicit deferral without human decision
- missing invariants, fallback behavior, or edge-case handling
- reasoning that sounds plausible but has no evidence
- for grouped plan items, inconsistent presentation of the same semantic role without justification
- for human-facing outputs, missing reader question, empty-state behavior, or screenshot/rendered-output acceptance
- for UI work, controls that are visible but not actually wired, filters with no sample coverage, unclear placeholder states, and mismatch between prototype fidelity and implementation scope
- for external resources, confusion between provider-side truth and internal estimates
- unsafe polling frequency, missing cost/rate-limit validation, or redundant pollers
- time-series type/query mismatches such as `increase()` on a snapshot gauge

### Reviewer Output Shape

Default output order:

1. blocking issues
2. non-blocking issues
3. overall judgment
4. whether comments should be written back

If there are no blocking issues, say so explicitly.

## Driver Role

Use this section only when `Role: driver`.

### Driver Responsibilities

The driver:
- owns the current artifact body
- reads reviewer comments carefully
- replies point-by-point where needed
- revises the artifact body when changes are accepted
- makes disagreements explicit instead of silently ignoring review

### How the Driver Should Respond

When replying to review:
- separate agreement, disagreement, and partial agreement
- explain what changed in the artifact body
- if rejecting a point, explain why
- if a reviewer found a real gap, fix the artifact instead of only defending it
- if validation was weak, strengthen it in the artifact body
- if implementation missed an accepted plan item, either implement it or record
  it as `Missing` / `Partial` / `Deferred` with evidence and human decision
- before handing off human-facing outputs, simulate the reader experience yourself: open the dashboard, read the report body, render the notification, or inspect the CLI/UI output; if you cannot simulate it, say so and ask the reviewer or human to do it

### Driver Output Shape

Default output order:

1. points accepted
2. points rejected or revised
3. artifact changes made
4. any remaining open questions

The driver is not scoring the artifact. The driver is responding to review and tightening the artifact.

## Human Shorthand

These are optional shortcuts for humans who already know them. They are not the primary interaction design. Agents must still present numbered decision menus when asking for human input.

Agents should recognize these shorthand tags in human input. Natural language is equally valid.

The human may use these shortcuts with either role:

- `[O]`
  Agree. Continue on this direction or write it back to the artifact.

- `[H]`
  Restate in plain language. Avoid jargon and explain more clearly.

- `[V]`
  Validation is not sufficient. Add stronger acceptance or self-verification before moving on.

- `[R]`
  The rationale is not convincing. Provide evidence and do not guess.

- `[X]`
  Drop this item or direction.

These may appear alone or with a short tail:

- `[H] too much jargon`
- `[V] define self-check first`
- `[R] what evidence supports this`
- `[X] drop this direction`

Common natural-language equivalents should also be recognized, for example:
- "say it plainly" / "说人话" -> `[H]`
- "no evidence" / "编的" -> `[R]`
- "not verifiable enough" / "验证不到" -> `[V]`
- "drop it" / "算了" -> `[X]`
- "OK" / "对" -> `[O]`

## Readiness Standard

An artifact is ready for its next step only when:
- the goal is clear
- non-goals are clear enough to prevent scope drift
- key assumptions are explicit
- acceptance is specific
- validation can be executed by the next agent where applicable
- unresolved questions are either closed or explicitly tracked

If these are not true, do not treat the artifact as ready for its next step.

## Iteration Discipline

If review rounds keep increasing without producing new high-value issues, either agent should proactively raise the possibility that the artifact is becoming over-specified.

In that situation, explicitly ask the human whether the artifact is already good enough to move to the next step.

## Post-Implementation Reality Check

If implementation or deployment exposes a gap that review should have caught:
- fix the immediate implementation issue
- write the gap back into the artifact or related review record in summarized form
- state the root cause clearly
- update this skill or its references if the gap reveals a systematic blind spot
- if the gap involves a human-facing output, add or strengthen reader-facing acceptance for future similar plans
- if the gap involves external resource usage, add or strengthen source-of-truth, polling-safety, and reconciliation checks

The goal is not blame. The goal is to turn a missed review failure mode into a stronger future protocol.

This skill document itself falls under this protocol when it is updated:
- treat changes to this skill as a plan-revision pass
- assign reviewer and driver roles explicitly

## Skill Self-Evolution Discipline

When updating this skill after a missed review case:
- add only generalized failure modes, not project-specific incidents
- keep the main `SKILL.md` as a short operating checklist, not an incident log
- prefer action-oriented checks over long explanations
- put concrete examples, case studies, and niche details in review threads or reference files instead of the main skill body
- if a new rule needs more than a few bullets, create a reference file and link it from `SKILL.md`
- periodically prune, merge, or shorten rules that overlap, rarely trigger, or describe the same underlying check

# Structured Review Collaboration

Load this reference for every structured-review reviewer or driver pass.

## Human Final Authority

Reviewer and driver propose. The human decides scope, priority tradeoffs,
done-enough decisions, merge authority, and whether a concern is over-engineered
relative to the task.

If reviewer and driver disagree and neither side yields, escalate to the human
instead of forcing a unilateral outcome.

## Reviewed File Model

The shared reviewed file has two functions:

1. Main artifact body.
   - Current source of truth.
   - Updated by the driver after accepted changes.

2. Review threads.
   - Appended near the end of the file.
   - Used for reviewer comments, driver replies, and explicit resolutions.

Use one issue or one tightly related cluster per thread.

Resolution examples:
- `Resolved. Artifact body updated in section 4.`
- `Resolved by human decision. Keep current scope; no further change.`
- `Superseded by later rewrite in section 7.`

## Write Ownership

Only one agent should be the active writer for a reviewed artifact at a time.

Default ownership:
- during review pass: reviewer writes comment threads;
- during revision pass: driver writes thread replies and artifact-body updates.

Avoid simultaneous edits to the same artifact file by both reviewer and driver.

## Handoff Commits

Structured review depends on clear git boundaries. After an agent writes to a
reviewed file, that agent must run `git status` and inspect the relevant diff
before handing off.

Default behavior after reviewed-file edits:
- runner `write-commit-to-plan` mode authorizes exactly the runner-verified
  review-thread commit;
- if the human has already authorized commits for this review session, create a
  small commit for the artifact change;
- if commit authorization is unclear outside runner mode, ask the human before
  committing;
- if the human chooses not to commit, explicitly say the artifact changes are
  left uncommitted.

Recommended commit message prefixes:
- reviewer comment pass: `structured-review: add reviewer comments for <topic>`;
- driver revision pass: `structured-review: respond to review for <topic>`;
- reviewer resolution pass: `structured-review: resolve review threads for <topic>`.

Do not mix unrelated code changes or unrelated reviewed files into a handoff
commit. If the worktree already has unrelated changes, mention them and commit
only the relevant file when authorized.

## Resolution Ownership

The reviewer is the default owner of final resolution.

Default lifecycle:
- reviewer opens the thread;
- driver replies and updates the artifact body if needed;
- reviewer checks the reply and updated body;
- reviewer writes the final resolution when satisfied.

A thread is not considered closed until the reviewer writes resolution. The
driver may mark a thread as ready for reviewer closure after replying and
updating the artifact body.

## Multi-Round Change Reading

When revisiting an artifact that already went through review:
- inspect recent diff or history first;
- use `git diff -- <artifact>` to find uncommitted changes;
- use `git log -1 -- <artifact>` or recent history to find the last committed
  handoff;
- read changed sections before expanding to the full file;
- read the newest review-thread additions before re-reading the whole artifact.

The current artifact file remains the source of truth.

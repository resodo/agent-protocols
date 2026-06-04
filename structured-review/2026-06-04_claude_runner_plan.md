# Claude Structured Review Runner Plan

Status: Draft for structured review
Owner: driver
Date: 2026-06-04

## Human Concern

The Claude reviewer runner is a general structured-review mechanism. It should
live in `agent-protocols`, not in a project repo such as `skynet-data`.
Project repos may add thin overlays later, but the core runner belongs with the
shared protocol.

## Goal

Add a reusable Claude Code `claude -p` runner to the shared
`structured-review` protocol so any target repo can run a reviewer pass with:

- explicit target worktree;
- explicit mode;
- direct loading of the shared `structured-review/SKILL.md`;
- optional target-repo overlays;
- true Claude Code auto permission mode;
- observable progress and durable non-tracked run evidence;
- final-state role-boundary verification.

## Non-Goals

- Do not add a `skynet-data` overlay in this PR.
- Do not update any downstream submodule pointer in this PR.
- Do not create tracked `.reviews/` packet directories.
- Do not add outer tool allowlists, denylists, high-risk command classifiers,
  or stream-side command enforcement around Claude.
- Do not replace human acceptance or human merge authority.

## Placement

Add the runner under the skill directory:

```text
structured-review/scripts/claude_structured_review.py
structured-review/tests/test_claude_structured_review.py
```

The script resolves the generic skill from its own location:

```text
<script>/../SKILL.md
```

The target repo is provided separately by `--worktree`. The runner loads local
overlays from the target repo:

```text
.agent-protocols/context.md
.agent-protocols/structured-review.md
```

This means the shared protocol stays canonical, while project-specific policy
remains in the project repo.

## Modes

Require `--mode` explicitly. Supported modes:

- `write-commit-to-plan`: Claude appends review threads to a driver-provided
  thread file in the target repo and commits exactly that file.
- `print-review`: Claude prints the review; it must not write files or commit.

`write-commit-to-plan` requires:

- `--thread-file <relative path in target worktree>`;
- `--topic <short commit-message topic>`.

`print-review` rejects `--thread-file`.

## Inputs

Required:

- `--worktree`: target repo root, not the `agent-protocols` repo root unless
  self-reviewing this repo;
- `--mode`;
- `--type`: `other-plan`, `impl-plan`, or `impl`;
- one or more `--artifact` paths relative to the target worktree;
- `--focus` or `--focus-file`.

Configurable:

- `--model`, default `opus`;
- `--effort`, default `xhigh`;
- `--timeout-sec`, default `1800`;
- `--heartbeat-sec`, default `30`;
- `--run-log-dir`, optional; default is a timestamped directory under the
  target repo's `.git/structured-review-runs/`.

The runner must reject paths that escape the target worktree.

## Claude Invocation

The runner invokes:

```text
claude -p --permission-mode auto --model <model> --effort <effort> \
  --output-format stream-json --include-partial-messages \
  --include-hook-events --verbose
```

It must not pass `--disallowedTools`, `--allowedTools`, or equivalent outer
tool restrictions by default. It must not classify, reject, or interrupt
stream tool-call content by command text.

This intentionally accepts residual invisible-side-effect risk from Claude
Code auto mode. That risk is a human-approved v1 tradeoff. The runner's safety
contract is final-state verification plus durable evidence, not partial tool
sandboxing.

## Prompt Contract

The generated prompt must include:

- role: reviewer;
- review type;
- worktree label using `<WORKTREE>`, not the real local absolute path;
- artifact list as relative paths;
- mode;
- thread file or `none`;
- topic or `none`;
- task-specific focus;
- full text of `structured-review/SKILL.md`;
- target repo context overlay if present;
- target repo structured-review overlay if present.

The prompt must not contain local user-home absolute paths. If focus text or
generated prompt contains the real worktree root, the runner fails before
calling Claude.

## Progress And Evidence

Progress:

- print a start line to stderr with mode, type, model, effort, and relative
  artifacts;
- print redacted `claude review event` lines for stream events;
- print redacted heartbeat lines every `--heartbeat-sec` seconds when no event
  arrives;
- redact target worktree, artifact paths, thread-file path, and local home.

Durable evidence:

- create a run-log directory outside tracked files by default:
  `.git/structured-review-runs/<timestamp>-<mode>-<type>/`;
- write `prompt.md`;
- write `stdout.stream.jsonl`;
- write `stderr.log`;
- write `metadata.json` with argv, mode, type, relative artifacts, model,
  effort, timeout, heartbeat, start/end timestamps, exit code, timeout flag,
  malformed stream count, and run outcome;
- write `review.md` containing rendered assistant text when available.

The run-log path may be printed redacted or relative to `.git`. The run-log
files are diagnostic evidence, not reviewed artifacts, and must not be
committed.

## Print Review Contract

In `print-review` mode:

- final Claude exit code must be zero;
- target repo `HEAD` must not change;
- target repo worktree status must not change;
- rendered review text must be non-empty;
- rendered review text must not contain local user-home absolute paths;
- the runner prints the redacted rendered review text to stdout after
  verification passes.

Progress remains on stderr so callers can capture stdout as review content.

## Write And Commit Contract

In `write-commit-to-plan` mode:

- target worktree must be clean before running;
- final Claude exit code must be zero;
- target worktree must be clean after running;
- exactly one new commit must exist;
- the new commit's parent must be the pre-run `HEAD`;
- the new commit must be the final target repo `HEAD`;
- the new commit must touch only `--thread-file`;
- commit subject must start with `structured-review: `;
- commit diff must add non-empty review-thread content;
- commit diff must not delete existing thread-file content;
- added lines must be under the target file's top-level `## Review Threads`
  section;
- commit diff must not contain local user-home absolute paths;
- commit diff must not contain obvious secret material.

The recommended commit subject is:

```text
structured-review: add reviewer comments for <topic>
```

## Driver Responsibility

The runner is not the driver. After Claude review:

- if Claude reports findings, the driver decides which to adopt, reject, or
  escalate before making implementation changes;
- if a finding changes accepted scope or adds meaningful risk, the driver
  should pause and discuss with the human before editing;
- the driver should summarize which decisions came from Claude, which were
  accepted, and which risks remain.

## Tests

Use Python standard library only. Add unit tests under
`structured-review/tests/` that cover:

- missing generic skill fails;
- target overlay loading from the target worktree;
- path escape rejection;
- explicit mode validation;
- multiple artifacts in prompt;
- prompt excludes real local worktree root;
- `claude_argv` uses auto mode and no outer allow/deny tool arguments;
- stream line with a `command` field is not classified;
- malformed stream line is counted;
- assistant text delta and final message text extraction;
- `print-review` rejects `HEAD` changes;
- `print-review` rejects empty review text;
- `print-review` renders review text to stdout after verification;
- dirty pre-run worktree rejection;
- write mode accepts exactly one review-thread commit;
- write mode rejects no commit, multiple commits, amended parent, wrong file,
  wrong prefix, deleted thread content, additions outside `## Review Threads`,
  additions without review-like content, local paths, and secret-like material;
- timeout reports whether dirty residue remains;
- run-loop writes prompt, stream stdout, stderr, metadata, and review evidence.

## CI

This repo currently has dispatch workflows but no pull-request CI for protocol
scripts. Add a small CI workflow for PRs and pushes that runs:

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
```

Keep the runner standard-library-only so the shared protocol repo does not
need package management to validate the script.

## Validation

Local validation:

```bash
python -m unittest discover -s structured-review/tests
python -m compileall -q structured-review
git diff --check
```

Manual dogfood validation:

- run `print-review` against a small target repo fixture or this repo and
  confirm stdout contains redacted review text;
- run `write-commit-to-plan` for this plan review and confirm the runner
  creates exactly one review-thread commit touching only this plan file.

## Acceptance Criteria

- Runner lives in `agent-protocols`, not in a project repo.
- Generic skill is loaded from the shared `structured-review` directory.
- Target repo overlays are loaded from the explicit target worktree.
- `write-commit-to-plan` and `print-review` are explicit and verified.
- Claude runs in true auto mode without outer tool allow/deny restrictions or
  stream command classification.
- Progress is observable and redacted.
- Prompt, stdout stream, stderr, metadata, and rendered review evidence are
  recorded in non-tracked run logs.
- Unit tests cover the safety and role-boundary behavior.
- CI validates tests and compileability.
- No downstream project overlay or submodule pointer update is included in this
  PR.

## Residual Risks

- Claude auto mode can perform side effects invisible to final git state. This
  is accepted for v1 and recorded here rather than hidden behind partial
  command filtering.
- Claude stream-json event shapes may change. The parser should stay narrow:
  malformed counting and assistant-text extraction only.
- The write-mode review-thread placement heuristic assumes a top-level
  `## Review Threads` section. Repos using a different artifact structure need
  an overlay or a later configurable anchor.

## Review Threads


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
- `--claude-bin`, optional; default `claude` resolved from `PATH`;
- `--run-log-dir`, optional; default is a timestamped directory under the
  target repo's resolved git dir.

The runner must reject paths that escape the target worktree.

`--focus` and `--focus-file` are mutually exclusive and exactly one is
required.

## Claude Invocation

The runner targets Claude Code `2.1.143` or newer. This plan was checked
against `claude -p --help` from Claude Code `2.1.143`, which documents:

- `--effort <level>` with `xhigh` as an accepted value;
- `--include-partial-messages`, valid with `--print` and stream-json output;
- `--include-hook-events`, valid with stream-json output.

The runner invokes:

```text
<claude-bin> -p --permission-mode auto --model <model> --effort <effort> \
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

## Deterministic Heuristics

The runner intentionally uses small deterministic checks instead of broad
security scanning or stream command policing.

### Local Path Detection

The redactor and repo-visible-output checks match:

- the exact resolved target worktree root;
- every resolved artifact path;
- the resolved thread-file path when provided;
- the current process home directory;
- macOS-style user-home prefixes expressed as slash, `Users`, slash,
  non-separator username, slash;
- Linux-style user-home prefixes expressed as slash, `home`, slash,
  non-separator username, slash, except the literal automation user `ubuntu`;
- Windows-style drive user-home prefixes expressed as drive letter, colon,
  separator, `Users`, separator, non-separator username, separator.

The runner replaces matched paths with neutral markers in progress and rendered
print-review output. It rejects matched paths in prompts, print-review rendered
text, and write-mode commit diffs.

### Secret-Like Material Detection

Write-mode commit diffs are rejected if they match any of these deterministic
patterns:

- case-insensitive private key block marker: `BEGIN [A-Z ]*PRIVATE KEY`;
- AWS access key IDs: `AKIA[0-9A-Z]{16}` or `ASIA[0-9A-Z]{16}`;
- GitHub classic tokens: `ghp_[A-Za-z0-9]{36}`;
- Slack tokens: `xox[baprs]-[A-Za-z0-9-]+`;
- generic assignment-like secrets:
  `(secret|password|token|api[_-]?key)\s*[:=]\s*['"]?[A-Za-z0-9_./+=-]{12,}`.

This is not a full secret scanner. Broader entropy checks and provider-specific
token inventories are deferred to repository-level secret scanning.

### Review Thread Anchor

For `write-commit-to-plan`, the thread file must already contain a top-level
review section before Claude is invoked:

```text
^##\s+Review Threads\s*$
```

The match is case-insensitive and must be a top-level `##` heading. The section
ends at the next top-level `## ` heading or at end of file. If the anchor is
missing, the runner fails before invoking Claude.

Post-commit verification requires every added line to land inside that section.
Nested headings such as `### Reviewer Pass` or `#### Thread A` are allowed
inside the section and must not become new anchors.

### Review-Like Added Content

Write-mode added content must include:

- at least one added `### ` heading inside the Review Threads section whose
  text contains `review`, `reviewer`, or `thread` case-insensitively; and
- at least one non-blank added body line after that heading.

This check is intentionally shallow. It proves Claude wrote a review-thread
shaped block, not that the review is semantically strong.

### Stream JSON Shapes

The stream parser only does two things: count malformed JSON lines and extract
assistant review text. It ignores tool-call content.

Accepted assistant text shapes:

- incremental text deltas:
  `{"type":"content_block_delta","delta":{"type":"text_delta","text":"..."}}`;
- final assistant message text blocks:
  `{"type":"assistant","message":{"content":[{"type":"text","text":"..."}]}}`.

Other valid JSON events are ignored for rendering and do not fail the run.

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
  `<resolved-git-dir>/structured-review-runs/<timestamp>-<pid>-<suffix>-<mode>-<type>/`;
- write `prompt.md`;
- write `stdout.stream.jsonl`;
- write `stderr.log`;
- write `metadata.json` with argv, mode, type, relative artifacts, model,
  effort, timeout, heartbeat, start/end timestamps, exit code, timeout flag,
  malformed stream count, `claude --version` output, and run outcome;
- write `review.md` containing rendered assistant text when available.

Resolve `<resolved-git-dir>` with `git rev-parse --git-dir` in the target
worktree; if the result is relative, resolve it against the target worktree.
This handles linked git worktrees where `.git` is a file. If `--worktree` is
not a git repo, fail before invoking Claude.

Use microsecond timestamp precision plus process ID and a short random suffix
to avoid concurrent-run collisions. No `.gitignore` entry is required because
the default log directory is outside the working tree.

The run-log path may be printed redacted or relative to the git dir. The
run-log files are diagnostic evidence, not reviewed artifacts, and must not be
committed.

Any stream event resets the heartbeat clock. Heartbeats are emitted only after
no stdout or stderr event has arrived for `--heartbeat-sec` seconds.

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
- `--thread-file` must contain the top-level `## Review Threads` anchor before
  invoking Claude;
- final Claude exit code must be zero;
- target worktree must be clean after running;
- exactly one new commit must exist;
- the new commit's parent must be the pre-run `HEAD`;
- the new commit must be the final target repo `HEAD`;
- the new commit must touch only `--thread-file`;
- commit subject must start with `structured-review: `;
- commit diff must add non-empty review-thread content;
- commit diff must not delete existing thread-file content;
- added lines must be inside the target file's top-level `## Review Threads`
  section and satisfy the review-like content heuristic;
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

## Exit Codes

- `0`: success.
- `1`: runner usage error, contract verification failure, git failure, missing
  anchor, path-hygiene failure, or Claude non-timeout failure.
- `2`: timeout. The runner records timeout and dirty-residue fields in
  `metadata.json` and prints a redacted stderr error that says whether the
  target worktree has uncommitted changes after timeout.

Malformed stream-json lines do not change the exit code by themselves; they
are counted in metadata.

## Maintenance

The runner's durable mechanisms are owned by the `structured-review` protocol:

- Claude CLI flags and minimum version;
- accepted stream-json event shapes;
- local path detection patterns;
- secret-like material patterns;
- Review Threads anchor and review-like content heuristics.

Any future change to those mechanisms must update this plan's successor,
`structured-review/SKILL.md` or runner help text as applicable, and the unit
tests in the same PR. Triggers for updates include a Claude Code version bump
that changes stream output, a real false positive or false negative in
redaction/secret/thread placement checks, or a new project repo overlay that
needs a different reviewed-file structure.

## Tests

Use Python standard library only. Add unit tests under
`structured-review/tests/` that cover:

- missing generic skill fails;
- target overlay loading from the target worktree;
- path escape rejection;
- explicit mode validation;
- `--focus` and `--focus-file` are mutually exclusive and exactly one is
  required;
- multiple artifacts in prompt;
- prompt excludes real local worktree root;
- `claude_argv` uses auto mode and no outer allow/deny tool arguments;
- `--claude-bin` override is honored and the default uses `PATH`;
- `claude --version` is recorded in metadata;
- stream line with a `command` field is not classified;
- malformed stream line is counted;
- assistant text delta and final message text extraction;
- redaction covers target worktree, artifact path, thread-file path, process
  home, and the specified user-home prefix patterns;
- `print-review` rejects `HEAD` changes;
- `print-review` rejects empty review text;
- `print-review` renders review text to stdout after verification;
- dirty pre-run worktree rejection;
- missing `## Review Threads` anchor rejects before Claude invocation;
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

Use Python 3.12 in CI. The runner should avoid non-standard dependencies.

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

### Thread 1: `--effort xhigh` default is an unvalidated CLI assumption

Blocking.

The Claude invocation defaults to `--effort xhigh`. Per the No-Made-Up-Rationale
rule, the plan should cite evidence that the targeted `claude` CLI accepts both
the `--effort` flag and the `xhigh` value, since a wrong flag breaks every
invocation before any review logic runs. Same concern, smaller scope, for
`--include-partial-messages` and `--include-hook-events`: pin the CLI version
the runner is being written against and call that out.

Suggested fix: name the minimum `claude` CLI version in the plan, and either
confirm the flags against `claude -p --help` for that version or downgrade
defaults to documented flags. Add a startup `claude --version` capture into
`metadata.json` so future debugging is not guesswork.

### Thread 2: "Obvious secret material" rejection has no defined heuristic

Blocking.

Write-mode lists `commit diff must not contain obvious secret material` and the
test list asserts rejection on `secret-like material`, but the plan never
defines what counts. Two implementing agents will pick incompatible heuristics
(one might check entropy, another only `BEGIN PRIVATE KEY`, a third nothing at
all), and the test will be impossible to write deterministically.

Suggested fix: enumerate the patterns to scan, for example case-insensitive
matches against `BEGIN [A-Z ]*PRIVATE KEY`, `AKIA[0-9A-Z]{16}`,
`ghp_[A-Za-z0-9]{36}`, `xox[baprs]-[A-Za-z0-9-]+`, and any other concrete
pattern set the runner will enforce. If broader scanning is out of scope for
v1, narrow the contract wording to match what is actually checked and record
the rest as deferred.

### Thread 3: Local-path redaction pattern is not specified

Blocking.

Multiple contracts say "must not contain local user-home absolute paths"
(prompt pre-check, rendered review text, commit diff) and the runner is
supposed to redact paths in progress lines and heartbeats, but the plan does
not define which strings count. macOS `/Users/<name>/...`, Linux
`/home/<name>/...`, `/private/var/folders/...`, `/Volumes/...`, expanded `~`,
literal `$HOME` are all candidates. Without a concrete list, the verifier and
the redactor will disagree.

Suggested fix: define the exact patterns the redactor matches and the
pre-check rejects. State whether the worktree root path itself (regardless of
prefix, e.g. `/tmp/...` worktrees) is also rejected, since the prompt contract
already says the real worktree root must not appear.

### Thread 4: "Review-like" content heuristic is undefined

Blocking.

The test list includes "rejects … additions without review-like content" and
the write contract says added lines must be "non-empty review-thread content."
Neither the body of the plan nor the contract section defines what shape
counts: a thread heading like `### Thread N:`, a `Resolved.` line, a minimum
line count, the presence of `Blocking` or `Non-blocking` markers, etc.

Suggested fix: pick one observable shape. For example: "at least one new line
matching `^### Thread \d+:` and at least one non-blank body line under it."
Whatever the choice, name it so the verifier and the prompt agree.

### Thread 5: `## Review Threads` anchor matcher and missing-section behavior

Blocking.

The contract requires additions to land under the target file's top-level
`## Review Threads` section, and the residual-risk section acknowledges this is
a heuristic. The plan does not specify:

- whether the match is exact (`## Review Threads`) or a regex
  (`^##\s+Review Threads\s*$`, case-insensitive);
- what the runner does when the section is missing (reject before calling
  Claude, vs. let Claude create it and then reject the commit);
- what counts as the end of the section when other top-level headings follow
  (next `^## ` line, end of file, etc.).

This drives both the prompt's instructions to Claude and the post-commit
verifier. Different choices will silently allow or block the same diff.

Suggested fix: specify the anchor regex, the section bounds rule, and the
missing-anchor failure mode (recommend: pre-flight reject before invoking
Claude, since this is a target-repo invariant).

### Thread 6: Stream-json event shape is not pinned

Non-blocking.

Residual risks acknowledge the stream-json shape may change and the parser
should stay narrow, but the plan does not name the specific event `type`
values and JSON paths used for assistant-text extraction or for the
malformed-line counter. The test "assistant text delta and final message text
extraction" relies on that shape. Two implementations will read different
fields and both call themselves correct.

Suggested fix: list the 1-2 event shapes the parser will accept (for example,
`message_delta` events with `delta.text`, and final `message` events with
`content[].text` of type `text`). Anything else counts as ignored or
malformed.

### Thread 7: Run-log directory under `.git/` does not handle git worktrees

Non-blocking.

Default run-log dir is `.git/structured-review-runs/<timestamp>-<mode>-<type>/`.
In a linked git worktree, `.git` is a file pointing to a worktree-specific
dir under the main repo's `.git/worktrees/<name>/`, not a directory the runner
can `mkdir` into.

Suggested fix: resolve the actual location with `git rev-parse --git-dir` (or
`--git-common-dir` if the intent is to share evidence across worktrees), and
state which one the plan chooses. Also state behavior when `--worktree` is
not a git repo: reject, or fall back to a tmp dir.

### Thread 8: Concurrent runs in the same second collide

Non-blocking.

Default subdirectory name uses `<timestamp>` only. Two runs started in the
same second produce the same path. With long-running reviews this is rare,
but with quick repeat dogfood runs it is realistic.

Suggested fix: use millisecond or microsecond precision in the timestamp, or
append a 4-char random suffix.

### Thread 9: `--focus` vs `--focus-file` interaction undefined

Non-blocking.

Inputs list both, written as "`--focus` or `--focus-file`". The plan does not
say whether they are mutually exclusive, whether one wins if both are given,
or whether they concatenate. Implementing agent will guess.

Suggested fix: declare them mutually exclusive with `argparse`'s mutually
exclusive group, and require exactly one.

### Thread 10: Heartbeat timer semantics not stated

Non-blocking.

"Print redacted heartbeat lines every `--heartbeat-sec` seconds when no event
arrives" is ambiguous: does any stream event reset the timer, or only a
text-bearing event? This affects how chatty the progress stream gets during
long tool calls.

Suggested fix: state that any stream event resets the heartbeat clock (or the
opposite, if the intent is to keep heartbeats firing during silent tool
loops).

### Thread 11: Mechanism Lifecycle coverage is thin

Non-blocking.

Per the Mechanism Lifecycle rule, durable mechanisms need owner, update
trigger, and stale-signal coverage. The plan introduces several: the stream
parser's accepted event shapes, the redaction pattern list, the secret-pattern
list, and the `## Review Threads` anchor heuristic. Residual risks mention
the schema may drift, but no owner or update trigger is named.

Suggested fix: in a short Maintenance section, name who reviews these lists
(e.g. driver of any future runner change), and the trigger (e.g. CLI version
bump in CI, or a parser regression observed in a real run).

### Thread 12: Redaction logic has no explicit unit test

Non-blocking.

The test list covers many contract behaviors but never names a direct test of
the redaction function itself ("redact `/Users/alice/repo/foo.md` →
`<WORKTREE>/foo.md`", etc.). Since redaction underlies both the print-review
output and the durability of the prompt pre-check, it deserves its own tests
independent of the surrounding flow.

Suggested fix: add explicit unit tests for the redactor against each pattern
class the plan ends up specifying in Thread 3.

### Thread 13: Claude binary discovery is unspecified

Non-blocking.

Plan does not say how the runner locates `claude`. Default `PATH` lookup is
fine, but an env override (e.g. `CLAUDE_BIN`) is common and is the kind of
thing the dogfood validation step will want.

Suggested fix: state PATH lookup as the default, and either add `CLAUDE_BIN`
support or explicitly defer it.

### Thread 14: Timeout exit code and dirty-residue reporting

Non-blocking.

The Tests section mentions "timeout reports whether dirty residue remains"
but no contract says what exit code the runner returns on timeout, or how
dirty residue is reported (stderr line, `metadata.json` field, both). For
the script to be scriptable in CI later, the exit code must be defined.

Suggested fix: define non-zero exit codes for timeout vs. contract violation
vs. malformed stream count, and state that dirty residue after timeout is
both logged to stderr and recorded in `metadata.json`.

### Thread 15: Run-log path under `.git/` and `.gitignore` interaction

Non-blocking.

Run-logs live under `.git/`, which is already outside the working tree, so
no `.gitignore` change is needed. Worth stating explicitly so an implementing
agent does not add a `.gitignore` rule "just to be safe" — that would
contradict the non-goal of touching downstream tracked files.

Suggested fix: one sentence in `## Progress And Evidence` clarifying that no
`.gitignore` entry is required because `.git/` is not part of the working
tree.

### Overall Judgment

The plan is well-aligned with the human concern: the runner lives in
`agent-protocols`, overlays are loaded from the target worktree, and there is
no skynet-data assumption embedded in the runner itself. True auto mode is
preserved explicitly, with outer allow/deny lists and stream-content
classification ruled out and called out as accepted residual risk.

Run-evidence durability under `.git/structured-review-runs/` is the right
shape, subject to Thread 7's worktree caveat.

The write/print contracts are mostly verifiable; the gaps are concentrated in
under-specified heuristics (Threads 2, 3, 4, 5) plus the unvalidated `--effort`
default (Thread 1). These are blockers for a confident implementation, but
each is a small targeted addition to the plan rather than an architectural
change.

CI scope (stdlib `unittest discover` plus `compileall`) is appropriate for a
standard-library shared script. Add an explicit Python minimum version and
the redaction-function tests from Thread 12 and the test plan is sufficient.

Five blocking threads (1, 2, 3, 4, 5). With those addressed, the plan is
ready for implementation. Non-blocking items can be folded into the same
revision pass or tracked as implementer follow-ups.

### Driver Response — 2026-06-04

Accepted Thread 1. I checked the local Claude Code CLI before revising the
plan: `claude --version` reports `2.1.143`, and `claude -p --help` documents
`--effort` with `xhigh`, plus `--include-partial-messages` and
`--include-hook-events`. The plan now targets Claude Code `2.1.143` or newer
and requires recording `claude --version` in metadata.

Accepted Thread 2. The plan now defines deterministic secret-like patterns:
private key block markers, AWS key IDs, GitHub classic tokens, Slack tokens,
and assignment-like secret/password/token/API-key values. Broader entropy
scanning is explicitly out of scope for v1 and left to repo-level scanners.

Accepted Thread 3. The plan now specifies exactly what the redactor and
repo-visible-output checks match: target worktree, artifact paths, thread-file
path, process home, and concrete macOS/Linux/Windows user-home prefix classes.

Accepted Thread 4. The plan now defines "review-like" added content as at
least one added `### ` heading inside the Review Threads section containing
`review`, `reviewer`, or `thread`, plus at least one non-blank body line after
that heading.

Accepted Thread 5. The plan now defines the Review Threads anchor as a
case-insensitive top-level `^##\s+Review Threads\s*$`, requires it to exist
before Claude is invoked, defines the section end as the next top-level
heading or EOF, and explicitly allows nested headings inside the section.

Accepted and folded in the non-blocking items:

- stream-json accepted shapes are specified;
- run logs use `git rev-parse --git-dir` instead of assuming `.git` is a
  directory;
- run-log names use microsecond timestamp plus process ID and random suffix;
- `--focus` and `--focus-file` are exactly-one mutually exclusive inputs;
- any stream event resets the heartbeat clock;
- mechanism lifecycle ownership and update triggers are documented;
- redaction-function tests are added to the test plan;
- `--claude-bin` is added, with `PATH` lookup as default;
- timeout exit code and dirty-residue metadata/stderr behavior are defined;
- no `.gitignore` entry is required because default run logs live outside the
  working tree.

Remaining risk: the deterministic checks are intentionally shallow. That is
acceptable for v1 because they protect the review workflow boundary; they are
not a replacement for semantic reviewer judgment or repository-level secret
scanning.

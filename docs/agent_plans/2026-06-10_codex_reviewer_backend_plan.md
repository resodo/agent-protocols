# Codex Reviewer Backend Plan

Status: historical - implemented via PR #15 (2026-06-10)
Branch: `feature/codex-reviewer-backend`
Worktree: `agent-protocols-codex-reviewer`

## Context

The structured-review runner currently invokes only Claude Code (`claude -p`)
as the reviewer. When the driver is also Claude, the reviewer shares the
driver's model family and its blind spots. The human wants cross-vendor
review: when the driver is Claude Code, the reviewer should default to Codex;
when the driver is Codex, the reviewer should default to Claude Code.

A spike (codex-cli 0.137.0, scratch repo) verified the key unknowns:

- `codex exec -` reads the prompt from stdin, like the current runner feeds
  `claude -p`.
- `--json` emits parseable JSONL events (`thread.started`, `item.started`,
  `item.completed` with `agent_message` / `command_execution` / `file_change`
  items, `turn.completed` with token usage). `--output-last-message FILE`
  writes the final agent message to a file.
- Under `--sandbox workspace-write`, Codex edits files but cannot commit: the
  sandbox blocks `.git/index.lock`. Adding `--add-dir <repo git dir>` was
  empirically shown to allow a clean `git commit` with the expected
  `structured-review:` message.
- `codex exec` exits 0 even when an inner command failed, so the runner's
  existing post-hoc write-mode verification stays the real gate. This matches
  the existing Claude path, which also does not trust the agent's exit
  behavior beyond returncode != 0.
- Driver detection markers exist on both sides: Claude Code sets `CLAUDECODE`
  (and `CLAUDE_CODE_*`) in child environments; Codex sets `CODEX_THREAD_ID`
  and `CODEX_SANDBOX` in its child environments.

Decisions already converged with the human:

1. Single runner script with a backend switch; keep the existing
   `structured-review/scripts/claude_structured_review.py` path because
   downstream repos reference it via submodule.
2. In write mode the Codex reviewer commits its own thread-file change
   (symmetric with Claude); `verify_write_mode` stays the single shared gate.
3. Review threads must record reviewer identity (backend) in pass headings.
4. Default reviewer backend is cross-vendor: Claude Code driver -> codex
   reviewer; Codex driver -> claude reviewer.
5. Codex defaults are pinned in the runner: model `gpt-5.5`, reasoning effort
   `xhigh`, overridable by flags.
6. Protocol text becomes backend-neutral where it currently says the runner is
   Claude-only.

## Problem

`claude_structured_review.py` hard-codes the Claude CLI: argv construction,
stream parsing, version probe, and the `--claude-bin` flag. Everything else
(prompt building, overlay loading, git snapshots, write/print verification,
redaction, run logs, metadata) is backend-agnostic. The protocol text
(`structured-review/SKILL.md`, `README.md`, `docs/CURRENT.md`) also assumes a
Claude reviewer.

## Goal

Let the bundled runner drive either Claude Code or Codex as the reviewer, with
a cross-vendor default keyed off the detected driver, without changing the
write/print verification contract.

## Non-Goals

- Do not rename or move the runner script.
- Do not change `verify_write_mode` / `verify_print_mode` semantics.
- Do not add multi-reviewer panels (both backends on one artifact) in this
  slice.
- Do not build a generic N-backend plugin system; exactly two backends.
- Do not touch Scout, closeout, planning, or backlog protocols beyond the
  structured-review text updates below.
- Do not weaken any SAFETY rule.

## Proposed Design

1. Backend abstraction in `claude_structured_review.py` (single file, stdlib
   only). A small registry keyed by backend name providing:
   - `argv(config, logs)`: full reviewer CLI argv;
   - `parse_line(line) -> StreamLineResult`: per-backend JSONL parsing;
   - `finalize(state, logs) -> review_text`: per-backend final text capture.
     Claude keeps the current delta-preference / last-message-wins behavior
     byte-for-byte; Codex accumulates `agent_message` items during the run and
     then prefers the `--output-last-message` file when present and non-empty;
   - `version(bin)`: version probe (`claude --version` / `codex --version`);
   - driver env markers for auto-detection.

   The existing module-level helpers keep their names: `claude_argv`,
   `process_stream_line`, and `claude_version` become the Claude backend's
   implementations, and the shared invocation loop keeps the `run_claude`
   name, so existing tests that reference or patch them stay valid. Existing
   tests are touched only where this plan requires it: pinning
   `--reviewer-backend claude` (or a marker-free env) for determinism, and
   the `reviewer_version` metadata rename below.

2. Codex backend specifics:
   - argv (write mode):
     `codex exec - --json --sandbox workspace-write --add-dir <git-dir>
     [--add-dir <git-common-dir>] -m <model>
     -c model_reasoning_effort=<effort> --output-last-message
     <run-log-dir>/last-message.txt`, run with `cwd=worktree`, prompt on
     stdin. Resolve git dirs via `git rev-parse --git-dir --git-common-dir`
     and pass both when they differ (linked worktrees).
   - argv (print mode): same minus `--add-dir`, with `--sandbox read-only`,
     keeping `--output-last-message`. The file is written by the codex
     harness outside the sandbox, not by a sandboxed child command: a spike
     probe under `--sandbox read-only` wrote the `-o` file successfully
     (codex-cli 0.137.0). For the same reason a caller-supplied
     `--run-log-dir` outside the worktree needs no extra `--add-dir`.
   - Review text: accumulate `agent_message` items from `item.completed`
     events; `finalize` prefers the `--output-last-message` file as the
     authoritative final text when present and non-empty, with the
     accumulated messages as fallback. Malformed JSONL lines keep using the
     existing malformed-line counter.
   - Stderr progress: print the existing heartbeat/event lines so long runs
     stay observable; record `turn.completed` usage in metadata as
     best-effort observability, not an acceptance contract.

3. Backend selection:
   - New flag `--reviewer-backend {auto,claude,codex}`, default `auto`.
   - `auto`: `CLAUDECODE` set and no Codex marker -> `codex`;
     `CODEX_THREAD_ID`/`CODEX_SANDBOX` set and no `CLAUDECODE` -> `claude`;
     both kinds of markers set -> hard error instructing an explicit
     `--reviewer-backend`; neither -> `claude` (today's behavior for humans
     invoking from a plain terminal).
   - When `auto` resolves through a detected driver marker, the runner
     preflights the selected backend binary (`shutil.which`) and fails with
     an actionable error naming `--reviewer-backend`, mirroring the
     both-markers error. The neither-marker default deliberately keeps
     today's no-preflight behavior so plain-terminal and CI invocations are
     unchanged.
   - `metadata.json` records the selected `backend`, the active backend's
     effective model and effort values in the existing `model`/`effort`
     fields, and a backend-neutral `reviewer_version` (renaming
     `claude_version`; the existing test asserting that key is updated).
     Codex token usage is recorded when seen, best-effort.

4. Flags and defaults:
   - Existing `--model` (default `opus`), `--effort` (default `xhigh`), and
     `--claude-bin` stay Claude-only, fully backward compatible.
   - New `--codex-bin` (default `codex`), `--codex-model` (default
     `gpt-5.5`), `--codex-effort` (default `xhigh`), as constants near the
     existing `DEFAULT_MODEL`. Rejected alternative: reusing `--model` for
     both backends, because existing callers pin `--model opus` and would
     silently misconfigure a Codex run under `auto`.

5. Reviewer identity in threads:
   - The prompt instructions gain one line for both backends: reviewer pass
     headings must name the reviewer backend, for example
     `### Reviewer pass 1 (impl, codex reviewer)`.
   - Commit-message contract is unchanged (`structured-review:` prefix).

6. Protocol and doc text:
   - `structured-review/SKILL.md`: rename the `Default Claude Runner Rule`
     section to a backend-neutral default-runner rule; state the cross-vendor
     default and the `auto` detection; define availability per configured
     backend binary; if the cross-vendor backend is unavailable, the runner
     fails loudly and substituting the same-vendor reviewer is an explicit
     human/driver decision via `--reviewer-backend`, not a silent fallback.
     Update the driver-summary wording (`Claude reviewer suggestions` ->
     reviewer suggestions with backend identity).
   - `README.md` usage section: add a `--reviewer-backend` example.
   - `docs/CURRENT.md`: structured-review entry mentions both reviewer
     backends.

7. Tests (`structured-review/tests/test_claude_structured_review.py`):
   - Backend selection: explicit flags; `auto` under each env-marker case,
     including the both-markers hard error and the marker-resolved
     preflight-unavailable error (env and `shutil.which` patched per test).
     Legacy tests pin `--reviewer-backend claude` or a marker-free env so
     they stay deterministic regardless of which agent runs them.
   - Codex argv construction: write vs print sandbox flags, `--add-dir`
     resolution for linked worktrees, pinned model/effort and overrides.
   - Codex stream parsing: agent_message extraction, last-message-file
     preference, malformed-line counting.
   - End-to-end fake `codex` bin (mirroring the existing fake `claude` test):
     write mode appends threads and commits, passes `verify_write_mode`;
     print mode prints and leaves the worktree untouched.
   - Prompt contains the reviewer-identity instruction for both backends.
   - Metadata records backend name and version string.

## Acceptance Criteria

- `--reviewer-backend codex` drives a fake `codex` bin through both modes and
  all existing verification rules pass unchanged.
- `auto` resolves: Claude driver env -> codex, Codex driver env -> claude,
  both -> hard error naming the flag, neither -> claude.
- A marker-resolved `auto` selection whose backend binary is missing fails
  with an error naming `--reviewer-backend`; the neither-marker default and
  explicit selections keep today's failure behavior.
- Codex defaults are `gpt-5.5` / `xhigh`, overridable via `--codex-model` /
  `--codex-effort`; Claude defaults and flags are byte-for-byte unchanged.
- Write-mode Codex argv includes the git-dir `--add-dir` entries; print-mode
  argv uses `--sandbox read-only` and no `--add-dir`.
- The reviewer prompt instructs backend-named pass headings for both
  backends.
- `metadata.json` records the selected backend, the active backend's
  effective model/effort, and a backend-neutral `reviewer_version`. Token
  usage recording is best-effort and not part of acceptance.
- `structured-review/SKILL.md`, `README.md`, and `docs/CURRENT.md` are
  backend-neutral and state the cross-vendor default and no-silent-fallback
  rule.
- The full existing test suite keeps passing.

## Validation Plan

Run locally in the feature worktree:

```bash
python -m unittest discover -s structured-review/tests
python -m unittest discover -s tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
```

CI runs the same set on the PR. No real `codex` or `claude` binary is invoked
by tests; both are faked, as today.

## Review Gates

1. Plan review gate: bundled runner, `write-commit-to-plan`, type
   `impl-plan`, this plan as artifact and thread file. The Codex backend does
   not exist yet, so this gate necessarily runs the Claude reviewer.
2. Implementation review gate: type `impl` against this accepted plan. If the
   implementation is green, prefer dogfooding the new Codex backend for this
   gate (Claude driver -> codex reviewer) and record the backend identity in
   the pass heading.
3. Closeout per `closeout/SKILL.md` after review gates resolve, with PR and
   human merge.

## Risks

- `codex exec` exits 0 despite inner failures; mitigated by the unchanged
  post-hoc verification (exactly one commit, thread-file-only, append-only).
- `--add-dir` grants the reviewer write access to the git dir; tampering is
  bounded by the same post-hoc verification plus run logs, and is no broader
  than the Claude path's `--permission-mode auto`.
- Env auto-detection can see both markers in nested agent chains; handled by
  the hard error plus explicit flag, never a silent guess.
- Codex's sandbox disables network (`CODEX_SANDBOX_NETWORK_DISABLED=1`), so a
  Codex reviewer cannot fetch external references. Reviews are repo-local by
  design; this parity difference is recorded here and in run metadata rather
  than in SKILL text, which stays lean.
- Pinned `gpt-5.5` will go stale; it is a named constant with an override
  flag, and the staleness signal is Codex rejecting the model name.
- `--json` is marked experimental upstream; tolerant parsing, the
  malformed-line counter, and the last-message file keep text capture robust.
- Fake-bin tests cannot exercise real Codex sandbox semantics (read-only
  blocking, `--add-dir` scope, harness-side `-o` writes); those claims rest
  on the spike evidence at codex-cli 0.137.0 and are re-validated live by the
  dogfooded implementation-review gate.

## Scope Addendum (2026-06-10, human-approved)

After the implementation review passed, the human approved two additions to
this PR during closeout discussion:

1. Closeout protocol delegation. `closeout/SKILL.md` carried a duplicated,
   now-stale copy of the runner policy ("use the bundled Claude runner",
   mode defaults). The duplicated mechanics are removed; closeout keeps its
   Closeout Review trigger list and defers runner/backend/mode policy to the
   structured-review skill. This was a non-goal of the original plan; the
   human explicitly widened scope to fix the drift at its root in this PR.

2. Runner-owned write mode. Field experience (roughly half of
   write-commit-to-plan runs historically, and one of four runner passes in
   this PR's own session) shows reviewer agents frequently violate the
   append-only thread-file contract, typically by deleting placeholder
   lines, invalidating otherwise-good reviews and forcing manual driver
   recovery. The write-mode mechanics change from reviewer-writes-and-commits
   to runner-writes-and-commits:
   - The reviewer always runs read-only and returns the review text; in
     write mode the runner itself appends that text verbatim under the
     thread file's `## Review Threads` section and creates the
     `structured-review:` commit. Append-only now holds by construction.
   - Before committing, the runner requires the reviewer to have left the
     worktree untouched, and checks the text is review-like, free of local
     absolute paths, and free of secret-like material. `verify_write_mode`
     is kept unchanged as a defense-in-depth self-check on the runner's own
     commit.
   - The Codex backend runs `--sandbox read-only` in both modes; the
     write-mode `--add-dir` git-dir grant is removed as no longer needed.
     The Claude backend's argv is unchanged.
   - The reviewer prompt no longer instructs committing; it instructs
     returning the complete review threads as markdown and explicitly
     forbids writing files.
   - The human's requirement driving this: the complete reviewer text must
     land in the durable thread verbatim with zero driver transcription
     burden, which the by-construction append guarantees.

Updated acceptance for the addendum (as amended after reviewer pass 3):

- Write mode produces exactly one runner-created commit whose added block is
  the reviewer's returned text byte-for-byte inside the `## Review Threads`
  section, for both backends, including when other `##` sections follow the
  threads section. The runner adds only the separating blank line before the
  block and a terminating newline when the returned text lacks one; an
  exact-output test pins this.
- A reviewer that modifies the worktree or HEAD in write mode fails the run
  before any append happens.
- Non-review-like, local-path-bearing, or secret-bearing reviewer output
  fails before any commit, with the text preserved in run logs.
- Codex argv contains `--sandbox workspace-write` and no `--add-dir` in both
  modes. Pass 3 ran under `read-only` and was environment-blocked from
  running the unittest suites (no writable temp dir), which would
  permanently remove reviewer-rerun validation from Codex reviews;
  `workspace-write` without any `.git` grant restores test execution (a
  sandbox probe confirmed writable temp dirs) while commits remain
  impossible and stray worktree writes still fail the run via the
  untouched-worktree check.
- `closeout/SKILL.md` keeps the trigger list and no longer states runner,
  backend, or mode policy.

## Review Threads

### Reviewer pass 1 (impl-plan, claude reviewer)

Original concern: is this plan concrete enough to implement a Codex reviewer
backend in the single-file runner without guessing, and does it keep the
write/print verification contract sound?

**Blocking issues**

None. Goal, non-goals, spike-backed assumptions, acceptance, and validation are
specific and executable; scope is right-sized to exactly two backends. The
items below are non-blocking refinements, not gaps that block starting.

**Non-blocking issues**

1. Backend-abstraction seam for review-text capture is under-specified against
   the current run loop. The enumerated registry interface (Proposed Design 1:
   `argv`, `parse_line`, `version`, env markers) does not name where Codex's
   documented text-capture behavior lives, and the existing loop is more
   entangled with backend specifics than that interface implies:
   - `run_claude` assembles `review_text` inline
     (`structured-review/scripts/claude_structured_review.py:698`) and
     *overwrites* `message_text_candidate` per line (`:684-685`, last-wins).
     Codex must *accumulate* multiple `agent_message` items and then *prefer the
     `--output-last-message` file* — a post-run step `parse_line` cannot do (it
     sees one line and cannot read a file). Name this seam (for example a
     backend `finalize(state, logs) -> review_text` hook) so the Claude path's
     delta-preference / last-wins behavior stays byte-for-byte while Codex gets
     accumulate-then-file.
   - Existing unit tests call `csr.claude_argv(...)`,
     `csr.process_stream_line(...)`, and `csr.claude_version(...)` by name
     (`structured-review/tests/test_claude_structured_review.py:237,290,298,301,308,313,319`).
     Acceptance says "full existing test suite keeps passing" and "Claude ...
     byte-for-byte unchanged." A registry refactor that renames these breaks
     those tests. State that these module-level helpers are preserved (wrapped
     as the Claude backend) or that the affected tests are updated, so the
     acceptance is not self-contradictory.

2. Print-mode `--output-last-message` under `--sandbox read-only` is unverified.
   Proposed Design 2 lists `--output-last-message` in the write-mode
   (workspace-write) argv and says print mode is "same minus `--add-dir`, with
   `--sandbox read-only`." If the sandboxed child writes that file, `read-only`
   blocks the write; if the codex harness writes it post-sandbox, it is fine.
   The spike covered workspace-write only. Pin whether print mode keeps
   `--output-last-message`, and if so confirm it works under `read-only`, or
   document the `agent_message` accumulation as the print-mode fallback. As
   written this ambiguity forces an implementer to guess.

3. A custom `--run-log-dir` can fall outside the Codex sandbox grant. The
   default run-log dir lives under the git-dir (`:542-546`), which write-mode
   `--add-dir <git-dir>` covers. But a caller-supplied `--run-log-dir` outside
   the worktree and git-dirs is in neither `workspace-write` (cwd) nor
   `--add-dir`, so the real sandbox would block
   `--output-last-message <run-log-dir>/last-message.txt`. Existing tests pass
   `--run-log-dir` to a temp path (`tests:558`), and a fake `codex` is not
   sandboxed, so the fake-bin e2e cannot catch this. Add the run-log dir as an
   `--add-dir` entry in write mode (or document `--output-last-message` as
   best-effort with the `agent_message` fallback), and call out that the faked
   bin masks real-sandbox-only failures.

4. Metadata semantics under Codex. `write_metadata` records `model`, `effort`,
   and `claude_version` (`:588-617`). On a Codex run, `--model`/`--effort`
   default to `opus`/`xhigh` and are unused; recording them verbatim mislabels a
   `gpt-5.5` run, and the `claude_version` key name is backend-specific.
   Acceptance says metadata records "the backend and its version" but is silent
   on these existing fields. Specify that metadata reflects the active backend's
   model/effort/version (namespaced or backend-keyed) and whether the
   `claude_version` key is preserved for backward compatibility or renamed.

5. An `auto`-selected-but-unavailable backend should fail with an actionable
   message. The no-silent-fallback property holds by construction: `auto`
   resolves to exactly one backend from env markers and the design has no
   substitution path, so the SKILL rule is enforceable as written. But Proposed
   Design 3 crafts a helpful hard error only for the both-markers case; an
   `auto`->codex resolution when `codex` is absent would surface as a raw
   `FileNotFoundError` ("fails loudly" but not clearly, and without naming the
   flag). Add a preflight availability check that mirrors the both-markers error
   and instructs an explicit `--reviewer-backend`, plus a test — the test plan
   currently omits this case.

**Overall judgment**

Ready for implementation. The plan is detailed, correctly scoped, and its
acceptance and validation are executable by the next agent. The write contract
is sound: `--add-dir <git-dir>` brings Codex to parity with the existing Claude
`--permission-mode auto` path, which already has full git-dir write access and
commits today, and `verify_write_mode` (`:443-478`) remains the single shared
gate bounding the HEAD movement, single-commit, thread-file-only, append-only,
no-local-path, and no-secret outcomes — so the `codex exec` exit-0-on-failure
behavior does not weaken the gate. Keeping `--model`/`--effort` Claude-only
while adding `--codex-*` is the right backward-compatibility call and preserves
existing callers that pin `--model opus`. The cross-vendor `auto` rule
(both-markers hard error, neither->claude) is coherent and reads the driver's
own inherited env, not the reviewer child's. The non-blocking items above are
clarity and edge-case tightenings.

**Residual risks / validation gaps**

- Git-dir side effects outside HEAD (refs, config, hooks, stash) are not
  verified by `verify_write_mode` for either backend; unchanged from today,
  parity preserved, acceptable.
- The fake-`codex` e2e cannot exercise real sandbox semantics (read-only
  writes, `--add-dir` scope, `--output-last-message` placement); those rest on
  the spike's empirical claims at codex-cli 0.137.0 plus the print-mode
  confirmation requested in item 2.
- Token-usage recording (`turn.completed`) appears in the design and risks but
  not in the acceptance criteria or the test list; if it is a contract, add
  coverage, otherwise mark it best-effort.

### Driver response 1

All five findings accepted; the plan body is updated accordingly.

- N1: the registry now names a `finalize(state, logs)` hook; Claude keeps its
  delta-preference/last-wins capture byte-for-byte, Codex accumulates then
  prefers the `-o` file. Module-level helper names (`claude_argv`,
  `process_stream_line`, `claude_version`, `run_claude`) are preserved as the
  Claude backend/shared loop, so name-coupled tests stay valid; tests change
  only for backend pinning and the `reviewer_version` rename.
- N2: resolved empirically rather than by fallback wording. An existing spike
  probe ran `codex exec --sandbox read-only` with `--output-last-message`
  targeting a path the sandbox could not have written, and the file was
  written: the codex harness writes `-o` outside the sandbox. Print mode
  keeps the flag, with accumulated `agent_message` text as fallback.
  Provenance: driver-reported spike at codex-cli 0.137.0.
- N3: the same harness-side `-o` evidence dissolves the custom
  `--run-log-dir` concern; no extra `--add-dir` is needed. The fake-bin
  masking caveat the reviewer raised is now recorded in Risks, with the
  dogfooded impl-review gate as the live re-validation.
- N4: metadata semantics specified: `backend`, active model/effort in the
  existing fields, backend-neutral `reviewer_version` (renamed from
  `claude_version`, updating the one asserting test), usage best-effort.
- N5: preflight added for marker-resolved `auto` selections with an error
  naming `--reviewer-backend`. Scope refinement: the neither-marker default
  and explicit selections keep today's no-preflight failure behavior, so
  plain-terminal and CI invocations do not change. Both-markers error stays
  as planned. A preflight test is added to the test plan.

Proceeding to implementation without a re-review pass: the reviewer found no
blocking issues and judged the plan ready for implementation; every change
above adopts the reviewer's own recommendations without altering accepted
scope. The human-mandated gate chain continues with the implementation
review dogfooding the Codex backend.

### Reviewer pass 2 (impl, codex reviewer)

Original concern: does commit `fba6a45` implement the accepted Codex reviewer
backend plan, including the driver response 1 refinements, without weakening
the structured-review runner contract?

**Blocking issues**

None.

**Non-blocking issues**

None.

**Traceability**

- Done: the backend seam is finalized with preserved helper names.
  `structured-review/scripts/claude_structured_review.py` keeps
  `claude_argv`, `process_stream_line`, `claude_version`, and `run_claude`,
  while adding `ReviewerBackend`, per-backend `finalize`, and Codex-specific
  stream handling. The Claude path still prefers streamed text deltas and then
  the last assistant message.
- Done: cross-vendor `auto` resolution matches the accepted rules.
  `resolve_reviewer_backend` maps Claude markers to `codex`, Codex markers to
  `claude`, neither marker to `claude`, and both marker kinds to a hard error
  naming `--reviewer-backend`. Marker-resolved missing binaries preflight with
  `shutil.which` and name the same flag.
- Done: Codex argv shape matches the plan for plain and linked worktrees.
  Write mode uses `codex exec - --json --sandbox workspace-write` plus
  `--add-dir` entries from `git rev-parse --git-dir --git-common-dir`; print
  mode uses `--sandbox read-only` and no `--add-dir`. The tests cover normal
  and linked worktree git-dir behavior.
- Done: Codex text capture prefers `last-message.txt` and falls back to
  accumulated `agent_message` items. The malformed-line counter and
  best-effort `turn.completed` usage capture are covered by the new tests.
- Done: metadata is backend-aware and uses `reviewer_version`. Metadata now
  records `backend`, active backend model and effort, `reviewer_version`, and
  optional token usage; the old `claude_version` test is updated
  deterministically.
- Done: reviewer identity is injected into the prompt, including the required
  backend-named pass heading example for both backends.
- Done: `structured-review/SKILL.md`, `README.md`, and `docs/CURRENT.md` are
  backend-neutral and state the cross-vendor default and no-silent-fallback
  rule.
- Done: Claude path behavior is preserved for the accepted surface. Legacy
  helper callers are pinned to `--reviewer-backend claude`, `--claude-bin`
  behavior remains path-based, and the existing verification functions keep the
  same write/print gate semantics.

**Overall judgment**

Ready for closeout. The implementation matches the accepted plan and the
driver response 1 refinements, and I found no blocking or non-blocking issues.

**Residual risks / validation gaps**

The local suite uses fake Claude and Codex binaries, so real Codex CLI sandbox
semantics for `--output-last-message` and `--add-dir` remain the spike-backed
risk already documented in the plan. I did not check PR CI status in this
review pass.

Validation rerun by reviewer:

```bash
python -m unittest discover -s structured-review/tests
python -m unittest discover -s tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
```

All five commands passed locally.

### Reviewer pass 3 (impl, codex reviewer)

Original concern: re-review commit `083f42c` against the human-approved Scope Addendum for runner-owned write mode and closeout runner-policy delegation.

**Blocking issues**

1. `append_and_commit_review` does not preserve the reviewer output verbatim. The addendum requires the runner-created commit’s added lines to be the reviewer’s output verbatim inside `## Review Threads` (`docs/agent_plans/2026-06-10_codex_reviewer_backend_plan.md:295`). The implementation writes `review_text.strip()` and normalizes surrounding newlines (`structured-review/scripts/claude_structured_review.py:494`-`498`), so leading/trailing reviewer text is changed before commit. The current tests check insertion before a later `##` section, but not exact equality of the committed block to the returned reviewer text (`structured-review/tests/test_claude_structured_review.py:859`). This weakens the addendum’s central “zero transcription / verbatim append” guarantee.

**Non-blocking issues**

None.

**Traceability**

- Done: closeout now keeps the Closeout Review trigger list and delegates runner/backend/mode policy to structured-review (`closeout/SKILL.md:46`).
- Partial: runner-owned write mode appends inside `## Review Threads`, including before later `##` sections, but not verbatim because of whitespace normalization.
- Done: write mode rejects reviewer HEAD/worktree changes before append (`structured-review/scripts/claude_structured_review.py:465`).
- Done: non-review-like, local-path, and secret-like output is rejected before append by `verify_reviewer_output`.
- Done: Codex argv is `--sandbox read-only` with no `--add-dir` in both modes (`structured-review/scripts/claude_structured_review.py:624`).
- Done: `verify_write_mode` remains as the post-commit self-check.
- Done: the write-mode prompt tells reviewers not to write files, stage, or commit (`structured-review/scripts/claude_structured_review.py:298`).
- Done: structured-review and closeout text are consistent on runner-policy delegation.

**Overall judgment**

Not ready for closeout until the verbatim append contract is fixed and covered by an exact-output test.

**Residual risks / validation gaps**

Reviewer validation was environment-blocked for the unittest commands: all three unittest suites failed before assertions because the read-only sandbox provided no writable temporary directory. `python -m compileall -q structured-review scout scripts tests` and `git diff --check` returned 0.

Commands attempted:

```bash
python -m unittest discover -s structured-review/tests
python -m unittest discover -s tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
```

### Driver response 2

Pass 3 findings, classified:

- B1 accepted. `append_and_commit_review` no longer strips the reviewer
  text: the returned text is appended byte-for-byte, with only a separating
  blank line before it and a terminating newline added when the text lacks
  one. The addendum acceptance wording is amended to state that exact
  contract, and a new exact-output test asserts the committed file contains
  the returned text unchanged.
- The environment-blocked validation in pass 3's residuals is treated as a
  finding in its own right: `--sandbox read-only` would permanently remove
  reviewer-rerun validation from Codex reviews because unittest needs
  writable temp dirs. Codex now runs `--sandbox workspace-write` with no
  `.git` grant in both modes: a sandbox probe confirmed temp dirs are
  writable, commits remain impossible (the original spike showed the sandbox
  blocks `.git`), and any stray worktree write still fails the run through
  `verify_reviewer_output`'s untouched-worktree check before any append.
  The addendum acceptance is amended accordingly.
- Validation after the fixes: full local suite green (structured-review,
  tests, scout, backlog checker, compileall, `git diff --check`),
  driver-reported; pass 4 should be able to rerun the suites under the new
  sandbox.

### Reviewer pass 4 (impl, codex reviewer)

Original concern: implementation re-review of the pass-3 fixes in Driver response 2: verbatim runner append with exact-output coverage, and Codex `workspace-write` without `.git` grant so reviewer validation can run.

**Blocking issues**

None.

**Non-blocking issues**

None.

**Traceability**

- Done: pass-3 B1 is resolved. `append_and_commit_review` now appends `review_text` without stripping it, adding only the separator before the block and a final newline when missing.
- Done: exact-output coverage was added in `test_append_preserves_review_text_byte_for_byte`, including indentation and trailing spaces inside the returned review text.
- Done: Codex argv uses `--sandbox workspace-write` in both write and print modes and does not include `--add-dir`.
- Done: the runner still verifies reviewer output before appending and runs `verify_write_mode` after the runner-created commit.
- Done: earlier accepted backend-selection, prompt, metadata, fake Codex, and protocol-text behavior did not regress in the inspected artifacts.

**Overall judgment**

Ready for closeout. The amended addendum acceptance is satisfied, and there are no blocking issues.

**Residual risks / validation gaps**

Reviewer-rerun validation passed locally. I ran:

```bash
python -m unittest discover -s structured-review/tests
python -m unittest discover -s tests
python -m unittest discover -s scout/tests
python -m compileall -q structured-review scout scripts tests
git diff --check
python scripts/check_backlog.py --root .
```

All passed. The worktree remained clean after validation.

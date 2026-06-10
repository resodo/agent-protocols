# Codex Reviewer Backend Plan

Status: draft for plan review
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
   - `version(bin)`: version probe (`claude --version` / `codex --version`);
   - driver env markers for auto-detection.

2. Codex backend specifics:
   - argv (write mode):
     `codex exec - --json --sandbox workspace-write --add-dir <git-dir>
     [--add-dir <git-common-dir>] -m <model>
     -c model_reasoning_effort=<effort> --output-last-message
     <run-log-dir>/last-message.txt`, run with `cwd=worktree`, prompt on
     stdin. Resolve git dirs via `git rev-parse --git-dir --git-common-dir`
     and pass both when they differ (linked worktrees).
   - argv (print mode): same minus `--add-dir`, with `--sandbox read-only`.
   - Review text: accumulate `agent_message` items from `item.completed`
     events; prefer the `--output-last-message` file as the authoritative
     final text when present and non-empty. Malformed JSONL lines keep using
     the existing malformed-line counter.
   - Stderr progress: print the existing heartbeat/event lines so long runs
     stay observable; record `turn.completed` usage in metadata.

3. Backend selection:
   - New flag `--reviewer-backend {auto,claude,codex}`, default `auto`.
   - `auto`: `CLAUDECODE` set and no Codex marker -> `codex`;
     `CODEX_THREAD_ID`/`CODEX_SANDBOX` set and no `CLAUDECODE` -> `claude`;
     both kinds of markers set -> hard error instructing an explicit
     `--reviewer-backend`; neither -> `claude` (today's behavior for humans
     invoking from a plain terminal).
   - The selected backend, binary version, argv, and (for Codex) token usage
     are recorded in `metadata.json`.

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
     including the both-markers hard error (env patched per test).
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
- Codex defaults are `gpt-5.5` / `xhigh`, overridable via `--codex-model` /
  `--codex-effort`; Claude defaults and flags are byte-for-byte unchanged.
- Write-mode Codex argv includes the git-dir `--add-dir` entries; print-mode
  argv uses `--sandbox read-only` and no `--add-dir`.
- The reviewer prompt instructs backend-named pass headings for both
  backends.
- `metadata.json` records the backend and its version.
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

# Plan: the docs check script and the scope-review runner

Status: active implementation plan
Branch: `docs-check-script`
Document level: plan (one PR).

## What and why

The development-docs mechanism (rules in `AGENTS.md` files, a scope review
before work, a docs check on every PR) was approved with all areas switching
at once. Its protocol text is a separate PR (`doc-mechanism-protocols`). This
PR delivers the two programs that text names, turned from a lab prototype
(one 452-line script, 12 subcommands, run against a toy repo) into a tested,
project-neutral tool:

1. `scripts/docs_check.py` - the docs check.
2. `scope-review/run_scope_review.py` and `scope-review/reviewer_prompt.md` -
   the runner that asks a fresh, tool-less model session to review one
   proposal, and the reviewer's question sheet.
3. `tests/test_docs_check.py` and `tests/test_scope_review_runner.py` -
   unittest, stdlib only, each test builds a tiny git repo in a temp dir.
   CI already runs `python -m unittest discover -s tests`, so no workflow
   change.

Everything project-specific comes from a per-repo config file
`.agent-protocols/docs-check.json` (JSON, read from the repo root; `--config`
overrides). The script carries no project names.

## Formats (unchanged from the design)

```
- <area>.R<n> <one sentence> [lint: <check>] | [review] (<source>)
  - exception: <what> (approved: <who> <YYYY-MM-DD>; review: <YYYY-MM-DD>; <PR or plan>)
```

Commit-message lines: `Rules-read:` followed by `- <id>: applies; ...` or
`- <id>: n/a; ...`; `Raises: <name> <old> -> <new> - <reason>`;
`Rules-removed: <id> - <reason>`. The script reads the messages of every
commit in `<base>..HEAD` (normally one commit at READY; on a GitHub
`pull_request` checkout HEAD is a merge commit, so reading only HEAD would
miss the PR's own message).

## Subcommands

Default base is `origin/main` (`--base REF`).

- `tags` - rule and exception lines well formed; ids unique repo-wide;
  every `[lint: X]` resolves to a check named by the config's lint sources
  or to one of the docs check's own two check names; an exception sits under
  a rule.
- `paths` - every backquoted path with a `/` in a rule line, an exception
  line or a routing-table row exists (repo-relative, or relative to that
  `AGENTS.md`'s directory).
- `claude-md` - every `CLAUDE.md` is a symlink to `AGENTS.md` or the single
  line `@AGENTS.md`.
- `routes` - every `.md` under the current-docs dir is a row of the root
  routing table; passes when the dir does not exist.
- `rule-ids` - every rule id at base still exists, unless `Rules-removed:`.
- `rules-read` - the commit messages account for every `[review]` rule in
  the `AGENTS.md` chain (root down to the file's directory) of every touched
  path, `AGENTS.md` files included. Touched paths are both sides of a rename
  and deleted paths; the chains are taken at HEAD and at base, so a rule whose
  directory the change deletes still has to be accounted for.
- `numbers` - each configured ratchet number at HEAD is not above its value
  at base; an increase passes only with a matching `Raises:` line (old and
  new must match). No baseline file.
- `scope` - decides whether a scope-review record is needed (four signals:
  a new `proposal.md` under `<plans>/<changes>/`; a rule or exception
  changed; a rule moved to another file unchanged; a ratchet number goes up;
  a non-rename change to a file under an `AGENTS.md` that carries the
  incident-only marker). When a signal fires and the change carries no
  record, it fails and says where to write it:
  `<plans>/<changes>/<name>/proposal.md` plus the runner's
  `scope-review.md` next to it (only records under that prefix count).
  Otherwise it checks every changed record there: verdict
  `go` or `ask` (`cut`, `no`, anything else fails), `proposal.md` next to it,
  `proposal_sha` matches, one line for every rule governing the touched
  paths (the same HEAD-and-base chains as `rules-read`, all tags).
- How a change to `AGENTS.md` files is classified (shared by `scope` and
  `gated`), in this order:
  1. Rule changed: an id whose rule line (text, tag, source) differs between
     base and HEAD, including an id added or removed; or an id under which
     HEAD has an exception line (rule, what, who, date, review date, ref)
     that base does not have, which covers a new exception and a later
     review date. An exception present at base and absent at HEAD is not a
     change; it is reported as "ended" (note, no stop).
  2. Rule moved: an id not in 1 whose rule line sits in a different
     `AGENTS.md` at HEAD. It is a pure rename, not a move, when the old file
     is gone at HEAD, the new file did not exist at base, and the two files
     hold the same rule ids (the file went with its directory); a pure
     rename is neither a trigger nor a stop.
  3. For the incident-only signal, a file renamed unchanged (`R100`) and
     `AGENTS.md` files themselves do not count.
  Adding or removing a `sys.` rule is a change to that rule under 1, so it
  needs the answer of the human, as does rewording it or a new or extended
  exception under it.
- `gated [--log FILE]` - what the merge agent stops on and whose answer it
  needs (exit 0; it is a list, not a gate):
  - needs the answer of the human: a `sys.` rule's text, or an exception
    under it new or changed (extended); a scope verdict `ask` that names a
    conflict with a `sys.` rule; any change to a file the config names as
    decision boundary or ledger.
  - needs the answer of the master (ledger entry) or the human: other rules
    and exceptions; a ratchet number up; a rule moved unchanged; `ask`
    without a `sys.` conflict. For `ask`, the question and cut list are
    printed under it.
  - send back to the author: a record whose sha is not in the runner's log.
  - no stop (a note at most): an exception ended (line deleted), a pure
    directory rename (the `AGENTS.md` content moved unchanged with it), a
    number down, non-rule text.
- `exceptions [--today YYYY-MM-DD]` - open exceptions, overdue marked.
- `report --range A..B` - rule counts, per-rule applies/n/a counts from
  `Rules-read:` blocks, scope verdict distribution, current numbers.
- `rules-for PATH...` - every rule (and its exceptions) governing PATH.

## Config (`.agent-protocols/docs-check.json`)

```json
{
  "system_prefix": "sys",
  "plans_dir": "docs/agent_plans",
  "changes_subdir": "changes",
  "archive_subdir": "archive",
  "current_docs_dir": "docs/current",
  "routing_heading": "## Read routing",
  "own_checks": {"incident_fixes_only": "docs-check:incident-fixes-only",
                 "ratchet": "docs-check:ratchet"},
  "incident_only_marker": "[lint: docs-check:incident-fixes-only]",
  "lint_sources": [
    {"kind": "toml_list", "file": "pyproject.toml",
     "table": "tool.importlinter.contracts", "key": "id", "fallback_key": "name",
     "prefix": "importlinter:"},
    {"kind": "regex", "file": "scripts/light_checks.sh",
     "pattern": "^\\s*check \"([^\"]+)\"", "prefix": "light:"}
  ],
  "ratchets": {
    "root_agents_md_lines": {"kind": "file_lines", "file": "AGENTS.md"},
    "layer_exemption_lines": {"kind": "regex_lines", "file": "pyproject.toml",
      "pattern": "^\\s*\"app\\.[^\"]+ -> [^\"]+\",?", "start": "ignore_imports = [", "end": "]"},
    "plans_outside_changes": {"kind": "glob_count", "glob": "docs/agent_plans/*",
      "exclude": ["docs/agent_plans/README.md"]},
    "top_modules_without_agents_md": {"kind": "dirs_without_agents_md", "dir": "app"}
  },
  "decision_boundary_paths": [".agent-protocols/decision-boundary.md"],
  "ledger_paths": [".agent-protocols/authority-ledger.md"],
  "placement_questions": "docs/architecture/placement.md",
  "scope_review": {"model": "...", "effort": "high", "command": ["..."], "log": "~/..."}
}
```

All keys optional; defaults are the values shown for the directory keys and
empty lists/maps otherwise. Ratchet kinds: `file_lines`, `glob_count`
(segment-wise `fnmatch`, `**` spans directories, over tracked files),
`regex_lines` (optionally between a start-marker line and the next end-marker
line), `dirs_without_agents_md` (top-level dirs under `dir` that contain
tracked files and lack `AGENTS.md`). A number whose source is missing at a
ref is not measured there. Everything is counted from tracked files at the
ref (or `git ls-files` for HEAD), never from untracked disk files.

## Runner

`scope-review/run_scope_review.py <name> [--repo DIR] [--config FILE]
[--dry-run]`:

1. Reads `<plans>/<changes>/<name>/proposal.md`; takes the bullet paths
   under `## Touches`.
2. Collects the governing rules with the docs check's `rules-for` logic
   (imported from `scripts/docs_check.py` in the same checkout).
3. Builds the prompt: `scope-review/reviewer_prompt.md`, the rules, the
   placement-questions file the config names (if any), the proposal.
4. Runs the model command from a fresh empty temp dir, prompt on stdin. The
   command is a list with `{model}`, `{effort}`, `{output}` placeholders from
   `scope_review.command`; default is Codex non-interactive with every tool
   family off: `codex exec - --ephemeral --skip-git-repo-check
   --ignore-user-config --ignore-rules --sandbox read-only --disable
   shell_tool --disable unified_exec --disable code_mode_host --disable apps
   --disable plugins --disable multi_agent --disable goals --disable
   image_generation --disable view_image -c web_search=disabled -m {model}
   -c model_reasoning_effort={effort} --color never --output-last-message
   {output}` (same `exec -` stdin pattern as the structured-review runner).
   Checked once against codex-cli 0.169 from an empty temp dir with that
   exact flag set: asked to run `ls /`, read `/etc/hosts`, search the web and
   start a sub-agent, the model reported "code-mode host is disabled", no
   file or web tool, and a failed sub-agent spawn. With only the two shell
   flags (the first draft) it still had web, MCP and image tools, so the
   longer set is needed. The user-level instruction file of the CLI is still
   loaded (it is not repo context); a fully clean profile is a follow-up. A
   custom `command` is the overlay's responsibility to keep tool-free.
   Model: env `SCOPE_REVIEW_MODEL`, else config, else `gpt-6-sol` (the
   structured-review normal default); effort likewise (`high`).
5. Takes the answer from the first `verdict:` line on; refuses to write a
   record when the verdict is not one of go/cut/ask/no.
6. Writes `scope-review.md` with front matter `verdict`, `reviewer`,
   `run_id` (`sr-<UTC>-<4 hex>`), `proposal_sha` (sha256 of the proposal,
   12 hex), then the body.
7. Appends the record's sha (sha256 of the file, 12 hex) to the log:
   env `SCOPE_REVIEW_LOG`, else config `scope_review.log` (`~` expanded).
   The log must be outside the repo; the runner refuses otherwise.

`--dry-run` prints the prompt and the command and calls nothing.

`reviewer_prompt.md` is in this PR (`scope-review/reviewer_prompt.md`), so
the implementation review reads its exact text. It is the lab question sheet
(six questions: problem real today, owner by rule id or placement line,
conflicts, smallest version, anything kept alive from now on, rules to
change; three borrowed questions: "No future-proofing?", "Using framework
directly?", the concrete failure mode before complexity; delete/move/conflict
only; four verdicts; the output format), plus a block asked only of rule
lines the proposal adds, rewords, moves or opens an exception under: a
source (incident number or dated decision); could a program check it; would
a skilled person get it wrong without it; name a change someone could argue
is outside the wording though the rule means to stop it, and does the
wording stop it; does an inner rule loosen an outer one.

## Tests

Neutral names only (`app/sources/`, `vendor_files/`, a fetch service). One
fixture repo builder reproduces the lab scenarios: base checks; malformed
lines; an exception opened under `sys.R1` (scope, gated, exceptions, rules-for);
paying debt (number down: no trigger, no stop); an undeclared then declared
raise; old-way plan file; a renamed dir named in the routing table;
CLAUDE.md own rules vs import vs symlink; current doc not routed; routes with
no current dir; dropped lint check; rename with `git mv` (rule-ids ok, no
trigger, no stop); split dropping `AGENTS.md`; `Rules-removed:`; rule moved
unchanged (trigger, master pile); a signal with no record (fails, names the
location); a deleted directory with its `AGENTS.md` (its `[review]` rules
still required in `Rules-read:`); exception ended (note, no stop) vs
extended (human); dir rule changed (master pile); decision-boundary and
ledger changes (human); ask records with and without a sys conflict;
hand-edited record not in the log; cut/no verdicts; proposal changed after
review; missing rule line in a record; rules-read missing/complete; report.
Runner tests use a fake model command (a small Python script) to check the
empty working dir, the prompt contents, front matter, sha, log append,
refusal of an in-repo log and of a bad verdict, and `--dry-run`.

Runner-side tests cannot prove tool isolation (they use a fake command);
the probe above is the evidence for the default command.

The runner is Python (stdlib, testable with a fake command), so its name is
`scope-review/run_scope_review.py`; the protocol-text PR currently says
`run_scope_review.sh` and must use the `.py` name.

## Not in scope

Protocol text (`scope-review/SKILL.md` and the rest; other PR), consumer
overlays and CI wiring in consumer repos, the doc watcher, archiving
finished plan dirs.

## Validation

Structured review: plan and implementation, Codex normal. CI on GitHub; no
local test runs. Diff grep for personal, company, product and host names and
machine paths before commit.

## Review Threads

### Reviewer pass 1 (impl-plan, codex reviewer)

The approved goal is a project-neutral docs check and an isolated scope-review runner that classify changes and required decisions accurately.

#### Blocking issues

**Thread 1 — Specify how `scope` fails when a required record is absent.** The plan says `scope` decides when review is needed, then describes checks on changed `scope-review.md` files (`docs/agent_plans/2026-11-26_docs_check_script_plan.md:65-72`). A change under an incident-only rule could have no record to check. Name the required record location, require its presence when a signal fires, and test the missing-record case.

**Thread 2 — Define the classification order for removals and renames.** “A rule or exception changed” and “a rule moved to another file” can also describe an ended exception or a pure directory rename (`:65-86`), although both belong in the no-stop pile. State how the check distinguishes those cases before classifying a change. Also say explicitly where adding or removing a `sys.` rule belongs; “a `sys.` rule’s text” does not settle that case. Test these boundaries.

**Thread 3 — Cover rules that existed only at the base ref.** `rules-read` does not say which revision supplies the governing `AGENTS.md` chain (`:59-61`). If a touched directory and its nested `AGENTS.md` are deleted, a HEAD-only walk misses its `[review]` rules. Require coverage of the applicable base and HEAD chains for touched old and new paths, and add a deletion or rename test that would fail without the base chain.

**Thread 4 — Establish the runner’s tool isolation.** The default command disables two Codex features, while `scope_review.command` can replace the command (`:147-155`). The plan does not establish that either invocation has no other tools; a read-only sandbox and empty working directory do not prove that property. Define the supported tool-free command configuration and include a negative exercise on the actual backend that shows a tool attempt is unavailable. The fake-command tests prove directory and prompt handling, but cannot prove tool isolation.

**Thread 5 — Identify the question sheet to implement.** The plan calls for “the lab question sheet” and three borrowed questions (`:167-173`), but gives neither their text nor a source location in this checkout. Add the exact questions or a reviewable source reference so implementation does not have to reconstruct the prompt.

#### Non-blocking issues

None.

#### Overall judgment

**Not ready for implementation.** The config keeps project-specific paths and ratchets outside the script, the `Raises:` comparison is specified, and the existing CI workflow runs `python -m unittest discover -s tests`. The five gaps above affect required behavior or leave implementation choices unresolved.

#### Residual risks and validation gaps

No tests were run, as instructed. CI should exercise the added negative cases in Threads 1–3; the actual backend isolation exercise in Thread 4 also remains to be demonstrated. The worktree was clean at review time.

### Driver response 1

Accepted all five. Thread 1: `scope` fails with the record location when a
signal fires and no record is present; only records under
`<plans>/<changes>/` count; a missing-record test is listed. Thread 2: the
classification order is now written out (rule changed, then moved vs pure
rename, then the incident signal), with `sys.` rule add/remove placed in the
human pile. Thread 3: governing chains are taken at HEAD and at base over
both sides of renames and deleted paths, for `rules-read` and the record's
rule lines; a test deletes a directory with its `AGENTS.md`. Thread 4: the
default command now switches off every tool family, and a one-off probe on
codex-cli 0.169 with the exact flags is recorded in the Runner section (the
two-flag draft still had web, MCP and image tools). Thread 5: the prompt file
is part of this PR and the plan lists its questions.

### Reviewer pass 2 (impl-plan, codex reviewer)

The approved goal is a project-neutral docs check and a scope-review runner that classify changes and required decisions accurately.

#### Blocking issues

None. All five round-one threads are resolved:

1. **Thread 1 — Resolved.** `scope` now fails when a signal requires a record and none is present, names the required location, and includes a missing-record test.
2. **Thread 2 — Resolved.** The plan defines classification order for changed rules, ended exceptions, moves, and pure renames. It places added and removed `sys.` rules in the human-decision category and lists boundary tests.
3. **Thread 3 — Resolved.** `rules-read` and scope records use the governing chains at both base and HEAD for touched old and new paths. The plan includes a deleted-directory test.
4. **Thread 4 — Resolved for the default command.** The plan specifies the disabled tool families and reports a negative exercise against codex-cli 0.169. It explicitly assigns tool isolation for custom commands to the consumer overlay.
5. **Thread 5 — Resolved.** `scope-review/reviewer_prompt.md` is present with the questions and output format the plan calls for.

#### Non-blocking issues

None.

#### Overall judgment

**Ready for implementation.** The five requested gaps no longer require the implementing agent to reconstruct behavior or prompt text.

#### Residual risks and validation gaps

The backend isolation exercise is driver-reported; I did not rerun it. Implementation review should compare the command and prompt with this plan. CI should run `python -m unittest discover -s tests`, including the specified negative cases. No tests were run during this review. The worktree was clean.

### Reviewer pass 1 (impl, codex reviewer)

The approved goal is a project-neutral docs check and a scope-review runner that reliably classify changes and identify required decisions.

#### Blocking issues

**Thread 1 — `tags` accepts exceptions outside a rule.** In `scripts/docs_check.py:205-224`, the parser keeps the last rule across unrelated text. A normal bullet followed by an exception can therefore pass `tags` even though the exception is not directly under the rule. Clear the association when an intervening line ends the rule block, and add a negative test.

**Thread 2 — `rules-read` accepts an empty explanation.** The optional ending in `stated_rules()` (`scripts/docs_check.py:544-549`) accepts `- sys.R1: applies` and `- sys.R1: applies;` as accounting for a rule. The approved format requires a reason after the semicolon. Tighten the match and test both empty forms.

**Thread 3 — `gated` can skip record provenance.** `scripts/docs_check.py:636-654` checks the runner log only when `--log` is passed. A hand-edited `go` record can therefore produce “nothing to stop on” with the ordinary `gated` invocation, despite the plan’s send-back requirement. Use the configured or environment log by default, or require a log whenever changed records exist; test the invocation without `--log`.

**Thread 4 — The reviewer prompt omits rule provenance.** `rules_for_lines()` (`scripts/docs_check.py:259-273`) drops each rule’s source and each exception’s approver, approval date, and reference. The runner uses those lines in its prompt, while `scope-review/reviewer_prompt.md:16-21` asks the reviewer to assess a rule’s source and exceptions. Include those fields in the rule listing and assert their presence in the runner prompt test.

#### Non-blocking issues

`scope-review/reviewer_prompt.md:12-14` names Spec Kit and OpenClaw. The plan and runner also name Codex, and the plan names GitHub. These are product names in a public repository; the driver should confirm each reference is intentional. I found no personal or private host name in the requested artifacts.

#### Overall judgment

**Not ready for closeout.** The base-and-HEAD governing chains, ratchet comparisons, change classification, record front matter, empty runner working directory, and outside-repository log path follow the approved plan by inspection. The four findings above leave core checks weaker than the plan requires. The worktree was clean at review time.

#### Residual risks and validation gaps

No tests were run locally, as instructed, and no CI result for this candidate was provided. After the fixes, GitHub CI should run `python -m unittest discover -s tests` on the reviewed commit. Until that candidate-bound result is available, runnable behavior remains **not validated**.

### Driver response 2 (impl)

Accepted all four. Thread 1: the parser now ends a rule's block at any line
that is neither a rule nor an exception, so an exception after a plain bullet
or a blank line has no rule; test added. Thread 2: a `Rules-read:` line needs
text after `applies;` or `n/a;`; test covers `applies` and `n/a;`. Thread 3:
`gated` takes the log from `--log`, else `SCOPE_REVIEW_LOG`, else
`scope_review.log` in the config; when records changed and no log is set it
lists a stop ("nobody checked they came from the runner"); tests cover a
hand-written `go` record without `--log`, then with the env log. Thread 4:
`rules-for` lines (and so the reviewer's prompt) carry each rule's source and
each exception's approver, date, review date and reference; the runner test
asserts the sources. Also: the runner hashes exactly the proposal bytes it
sent. Non-blocking: Spec Kit and OpenClaw are cited on purpose (public
projects the questions come from); Codex is the required default CLI.

### Reviewer pass 2 (impl, codex reviewer)

The approved goal is a project-neutral docs check and scope-review runner that reliably classify changes and identify required decisions.

#### Blocking issues

No remaining blocking implementation issues were found in the four threads.

#### Thread resolutions

1. **Thread 1 — Resolved.** The parser clears the current rule after an unrelated line. The new test places an exception after a plain bullet and expects `tags` to reject it.
2. **Thread 2 — Resolved.** `stated_rules()` requires a semicolon and following text. The new test rejects both `applies` without a semicolon and `n/a;` without an explanation.
3. **Thread 3 — Resolved.** `gated` checks the log from `--log`, the environment, or config, and lists a stop when changed records have no log. The new test covers a hand-written `go` record with no log, an unmatched log, and a matching log.
4. **Thread 4 — Resolved.** The rule listing includes each rule’s source and each exception’s approval details. The runner passes that listing into its prompt; the updated tests check the rule sources in the prompt and the exception details in `rules-for`.

The runner also hashes the proposal bytes read before invoking the reviewer, closing the read-after-review race. The driver confirmed that the public project references and default Codex command are intentional.

#### Overall judgment

The four implementation threads are resolved by inspection of `HEAD~1..HEAD`. **Candidate behavior remains not validated**, so this is not yet ready for closeout.

#### Residual risks and validation gaps

No tests were run locally, as instructed. No GitHub CI result for the reviewed commit was provided. GitHub CI should run `python -m unittest discover -s tests` on this commit; a related failure would reopen readiness. The worktree was clean during review.

# Reviewer model profile refresh

Status: active implementation plan
Branch: `feature/reviewer-model-refresh`, based on `origin/main` at `119b52a`

## Goal and accepted decision

Refresh the explicit normal/hard reviewer profiles for Claude Code, Codex, and
Grok Build. The human accepted this matrix on 2026-09-24:

| Backend | Normal | Hard |
| --- | --- | --- |
| Claude Code | `claude-opus-5-5` / `high` | `claude-fable-5-1` / `xhigh` |
| Codex | `gpt-6-sol` / `high` | `gpt-6-astra` / `xhigh` |
| Grok Build | `grok-4.7` / `medium` | `grok-4.7` / `xhigh` |

The driver continues to select the tier. Normal remains the default and hard
requires a semantic reason. Backend order, same-agent exclusion, fallback,
override behavior, readiness standard, and 1800/3600-second timeouts remain
unchanged. The accepted change is the six model/effort values only.

The `high` normal effort on Claude and Codex is intentional: routine reviews
still need careful logic and edge-case checks, while this setting should use
less time and allowance than the previous `xhigh`. The new normal models carry
the capability refresh; whether the combined profiles preserve review quality
must be judged from representative review use, not inferred from model names.

## Evidence and uncertainty

Official model and effort documentation supports the chosen IDs and levels:

- Anthropic: https://platform.claude.com/docs/en/models/overview and
  https://platform.claude.com/docs/en/build-with-claude/effort
- OpenAI: https://developers.openai.com/api/docs/models/gpt-6-sol and
  https://developers.openai.com/api/docs/models/gpt-6-astra
- xAI: https://docs.x.ai/developers/models and
  https://docs.x.ai/developers/model-capabilities/text/reasoning

Local Grok Build 1.0.40 lists `grok-4.7` as its default and available model.
The installed Codex CLI is 0.155.1; the official Codex changelog says 0.156.1
added Sol to its model picker. This does not establish whether explicit
`-m gpt-6-sol` works on 0.155.1. The installed Claude CLI accepts `high` effort
but its acceptance of `claude-opus-5-5` through this account is also unproven.
The implementation must not claim actual account access to a new model until a
bounded call demonstrates it.

## Implementation

1. Change `REVIEW_MODEL_MATRIX`, its directly used defaults, and the independent
   `RunConfig.grok_model` default in
   `structured-review/scripts/claude_structured_review.py`.
2. Update exact-profile, argv, override-guard, and metadata assertions in
   structured-review tests. Match exact SKILL matrix rows and reject retired
   rows within that table. Change the Codex normal effort override test to use
   a value different from the new `high` default, so it still proves the flag
   takes effect. Retain tests that show selected tier, recommendation, fallback,
   and provider override remain separate.
3. Update the live profile matrix in `structured-review/SKILL.md`, the root
   `README.md` runner summary, and `docs/CURRENT.md` in the same change. The
   SKILL table must state effort by tier; the README's all-`xhigh` sentence must
   change. The plan is already indexed in `docs/agent_plans/README.md`.
   Historical plans stay untouched.

## Validation and review gates

- Plan Review before executable edits, through this checkout's structured-review
  runner with explicit normal tier.
- Focused profile and argv tests must demonstrate all six selected values and
  the normal-tier hard-model guard. Run the full structured-review test suite,
  compile the runner, and check `git diff --check`.
- Before Implementation Review, run bounded real CLI probes against each
  changed profile: Claude normal with `claude -p --model claude-opus-5-5
  --effort high --output-format stream-json --verbose`; Codex normal with
  `codex exec - --json -m gpt-6-sol -c model_reasoning_effort=high`;
  Grok normal and hard with `grok --model grok-4.7 --reasoning-effort medium`
  and `xhigh`, using `--permission-mode plan --no-subagents
  --output-format streaming-messages-json --prompt-file FILE`. Give each a
  short reviewer-shaped prompt, a 120-second process timeout, and a private
  output file outside the git worktree. Also exercise the candidate runner's
  selected profile/argv path with focused tests. For Claude and Grok, inspect
  the provider stream's init/result model field where present, plus successful
  final output. For Codex, inspect the stream or local session metadata for a
  served-model field; if the CLI exposes only the requested model, record that
  limit explicitly and require a successful provider turn with the explicit
  model and effort flags. Commit only a sanitized summary: CLI version, profile
  requested, observed served-model evidence or its absence, outcome, and date.
- If a new model is rejected, the driver owns diagnosis and must not silently
  substitute another accepted matrix value. For a Sol catalog/version failure,
  upgrade the local Codex CLI to 0.156.1 or newer and repeat the probe. For
  account-access or other failures, leave the affected cell `not validated`
  and return to the human for a matrix decision; Implementation Review readiness
  remains blocked unless the human explicitly accepts that scoped limitation.
- Implementation Review through this checkout's runner after the candidate
  passes its change-specific validation; resolve findings. Closeout checks
  current docs, validation provenance (including date), and git state. Inspect
  `README.md` and `docs/CURRENT.md` directly because their exact text is not
  covered by profile tests. Consumer submodule pin updates are a handoff item.
  Merge remains human-owned.

## Implementation record (2026-09-24)

The candidate changes only the six accepted profile values, the independent
Grok `RunConfig` model default, exact profile/argv assertions, and the live
SKILL/README/CURRENT summaries. The selected-tier algorithm, backend ordering,
fallback, override policy, and timeouts are unchanged.

Change-specific evidence on this candidate:

| Profile | CLI version and private probe observation | Outcome |
| --- | --- | --- |
| Claude normal: `claude-opus-5-5` / `high` | Claude Code 2.1.281; `system/init.model` reported `claude-opus-5-5`; final result was successful and returned the exact short reply. | Validated |
| Codex normal: `gpt-6-sol` / `high` | Codex CLI 0.155.1; explicit `-m` and effort flags completed a provider turn and returned the exact short reply. The public JSON stream has no served-model field; the local `turn_context.model` recorded `gpt-6-sol`, which confirms the active request configuration but is not an independent provider echo. | CLI acceptance validated; served model is not independently exposed |
| Grok normal: `grok-4.7` / `medium` | Grok Build 1.0.40; `system/init.model` reported `grok-4.7`; final `end_turn` result was successful and returned the exact short reply. | Validated |
| Grok hard: `grok-4.7` / `xhigh` | Grok Build 1.0.40; `system/init.model` reported `grok-4.7`; final `end_turn` result was successful and returned the exact short reply. | Validated |

Each probe used a 120-second process limit and private temporary output outside
the worktree. All finished in under ten seconds. A timeout would have prompted
a shorter prompt or longer bounded retry; none occurred. These calls prove
profile acceptance and the reported model where exposed, not review quality.
Claude Fable 5.1 / `xhigh` and Codex Astra / `xhigh` are unchanged hard cells;
their current profile resolution is covered by the exact matrix test.

Validation: focused profile/argv tests passed (9 selected tests), the full
structured-review suite passed (119 tests), and a further three affected argv
and matrix tests passed after the final assertion-only edit. The initial full
run exposed a stale recovery test whose supposed effort change had become the
new default; changing that input to `xhigh` restored the fingerprint check.
`py_compile` and `git diff --check` passed. The README and `docs/CURRENT.md`
were inspected directly against the SKILL table and runner constants.

## Review Threads

### Reviewer pass 1 (impl-plan, claude reviewer)

Human concern, restated: the human accepted a refreshed six-cell reviewer profile matrix on 2026-09-24 and wants the runner constants, tests, and protocol docs moved to those values without changing any other reviewer-selection behavior.

What I inspected, and what I verified independently:

- The plan at `docs/agent_plans/2026-09-24_reviewer_model_refresh_plan.md` (65 lines).
- Current runner touchpoints: `structured-review/scripts/claude_structured_review.py:30-35` (model/effort constants), `:57-69` (`REVIEW_MODEL_MATRIX`), `:222-223` (`RunConfig` grok defaults), `:426-458` (profile resolution and hard-only guard), `:897-952` (per-backend argv), `:1285-1298` (resume fingerprint), `:1715-1748` (config build).
- Doc touchpoints: `structured-review/SKILL.md:124-128`, `README.md:126-147`, `docs/CURRENT.md:20-38`, `docs/agent_plans/README.md:21`.
- Tests: `structured-review/tests/test_claude_structured_review.py`, `structured-review/tests/test_grok_selection.py`, `structured-review/tests/test_recovery.py`.
- Branch claim: `origin/main` is `119b52a` and this branch is 1 commit ahead, so the plan header is accurate.
- Baseline suite is green before any edit: `python3 -m pytest structured-review/tests -q` -> 119 passed. Any post-change failure is therefore attributable to this change.
- The plan's Grok evidence holds: the local Grok Build CLI's model list reports `grok-4.7` as default and available, and still lists `grok-4.6` (so `grok-4.6` remains valid as a deliberate override value).
- The plan's Claude effort concern is settled locally: `claude --help` documents `--effort <level>` as `(low, medium, high, xhigh, max)`, so the new normal `high` is an accepted CLI value. Codex already runs `model_reasoning_effort=xhigh`, and Grok's effort values do not change. The open validation question is model access, not effort acceptance.
- I did not verify the Codex changelog claim from this checkout (no network check performed). The installed Codex CLI is `codex-cli 0.155.1`, which matches the plan.
- Paths in the plan are relative, and it contains no secrets or account details.

#### Blocking issues

Thread B1 - pinned normal-tier defaults have no proof rule and no failure decision

Two of the three new normal-tier values are unverified against the installed CLIs and account, and the plan's validation language permits landing them anyway.

- Codex: the plan itself says the changelog attributes Sol to 0.156.1 while 0.155.1 is installed, and that this does not establish whether explicit `-m gpt-6-sol` works. Good that it is flagged.
- Claude: the plan does not flag the same uncertainty for `claude-opus-5-5`. It states only that official documentation supports the chosen IDs. That is evidence about the provider's model list, not about the installed CLI plus this account resolving that ID. `claude --help` on the installed CLI documents aliases `fable`/`opus`/`sonnet` and full names of the form `claude-fable-5`; nothing in this checkout shows `claude-opus-5-5` resolving. This is the highest-impact cell, because Claude is the first backend for every non-Claude driver.
- Why a wrong value does not degrade gracefully: only specific quota strings map to `credit_exhausted` and trigger the next-backend advance (`structured-review/scripts/claude_structured_review.py:975-987`, `:1855-1861`). A rejected model is a generic failure, so the runner stops the run and the driver must diagnose and relaunch manually. Every normal review on that backend would burn an attempt first.
- Why the current validation text is not sufficient: "record any model whose access or CLI support is not validated" is the right posture for an incidental behavior, but these are the pinned defaults for all future normal reviews. Under the readiness standard, an unvalidated item stays `Partial` and the next step stays blocked unless the human explicitly accepts the residual limitation.

To close this thread, the plan should state:

1. Per backend, the bounded command that counts as proof, exercising both the new model and the new profile effort in one shot (a minimal reviewer-shaped call with `--model` / `-m` plus the profile effort value).
2. What evidence shows the model that actually served the call, not the model requested. Metadata and the resume fingerprint record `active_model(config)`, i.e. the request (`:1160`, `:1293`); the served model appears only in the provider stream (for example the Claude/Grok `init` event), which lives in private attempt logs that must not be committed. Say what non-private summary of that observation lands in the repo.
3. The decision rule if a value fails, decided in advance rather than mid-implementation. The matrix is human-accepted, so substituting a value is escalation-shaped. Name the options explicitly: upgrade the Codex CLI to >= 0.156.1 and re-validate, leave that one cell unchanged pending human approval, or land with `not validated` only under recorded human acceptance. Also name the owner.

#### Non-blocking issues

Thread N1 - two touchpoints are not named, and one existing guard cannot catch a stale value

- `structured-review/scripts/claude_structured_review.py:222-223` hardcodes `grok_model = "grok-4.6"` and `grok_effort = "medium"` as `RunConfig` defaults, outside `REVIEW_MODEL_MATRIX`. `build_config` always overrides them (`:1717`, `:1742-1743`), so a stale default would be invisible to the whole suite. Name it in implementation step 1 so it is not left behind.
- `structured-review/tests/test_claude_structured_review.py:664-682` pins model IDs by reading `structured-review/SKILL.md`. It is a documentation pin rather than a profile assertion, so step 2's list ("exact-profile, argv, override-guard, and metadata assertions") does not obviously cover it. The `gpt-5.6-terra` assertion will fail loudly after the doc edit, which is fine; the quieter problem is that `assertIn("claude-opus-5", skill)` stays true for `claude-opus-5-5`, so this guard cannot catch a stale `claude-opus-5` row. Recommend matching the matrix row exactly and adding negative assertions for retired IDs. Scope those negatives to the matrix table rather than the whole file: `grok-4.6` legitimately remains a valid override value, and `claude-opus-5` is a prefix of the new ID.

Thread N2 - an override test becomes degenerate at the new normal values

`structured-review/tests/test_claude_structured_review.py:1271-1286` runs the default (normal) tier with `--codex-effort high` and asserts `model_reasoning_effort=high` appears in argv. Once the codex normal profile effort is `high`, that assertion passes whether or not the override is honored, so it stops testing the override. Step 2 should require override test values that differ from the new profile value (for example `medium` or `max`) and keep the `effort_source` provenance assertions. The hard-tier override test at `:578-601` is unaffected, since hard stays `xhigh`.

Thread N3 - documentation edits include one shape change and two now-false sentences

The plan names the right files but not the claims that break, and one of them is not a token swap:

- `structured-review/SKILL.md:124-128` uses a single shared `Effort` column, `xhigh` for both claude and codex rows. The new matrix makes claude and codex per-tier (`high` normal, `xhigh` hard), so those rows need the per-tier form the grok row already uses.
- `README.md:132-134` says the profiles are "all at `xhigh`", which becomes false, and its prose names ("Claude Opus 5", "Codex GPT-5.6 Terra") need refreshing alongside the IDs.
- `docs/CURRENT.md:29-31` says "Grok uses 4.6 at medium/xhigh" and needs the 4.7 update.
- Only `SKILL.md` is test-pinned. `README.md` and `docs/CURRENT.md` have no guard at all, so their verification is direct inspection; the plan should say that rather than leaving it implied by "run the full suite".
- Factual note: `docs/agent_plans/README.md:21` already indexes this plan at `0a4f52d`, so that part of step 3 is already satisfied.

Thread N4 - record why normal drops from xhigh to high

The refresh lowers claude and codex normal effort from `xhigh` to `high`. That is the path almost every review takes, and it is the only part of this change that alters default review behavior rather than just naming a newer model. The plan's evidence section establishes that these levels exist in provider documentation, but not why normal moves down. One line of rationale (cost, latency, provider default parity, whatever the human's reason was) keeps a later reader from treating it as a typo and reverting it, and gives closeout an accepted tradeoff to cite. This is not a scope challenge; the human accepted the matrix.

#### Overall judgment

Scope discipline is good: the plan explicitly leaves backend order, same-agent exclusion, fallback, override semantics, the recommendation signal table, legacy-auto compatibility, the 1800/3600-second limits, and the readiness standard untouched, and it correctly identifies that the matrix plus SKILL.md, README.md, and docs/CURRENT.md must move in one reviewed change. The six accepted values are stated unambiguously enough that an implementer will not have to guess what to write. Sequencing (plan review, then edits, then candidate-bound validation, then implementation review, then closeout) matches the protocol.

One blocking issue: B1. As written, the plan can reach Implementation Review with pinned defaults whose model access was never demonstrated and with no pre-agreed decision for the failure case, on a code path where a rejected model stops the run instead of falling through. Once the plan records the per-backend bounded proof command, what evidence identifies the served model, and the named failure decision with an owner, this plan is ready for implementation. N1 through N4 are worth folding in while editing, but none of them should hold the gate.

#### Residual risks and validation gaps

- Codex Sol on 0.155.1 stays unresolved until a bounded call is made. Treat a successful exit alone as insufficient; confirm the served model.
- `claude-opus-5-5` acceptance by the installed Claude CLI and this account is unverified in this checkout. Same standard applies.
- Consumer repos that pin this protocol as a submodule with committed skill mounts keep showing the old matrix until their pin and mount are refreshed. Out of scope here, but a closeout handoff item.
- Any interrupted review attempt started before this change cannot resume after it: the resume fingerprint (`structured-review/scripts/claude_structured_review.py:1285-1298`) includes `runner_sha256` as well as model and effort, so any runner edit already invalidates resumption. Finish or abandon in-flight reviews around the merge. No extra plan work needed.
- The pinned matrix is a durable mechanism that will drift again as providers rotate models. `structured-review/SKILL.md` already carries the one-reviewed-change rule, so no new lifecycle rule is needed here, but closeout should record the date the six values were validated so the next rotation knows how stale the evidence is.

### Driver response 1 (Codex)

- B1 accepted. Validation now names four bounded CLI probes, the requested
  model and effort flags, served-model evidence where exposed, private logs,
  sanitized repo evidence, and the decision rule if a profile fails. Codex CLI
  upgrade is the first response to a Sol version failure; a changed model
  requires a new human decision. Claude account access is explicitly open.
- N1 accepted. The implementation list now names `RunConfig.grok_model` and
  exact SKILL matrix-row assertions.
- N2 accepted. The Codex normal effort override test will use a value distinct
  from the new profile default.
- N3 accepted. The plan names the SKILL table shape and the README sentence,
  and requires direct inspection of the unguarded README/CURRENT summaries.
- N4 accepted. The plan records the intended normal-effort tradeoff and treats
  review quality as something to validate on representative use.

Request plan re-review of the updated body and this response before executable
changes.

### Reviewer pass 2 (impl-plan, claude reviewer)

Human concern, restated: the human accepted a refreshed six-cell reviewer profile matrix on 2026-09-24, and this re-review asks only whether Driver response 1 and the updated plan body close pass 1's B1 and N1-N4 well enough to start executable work.

Scope of this pass: re-review of B1 and N1-N4 against the driver's edits only. I did not rerun a full baseline review of the plan.

What I inspected for this pass:

- `git diff d4ae8d9 52f7acd -- docs/agent_plans/2026-09-24_reviewer_model_refresh_plan.md`, i.e. exactly what the driver changed, plus the new Driver response 1 block.
- The touchpoints each thread turns on: `structured-review/scripts/claude_structured_review.py:30-35` (profile constants), `:57-69` (`REVIEW_MODEL_MATRIX`), `:222-223` (`RunConfig` grok defaults), `:452-460` (hard-only model guard), `:895-950` (per-backend argv); `structured-review/tests/test_claude_structured_review.py:286-298`, `:664-682`, `:1245-1254`, `:1271-1286`, `:1400`; `structured-review/tests/test_grok_selection.py:40`, `:113-125`; `structured-review/SKILL.md:124-128`; `README.md:132-134`; `docs/CURRENT.md:29-31`; `docs/agent_plans/README.md:21`.
- Baseline is still green immediately before implementation: `python3 -m pytest structured-review/tests -q` -> 119 passed. Worktree is clean at `52f7acd`.

#### Thread resolutions

Thread B1 - Resolved.

The updated plan now carries all three things the thread asked for, and I checked each against the code rather than accepting the driver's summary:

- Proof commands. The four probes are `claude -p --model claude-opus-5-5 --effort high`, `codex exec - --json -m gpt-6-sol -c model_reasoning_effort=high`, and `grok --model grok-4.7 --reasoning-effort medium` / `xhigh`. Each carries both the new model and the profile effort in one call, and the flag shapes match what the runner actually sends (`claude_argv` uses `--model`/`--effort`, `codex_argv` uses `-m` plus `-c model_reasoning_effort=`, `grok_argv` uses `--model`/`--reasoning-effort` with `--permission-mode plan --no-subagents --output-format streaming-messages-json --prompt-file`). So a probe failure will be about model or effort acceptance, not about a flag the runner never uses.
- Probe set completeness. Comparing the accepted matrix against `:30-35` and `:57-69`, exactly four cells change model or effort in a way the provider must accept: claude normal (`claude-opus-5` -> `claude-opus-5-5`, `xhigh` -> `high`), codex normal (`gpt-5.6-terra` -> `gpt-6-sol`, `xhigh` -> `high`), grok normal model, grok hard model. Claude hard (`claude-fable-5-1`/`xhigh`) and codex hard (`gpt-6-astra`/`xhigh`) are unchanged and already have prior live evidence. The four listed probes therefore cover every newly unproven cell; the plan does not silently skip one.
- Served-model evidence and where it lands. The premise of the thread holds: nothing in the runner reads a served-model field from any provider stream, so metadata and the resume fingerprint record only the request. The plan now says to inspect the provider stream's init/result model field for Claude and Grok, to look for a served-model field in Codex's stream or local session metadata, and to record the absence explicitly if Codex exposes only the requested model, backed by a successful provider turn with the explicit flags. Private output goes outside the worktree; only a sanitized summary (CLI version, profile requested, served-model evidence or its absence, outcome, date) is committed. That satisfies the negative-evidence rule: an unobservable served model is recorded as a named limit rather than treated as confirmation.
- Failure decision and owner. Driver owns diagnosis, no silent substitution of another accepted matrix value, Codex CLI upgrade to >= 0.156.1 is the first response to a Sol catalog/version failure, and anything else leaves the cell `not validated`, returns to the human for a matrix decision, and keeps Implementation Review blocked absent explicit human acceptance. That matches the readiness standard.
- The Claude-side gap pass 1 flagged is now closed in the body: `claude-opus-5-5` acceptance through this account is stated as unproven, and the plan says the implementation must not claim account access before a bounded call demonstrates it.

Thread N1 - Resolved. Step 1 now names `RunConfig.grok_model` explicitly. The narrower phrasing is correct, not an oversight: `:222-223` also hardcodes `grok_effort = "medium"`, but grok normal effort stays `medium`, so that default does not go stale. Step 2 now requires matching exact SKILL matrix rows and rejecting retired rows within that table, which is what the `assertIn("claude-opus-5", skill)` guard at `:664-682` needs, since that substring survives `claude-opus-5-5`. Scoping the negatives to the matrix table is the right call: `grok-4.6` remains a legitimate override value and is still used as one at `test_grok_selection.py:124`.

Thread N2 - Resolved. Step 2 requires the Codex normal effort override test to use a value distinct from the new `high` default, which restores the meaning of `:1271-1286`.

Thread N3 - Resolved. Step 3 now names the two shape-level changes (SKILL table must state effort by tier; the README all-`xhigh` sentence must change), and validation now requires direct inspection of `README.md` and `docs/CURRENT.md` because no test pins them. I re-grepped the repo outside `docs/agent_plans/`: the only live model references are `structured-review/SKILL.md:126-128`, `README.md:132-134`, `docs/CURRENT.md:30`, the runner constants, and the tests. No fourth doc is missing from step 3, and `closeout/SKILL.md` carries no model IDs. The already-indexed claim at `docs/agent_plans/README.md:21` is accurate.

Thread N4 - Resolved. The rationale paragraph records the intended tradeoff (routine reviews still need careful logic, at less time and allowance than `xhigh`) and, better than asked, refuses to infer preserved review quality from model names, leaving that to representative use.

#### Blocking issues

None. There are no blocking issues in this pass.

#### Non-blocking issues

Thread N5 - a probe timeout would be routed to human escalation as if it were a rejection

The probes get a 120-second process timeout, and the decision rule sends "account-access or other failures" to `not validated` plus a human matrix decision. A probe that exceeds 120 seconds is neither: it is a local budget artifact, most plausible on the Grok `xhigh` probe and on any reviewer-shaped prompt at `high`. Suggest one clause separating "the CLI or provider rejected the model or effort" (a real matrix problem, escalate as written) from "the probe exceeded the local time budget" (retry with a longer limit or a shorter prompt before escalating). Optional, and the driver can handle it at implementation time without a plan edit; I mention it because mis-binning a timeout is the one way this otherwise-good decision rule pulls the human in for nothing.

Thread N6 - the sanitized evidence summary has content but no named destination

The plan says exactly what the committed summary must contain but not which file receives it. Closeout is told to check validation provenance including date, so the gap is small, but naming the destination (this plan's body, or the closeout report) removes a guess.

Both of these are minor. Nothing here should hold the gate, and I would not open a further round over them: the plan is already specific enough that an implementer will not have to guess what to write or what counts as proof.

#### Overall judgment

B1 is resolved and N1 through N4 are resolved. The driver's response is accurate about its own edits; I verified each claim against the runner, the tests, and the docs rather than taking the summary at face value, and found no overstatement. The plan now states, in advance, what proves each changed cell, what evidence identifies the served model where the CLI exposes it, what to record when it does not, and who decides what if a value is rejected.

This plan is ready for implementation. The next agent can execute step 1 through step 3 and the validation sequence without guessing.

#### Residual risks and validation gaps

- Codex `gpt-6-sol` on CLI 0.155.1 and `claude-opus-5-5` through this account remain unproven until the bounded probes run. Until then, four of the twelve matrix cells are documentation-backed only. A successful exit alone is not evidence; the served-model check or its explicitly recorded absence is.
- Three test sites will need edits that step 2 covers generically but does not enumerate, and each is a place where a naive edit leaves a vacuous assertion: `test_claude_structured_review.py:1253` (`model_reasoning_effort=xhigh` becomes the wrong default), `:1285` (`assertNotIn("gpt-5.6-terra")` becomes vacuous once the default is `gpt-6-sol`), and `test_grok_selection.py:40`/`:117` (fake-CLI init payload and the both-tiers profile assertion). The green suite after editing does not by itself show these still test what they claim.
- `DEFAULT_EFFORT` and `DEFAULT_CODEX_EFFORT` are each shared across both tiers in `REVIEW_MODEL_MATRIX` today, so the split into per-tier effort is a structural edit, not a value swap. I confirmed both constants are referenced nowhere but the matrix, so the change stays contained and cannot leak into argparse defaults or help text.
- Unchanged from pass 1: consumer submodule pins and committed skill mounts keep showing the old matrix until refreshed (closeout handoff item); in-flight review attempts cannot resume across any runner edit because the fingerprint includes `runner_sha256`; and closeout should record the validation date so the next provider rotation knows how stale this evidence is.

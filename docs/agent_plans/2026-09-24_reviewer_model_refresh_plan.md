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
added Sol to its model picker. This does not establish whether explicit `-m
gpt-6-sol` works on 0.155.1. The implementation should not claim actual
account access to a new model until a bounded call demonstrates it.

## Implementation

1. Change only `REVIEW_MODEL_MATRIX` and its directly used defaults in
   `structured-review/scripts/claude_structured_review.py`.
2. Update exact-profile, argv, override-guard, and metadata assertions in
   structured-review tests. Retain tests that show selected tier, recommendation,
   fallback, and provider override remain separate.
3. Update the live profile matrix in `structured-review/SKILL.md`, the root
   `README.md` runner summary, and `docs/CURRENT.md` in the same change. Add
   this plan to `docs/agent_plans/README.md`. Historical plans stay untouched.

## Validation and review gates

- Plan Review before executable edits, through this checkout's structured-review
  runner with explicit normal tier.
- Focused profile and argv tests must demonstrate all six selected values and
  the normal-tier hard-model guard. Run the full structured-review test suite,
  compile the runner, and check `git diff --check`.
- Before Implementation Review, exercise the reviewable candidate through a
  bounded real call for the new profile routing where possible. At minimum,
  distinguish successful model invocation from local argument construction;
  record any model whose access or CLI support is not validated.
- Implementation Review through this checkout's runner after the candidate
  passes its change-specific validation; resolve findings. Closeout checks
  current docs, validation provenance, and git state. Merge remains human-owned.

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

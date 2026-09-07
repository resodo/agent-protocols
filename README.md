# Agent Protocols

Reusable local protocols for human-agent and multi-agent software work.

Agents should start with `AGENTS.md`. Documentation placement and lifecycle
rules live in `docs/README.md`; the current protocol map lives in
`docs/CURRENT.md`.

## Protocols

- `structured-review/` - structured review for high-level plans, implementation plans, and completed implementation validation.
- `closeout/` - final hygiene checklist before handing off completed work.
- `planning/` - discussion-to-plan workflow before implementation starts.
- `retrospective/` - evidence-based post-incident or post-closeout learning workflow.
- `backlog-maintenance/` - YAML backlog registry maintenance for deferred work, including add/update/close/read operations and CI schema expectations.
- `scout/` - judgment-heavy repository discovery workflow that produces Scout reports and human-reviewed backlog candidate proposals without replacing CI.

## Guidance

- `agent-readiness/` - worktree guard contract and `AGENTS.md` bootstrap template for keeping project coordinates and shared protocol availability explicit.

## Docs

- `docs/agent_plans/` - dated plans, review-thread artifacts, and closeout
  evidence for protocol changes.
- `docs/backlog.yml` - this repo's protocol-development backlog.

Protocol directories should hold executable or reusable protocol material:
`SKILL.md`, `scripts/`, `tests/`, `references/`, and templates. Do not put
dated plans or one-off review artifacts in protocol directories.

## Local Overlays

Protocols are reusable. Project-specific policy belongs in the repo being worked
on, under:

```text
.agent-protocols/context.md
.agent-protocols/<protocol-name>.md
```

When a protocol is loaded inside a repo:

1. Read the generic protocol from this directory.
2. Read `.agent-protocols/context.md` if present.
3. Read `.agent-protocols/<protocol-name>.md` if present.

Overlays are loaded only for the protocol being used. Unknown overlay files are
ignored. A project overlay may be more specific than the generic protocol, but
must not override a generic `SAFETY` rule.

`SAFETY` rules may appear at H2 or H3 depending on a protocol's internal
structure. The heading text is the contract; overlays must not weaken those
rules.

## Canonical Source

The canonical source of these protocols is this repository's `origin/main`.

1. Repos that consume the protocols pin them as an
   `external/agent-protocols` submodule and run a worktree guard that
   fetches from origin before branching, bases feature worktrees on the
   fresh default branch, materializes the pinned submodule, and verifies
   the skill mounts (see `agent-readiness/worktree-guard.md`). When the
   fetch fails, work stops: freshness is checked mechanically, never
   assumed.
2. The protocols surface inside each coding agent through committed skill
   mounts - `.claude/skills/<protocol>` for Claude Code and
   `.agents/skills/<protocol>` for Codex, symlinked into the vendored
   submodule - so a fresh submodule makes the agents load the protocols
   natively at startup. No pointer files, and no copied protocol content.
3. There is no machine-global read path. Outside a vendoring repo, the
   human directs the agent to a checkout explicitly in session.

Do not write machine-specific absolute paths into this repo's docs. The
project-local `.agent-protocols/` overlay directory described above is
unrelated to where the protocols themselves live; it holds per-repo
refinements only.

## Usage

Point an agent at the relevant `SKILL.md` file and provide the requested role, artifact, and type.

Example:

```text
Please read <your agent-protocols checkout>/structured-review/SKILL.md
Role: reviewer
Artifact: docs/some_plan.md
Type: impl-plan
```

For implementation closeout:

```text
Please read <your agent-protocols checkout>/closeout/SKILL.md
Scope: current implementation task
```

For structured-review reviewer passes, use the bundled runner:

```bash
python structured-review/scripts/claude_structured_review.py \
  --worktree /path/to/target-repo \
  --mode write-commit-to-plan \
  --type impl-plan \
  --thread-file docs/some_plan.md \
  --artifact docs/some_plan.md \
  --review-tier normal \
  --focus "Review acceptance, validation, scope, and role boundaries." \
  --topic "some plan"
```

The runner loads the shared skill from this repo and target-repo overlays from
the explicit `--worktree`.

The runner supports Claude Code, Codex, and Grok Build. `--reviewer-backend auto`
tries Claude > Codex > Grok, excluding `--coding-agent NAME`. Missing binaries
and authoritative exhausted-allowance errors advance without human permission.
For Codex with Claude exhausted this selects Grok; for Kimi Code it can select
Codex. Pass the coding identity explicitly, especially for Grok (no pinned
environment marker). Explicit backend pins do not fall back. Diagnose other
failures and try eligible alternatives without asking per-provider permission;
escalate availability only when all three are unavailable or excluded.

Drivers must pass `--review-tier normal` or `--review-tier hard` for new
repo-backed reviews. Hard additionally requires `--tier-reason` with a concrete
semantic rationale. Normal is the default; hard is for roughly the hardest 20%
of the agent's tasks, such as major design/architecture or unusually difficult
bugs. This is judgment, not a numerical quota. Routine protocol edits and
mechanical complexity hints alone do not qualify; use normal when in doubt.
Claude Opus 5 / Fable 5.1 and Codex GPT-5.6 Terra / GPT-6 Astra are the normal /
hard profiles, all at `xhigh`. Grok uses `grok-4.6` for both, with `medium` /
`xhigh` effort respectively.

For legacy callers, omitted tier or `--review-tier auto` emits a deprecation
warning and always selects normal. The runner may recommend hard from review
type, artifact body size, multi-artifact implementation scope, or pinned
complexity signals, but that recommendation never changes selected tier,
model, timeout, scope, or quality gate. Prompt and run metadata record driver
selection/reason separately from runner recommendation/reasons.

Provider-specific model/effort flags remain deliberate overrides for the
selected backend, but normal/auto cannot use them to select that backend's
pinned hard-only profile model; select hard with `--tier-reason` instead. Grok's
shared model is allowed for normal. Do not evade rare-hard guidance with effort
overrides. Grok flags are `--grok-bin`, `--grok-model`, and `--grok-effort`. An
override for the non-selected provider is ignored with a warning.

`--protocol-dir` is optional and mainly for tests or intentional alternate
checkouts; normal usage relies on the script's own `structured-review`
directory.

Review attempts default to 1800 seconds for normal and 3600 seconds for hard,
with explicit `--timeout-sec` overrides. Drivers can queue a reasoned stop via
`--stop-run RUN --stop-reason REASON`, then resume a cleaned incomplete attempt
with `--resume-run RUN` and the same review arguments. Auto resume stays on the
recorded backend/identity, even if a preferred provider becomes available.
Each launch prints its
private attempt directory. Recovery preserves the CLI conversation and rejects
changed targets, concurrent/stale attempts, and repeated write-back. See
`structured-review/references/recovery.md` for lifecycle and limitations.

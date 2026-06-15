# Code Structure Subskill

Use this reference when `code-structure` is enabled in
`.agent-protocols/scout.yml`.

## Purpose

Find active code modules or module clusters whose structure makes safe
agent/human maintenance difficult.

This subskill does not decide whether code is dead, test-only, or
compatibility-only; that belongs to `code-reachability`. It also does not
review visual design, accessibility, or product quality. It asks whether active
code structure makes targeted edits, review, validation, or ownership risky.

`code-structure` uses language/framework adapters inside one subskill because
structure findings share one admission rule across active code surfaces. This
differs intentionally from `code-reachability`, where frontend/TypeScript
reachability remains a separate future extension because static-analysis
false-positive classes are more language-specific.

## Overlay Fields

Required:

- `roots`: mapping with at least one declared adapter. Every declared adapter
  root list must be non-empty. Declare only adapters you actually scan.

Supported v1 adapters:

- `python`
- `typescript_react`

Optional:

- `test_roots`: mapping of adapter names to test roots. Adapter keys must be
  supported v1 adapters; lists may be empty.
- `active_contract_sources`: active docs, manifests, or config sources that
  define code ownership, entrypoints, or product/runtime contracts.
- `thresholds`: scan-hint threshold overrides.
- `repo_notes`: repo-specific interpretation notes.

Default thresholds:

- Python:
  - `review_lines: 800`
  - `large_lines: 1000`
  - `script_review_lines: 600`
- TypeScript/React:
  - `review_lines: 400`
  - `large_lines: 600`
  - `route_large_lines: 600`
- Shared:
  - `churn_since_days: 45`
  - `high_churn_commits: 6`

Thresholds are scan hints, not admission rules. Revisit them when a repo's code
norms change. A module is not a candidate merely because it exceeds a
threshold.

## Evidence Loop

For each candidate-worthy module or coherent module cluster:

1. Confirm it is active code under an overlay-declared root.
2. Collect tracked files under the declared adapter roots.
3. Collect line counts and top offenders.
4. Run language-aware structure scans where feasible.
5. Inspect dependency categories and entrypoint/internal boundaries.
6. Search tests, docs, active contract sources, and backlog for references to
   the module or cluster.
7. Inspect recent git churn for top candidates.
8. Compare candidate-worthy findings with existing backlog items.
9. Record commands and skipped evidence with reasons.

Useful tools are ordinary repo tools such as `git ls-files`, `rg`, `git log`,
language-aware one-off snippets, package-manager commands already available in
the repo, and mature project tools when they are already part of the project
toolchain. Do not require the Scout runner to know project toolchains in v1.

## Python Adapter Evidence

For Python roots, collect evidence such as:

- tracked `.py` files under declared roots;
- line counts and top offenders;
- AST or equivalent scan for top-level functions, classes, methods, public
  symbols, and module-level executable blocks;
- entrypoint hints such as FastAPI decorators, Typer commands, argparse
  parsers, and `if __name__ == "__main__"`;
- dependency-category hints from imports or direct reads, such as DB, HTTP/API,
  filesystem, metrics, provider/LLM, subprocess, and CLI boundaries;
- tests/docs/backlog references;
- recent git churn for top candidates.

## TypeScript/React Adapter Evidence

For TypeScript/React roots, collect evidence such as:

- tracked `.ts` and `.tsx` files under declared roots;
- line counts and top route/component offenders;
- component/function and hook counts where feasible;
- route/page file hints;
- API/data shaping, feature flag, interaction/state, and rendering-policy
  density hints;
- frontend test/e2e/package-script references when present;
- recent git churn for top candidates.

Use project-available tooling when practical, such as TypeScript, ESLint, or
React-aware parsers, but do not make unavailable frontend tooling a blocker for
a Scout run. Record skipped tools with reasons.

## Candidate Unit

One module or one coherent module cluster that needs one structural decision.

Combine observations when:

- several modules form one tangled workflow boundary;
- one route/component cluster shares a single product-surface ownership issue;
- a service and helper module must be split or documented together.

Split observations when:

- modules have different owners or runtime surfaces;
- likely next actions differ;
- one issue is reachability and another is structure.

## Candidate Admission

Propose a candidate only when all are true:

- the module or cluster is active code under declared roots;
- a mechanical signal exists, such as size, dependency breadth, many
  entrypoints, high churn, mixed runtime roles, or test/doc/backlog friction;
- agent inspection proves a concrete maintenance risk;
- there is a clear restructuring next action;
- no existing backlog item semantically covers the same decision.

Concrete risks include:

- unrelated responsibilities in one module;
- small changes requiring broad unrelated context;
- public entrypoint and internal helper boundaries mixed together;
- production, test, debug, and provenance surfaces mixed together;
- hidden domain boundaries;
- consistently broad review scope;
- frontend routes mixing data shaping, state orchestration, rendering, and
  interaction policy too heavily.

Good next actions include split modules, extract a service, move data shaping,
separate entrypoint from implementation, add boundary tests, document ownership,
or create an explicit implementation plan for a coherent refactor.

## Report-Only Or Ignore

Use report-only when a module is large or high-churn but cohesive, or when the
next action is not yet clear.

Use ignored noise when:

- framework-heavy modules are large but have clear registration boundaries;
- generated files, migrations, schemas, or typed data carriers are doing their
  intended job;
- test-only complexity does not obscure production behavior or reusable test
  infrastructure ownership;
- the issue is dead/test-only code better handled by `code-reachability`.

## Evidence Standard

Each candidate proposal should cite:

- module path or cluster;
- adapter evidence gathered;
- mechanical signals used only as candidate-pool evidence;
- active-code evidence;
- tests/docs/backlog reference check;
- recent churn evidence when relevant;
- concrete maintenance risk;
- existing backlog overlap check;
- clear next decision/action.

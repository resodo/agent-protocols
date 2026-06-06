# Backend Python Code Reachability Subskill

Use this reference when `code-reachability` is enabled for backend/Python in
`.agent-protocols/scout.yml`.

## Purpose

Identify backend Python code that appears dead, test-only, compatibility-only,
or misleadingly exported while avoiding raw static-analysis noise.

Slice 1 is backend/Python only. Frontend/TypeScript reachability is a separate
future extension.

## Overlay Fields

Required under `subskills.code-reachability.python`:

- `production_roots`: non-empty list defining semantic production scope.
- `test_roots`: list, allowed to be empty.
- `active_contract_sources`: list, allowed to be empty.
- `dynamic_entrypoint_sources`: list, allowed to be empty.

Optional:

- `known_false_positive_classes`: additional repo-specific false-positive
  classes; shared defaults already include framework and dynamic-entrypoint
  patterns.
- `repo_notes`: repo-specific interpretation notes.

Required when Vulture is used:

- `vulture.roots`: non-empty tool scan paths.
- `vulture.version`: exact Vulture version pin for comparable dry-runs.

Optional Vulture fields:

- `vulture.min_confidence`: default `60`.
- `vulture.ignore_decorators`: list, default empty.
- `vulture.ignore_names`: list, default empty.

`production_roots` and `vulture.roots` are separate. Production roots define
semantic scope; Vulture roots define tool scan scope.

## Tools

Use Vulture only as a noisy candidate-pool generator. Configure it through the
overlay, and let the runner generate a deterministic temporary TOML adapter
when useful.

Always pair static tool output with semantic checks using `rg`, direct file
reads, tests, docs, and config/entrypoint inspection.

Do not introduce obscure or immature reachability tools in v1. If a mature tool
cannot decide the case objectively, Scout should keep the judgment explicit.

## Evidence Loop

For each raw signal:

1. Read the definition context.
2. Search production references.
3. Search test references.
4. Search docs references.
5. Search config and dynamic entrypoint references.
6. Rule out known false-positive classes.
7. For candidate-worthy signals, inspect `git blame` / `git log` on the
   definition and nearby callers, plus related plan text, to understand whether
   the code is planned residue, a regression, a compatibility shim, or old debt.
8. Decide whether the action is clear enough for a candidate.

Raw Vulture output, low reference count, single reference, or test-only
reference is not enough by itself.

## False-Positive Defaults

Ignore or keep report-only unless additional evidence shows a real lifecycle
problem:

- FastAPI route handlers;
- Typer commands;
- Pydantic models and fields;
- SQLAlchemy mapped fields;
- validators and decorated hooks;
- dynamically imported modules;
- Alembic, migration, or runtime entrypoints;
- pytest fixtures/helpers;
- actively documented compatibility shims.

False-positive classes and ignore lists are maintenance surfaces. Review them
when framework wiring changes, a decorator/name no longer exists, or repeated
Scout runs show useful signal is being suppressed.

## Candidate Admission

Propose a candidate only when:

- there is at least one mature static/search signal;
- definition, production refs, test refs, docs refs, and entrypoint refs were
  checked;
- known dynamic/framework usage was ruled out;
- retaining the code has maintenance, misleading-test, public-contract, or
  legacy risk;
- there is a clear next human decision/action.

Only-referenced-by-tests is candidate-worthy only when the definition is under
production roots and no production wiring, dynamic entrypoint, or active
public-contract justification is found. The action should ask whether to remove
the code, wire/document the intended production seam, or convert the logic into
explicit test-only support. Do not simply assert that test-only production code
is dead.

## Report-Only Or Ignore

Use report-only when evidence is incomplete, dynamic use remains plausible,
tool output is noisy but not meaningless, or the next action is unclear.

Use ignored noise for confirmed framework registrations, model fields, mapped
fields, validators, fixtures, migration/runtime entrypoints, and documented
compatibility contracts.

## Evidence Standard

Each candidate proposal should cite:

- definition path and symbol;
- static/tool signal;
- production reference search result;
- test reference search result;
- docs/config/entrypoint search result;
- false-positive classes ruled out;
- history provenance, such as introducing or last-semantic-change commit/plan,
  when available;
- risk and clear next decision/action.

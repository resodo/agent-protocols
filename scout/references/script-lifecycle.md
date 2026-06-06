# Script Lifecycle Subskill

Use this reference when `script-lifecycle` is enabled in `.agent-protocols/scout.yml`.

## Purpose

Find active helper scripts whose lifecycle, ownership, maintenance coverage, or
retirement path is unclear.

Do not assume every repo uses a `scripts/` directory. The overlay declares
script roots and entrypoint sources.

## Overlay Fields

Required:

- `script_roots`: non-empty list of active helper/script roots to inspect.
- `script_entrypoint_sources`: non-empty list of files or directories that
  declare active script entrypoints, such as CI workflows, README commands,
  package manifests, Makefiles, deploy docs, or runbooks.

Optional:

- `known_manual_entrypoints`: scripts known to be manual entrypoints; lack of CI
  usage alone is not suspicious.
- `historical_script_contexts`: paths whose script references are historical or
  provenance context. Defaults to `repo_context.archive_paths`.
- `repo_notes`: repo-specific interpretation notes.

If a more-specific historical path sits under a broader active path, the
historical classification wins.

## Evidence Loop

For each script or coherent script group:

1. Confirm it is under an overlay-declared active script root.
2. Check overlay-declared entrypoint sources.
3. Search active docs and current source-of-truth docs.
4. Separate active references from historical/provenance-only references.
5. Check CI, import smoke, syntax checks, docs, or runbooks for ownership.
6. Look for duplicate, superseded, legacy-service, or obsolete-dependency
   signals.
7. For candidate-worthy scripts, check `git blame` / `git log -- <path>` and
   related plan references to identify when the script was introduced, last
   materially changed, or last used as evidence.
8. Classify the finding.

Useful tools are ordinary repo tools such as `rg`, `find`, shell syntax checks,
package manifest reads, and CI workflow reads. Do not create a new helper script
for one-off inspection unless the logic is repeatable enough to maintain.

## Candidate Unit

One script or one coherent script group that needs one lifecycle decision.

Combine observations when:

- a runner and helper belong to the same workflow or experiment;
- several scripts belong to one incident cleanup or one migration;
- the likely decision is shared, such as archive together, keep together, or
  replace together.

Split observations when:

- scripts have different purposes, owners, or runtime contexts;
- one issue is production/deploy safety and another is historical provenance;
- likely next actions differ.

## Candidate Admission

Propose a candidate only when all are true:

- the script or group is under an active script root;
- lifecycle is unclear, contradictory, weakly maintained, or likely obsolete;
- keeping it has maintenance, safety, provenance, or review-cost risk;
- there is a clear next human decision/action.

Good next actions include archive, delete, keep with ownership, move to
historical provenance, add CI/smoke coverage, or replace with a maintained
workflow.

## Report-Only Or Ignore

Use report-only when evidence is interesting but action is unclear, or when
historical references exist but current placement may still be acceptable.

Use ignored noise when the path is historical/archive/vendor/generated, the
script is a known manual entrypoint, or the reference is intentionally
provenance-only.

## Evidence Standard

Each candidate proposal should cite:

- script path or group;
- active entrypoint evidence or absence;
- active-doc or historical-only references;
- CI/test/import/syntax ownership evidence;
- history provenance, such as introducing or last-active plan/commit, when
  available;
- concrete risk;
- clear next decision/action.

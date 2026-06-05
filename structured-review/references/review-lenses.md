# Structured Review Lenses

Load this reference for every structured-review reviewer pass.

## Validation First

An artifact is not ready if acceptance is vague.

Always check:
- what exactly proves success;
- whether the implementing agent can verify that by itself;
- what artifact, query, command, screenshot, or test will be used;
- what result would falsify the artifact.

For external facts, data, metrics, dashboards, reports, APIs, logs, or database
fields, also check:
- whether the required data actually exists and is usable;
- whether the correct source-of-truth layer is being used;
- whether different representations are being confused.

## Mechanism Lifecycle

When an artifact introduces or materially changes a durable mechanism, review
its maintenance lifecycle, not only whether it works today.

Durable mechanisms include hard-coded lists, allowlists, denylists, path globs,
status/config tables, required-check lists, CI jobs, hooks, scripts, generated
output rules, protocol checklists, caches, archives, retention policies, and
private-output handling.

For plans, require explicit coverage of:
- who maintains the mechanism;
- when it is updated;
- how stale entries, obsolete rules, or temporary exceptions are removed;
- whether human participation is required;
- what signal shows the mechanism is stale or incomplete;
- whether a simpler default rule can replace a manually maintained list.

For implementation reviews, check:
- the implemented mechanism matches the accepted lifecycle contract;
- broad allowlists are not hiding future maintenance work;
- exceptions are narrow and documented with owner/update/removal expectations;
- tests or validation prove both clean and negative cases where practical;
- unresolved lifecycle questions are recorded as residual risk or deferred work.

## Persistent Schema Lifecycle

When an artifact touches persisted schemas, database models, migration plans,
status/state fields, retry/rerun behavior, JSON payload columns, cache
freshness, or source/target database boundaries, check lifecycle semantics, not
only create-time shape.

For plans, require explicit coverage of:
- owner service or writer;
- create path and update path;
- allowed states and state transitions;
- retry, rerun, and idempotency behavior;
- archive, delete, expiry, or retention behavior;
- JSON inner contract vs intentionally opaque raw payload;
- cache freshness, stale behavior, and refresh trigger;
- source database vs target database role boundary;
- validation strategy, including tests or explicit deferral.

For implementation reviews, check:
- code follows the accepted lifecycle contract;
- string statuses and categorical fields have named allowed values or explicit
  deferral;
- contract-bound JSON dicts are typed/validated, or documented as opaque;
- create-only code did not omit required update, rerun, archive, or cleanup;
- migrations match the lifecycle contract when schema changes are in scope;
- tests cover the relevant lifecycle path, or the missing path is explicitly
  deferred with human approval.

## Human-Facing Output

For human-facing outputs, query/API success is not sufficient validation.

Human-facing outputs include dashboards, Grafana panels, reports, daily
summaries, notification bodies, CLI tables, UI screens, rendered docs, and
charts.

Always check:
- who reads it;
- what question the reader is trying to answer;
- what the output looks like under current real data;
- how empty data, missing series, zero values, `NaN`, and low-volume data
  render;
- what artifact proves the rendered output is usable.

For UI implementation review specifically:
- page load is not enough;
- exercise normal, empty/no-match, and recovery/reset states when controls
  exist;
- exercise visible search, filters, navigation, detail pages, and empty-result
  states;
- verify filter options with no matching sample data return intentional empty
  states and reset restores data;
- validate screenshots for desktop and any responsive viewport in scope;
- check long content containment for titles, names, identifiers, URLs, JSON,
  tags, table cells, and multi-line text;
- check information hierarchy and basic accessibility;
- verify data wiring against real or acceptance-grade data unless the artifact
  explicitly limits the scope to a mock prototype.

For high-touch product UI, dashboards, charts, data review tools, and operator
consoles, also apply `structured-review/references/ui-review.md`.

When grouping multiple outputs into one surface, justify the grouping by reader
scenario: who reads it, when they read it, and what question it helps answer.

## Sample Data Before Endorsement

For any artifact item that depends on a field, table, API response field, log
record, metric, or other live data source:
- do not endorse it based only on schema, docs, or naming;
- check sample live data before endorsing the item;
- treat "the field exists" as insufficient evidence that it is usable;
- when both raw and enriched/corrected variants exist, default to enriched or
  corrected unless there is a reason to prefer raw.

## External Resource Source Of Truth

For third-party quota, billing, rate limits, usage budgets, API availability,
external account state, or service-side counters, internal metrics are not
automatically authoritative.

Always check:
- who owns the authoritative number;
- whether an API, dashboard, invoice, admin page, or provider-side response
  exposes that number;
- whether the artifact's metric is authoritative, derived, sampled, or a proxy;
- what conversion factor connects internal events to external units;
- whether that conversion factor is validated or guessed.

If both external truth and internal estimates exist, prefer a reconciliation
design: show external truth, show internal estimate, and show drift only when
both sides cover the same scope.

## Plan To Implementation Traceability

For `Type: impl` reviews, passing tests and healthy production smoke are not
enough.

Compare completed work against the accepted plan, PRD, or acceptance list item
by item:
- mark each in-scope item as `Done`, `Partial`, `Missing`, or `Deferred`;
- require concrete evidence for `Done`;
- treat an empty evidence cell, chat memory, or "looks fine" as insufficient;
- treat planned-but-unimplemented items as `Missing` unless the human explicitly
  defers them;
- call out status docs that imply completion while rows remain missing or
  partial.

If no accepted plan or acceptance list exists, say that directly and create a
minimal traceability list before judging implementation complete.

## Branch And PR Hygiene

When the artifact closes a branch, worktree, feature, or PR, check the process
gate as part of the review.

Always verify or ask for:
- branch/worktree status and unrelated dirty files;
- PR or merge path, if the repo requires one;
- required CI/check status and exact check names;
- review-thread status, including unresolved blocking threads;
- validation provenance: CI-backed, reviewer-rerun, driver-reported, or human
  acceptance;
- deferred work owner and backlog/plan link.

Do not treat a pushed commit as equivalent to branch closeout when the repo
requires PR, CI, review, or human acceptance.

## Polling Safety

For artifacts that periodically call an external API or service, check polling
safety before accepting the interval.

The artifact should define:
- polling interval;
- whether the endpoint costs money, quota, credits, tokens, or rate-limit
  budget;
- documented or observed rate limits;
- whether multiple processes could poll redundantly;
- backoff or disable behavior after failures;
- whether a controlled live check proved the polling call is safe.

If cost or rate-limit behavior is unknown, treat the endpoint as expensive until
proven otherwise.

## Time-Series Semantics

For Prometheus, Grafana, or other time-series systems, check metric type and
query semantics.

Always check:
- counters are used for monotonically increasing event counts;
- gauges are used for current snapshots;
- `rate()` / `increase()` are only used on counters or values with explicit
  reset/decrease handling;
- snapshot gauges are not treated as consumption counters without a computed
  monotonic delta;
- low-volume business events use human-scale units such as per-hour or per-day;
- missing series and zero events are handled intentionally.

If an artifact derives consumption from periodic snapshots, it must define reset
handling.

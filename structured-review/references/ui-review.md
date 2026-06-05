# Structured Review UI Reference

Use this reference with `SKILL.md` for high-touch product UI, dashboards,
charts, data review tools, and operator consoles.

The goal is not aesthetic nitpicking. The goal is to catch visual and semantic
failures that make human review, debugging, or product use unreliable.

## Visual State Matrix

The reviewer must do a visual state-matrix review. This is stricter than
checking that screenshots exist.

The matrix should cover every UI state that the artifact claims or that the
human explicitly discussed. Common states include:

- compact and expanded chart states
- filter panel open and collapsed states
- show-more and show-less states
- hover and click states for markers, rows, clusters, chips, and inspectors
- enabled and disabled toggles
- selected and unselected segmented controls
- empty, sparse, normal, and dense data states where sample data allows
- desktop and narrow/responsive viewport states

This list is illustrative. The matrix is whatever states the artifact actually
claims or the human discussed; expand it per artifact. Common additions include
loading, error, focus, validation-error, and transient feedback states.

## Visible Defect Checklist

For each reviewed state, inspect the rendered page or full-size screenshot and
actively look for visible defects:

- text overlapping borders, axes, grid lines, controls, chips, or other text
- clipped labels, out-of-container text, unintended horizontal scroll, or hidden
  important content
- inconsistent alignment between states, such as a chart plot area changing
  width when only height should change
- axis, legend, lane, marker, or timeline misalignment
- controls that are too visually heavy for their job, or labels that occupy more
  space than the information they provide
- ambiguous status copy, especially copy that blames "no data" when the user
  merely disabled a layer
- density failures where the primary reader surface has too little usable space
  after headers, controls, charts, or sidebars consume the viewport

Do not mark visual acceptance as complete if the screenshot itself visibly shows
one of these defects. If a defect is accepted as a tradeoff, the artifact must
name it as a known compromise or backlog item rather than treating it as passed.

## Screenshot Evidence

Screenshot evidence must prove the exact claim being made.

A screenshot is weak evidence when it:

- does not show the relevant state
- does not include the affected rows or controls
- is too cropped to confirm the behavior
- shows only the marker/control but not the corresponding affected content
- predates later UI revisions without being explicitly marked historical

When iterating implementation across multiple review rounds, retire or
explicitly annotate superseded screenshots in the report body so the screenshot
list points only at current evidence. Do not silently leave stale screenshots in
place; readers cannot distinguish current from historical without explicit
labels.

## Acceptance Criteria

Do not relax a load-bearing acceptance criterion solely inside the
implementation report.

If a measurable threshold shifts, such as a stated count, viewport size, density
requirement, latency target, or coverage requirement, amend the plan via an
explicit review thread before treating the implementation as compliant.

A known-compromise note may record a defect or tradeoff, but it must not silently
rewrite previously agreed acceptance.

## Design References

When design-tool output or a visual prototype is used:

- compare against the prototype for the agreed layout direction and interaction
  intent, not merely color or surface styling
- do not let the prototype silently delete a previously accepted product
  concept; call out missing concepts such as markers, filters, drilldowns,
  status badges, or trace links
- if the implementation intentionally diverges from the prototype, require a
  short reason in the artifact

## Cross-Surface Consistency

When the same concept appears across multiple surfaces, review semantic and
visual consistency:

- filters with the same names should have the same meaning unless the artifact
  explicitly scopes them differently
- chips, badges, severity labels, direction labels, bucket labels, and fact-tag
  labels should use the same product language across related pages
- the same state should not be called `review`, `needs_review`, `LLM uncertain`,
  and `attention` in different places unless those are intentionally different
  layers and the artifact explains the distinction
- if the UI exposes both a summary surface and a detail/trace surface, verify
  that summary labels can be understood from the detail data and that the detail
  page can explain the summary

Minor wording differences are acceptable. Flag only when the difference changes
filter semantics, user understanding of state, or the operator's mental model,
not surface-level copy preference.

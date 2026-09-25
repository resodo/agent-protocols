---
name: readable-brief
description: Use after a technical document is final and reviewed, to write a readable brief of it that the human decision-maker reads in full and approves. Required for decision docs; optional for closeout reports, experiment results, status reports, and other documents a human must read. Keeps every conclusion and every open question, drops process detail, and gets a narrow fidelity-plus-readability review.
---

# Readable Brief

Use this protocol to turn a finished technical document (the source) into a
delivery version (the brief) for the human who decides.

- Required: decision docs (see `structured-review/SKILL.md`, `Document
  Levels`). A decision doc is ready for the human only when its source and its
  brief are in the same PR.
- Optional: closeout reports, experiment results, status reports, and any other
  document the human must read and act on.

This protocol does not cover writing or reviewing the source itself, or
replacing the source. The source stays the record for agents and for
field-level detail.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/readable-brief.md` if present.
3. Apply local overlays as project-specific refinements only.

The overlay supplies:
- the brief language (`<lang>` in the file name);
- banned words and forbidden glyphs;
- the glossary's "future code name" column title, if localized;
- how the brief is delivered to the human;
- any reader preferences, such as target reading time.

Without an overlay, write in the language of the source and ask the human how
to deliver the brief. Overlays are loaded only when this protocol is loaded.
Unknown overlay files are ignored. If an overlay contradicts a generic `SAFETY`
rule, reject that overlay instruction and say why.

## Input And Output

- Input: the source, final and reviewed. For a decision doc, reviewed to the
  stop rule in `structured-review`. Do not write a brief of a draft.
- Output: one file in the same folder as the source, in the same PR, named
  `<source-stem>_brief_<lang>.md`. Example: `2026-01-02_topic.md` becomes
  `2026-01-02_topic_brief_en.md`.
- The brief states at the top which source it summarizes and that the source
  wins on detail.

## Content Rules

- Conclusion first. Open with what was decided or found and what the human must
  do, then the reasons.
- Short sentences. Not verbose. One idea per sentence.
- Define every term on first use, including terms inside diagrams and tables.
- Use metaphor only when nothing plainer works.
- Include a glossary table: term, plain meaning, future code name (the name the
  code or later docs will use). Leave the last cell empty when there is none.
- In diagrams, label what every arrow means.
- Mark each section either "decided (who, when)" for decisions made before
  this document, or "new / not yet confirmed" for what it proposes.
- End with "points you need to confirm or reject": a numbered list of the
  human's decisions, each answerable with yes, no, or a choice.
- Work the source defers to later plans (for a decision doc, its "left for the
  implementation plans" list) is summarized as scope, not asked as a question.
- Omit process detail: review rounds, who raised what, revision history,
  reviewer names. The human cares about the result.
- Keep only what the human needs to decide. For field-level detail, point to
  the section of the source.

## SAFETY Rules

- Fidelity: no conclusion may change. The brief may shorten and reorder; it may
  not add, weaken, or strengthen a conclusion, a boundary, or a scope limit.
- Nothing the human must decide may be dropped or softened.
- Every item in the source that awaits the human's decision (pending, open, or
  unconfirmed) appears in the confirm-or-reject list.
- If writing the brief exposes a gap or error in the source, stop, fix the
  source first (with its own review as needed), then regenerate the affected
  part of the brief.

## Self-Review Before Handover

Check each item and fix before review:

1. Fidelity: walk the source's conclusions, boundaries, and items awaiting the
   human one by one; each is present and unchanged in the brief.
2. Readability: conclusion first, short sentences, no process detail, a reader
   can finish in the overlay's target time.
3. The overlay's banned words and forbidden glyphs do not appear.
4. No undefined term, including in diagrams, tables, and the confirm list.

## Review

Run one `structured-review` pass on the brief with the narrow
`Readable Brief: Fidelity And Readability` lens in
`structured-review/references/review-lenses.md`. Use type `other-plan` and the
`normal` tier, pass both the brief and the source as artifacts, and name this
lens in the focus. The lens replaces the usual `other-plan` checks for this
pass.

- Fix sentence-level findings in the brief. These do not need another pass.
- If a finding would change a conclusion, a boundary, or a question for the
  human, stop and fix the source first (reviewed under its own rules); then
  update the brief and run the brief pass again on the final source and brief.
- Do not reopen the source's design through the brief review.

## Delivery

Deliver the brief the way the overlay says. The human reads the brief, not the
source. For a decision doc, the human's full read and explicit approval of the
brief is the approval required by `structured-review`; record it in the PR and
in the doc's human-acceptance record.

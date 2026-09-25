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
- any reader preferences, such as an approximate target reading time.

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
- End the body with "points you need to confirm or reject": a numbered list of
  the human's decisions, each answerable with yes, no, or a choice. Order it in
  two tiers:
  - Core questions first: real choices where the answer changes what gets built
    or a boundary. Each opens with 2-3 lines of background (the current state
    and why it is being asked, readable without earlier documents), then its
    options, then the recommendation.
  - Then "confirm in passing": points whose recommendation should be
    uncontroversial (a scope confirmation, "we will not build X", a window to
    re-confirm later), grouped so one answer accepts them all while any single
    one can still be rejected.
  Conclusions the body already states are confirmed by the human's one
  whole-text approval, not split into separate choice questions. Tiering only
  orders the list; the full-read approval rule is unchanged.
- Work the source defers to later plans (for a decision doc, its "left for the
  implementation plans" list) is summarized as scope, not asked as a question.
- Omit process detail: review rounds, who raised what, revision history,
  reviewer names. The human cares about the result.
- Keep only what the human needs to decide. For field-level detail, point to
  the section of the source.
- No bare reference IDs as explanation. When the brief refers to an earlier
  decision, section, question, or item, state its content in one plain sentence
  (what was decided, and when and by whom if relevant); an ID may appear only
  as a parenthetical source after that sentence.
- Every remaining reference is a clickable link: repository file links pinned
  to the default branch with line anchors, or PR and issue links. Gather them
  in a short "sources" appendix after the confirm list so the body stays
  clean. Check that each anchor points at the intended text.
- Use code identifiers only when necessary, and gloss each in plain language at
  first use.
- Reading time is a target, not a limit. Completeness of conclusions,
  boundaries, and points to confirm wins over length.

## SAFETY Rules

- Fidelity: no conclusion may change. The brief may shorten and reorder; it may
  not add, weaken, or strengthen a conclusion, a boundary, or a scope limit.
- Nothing the human must decide may be dropped or softened.
- Every question the source leaves for the human (pending or open) appears in
  the confirm-or-reject list, and no real choice is placed in "confirm in
  passing". Proposed conclusions the body states are covered by the whole-text
  approval, not listed as separate questions.
- If writing the brief exposes a gap or error in the source, stop, fix the
  source first (with its own review as needed), then regenerate the affected
  part of the brief.

## Self-Review Before Handover

Check each item and fix before review:

1. Fidelity: walk the source's conclusions, boundaries, and items awaiting the
   human one by one; each is present and unchanged in the brief.
2. Readability: conclusion first, short sentences, no process detail, reading
   time near the overlay's target.
3. The overlay's banned words and forbidden glyphs do not appear.
4. No undefined term, including in diagrams, tables, and the confirm list.
5. No bare-ID explanation; every reference is a working link with the intended
   anchor; each core question opens with its background.

## Review

Run one `structured-review` pass on the brief with the narrow
`Readable Brief: Fidelity And Readability` lens in
`structured-review/references/review-lenses.md`. Use type `other-plan` and the
`normal` tier, pass both the brief and the source as artifacts, and name this
lens in the focus. The lens replaces the usual `other-plan` checks for this
pass.

- If the brief misstates or is hard to read but the source is right, fix the
  brief. These fixes do not need another pass; record them in the review record
  (for example the output MANIFEST's review table) as a "brief-only fix, no
  re-review" row.
- If a finding shows the source itself must change (a conclusion, boundary, or
  question for the human is wrong or missing there), stop and fix the source
  first, reviewed under its own rules; then update the brief and run the brief
  pass again on the final source and brief.
- Do not reopen the source's design through the brief review.

## Delivery

Deliver the brief the way the overlay says. The human reads the brief, not the
source. For a decision doc, the human's full read and explicit approval of the
brief is the approval required by `structured-review`; record it in the PR and
in the doc's human-acceptance record. Only the session that received the
approval directly records it (see `SAFETY Rules` in `structured-review`).

The human may annotate the brief file directly. Commit the annotations verbatim
first, as the record (commit authorization as in `structured-review`'s
`references/collaboration.md`). Then revise the source and the brief (the source under its
own review rules, the brief under `Review` above) and hand the brief back.
Answers given before a full read, in annotations or in chat, are recorded but
are not approval (see `Document Levels` in `structured-review`).

---
name: visual-qa
description: "[QA agent] Preloaded by a non-author agent that audits a user-visible change before the human sees it. Use whenever screenshots of a visible change are about to go to the human: element-by-element review against a published interface guideline, the author fixes, then screenshots go out."
---

# Visual QA

Functional correctness is not enough for anything the human will look at. A
non-author agent reviews it first; the author fixes; only then do screenshots
go to the human (gate G6 still applies: the human approves visible changes).

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/visual-qa.md`: viewports, browsers, theme, test
   accounts, how to start the app, which guideline skill to load.

## Inputs

The author's screenshots and their caption (what the screenshots are supposed
to show). Not the author's self-assessment.

## Review

Load the guideline named in the overlay (for example a web interface
guideline skill) and go element by element:

- grid and column alignment; consistent sizes, padding and color meaning of
  chips and badges; weight hierarchy; consistent number, date and duration
  formats; spacing rhythm;
- every state the caption claims is actually visible in a screenshot;
- the caption and the images match exactly;
- behavior, not only looks: try the interaction the change adds;
- the widest and the narrowest required viewport.

## Output

A list: each finding with the screenshot, the element, what is wrong, and the
expected state. "No findings" only after every item above was checked. The
author fixes and reshoots; QA rechecks the fixed items.

## SAFETY Rules

- The QA agent never fixes the author's code.
- Never send screenshots to the human before this review passes.
- Never open windows or pages on the human's own machine.

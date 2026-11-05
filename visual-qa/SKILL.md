---
name: visual-qa
description: "[QA agent] Preloaded by a non-author agent that audits a user-visible change before the human sees it. Use whenever screenshots of a visible change are about to go to the human: headless screenshots, element-by-element review against the bundled Vercel Web Interface Guidelines, a pass/fail report with a verdict, the author fixes, then screenshots go out."
---

# Visual QA

Functional correctness is not enough for anything the human will look at. A
non-author agent reviews it first; the author fixes; only then do screenshots
go to the human (gate G6 still applies: the human approves visible changes).
This covers backend changes too when they alter what a page shows.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/visual-qa.md` if present. It holds only project
   specifics: how to start the app, fixtures and harnesses, check accounts
   (by key name), themes, key pages, extra viewports, and any extra guideline
   on top of the default one.

## Inputs

The PR, the author's screenshots and their caption (what the screenshots are
supposed to show). Not the author's self-assessment.

## Standard

The default guideline ships with this protocol: the Vercel Web Interface
Guidelines in `references/web-interface-guidelines/` (`rules.md` for the
MUST / SHOULD / NEVER list, `guidelines.md` for the reasons; source and
version in `SOURCE.md`). Read it before every review; an overlay may add a
guideline, never drop this one. Where the two files disagree, `rules.md`
wins; their upstream install and integration sections are not steps of this
protocol.

Check every place the change touches:

- in Chromium and WebKit, at 1440 and 390 wide, an ultra-wide check (2880
  wide, or 1440 at 50% zoom), and any viewport the overlay adds;
- in every language the site offers (for example EN and ZH), and every theme
  the overlay lists;
- element by element: grid and column alignment; consistent sizes, padding
  and color meaning of chips and badges; weight hierarchy; consistent number,
  date and duration formats; spacing rhythm; text that overflows, clips or
  overlaps;
- every state the caption claims is visible in a screenshot, and the caption
  and the images match exactly;
- behavior, not only looks: try the interaction the change adds.

A MUST or NEVER rule broken, or a visible defect, blocks. SHOULD items and
taste notes do not block; list them separately.

## Running The App

Headless browsers only (for example Playwright with `headless: true`). Start
the app bound to `127.0.0.1` on a fixed port, for example
`vite --host 127.0.0.1 --port 5190 --strictPort`. Never run a command that
opens a browser window, such as a preview script that passes `--open`; run the
underlying server command without it.

Save screenshots in your own scratchpad as
`<browser>-<width>-<place>-<lang>.png`, for example
`webkit-390-company-overview-zh.png`.

## Output

```text
Guideline: Vercel Web Interface Guidelines, references/web-interface-guidelines (commit 434b7f9), read 2026-11-05
Checked: chromium + webkit, 1440 + 390 + 2880, EN + ZH

1. pass  Overview header alignment   /abs/path/chromium-1440-overview-en.png
2. fail  Overview "Updated" chip      /abs/path/webkit-390-overview-zh.png
         Element: date chip in the header row
         Wrong:   wraps to two lines and overlaps the price
         Expected: one line, truncated, price unmoved

Non-blocking:
- SHOULD: loading text "Loading..." should end with an ellipsis character

Verdict: fail
```

- The report opens with the guideline, its source and the date it was read;
  a report without it does not count.
- Each item: pass or fail, with the absolute path of its screenshot; each
  failure names the element, what is wrong, and the expected state.
- The verdict is `pass` or `fail` for visual QA only; it is not merge
  approval and does not replace closeout. Send it to whoever dispatched the
  QA, and also to the merge-queue agent when the brief names one.
- After the author fixes and reshoots, a recheck covers the fixed items and
  the states the fix could affect (shared styles, layout); replace or mark
  superseded screenshots.

## SAFETY Rules

- The QA agent never changes the author's code and never pushes to the
  author's branch.
- Never send screenshots to the human before this review passes.
- Never open windows, browsers or pages on the human's own machine.

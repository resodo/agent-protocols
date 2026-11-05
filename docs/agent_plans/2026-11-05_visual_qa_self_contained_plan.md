# Plan: a self-contained visual QA protocol

Document level: plan (one small PR).

Source: resodo, 2026-11-05 (relayed by the master), approved making the
visual QA protocol self-contained so any agent on any machine can use it.
Before this change `visual-qa/SKILL.md` said to "load the guideline named in
the overlay", and the named guideline (a web-design-guidelines skill) existed
only in one machine's user-level skills directory. Several generic practices
(headless only, no `--open`, default viewports and browsers, languages,
screenshot naming, report format, verdict routing, no pushes to the author's
branch, backend changes with visible output) lived only in dispatch briefs.

## Scope

- `visual-qa/references/web-interface-guidelines/` (new): verbatim copies of
  the Vercel Web Interface Guidelines from
  `vercel-labs/web-interface-guidelines` at commit `434b7f9`
  (`README.md` as `guidelines.md`, `AGENTS.md` as `rules.md`), the upstream
  MIT `LICENSE`, and `SOURCE.md` (source URL, commit, date, refresh steps).
  The upstream license is MIT, which allows redistribution with the notice.
- `visual-qa/SKILL.md`: the process plus the generic practices above; the
  vendored guideline is the default; overlays carry only project specifics.
- `agents/visual-qa.md`: the role also stops at pushing to the author's
  branch.
- `README.md` and `docs/CURRENT.md`: mention the bundled guideline.

Not in scope: consumer overlays and submodule bumps (separate consumer PRs,
per AGENTS.md "Rollout To Consumers").

## Verification

- `python -m unittest discover -s tests` (skill frontmatter) and the CI job.
- The vendored files are byte-identical to the upstream files at the pinned
  commit (`curl` the three raw files at that SHA and `cmp`).

## Review Threads

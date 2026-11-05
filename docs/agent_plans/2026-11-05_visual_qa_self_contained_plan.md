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

### Reviewer pass 1 (impl, codex reviewer)

The requested outcome is a visual QA protocol that an agent can use from the checkout, with project specifics left to overlays.

#### Blocking issues

1. **The vendored guide still directs agents to install another skill.** `visual-qa/references/web-interface-guidelines/guidelines.md:178-189` contains an installation command, while `visual-qa/SKILL.md:28-32` tells agents to read that file before every review. Keep the upstream copy verbatim, but state in `visual-qa/SKILL.md` that its upstream integration instructions are not steps in this protocol. Also make `rules.md` authoritative where the two vendored files disagree: `guidelines.md:11` offers `maximum-scale=1`, which `rules.md:16` forbids.

2. **The QA verdict claims merge readiness.** `visual-qa/SKILL.md:85-86` prescribes `ready to merge` and direct delivery to a merge agent. Visual QA owns a findings report; closeout owns merge readiness, and `agents/visual-qa.md:8-10` routes the agent through its dispatcher. Use a visual QA pass/fail verdict and report it to the dispatcher for onward routing.

3. **The prescribed recheck can miss regressions.** `visual-qa/SKILL.md:87` limits rechecks to fixed items. A shared CSS or layout fix can change previously passing states, and `structured-review/references/ui-review.md` requires current screenshot evidence. Recheck the fixed items **and any states affected by the fix**, and replace or mark superseded screenshots.

4. **The default viewport list omits a bundled MUST.** `visual-qa/SKILL.md:36-37` names 1440 and 390 pixels plus overlay additions; `visual-qa/references/web-interface-guidelines/rules.md:85` also requires an ultra-wide check. Include that check in the default standard or clarify that the listed widths are a minimum and the bundled MUST also applies.

5. **The pinned-copy acceptance check has no recorded result.** The plan requires a byte comparison of all three vendored files with the pinned upstream commit. The files and MIT notice are present, and the [pinned upstream license](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/434b7f91364665f2f733b310ec54809bf8f37937/LICENSE) supports the attribution, but no comparison result appears in the reviewed artifacts. Network access prevented an independent `cmp` in this review environment. The driver should record the three comparison results before marking vendoring complete.

#### Non-blocking issues

None.

#### Overall judgment

**Partial; not ready for closeout.** Direct inspection supports the role-file and index updates. The protocol and vendoring items remain partial for the reasons above.

#### Residual risks or validation gaps

The plan lists a unit-test command and CI job, but the reviewed artifacts contain no results. The driver should record their provenance during closeout. No files were changed during this review.

### Driver response to pass 1

1. Fixed: `SKILL.md` says `rules.md` wins where the two files disagree and
   that the upstream install and integration sections are not protocol
   steps. The vendored files stay verbatim.
2. Fixed: the verdict is visual-QA `pass` / `fail`, stated as not merge
   approval and not a closeout replacement; it goes to the dispatcher and to
   the merge-queue agent only when the brief names one (the human asked for
   the verdict to reach the merge queue). `agents/visual-qa.md` says the same.
3. Fixed: a recheck covers the fixed items and the states the fix could
   affect, and superseded screenshots are replaced or marked.
4. Fixed: the default standard adds an ultra-wide check (2880 wide, or 1440
   at 50% zoom), matching the bundled MUST.
5. Recorded: on 2026-11-05 the driver downloaded `README.md`, `AGENTS.md` and
   `LICENSE` from `raw.githubusercontent.com` at commit `434b7f9` and ran
   `cmp` against `guidelines.md`, `rules.md` and `LICENSE`: all three
   identical. `python -m unittest discover -s tests` (with PyYAML): OK;
   `python scripts/check_backlog.py`: OK.

### Reviewer pass 2 (impl, codex reviewer)

The requested outcome is a visual QA protocol that agents can use from this checkout without a machine-specific guideline skill.

#### Blocking issues

None. The driver’s changes resolve all five blocking issues from pass 1:

1. **Resolved.** `visual-qa/SKILL.md` makes `rules.md` authoritative where the vendored files disagree and excludes upstream installation instructions from this protocol.
2. **Resolved.** The verdict is now visual QA `pass` or `fail`, explicitly separate from merge approval and closeout. Routing to a named merge-queue agent matches the driver’s recorded human direction.
3. **Resolved.** Rechecks cover fixed items and other states the fix could affect; superseded screenshots are replaced or marked.
4. **Resolved.** The default checks now include ultra-wide coverage, consistent with the bundled MUST.
5. **Resolved on driver-reported evidence.** The driver records successful byte comparisons for all three vendored files against the pinned commit.

#### Non-blocking issues

None.

#### Overall judgment

**Ready for closeout.** The worktree is clean. The four requested artifacts are consistent with the plan and the pass 1 resolutions.

#### Residual risks or validation gaps

The upstream comparisons and local test results are driver-reported; I did not rerun them. CI status remains for closeout to verify.

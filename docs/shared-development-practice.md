# Shared Development Practice

Status: active
Agreed: 2026-11-10 (resodo; decisions in the last section)
Applies to: skynet-intern, skynet-thesis-room, skynet-analyst-plugins, and the
other repos either team works in

This is one document for both teams. Each repo's `AGENTS.md` (or, where a repo
has none, its collaboration page) points here in one line. Whoever finds a
better practice changes this file in a PR; the repo-level rules that implement
a point stay in that repo and are cited here.

## Who this is for

- **Infra team:** resodo, plus the Claude master session and the agents it
  dispatches. Works mainly in skynet-intern, skynet-ingest, skynet-twitter,
  skynet-agent-kit and agent-protocols.
- **Product team:** FD (product owner, GitHub `Fredi111-bot`) and atticcas
  (technical changes), working mainly in skynet-thesis-room and
  skynet-analyst-plugins with Codex agents.

The two teams grew separate habits. Some already match, some conflict, and in
some places one side is clearly better. This document is organised by
situation. Each situation has four parts:

- **Now:** what each side does today, with the source (file or PR number).
- **Practice:** what both sides do from now on.
- **Why:** at least one real example from our history, with dates and numbers
  where possible.
- **Cost:** what the practice costs.

The whole document comes down to three sentences: **before adding anything,
ask whether it can be deleted; put a change in the layer that owns it; for a
user-visible change, "done" means the right result seen on the production
page.** The 14 situations below are those three sentences applied.

---

## 1. Over-engineering (the most important, so first)

**Now**

- Infra: agent-protocols `structured-review/SKILL.md` asks reviewers to
  "point out what can be deleted before what can be added". A reviewer who
  proposes a new mechanism must also give the no-mechanism option (delete it,
  change one sentence, record a known limitation) and compare costs. Before
  accepting any blocking finding, the author writes one line on whether it can
  be solved by deleting something, changing one sentence or recording a known
  limitation. Intern `AGENTS.md` (decision boundary): a new standing mechanism
  (alert, counter, registry, config field, guard, approval step) needs the
  human first.
- Product: thesis-room `AGENTS.md` item 1 says our merge review "covers code
  size, simplification and reuse of existing patterns"; the product team's own
  pre-merge review tool is free choice. Codex is not explicitly told to ask
  "can this be deleted?" first.
- Honestly, both sides have over-engineered, and the infra team more often.

**Practice**

1. The first question in design and review is "can this be deleted?". When
   fixing a gap, prefer the fix that removes something over the fix that adds
   a layer.
2. No "might be useful later" mechanism that nobody asked for and nobody
   discussed. To add one, name the real incident it prevents (date, numbers);
   if you cannot, delete it.
3. Length caps, count caps, caches, thresholds and gates: measure first. Only
   record data at first; add the limit when a real problem shows up, sized by
   that data.
4. Reviews ask once "is there anything that can be deleted or simplified?". If
   not, say so; nobody has to find something to delete. A PR that deletes
   something says in one line what it deleted.
5. A temporary switch (a config value or flag that exists only for a
   transition) names an owner and a delete-by date where it is defined.
   Borrowed from Thesis feature flags (situation 6).
6. When an existing mechanism starts getting in the way (false blocks, stuck
   work), look back: why it was added, how many times it blocked correctly,
   how many times wrongly, what it cost. Then keep, simplify or delete it. No
   standing statistics job for this.

**Why**

- 2026-09-16: a paid run that had been going for 38 minutes was killed by a
  log-count cap we had added ourselves. resodo's conclusion: "an observation
  tool must not be able to kill what it observes". Raising the cap from 20 to
  50 would only have postponed the same mistake.
- 2026-09-26: governance data had to be frozen during an evaluation. Agents
  built a whole freeze-and-verify mechanism that dragged on ("building this
  mechanism took forever"). The final answer was a convention: only one agent
  writes governance data, and the existing `curator_enabled` switch turns
  Curator off. No new code.
- 2026-10-01: a proposal to check a dictionary before Curator research, to
  save some research. Rejected: ambiguous words would be missed, and the big
  scope cut just made had not been measured yet. Run a round, measure the
  remaining waste, then propose a mechanism with data.
- 2026-10-26: Thesis #300 added a "skip unknown companies" protection layer in
  case some feature had to be rolled back later. resodo judged it an excess
  mechanism: fix forward when something breaks; do not pre-build protection
  for a hypothetical rollback.
- 2026-10-28: weekly themes were to mark citations "unchanged / updated /
  withdrawn" and fetch the version as of that time. resodo: "this mechanism is
  a bit redundant." Citations now keep only the id and read the latest
  content.
- 2026-11-02: in the analyst's first scheduled run, half the turns went into
  "shortening", because the instructions set a length threshold in advance.
  Deleted; add it back when a real problem shows up.
- 2026-11-06: on the day the infra team ran Codex as master, it proposed a
  batch of general platform mechanisms for Intern (input binding, a source
  catalogue, a lifecycle inbox, a compute graph, new policy switches). resodo
  put all of them on hold until each was shown to be necessary against real
  open-source implementations and to reuse existing interfaces. The same day
  he rejected a new mechanism that would block saves containing uncited
  numbers ("do not block the launch, do not add this mechanism"). The tendency
  belongs to the agent, not to the person using it, so the rule has to be
  written for agents to read, not left to people's memory.
- A good counter-example: Thesis #475 deleted about 1,080 lines of dead code.
  It was asked to drop five tables; the agent showed that only one (44 rows)
  was really unread, dropped only that one, and named who still reads the
  other four.

**Cost:** some things that are really needed arrive later, after the first
failure; PR descriptions get two more lines. We think this is much cheaper
than "added and can never be removed".

---

## 2. Which layer and which repo a change belongs in

**Now**

- The boundary resodo set on 2026-11-09; the test is "if I change this, what
  changes?":
  - Only what readers read (which outputs exist, how they are written, format,
    writing and number standards, when they refresh), without touching stored
    data or computed numbers: skynet-analyst-plugins, owned by the product
    team.
  - What the analyst knows or does, what data it stores, what numbers it
    computes, what checks it runs: Intern.
  - Thesis displays the outputs of Intern and plugins; it does not recompute
    numbers Intern already computed.
  - In one line: plugins decides what readers read; Intern decides what the
    analyst knows and does.
  - The test covers the analyst's shared data and outputs. Existing exceptions
    stand: a user's own valuation model is application-private data and stays
    in Thesis (the example in intern
    `docs/collaboration/system_layering_standard.md` section 4.9); in a Deep
    Dive, calculated cells with formulas and inputs written by the author are
    content defined by plugins, and Intern checks only their references, never
    executes their arithmetic (plugins `COLLABORATION.md`).
- Intern `system_layering_standard.md` section 4.5: the unified interface
  layer (`/intern/v1/`) is the only way applications read Intern, and it may
  accept permission-managed writes (only an exchanged user token or an
  explicit service token, only into Intern's own tables, audited). Section
  4.9: data is of three kinds (Intern-owned, written through the interface
  layer, application-private), with four questions to place a new kind; to
  change Intern's data from outside, "send a request, never change it
  directly".
- Plugins `COLLABORATION.md` already says "infra guards the data, product
  decides the content" and lists three interfaces. Thesis-room `AGENTS.md`
  items 3, 4 and 8: read and write Intern only through `/intern/v1/`, heavy
  work goes to Intern nodes, and a missing piece is requested, never worked
  around downstream.

**Practice**

1. Before starting, place the change with the one-line test above. If you
   cannot, ask in an issue; do not build a stand-in in your own repo first.
2. If the cause is in another layer, stop and request it there; do not
   compensate or work around it in your layer. Thesis
   `docs/collaborators/workflow.md` says "Fix the cause where it is; no
   downstream workarounds", word for word our rule. Keep it.
3. The frontend never guesses structure from text (situation 8).

**Why:** FD's layout delivery package (Implementation Kit, 2026-11-08) asked
Intern to change the writing skills, but under the 2026-11-09 boundary those
skills belong to plugins; the same FD rules existed in two places and had
already started to diverge. Another example: on 2026-10-27, while designing
Thesis company data, "does the generation logic live in Thesis or Intern?"
flip-flopped until the four questions of section 4.9 settled it.

**Cost:** a cross-repo need takes one more issue and waits for the other
side's schedule.

---

## 3. Code conventions

**Now**

- Language: Thesis requires English for code, comments, plans, commits and PRs
  (top of thesis-room `AGENTS.md`). Intern requires English for code and
  comments (intern `docs/code_language_policy.md`); CI runs
  `scripts/check_no_chinese_in_code.py` over code and config, with Chinese
  allowed in prompt directories and on lines marked `zh-ok`; Markdown docs and
  JSON test data are not checked.
- Deployment endpoints, model ids and gateway addresses are read from host
  config, never written in code (both `AGENTS.md` files, 2026-11-05, each
  with a CI check). Intern also allows a model id default in code that host
  config overrides; current Thesis docs have no such exception.
- Code structure: intern `docs/architecture/backend_layout.md` says what each
  module holds and what it may import, guarded by import-linter, with an
  exemption list that only shrinks. Thesis is a monolith of one backend, one
  frontend and one library (`.agent-protocols/context.md`).
- Naming: intern `api_style_guide.md` keeps a registry of "one concept, one
  name across the system".

**Practice**

1. Simple, clear code structure comes first. For a simpler structure it is
   acceptable that a small part of the data is temporarily unreadable (resodo,
   2026-10-31). Directories split by responsibility; no folder mixes dozens of
   kinds of service.
2. One thing has one name. Something used in one place that one line can
   explain gets no concept name and no extracted function.
3. Comments say why, not what the code does.
4. Server logs record the full error and stack trace. No redaction or hiding
   rules "just in case" (internal users; secrets still never go into logs).
5. No new per-company special cases (for example "Tencent does X"); put the
   difference in data or a small table.

**Why**

- 2026-10-27: a Thesis task failed and the log showed only a
  `ValidationError`, because the code deliberately kept the original error
  out of the log; tracing that Tencent failure took an hour of log reading.
  resodo: "rules like this are unnecessary extra rules ... early on we can
  delete all of them."
- 2026-10-11: daily reports and subscriptions for companies, ETFs and themes
  could share one path, but the "which target kinds is this on for" decision
  was scattered over 15 places. It became one path plus a small table with
  one row per target kind.

**Cost:** naming and placement take a few minutes of checking existing
patterns instead of inventing on the spot.

---

## 4. Plans and design documents

**Now**

- Infra: intern `.agent-protocols/planning.md` required a plan and a plan
  review before any feature code. Large designs follow the order resodo set:
  state the problem and the dilemma -> a table of short and mid-term scenarios
  (who, what, how often, how much) -> a rubric (simplicity and elegance
  weighted highest) -> research open-source and other implementations -> score
  several options against the rubric -> only then the design and
  implementation. A large plan is an umbrella plan in phases, each with a
  one-sentence goal and acceptance criteria; the first phase is detailed
  enough to start.
- Product: thesis-room `AGENTS.md` lets a small change carry its plan in the
  PR description; a migration, a change on the close-review list, or a change
  across several features gets a plan file.

**Practice** (decided 2026-11-10, see the last section)

1. Where the plan lives, both sides, borrowed from Thesis: a small change
   (item 2) carries its plan in the PR description; any other change gets a
   plan file.
2. **Small changes are reviewed once: plan and code together.** The plan is
   in the PR description, and one implementation review (structured review
   type `impl`) covers both. A change is small when it changes no API
   contract, adds no schema change or migration, does not touch CI or release
   scripts, touches no secrets or credentials, and is roughly 300 changed
   lines or fewer. Anything larger keeps plan review before code.
3. Architecture-level and cross-repo designs follow the order above,
   especially two points: simplicity and elegance carry the highest weight in
   the rubric, and each option answers a few real scenario questions in one
   sentence each; an option that cannot answer cleanly is not simple.
4. Look for what exists before building: existing standards files, existing
   skills, open-source tools. Before setting a rule that differs from common
   practice or inventing a field name, check how two or three mainstream
   implementations do it.
5. Any "may be needed later" item in a plan is either deleted or marked as a
   candidate; it is never written as decided.

**Why**

- 2026-09-15: resodo found "writing a plan and running several review rounds
  first is too slow", and the same day rejected a shortcut that would work at
  once but leave technical debt. The two do not conflict: fast in process,
  right in result.
- 2026-09-24: we invented a rule that technical retries and format re-asks
  share one count. resodo asked "does anyone else do this?". The Instructor
  and pydantic-ai sources multiply them, bounded by a total request cap per
  run; nobody does what we did, so we changed it.
- 2026-11-08: the first draft of a data-architecture design did not read
  `system_layering_standard.md` 4.5 and 4.9 first and reinvented what was
  already decided; review sent it back.

**Cost:** large designs start a day or two slower; small changes get faster.

---

## 5. Review

**Now**

- Infra: the agent-protocols structured-review runner with Codex as the other
  model: Sol for normal difficulty, Astra for genuinely hard work (resodo's
  standing authorisation of 2026-09-07: review calls need no per-call
  approval). Review rules as in situation 1, plus a stop condition: when three
  rounds in a row only block on mechanisms the document itself added, stop
  and ask whether the mechanism should exist.
- Product: pre-merge self-review is free choice
  (`docs/collaborators/workflow.md`); we review before a Thesis PR reaches
  `main`, for correctness and also size and reuse. Since 2026-11-05 a new push
  from FD or atticcas is not a review request; we review when they explicitly
  ask.
- Our tone on their PRs: observations and questions, with suggestions, not
  verdicts. Product choices (layout, what shows first) are FD's.

**Practice**

1. Two tiers, chosen by real difficulty; normal by default; the high tier
   only for genuinely hard work (cross-layer design, concurrency, data
   migration).
2. A reviewer always checks four things: whether the conclusion agrees with
   decisions already made; whether the change is in the right layer; what can
   be deleted; whether verification is enough (situation 11).
3. Do not tell the reviewer your conclusion first. Give it the code and the
   requirement, not "I think this is fine", or it will agree with you.
4. The product team keeps choosing its own review tool, but its review prompt
   includes "list what can be deleted".

**Why:** on 2026-09-25 resodo asked whether the tool cache should get an
"idempotent" field (a request is cacheable only if repeating it gives the same
result). We went along with it and review found nothing; only his own
follow-up showed the cache did not belong in the Kit at all. His words: "what
I need is someone who wakes me up." Review must be able to ask whether the
question itself is right.

**Cost:** the high tier is dearer and slower, so it is used only when the work
is really hard.

---

## 6. CI, merge and release

**Now** (with the 2026-11-10 merge decision applied)

| | Intern (infra) | Thesis (shared) | plugins (product) |
|---|---|---|---|
| CI on a PR push | nothing; the author runs light checks and related tests locally (after merge, CI runs again only when the merged result differs from what was tested) | full `checks` on every push | only checks that `plugins.yaml` parses |
| Before merge | `scripts/ci/premerge.sh` rebases the PR onto the latest `main` and runs full CI; merges only on green; docs-only changes run light checks; several PRs may be batched into one run | `checks` green, and an infra approval on the current head | product reviews its own PRs |
| Who merges | the master or its single merge agent, one at a time | ordinary PRs: the product team itself, after our approval with all checks green; sensitive PRs (migrations, CI/release/deploy scripts, the pinned Intern contract, secrets or credentials): infra | product |
| Runs on | our own AWS machines; CI must not use GitHub-hosted runners | same | GitHub-hosted runners allowed |
| Release | ops command with a receipt; 30-minute check; blocks only on gross failures (service down, new 5xx, a new page-acceptance failure, and so on) | the release bot; before a release, `checks` and `package` are run again for that exact commit; 7 minutes of watching after the switch, with automatic rollback if a worker restarts | live a few minutes after merge |

Sources: intern `AGENTS.md`, `.agent-protocols/merge-queue.md`,
`release.md`; thesis-room `AGENTS.md` items 1, 5, 6 and
`docs/collaborators/release.md`; plugins `COLLABORATION.md`.

**Practice**

1. Triggers stay per repo for now: Intern's full CI is heavy and skipping it
   on PR pushes saves money; Thesis running full CI on every PR push is fine
   for now.
2. Both sides hold this line: before merge and before release, get the green
   CI evidence the repo already requires (including the approved Intern
   practices of light checks for docs-only changes and batched runs), and it
   must be for the exact commit being merged or released. One merger at a
   time per repo, so reruns do not push each other out. In Thesis an ordinary
   PR is merged by its product-team author once our approval is on the
   current head and `checks` is green; a new commit after our approval needs
   approval again.
3. Two things borrowed from Thesis: unfinished features ship behind a flag
   with an owner and a delete-by date; a PR that changes rules, process or
   page locations updates the docs in the same PR (thesis-room `AGENTS.md`
   item 10).
4. Releases block only on gross failures: small latency changes no longer
   cause rollbacks, but a new page-timing acceptance failure (for example a
   page cold start above 2 seconds twice in a row) and a real-traffic latency
   alert still block (intern `.agent-protocols/release.md`). Release soon
   after merging; no "it will go out with the next one". Thesis releases
   still go through the release bot.

**Why**

- 2026-10-26: two Intern PRs skipped the merge agent and each ran premerge;
  #1841 and #1836 collided and #1836 burned two extra heavy CI runs.
- 2026-10-25: a release was rolled back twice for being 26 ms slower; later it
  turned out the same code is 14 to 24 ms slower after a mere restart, and
  measurement noise was about 22 ms. Since then releases block only on gross
  failures.
- 2026-10-23: resodo ruled that no CI runs on GitHub machines (Intern and
  Thesis); on 10-26 he relaxed it so light, rarely run repos (ops, twitter,
  ingest, boards, protocols) may stay on GitHub, because together they cost
  about USD 3.4 a month.

**Cost:** a single merger means a queue; at peak times PRs wait.

---

## 7. Changing production data

**Now**

- Infra: production changes go only through ops commands under
  `scripts/ops/`, with `--env prod --confirm prod --authorized-by <plan path
  or chat date>` and a receipt each time; migrations only add; before
  deleting data, archive to S3 and verify the restore; read-only forensics
  leave no file on the host, `/tmp` included (intern
  `.agent-protocols/release.md`, `decision-boundary.md`).
- Product: the Thesis database allows a direct connection (own account), but
  schema changes go only through migrations, and hand-written SQL waits for a
  snapshot from us; a migration that can lose data needs the master's
  approval, and deleting user-written content needs resodo's (thesis-room
  `AGENTS.md` items 2 and 3).

**Practice**

1. Before changing production data, tell resodo (or the other side's owner)
   in one plain sentence: what data, where it came from, one concrete
   example, what the command does (append, mark or delete), and why now. Even
   when the command exists and the change is within an authorisation. With
   an existing authorisation, say it and go ahead without waiting for a reply;
   only a change that needs new authorisation waits for a yes.
2. One-off data fixes use the existing ops commands first; write a script
   only when none exists. Either way, dry-run first to produce the list of
   rows to change, confirm the list, run exactly that list, read back to
   check, and keep a receipt.
3. A deleting PR says on the first line under the title what it deletes and
   how many rows, with evidence of who still reads it. Thesis #475 ("DESTRUCTIVE:
   drops 1 production table (44 rows)") is the model.

**Why:** on 2026-11-04, within an overnight authorisation, we used an existing
command to withdraw three wrong "earnings released" records, and only told
resodo afterwards, in internal terms. He could not tell where those records
came from (FMP press-release headlines, not SEC) and took it for a new,
unapproved mechanism.

**Cost:** one more message per data change; a change that needs new
authorisation waits for the reply.

---

## 8. Frontend

**Now**

- Infra: the frontend has three layers: design values (colour, spacing, type
  size) -> generic small components -> business components; pages only
  compose components. Lint, `check_ui_layers.py` and screenshot comparison
  guard this (intern `docs/frontend_components.md`; the portal's copy lives in
  skynet-apps). Fonts only through the defined variables. Visible changes get
  a visual check by a non-author against the Vercel web-design-guidelines
  (agent-protocols `visual-qa`).
- Product: Thesis also requires a non-author visual check and has a
  design-token guard (#463). FD's layout delivery package has several very
  good rules: the frontend shows only the structure Intern provides and
  **never guesses from text which sentence is a heading, adds its own bullet
  marks, or picks words to bold**; content, numbers and citations never change
  by a single character; tests use the font size the browser actually
  computes, not only the CSS; old reports and newly generated reports are
  accepted separately; final acceptance happens on the real page after
  release, where a separate QA agent gives a clear pass or fail and names the
  first failing criterion.

**Practice**

1. Adopt those rules from FD's package as written, in both teams' frontend
   rules.
2. Keep the three component layers and the non-author visual check; the visual
   check happens after the feature has settled and before a human sees it, and
   does not block merging the feature PR.
3. The visual check also looks at loading (a flash of large-then-small
   content), information density and usefulness, not only conformance.
4. A backend-only change that changes what users see (ordering, search
   results) also gets a visual check.

**Why**

- 2026-10-11: the frontend was split by page across several parallel agents
  with no shared component layer; the same element had 2 to 10
  implementations, and checks kept catching inconsistencies.
- 2026-11-04: Intern #2227 only changed backend search correction, but it
  changed the add-company page's results and shipped without a visual check;
  typing "tsla" returned Slash, Slate Auto and the like, plus unlisted
  companies with an add button.
- FD's "the frontend does not guess structure" rule prevents a class of bug
  that is hard to find: a right guess is invisible, a wrong one turns body
  text into a heading, and every company goes wrong differently.

**Cost:** some old reports improve little until Intern or plugins regenerate
them.

---

## 9. Interfaces and data structures

**Now**

- `/intern/v1/` only grows: new endpoints and new optional fields are fine;
  deleting, renaming, retyping or changing meaning needs `/intern/v2/` side by
  side (intern `api_style_guide.md` section 11, which also records the few
  exceptions resodo approved, such as one field's value exception and a v1
  fix to the meaning of an output's refresh condition; these stand). CI checks
  it mechanically with `check_api_contract_compat.py` (oasdiff). Intern serves
  its own live interface reference (`/intern/v1/reference`,
  `/intern/v1/openapi.json`). Every shape change to `/intern/v1/` is told to
  resodo.
- Thesis uses one pinned Intern contract file plus a generated client;
  generated files are never edited by hand (thesis-room
  `.agent-protocols/context.md`).
- Database migrations only add on both sides; Thesis renames in three steps
  (add the new, switch the code, drop the old in a later release). Intern
  `persistent_schema_lifecycle.md` asks every new field to state who writes
  it, who reads it, its states and its retention.
- One company ID system-wide: Intern's company UUID (thesis-room `AGENTS.md`
  item 11, 2026-10-26).

**Practice**

1. Keep all of the above on both sides, including the recorded exceptions.
2. Fields that classify content (for example the model's judgement of what
   kind a piece of material is) grow their categories from real data, are not
   invented in advance, and carry an `other`; when `other` fills up, look at
   adding a category. Process states are different: Curator escalations have
   only `open` and `resolved`, with no `other`.
3. Internal interfaces get no version numbers or compatibility layers; both
   sides upgrade in one change. Version numbers are only for external
   interfaces such as `/intern/v1/`.
4. Before handing a new Intern endpoint to the other side, we accept it
   ourselves in production with a real account, field by field against the
   original source.

**Why**

- 2026-10-26: a second company key system appeared (FD's `c_...` keys and
  nine short keys). resodo: "our system has no need for two ID systems; the
  later cost is far too high." Thesis is switching to UUIDs in three PRs.
- 2026-10-26: we handed over an endpoint without opening it to check it
  ourselves. resodo: "why didn't you open it and try to accept it?"

**Cost:** renames and field removals take several releases; slow.

---

## 10. Cross-repo requests and issues

**Now** (with the 2026-11-10 decision applied)

- Thesis has an "Intern request" issue form
  (`.github/ISSUE_TEMPLATE/intern-request.md`): the kind of request, what is
  needed and why; a node request gives inputs, frequency, scale and cost; a
  field request gives examples; a data problem gives the endpoint, the IDs,
  and "what I got, what I expected". FD's Thesis #477 (11 companies missing a
  dividend assumption, so their rating was empty, with a per-company table and
  a control group, asking Intern for "the smallest lasting fix in the layer
  that owns it") and atticcas's #469 (explicitly "no new endpoint, no new
  field") are good models. Thesis #483 is a request filed this way.
- Infra: in an existing PR or issue we may reply within the agreed scope;
  opening a new issue addressed to the product team needs resodo's yes first
  (2026-11-05).

**Practice**

1. **Requests from the product team to Intern are opened in the Thesis repo**
   with the "Intern request" form, as the product team already does. The
   infra team opens the Intern PR and links it back on the Thesis issue.
2. One issue covers one concrete problem: "what is, what should be, one
   example". Say what is needed, not how the other side should implement it.
3. Continue in an existing thread instead of opening a new one; open a new
   one only when the scope or the problem changes.
4. When it is urgent, also message resodo directly.

**Why:** on 2026-11-05 an infra agent opened three Thesis issues for atticcas
(#448, #449, #450) without showing resodo; all were closed and kept as drafts.
A new issue is a new request to the product team in his name; its scope and
timing are his call. Before the decision, plugins `COLLABORATION.md` said to
open requests in Intern with a `product-request` label while thesis-room
`AGENTS.md` item 8 said Thesis; the Intern label was never used.

**Cost:** opening a new issue takes one confirmation step.

---

## 11. Verification and reporting

**Now**

- The product team does this better: PRs separate "accepted locally / CI
  pending / production acceptance pending" (Thesis #456) and list what was
  tested apart from what was not (#470, plugins #10); FD's delivery package
  says plainly "a PR, a green CI, a merge or a deploy receipt is not done".
- Infra: intern `AGENTS.md` requires stating where a result came from (CI, a
  reviewer's rerun, the author's local run, a human's acceptance). Thesis #476
  is a good infra example: old and new company figures compared one by one,
  6,572 actuals and 195 guidance items identical, the only differences 43 KPI
  statements, with the reason.
- A shared fault: PR descriptions are too long and too dense with jargon. #456
  has more than a screen of status and qualifiers; #475 and #476 are long too.

**Practice**

1. One short format for PRs and reports: what was done and why; **verified**
   (where, with evidence links); **not verified** (who will, when); risks; how
   to check after release. Aim for one screen.
2. For a user-visible change, "done" means the right result seen on the real
   production page after release; local screenshots, green CI and deploy
   receipts are intermediate evidence. A change without a page (protocol
   docs, the kit library, back-office tools) is accepted along the path it is
   actually used.
3. Understand what a number measures before reporting it; check someone
   else's conclusion yourself before repeating it.
4. Write status in plain words ("not yet seen in production"); no invented
   status words.

**Why:** on 2026-10-21 a worker crash from Thesis #182 reached production.
`main` CI had been red since #178, and PRs were merged on the agents' own
reports of local results.

**Cost:** a real look at production every time, a few more minutes.

---

## 12. Resident agents do the routine work they are authorised for

**Now**

- The system is a funnel: front desk -> Curator (governance agent) -> Keeper
  (the governance agent above it) -> human. Each layer passes up only what it
  cannot handle; front-desk business questions (a missing target, an unsure
  call) go only to Curator, and only "the mechanism is broken" may go straight
  to a human. Intern `system_layering_standard.md` section 3.1 describes the
  roles; the top of intern `.agent-protocols/authority-ledger.md` says who
  holds governance decisions. When resodo defined Keeper on 2026-10-08, the
  goal was that about 0.1% to 0.5% of cases end up with a human.
- Each company has a resident analyst agent; readers' follow-ups and
  corrections go to its inbox and it updates its notes (the
  `system_layering_standard.md` 4.9 example: FD wants Tencent's capex guidance
  changed in the notes, says so in the analyst chat on Thesis, and the analyst
  changes it in its next turn and records whose instruction it was).
- Authorisations are written in an authority ledger (intern
  `.agent-protocols/authority-ledger.md`): each entry records resodo's exact
  words, the scope and what is excluded; one sentence revokes it; nothing
  extends by analogy.
- Product: Codex runs as a direct session and asks its own human when it
  needs one; there is no ledger.

**Practice**

1. Routine, rule-based work goes to the matching resident agent first:
   content and number corrections to that company's analyst; company
   identity, mapping and instrument questions to Curator or Keeper. People do
   not edit these by hand.
2. People handle only what the funnel passes up: system problems that need a
   code change, large migrations, dangerous operations.
3. To let an agent do a new kind of work, write the authorisation down: the
   exact words, the scope, what is excluded, in one file. If the product team
   wants its agents to act on their own for some kind of work, it can keep its
   own small ledger.
4. What a higher layer has decided is executed directly with the same tools,
   not handed down to be researched again.

**Why:** from 2026-10-01 to 10-05 Curator submitted 997 change sets. Of those
with a review record, only "create company" was ever rejected (14 of 255: 12
duplicates, 2 rule violations, 0 factual errors); about 610 mapping,
instrument and description change sets had zero rejections. On that basis
resodo made Curator fully automatic on 10-05; nobody approves change sets one
by one any more.

**Cost:** rules must be written clearly enough for agents to follow; writing
them takes time, and someone has to check regularly that the agent is right.

---

## 13. How agents work

**Now:** both sides use one worktree per task (`wt switch --create <branch>`,
never editing the main checkout) and run `scripts/agent_protocols_guard.sh
start` before work (both `AGENTS.md` files). Infra also: one subagent per
task in parallel, never piling work onto a busy agent (10-27); long tasks
start in the proper background mode so people can see them in `/tasks`
(11-08); cheap models for easy work (11-05); on a denial, stop and report,
never take another route.

**Practice**

1. Both sides adopt the above. Thesis `workflow.md` already has "stop and
   report on a denial"; keep it.
2. Run only the affected tests and cheap checks locally; push and let cloud CI
   run the full suite, and debug from CI logs instead of reproducing large
   suites on a dev machine.
3. Pick the model by difficulty: cheap ones for mechanical work, the strongest
   only for hard design and debugging, with the reason stated.

**Why:** on 2026-10-27 the Thesis #330 CI fix queued behind an agent already
holding six tasks, and sat waiting. On 2026-11-04, local browser tests plus a
VM pushed a 16 GB dev machine into 6 GB of swap.

**Cost:** more agents at once means someone has to watch the lines.

---

## 14. Incidents and who fixes them

**Now:** on the infra side a red full CI on `main` is the master's job that
day, dispatched at once. Alerts go only to people (urgent ones by Bark and
Slack, others by Slack), never to the master or any agent, because no agent
is guaranteed to be online around the clock; each alert is defined in one
place. A gross release failure rolls back to the previous release; functional
problems are fixed forward.

**Practice**

1. A red `main` is fixed the same day by the repo's owner; if someone else's
   change turned it red, tell them instead of working around it for them.
2. Alerts go only to people; each is defined once.
3. Gross release failures roll back; everything else is fixed forward, with
   no protection layer built in advance "in case we need to roll back".
4. Before a fix, think through what normal behaviour it blocks, and cover that
   normal path with a test, not only "the bad case is blocked".

**Why**

- 2026-10-22: Thesis nightly CI failed and nobody looked for more than seven
  hours, until resodo wanted to release. He rejected adding a reminder: "the
  root cause is ignoring CI errors; no reminder will help."
- 2026-11-01: a subagent found the temp directory could be read across
  companies and proposed forbidding reads there, saying "normal reads are not
  affected". resodo saw at once that the model would then lose the full text
  of truncated tool results.

**Cost:** same-day fixes interrupt current work.

---

## Where the two sides converge

1. **Who owns the writing skills.** FD's layout package said "Intern owns
   this writing skill"; under the 2026-11-09 boundary, writing, format and
   standards belong to plugins. Direction: plugins; the writing part of that
   package is done in plugins, and Intern drops its duplicate reader-chapter
   skills (after checking new companies' outputs do not depend on them).
2. **Where cross-repo requests are opened.** Decided 2026-11-10: in the
   Thesis repo (situation 10).
3. **Where plans live.** Both sides use the Thesis tiers (situation 4). Here
   the infra team learns from the product team.
4. **How PRs are written.** The short format of situation 11, aiming for one
   screen.
5. **Temporary switches.** Thesis flags carry an owner and a delete-by date,
   and CI fails after the date; Intern transition switches (for example
   `outputs_enabled`) have no delete-by date. The infra team adopts the owner
   and delete-by date where a switch is defined, without building a second
   flag system.

## Decisions (resodo, 2026-11-10)

1. **Cross-repo requests:** the product team opens requests to Intern in the
   Thesis repo ("Intern request" form, as already done, for example Thesis
   #483). The infra team opens the Intern PR and links it back. Plugins
   `COLLABORATION.md` is changed to match (skynet-analyst-plugins#16).
2. **Small changes:** plan and code are reviewed together once (structured
   review type `impl`, plan in the PR description). Small means no API
   contract change, no schema or migration, no CI or release scripts, no
   secrets, and roughly 300 changed lines or fewer. Larger changes keep plan
   review first. Recorded in intern `.agent-protocols/planning.md` and its
   authority ledger (skynet-intern#2412).
3. **Thesis merges:** ordinary PRs are merged by the product team
   (`Fredi111-bot`, atticcas) themselves, after the infra team's approval on
   the current head with all checks green. Sensitive changes (migrations, CI
   and release/deploy scripts, the pinned Intern contract
   `contracts/intern/`, secrets and credentials) are still merged by the infra
   team. Releases still go through the release bot. GitHub branch protection
   is not available on the organisation's current plan, so the approval is
   checked by Thesis's CI territory check instead: `Fredi111-bot` is no
   longer a core owner, so a product-team PR into `main` fails `checks` until
   resodo approves its current head, and an approval on an older commit does
   not count (skynet-thesis-room#488). Who presses merge on a sensitive
   PR is a team rule; GitHub cannot restrict it on this plan.

One historical lesson, not anyone's current position: Thesis #300 (2026-10-26)
once added protection for a hypothetical rollback, later removed in favour of
fixing forward. Both sides follow situation 14 from now on.

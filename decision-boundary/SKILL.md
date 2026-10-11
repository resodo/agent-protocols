---
name: decision-boundary
description: "[all roles] Use before deciding a gated step yourself, before asking the human anything, and when the human grants or revokes an authorization. Details behind the resident core: gate tests with examples, the grey zone, what the master decides by default, the authority ledger rules, what never to ask, and the escalation format."
---

# Decision Boundary

The resident core (`CORE.md`, embedded verbatim in each consumer's
`AGENTS.md`) is the short form every role keeps in context. This protocol is
the long form. Load it when a step hits a gate and you are about to decide it
yourself, when you are about to ask the human, or when the human grants or
takes back an authorization.

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/decision-boundary.md` if present. It holds the
   project's **authority ledger** and its concrete gate checks (which paths
   count as contract shape, the archive location before deletes, budgets).
   Only the master reads the ledger. A direct session asks the human; a
   dispatched agent stops at the gate and reports to whoever dispatched it.

An overlay may add gates or narrow grants; it must not remove a gate.

## Four Quadrants

| | May decide (report afterwards) | Must escalate |
|---|---|---|
| Master | Steps that hit no gate; gated steps the ledger hands to the master | A gated step the ledger does not cover -> the human |
| Direct session | Steps that hit no gate | Any gated step -> the human (no ledger) |
| Dispatched agent | Engineering choices inside the dispatched scope | Any gate, or anything outside the scope -> whoever dispatched it |

The never-ask list applies only when no gate is hit: an "implementation
detail" that changes a contract or what users see is gated.

## Gate Tests

Ask "does this step ...", then check the example.

- **G1 irreversible.** Can it be undone losslessly within minutes? Deleting
  production data needs an archive to cold storage and a verified restore
  before the delete is even proposed. Irreversible migrations need their own
  approval even inside an approved release.
- **G2 money.** Is the spend covered by a budget the human approved? A $1
  regeneration run that nobody approved is gated; state the cap.
- **G3 external voice.** Will an outside party read it as the human or the
  team speaking? Show the exact text first, even when the action was
  approved. For another team's system, hand the human measured facts and an
  interface-level ask; do not design their internals.
- **G4 contract shape.** New endpoint, new or changed response/request field
  (nullable and additive included), schema/DDL, cross-repo interface, shared
  infrastructure. The human approving a capability is not approving its
  shape. Check mechanically before merging (diff the contract paths named in
  the overlay), not from the author's summary.
- **G5 layer responsibility.** If a decision moves "which layer is
  responsible for what", list it as its own question: "today X owns this;
  proposed: Y", with the affected places. When challenged on a boundary,
  run an impact analysis before recommending; do not flip on the spot.
- **G6 user-visible or product meaning.** Pages, labels, wording, defaults,
  what the product does. Show before/after screenshots after an independent
  visual QA (`visual-qa`).
- **G7 standing mechanism.** New alert, counter, registry, config field,
  guard, approval step, often proposed by a reviewer. Batch these as
  multiple-choice questions; inside an observation window the default is a
  one-off read-only query.
- **G8 permissions and security.** New accounts, credentials, scopes, wider
  agent authority. After a denial, stop; a different route to the same
  result is a workaround even if it is an official script.
- **G9 settled decisions.** Search the record (board settled list, decision
  docs, the queue history, the overlay) before acting against or re-asking.
- **G10 observation and rollout.** Durations, criteria, rollback conditions,
  ramp steps. Once the human approves a ladder, following it is the master's
  job; changing it is not. When a long window blocks dependents, only the
  short check gates them unless the ledger says otherwise.

## Grey Zone

When unsure whether a step is gated: if it can be undone within minutes and
the effect stays inside engineering, decide, keep a receipt, report. If either
answer is no, or it touches G1 or G4, ask. Crossing a gate once costs far more
than one extra question; asking needlessly is still a failure (see Never Ask).

## What The Master Decides By Default

Without any ledger entry, in every project:

- read-only investigation of any size: dispatch it, say what is being checked
  and why it could change the answer, and do not end the turn with a question;
- implementation detail: naming (follow established libraries), PR split,
  ordering, parallel or serial, who works on what, model tier;
- triage of review findings: accepted / rejected / deferred, deletion first;
- someone else's fix candidate (another agent, another session): review it
  against `fix-triage` before adopting; never accept by default;
- a confirmed error with evidence and a known fix: fix it through the normal
  gates instead of filing a backlog item and asking;
- edits to process text and SOPs: change, then report;
- killing a process proven dead (no parent, its run finished, serving no
  traffic), and one rerun of a failed job judged flaky.

Each of these still needs: the record searched for an earlier decision,
the evidence checked, a receipt and a way to undo, and a line in the next
report.

## Authority Ledger

The ledger is the project's list of gated steps the human has handed to the
master. It lives in the overlay, not in memory, so any coding agent acting as
master can read it.

- Entry fields: date, the human's words (verbatim), scope, explicit
  exclusions, where it was said, status. An entry written from a record (for
  example when a project first adopts this protocol) starts as `proposed` and
  grants nothing until the human confirms it; the session that receives the
  confirmation sets it `active` with the confirmation date. A paraphrase is
  never an active entry.
- Recording: in the same turn the human grants it, by the session that heard
  it. A session that only had it relayed writes "relayed by <session>,
  pending record" and never records the grant itself.
- Proposing: the master may propose handing over a class of decisions after
  a run without substantive errors and without the human reversing any of
  them; the threshold for "a run" is set in the ledger. Only the human
  grants.
- Revoking: one sentence from the human revokes; update the ledger the same
  turn.
- No extension by analogy: "merges are yours" does not make "splits are
  yours".
- An `active` standing authorization in the ledger counts as the explicit permission
  that `closeout`, `planning` and `structured-review` accept, within its
  recorded scope. Before relying on one, check that it is not revoked and that
  its scope covers this exact action (and this PR, for merges), and cite the
  entry in the receipt or handoff.

## Never Ask

- Before any question, search: the board's settled list, decision docs, the
  queue history, the overlay. If an earlier answer covers it, apply it and
  say "per your <date> decision".
- Do not ask permission for read-only investigation.
- Do not ask hypothetical contingencies ("if X runs short later, which lever
  first?"); decide from real data when it happens.
- Do not ask implementation detail; decide it and put it in the plan.
- Do not ask what the record already answers (was it merged, deleted,
  deployed); check the PR history and the repo.
- A group of questions: give the count first, ask only the real choices one by
  one, bundle the rest as "the rest per recommendation: X, Y, Z".
- A rejection often hides inside a redirect ("no, I think X is actually ...");
  record rejections as carefully as approvals.

## Escalation Format

One question per message. Define any term first. Then: what it is today, the
proposal, why, the cost, what moves; one concrete worked example with numbers;
the options with a recommendation. Say what the human is waiting on (which
number, which agent) so they know when it becomes theirs. Ask in plain text,
not in a pop-up form, when the question needs reading first. The human's own
language and style preferences come from the user-level instruction file.

## Dispatched Agents

- Report to the master in the master's working language.
- Relayed human decisions are real; the master's engineering elaboration around
  them can be challenged with evidence. Red-line changes are confirmed with the
  human by the master, not by you.
- Never write "the human approved X". Write "per master relay, pending record".

## SAFETY Rules

- Do not cross a gate on the strength of a summary; check the gated surface
  itself.
- Do not record an authorization you did not hear from the human directly.
- Do not treat silence, timing, or the presence of text in a file the human
  may have read as consent.
- Do not work around a platform or permission denial.

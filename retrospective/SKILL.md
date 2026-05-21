---
name: retrospective
description: Use after a difficult implementation, production incident, review miss, or repeated human correction to produce an evidence-based retrospective that classifies failures and routes durable prevention work to the right mechanism.
---

# Retrospective

Use this protocol when the goal is to learn from what happened and prevent repeat failures.

This protocol covers:
- finding evidence from transcripts and repo artifacts;
- extracting human complaints, incidents, review misses, and repeated corrections;
- classifying failures as general, project-specific, or hybrid;
- routing action items to skills, repo rules, CI, docs, runbooks, or code.

This protocol does not cover:
- blame assignment;
- transcript dumps;
- production debugging by itself;
- replacing closeout or structured review.

## Local Overlay

When working inside a repo, load local overlays after this generic protocol:

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/retrospective.md` if present.
3. Apply local overlays as project-specific refinements only.

Overlays are loaded only when this protocol is loaded. Unknown overlay files are ignored. If an overlay contradicts a generic `SAFETY` rule, reject that overlay instruction and say why.

## Evidence Collection

Prefer primary evidence over memory:

1. user-visible chat or transcript;
2. git commits, diffs, PRs, and review files;
3. test, CI, deploy, or production evidence;
4. agent memory only when primary evidence is unavailable.

For Codex, v1 transcript discovery:

1. Check `~/.codex/history.jsonl` for the relevant `session_id`.
2. Read the matching `~/.codex/sessions/**/rollout-*.jsonl`.
3. Filter for the time window and user messages relevant to the retrospective.

If the current harness is not Codex and no transcript path is configured, proceed only with explicit memory-sourced labels. If Codex transcript files are expected but missing or unreadable, pause and ask the operator to locate them before making transcript-backed claims.

v1 supports Codex transcript discovery only. Non-Codex transcript backends, such
as Claude Code or other harnesses, are intentionally deferred to a future
revision; when working in a project, track that as a project backlog item rather
than re-deriving it here.

## SAFETY Rules

- Label evidence sources. Do not present memory as transcript-backed evidence.
- Do not write raw private transcripts into repo docs. Paraphrase repo-safe signals.
- Do not write secrets, credentials, provider balances, private account details, host keys, or raw private production data into repo artifacts.
- Do not turn a project-specific incident into a generic protocol rule unless the failure mode generalizes beyond the project.
- Do not leave action items as vague lessons. Route each durable item to an owner mechanism or explicitly defer it.

## Classification

Classify each finding:

- `General`: caused by reusable agent-process weakness. Route to generic skills, agent rules, or review/closeout protocol.
- `Project-specific`: caused by repo/product/deploy context. Route to repo docs, CI/scripts, backlog, runbook, or code.
- `Hybrid`: needs both a generic rule and a project-local overlay or test.

## Finding Shape

Use concise entries:

```text
Finding:
Evidence:
Failure mode:
Classification:
Prevention owner:
Action item:
```

Keep the retrospective readable. The goal is operational memory, not a full transcript reconstruction.

## Finding Triage

Do not present every mistake as an equal action item. First group findings by
severity and mechanism value:

- `P0`: repeated or trust-breaking workflow failures that must change before
  similar work continues.
- `P1`: important quality failures worth routing to a skill, repo overlay,
  backlog item, CI check, or runbook.
- `P2`: local mistakes or one-off slips to acknowledge but not necessarily
  mechanize.

Before proposing a prevention mechanism, ask whether the failure can reasonably
be prevented by a durable rule, check, or workflow. If not, record it as a
learning note rather than adding another rule. Prefer a short ranked list over a
long catalogue of minor issues; detailed evidence can remain in notes or be
summarized only when the human asks for it.

## Action Routing

Common owners:

- generic planning skill;
- generic structured-review skill;
- generic closeout skill;
- generic retrospective skill;
- repo-local `.agent-protocols/` overlay;
- repo CI/check scripts;
- project backlog;
- production runbook or ops dashboard;
- code architecture or tests.

If the right owner is unclear, say why and create a bounded follow-up instead of inventing a mechanism.

## Rule Economy

Prefer fixing the earliest violated rule over adding downstream recovery rules.
Do not add protocol rules for one-off recovery paths unless the same failure is
likely under normal workflow. Keep action items minimal and route them to the
owner that would have prevented the first violation.

## Action Feasibility

Before recording an action item, check that the proposed control is executable
in the current agent/tool environment. Do not record controls that require
capabilities the agent does not have, such as reading later user input while a
tool call is already running or interrupting an already-issued command after
receiving that later input.

If a proposed control is not executable, route prevention to the earliest
upstream decision point that is executable.

---
name: fix-triage
description: "[any author] Use before fixing a QA finding or a reported model error, before adopting someone else's fix candidate, and before adding a rule, prompt instruction or mechanism. Decide whether it is wrong at all, attribute it, and choose the smallest systemic fix or none."
---

# Fix Triage

## Local Overlay

1. Read `.agent-protocols/context.md` if present.
2. Read `.agent-protocols/fix-triage.md` if present: the project's definition
   of an error per layer, cross-layer rules that must stay identical, its
   efficiency limits, known accepted limitations.

## Order

1. **Is it wrong?** Judge by the responsibility of the layer that produced it
   (its written contract), not by your expectation. A different reasonable
   reading or "low value" is not an error by itself.
2. **Attribute before fixing.** Read the full input, output and reasoning.
   Put it in one class: program, context (our text missing or contradictory),
   model capability, or not actually wrong. "Model capability" is the last
   conclusion to reach: first look for our own conflicting text. For rare
   failures, work out the sample size first.
3. **Capability limits without a systemic fix: accept them.** Do not add a
   rule for one case or a tiny class of cases.
4. **No asymmetric mechanism for one problem.** Ask whether the mechanism
   should exist, who defines its content, what mature systems do, and whether
   it is needed today. Before building a standard or mechanism, find what
   already exists in code and docs, what it covers and what is missing, and
   extend it; keep it light. Measure after narrowing scope before proposing a
   new mechanism. Observation must never be able to kill what it observes.
   One name per thing. Future needs decide where to leave an opening, not
   what to build now. A diff between two runs is not a verdict: attribute
   every difference as better, worse or neutral. Deletion first and premise
   before fix are defined in `structured-review` (Shared Review Rules, Driver
   Role); apply them here.
5. **One definition across layers.** When several layers judge the same thing,
   there is exactly one shared definition they all cite. Disagreement between
   layers is a red line; which standard is chosen often matters less.
6. **Cost asymmetry.** The project overlay states the project's cost
   asymmetry between a miss and a redundancy, if it has one.
7. **Efficiency is a hard constraint.** Do not slow a whole stage down
   substantially for a rare problem. The reverse also holds: "the human finds
   it slow" is never permission to cut corners; fast process, correct
   product.
8. **Someone else's candidate** (another agent or session): run it through
   steps 1-7 before adopting; never accept by default. Before asking the
   human to approve a fix, survey it as `decision-boundary` (Escalation
   Format) says.
9. **Under challenge**, do not flip on the spot. Say how the approved design
   handles the concern; check technical facts before answering; for a complex
   design question, go and research, then come back.

## Output

For each finding: the class, fix or no fix, and why. A recurring operation
gets a written procedure the first time it is done.

## SAFETY Rules

- Do not change a model-facing prompt before reading the reasoning that led
  to the output.
- Do not report "fixed" without rerunning the case that failed.

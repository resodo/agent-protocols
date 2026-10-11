# Principles behind fix triage

- Deletion first and premise before fix: see `structured-review`.
- "The human finds it slow" is never permission to cut corners: fast process,
  correct product.
- Measure after narrowing scope before proposing a new mechanism.
- Observation must never be able to kill what it observes.
- Categories grow from real data, and every enum carries an `other` bucket
  that is mined periodically.
- Tool behavior is defined once, in the tool definition; prompts reference
  tools by name.
- When a principle is overturned, sweep every document that repeats it.
- Explain with designs that are running or planned, not with dead code.
- One name per thing.
- Future needs decide where to leave an opening, not what to build now.
- A diff between two runs is not a verdict: attribute every difference as
  better, worse or neutral.

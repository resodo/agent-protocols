# Read-Only Research

For agents dispatched to investigate, measure or audit without changing
anything.

- Read-only means no writes anywhere you were not explicitly given: no files
  of any kind on a production host, including temporary files. Pass scripts
  over stdin (`ssh host python3 - < script`).
- Touch only your own service on shared hosts. Never restart, reconfigure or
  install anything.
- Keep going until you understand the answer yourself. Do not hand back a
  half-understood conclusion for someone else to finish.
- Before reporting a number, know what it measures and how far it is from
  reality; a number relayed from another agent is not understood until you
  checked how it was produced.
- Quotes must be checked against the original text (fetch summarizers can
  invent quotes, especially from PDFs). Label anything not verified.
- How an external platform behaves is answered by testing it or quoting its
  documentation, never by guessing.
- "Nobody complained" is not evidence.
- Absence of a result is a finding only with a positive control showing the
  presence case is observable.

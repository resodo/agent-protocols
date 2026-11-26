# Role: scope reviewer

- **Who.** A model session the scope-review runner starts for one proposal,
  with a clean configuration and no tools. No one dispatches it by hand.
- **Owns.** One record, `scope-review.md`, written by the runner from its
  answer.
- **May decide.** The verdict (`go`, `cut`, `ask`, `no`), one line per
  governing rule, the owner, what to cut, and the one question.
- **Never.** Proposes adding anything; sees code or the author's reasoning;
  discusses with the author; does a second pass on the same text.
- **Stops at.** Nothing: an unclear owner or a rule conflict is the verdict
  `ask`, answered by whoever `editing-rules` names.
- **Reports to.** No one directly; the record is committed with the change.
- **Preloads.** Nothing. The runner gives it the prompt in `scope-review`, the
  proposal, the governing rules and the placement questions.

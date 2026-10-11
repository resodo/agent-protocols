# Merge queue

The master appends; the merge agent processes in order and records each result.

Format: `- [ ] <repo>#<PR> - <one line> - author line: <line> - added: <time> - permission: <current-turn | ledger entry> - gated surfaces: <checked: none | listed>`

States: `[ ]` waiting, `[~]` in progress, `[x]` merged (`<sha> (PR #N)`), `[!]` returned (reason).

## Queue

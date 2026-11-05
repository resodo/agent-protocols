# Vendored: Vercel Web Interface Guidelines

Verbatim copies; do not edit them here. Local rules go in `visual-qa/SKILL.md`
or a project overlay.

- Upstream: https://github.com/vercel-labs/web-interface-guidelines (the
  same text is published at https://vercel.com/design/guidelines).
- License: MIT, Copyright (c) 2025 Vercel Labs; full text in `LICENSE`, which
  must travel with these files.
- Pinned commit: `434b7f91364665f2f733b310ec54809bf8f37937`
  (2026-10-05T20:49:16Z); copied 2026-11-05.

| File here | Upstream file | What it is |
| --- | --- | --- |
| `guidelines.md` | `README.md` | the full guideline with reasons and links |
| `rules.md` | `AGENTS.md` | the same guideline as MUST / SHOULD / NEVER rules |
| `LICENSE` | `LICENSE` | MIT license |

## Refresh

```bash
SHA=$(gh api repos/vercel-labs/web-interface-guidelines/commits/main --jq .sha)
BASE=https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/$SHA
curl -fsSL "$BASE/README.md" -o guidelines.md
curl -fsSL "$BASE/AGENTS.md" -o rules.md
curl -fsSL "$BASE/LICENSE"   -o LICENSE
```

Run it in this directory, check that the license is still MIT, read the diff,
and update the pinned commit and dates above in the same change.

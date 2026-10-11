#!/usr/bin/env python3
"""Check that a consumer's instruction file embeds the decision-boundary core verbatim.

Usage: check_resident_core.py <consumer AGENTS.md> <path to decision-boundary/CORE.md>

Exit 0 only when the consumer file contains exactly one begin marker and one
end marker, in that order, and the text between them (markers included) is
identical to CORE.md (line endings normalized). Any other state exits 1 with a
message.

Claude Code reads AGENTS.md only when no CLAUDE.md, .claude/CLAUDE.md or
CLAUDE.local.md exists next to it. If any of those exists, at least one of them
must carry the core itself or import AGENTS.md with a line "@AGENTS.md";
otherwise exit 1.
"""
from __future__ import annotations

import sys
from pathlib import Path

BEGIN = "<!-- agent-protocols:decision-boundary-core"
END = "<!-- /agent-protocols:decision-boundary-core -->"


def extract(text: str) -> str:
    begins = text.count(BEGIN)
    ends = text.count(END)
    if begins == 0 and ends == 0:
        raise ValueError("resident core block is missing")
    if begins != 1 or ends != 1:
        raise ValueError(f"expected one resident core block, found {begins} begin and {ends} end markers")
    start = text.index(BEGIN)
    stop = text.find(END, start)
    if stop == -1:
        raise ValueError("resident core block is not closed")
    return text[start : stop + len(END)]


CLAUDE_FILES = ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md")


def claude_shadow_problem(consumer: Path) -> str | None:
    present = [consumer.parent / name for name in CLAUDE_FILES if (consumer.parent / name).is_file()]
    if not present:
        return None
    for path in present:
        text = path.read_text(encoding="utf-8")
        if BEGIN in text or any(line.strip() == "@AGENTS.md" for line in text.splitlines()):
            return None
    names = ", ".join(str(p.relative_to(consumer.parent)) for p in present)
    return (f"{names} exists, so Claude Code does not read {consumer.name}; "
            f"add a line '@AGENTS.md' to one of them")


def check(consumer: Path, core: Path) -> str | None:
    expected = core.read_text(encoding="utf-8").strip()
    try:
        found = extract(consumer.read_text(encoding="utf-8"))
    except ValueError as exc:
        return f"{consumer}: {exc}"
    if found.strip() != expected:
        return f"{consumer}: resident core differs from {core}; copy it verbatim"
    return claude_shadow_problem(consumer)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    problem = check(Path(argv[1]), Path(argv[2]))
    if problem:
        print(problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

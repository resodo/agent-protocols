#!/usr/bin/env python3
"""Check that a consumer's instruction file embeds the decision-boundary core verbatim.

Usage: check_resident_core.py <consumer AGENTS.md> <path to decision-boundary/CORE.md>

Exit 0 only when the consumer file contains exactly one begin marker and one
end marker, in that order, and the text between them (markers included) is
identical to CORE.md (line endings normalized). Any other state exits 1 with a
message.

Claude Code reads AGENTS.md only when no CLAUDE.md, .claude/CLAUDE.md or
CLAUDE.local.md exists in its directory or any directory above it (the
user-level ~/.claude/CLAUDE.md does not count). If any such file exists, at
least one of them must carry the full core block or import AGENTS.md with a
line "@AGENTS.md"; otherwise exit 1. Files above the repository can only be
seen on the machine where the check runs.

Codex reads AGENTS.override.md instead of AGENTS.md in the same directory. If
an AGENTS.override.md exists next to AGENTS.md or in any ancestor, it must
carry the full core block; otherwise exit 1.
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


def claude_shadow_files(consumer: Path) -> list[Path]:
    user_level = (Path.home() / ".claude" / "CLAUDE.md").resolve()
    found = []
    for directory in [consumer.resolve().parent, *consumer.resolve().parent.parents]:
        for name in CLAUDE_FILES:
            path = directory / name
            if path.is_file() and path.resolve() != user_level:
                found.append(path)
    return found


def claude_shadow_problem(consumer: Path, expected: str) -> str | None:
    present = claude_shadow_files(consumer)
    if not present:
        return None
    for path in present:
        text = path.read_text(encoding="utf-8")
        if any(line.strip() == "@AGENTS.md" for line in text.splitlines()) and path.parent == consumer.resolve().parent:
            return None
        try:
            if extract(text).strip() == expected:
                return None
        except ValueError:
            continue
    names = ", ".join(str(p) for p in present)
    return (f"{names} exists, so Claude Code does not read {consumer.name}; "
            f"add a line '@AGENTS.md' next to it or embed the full core")


def codex_override_problem(consumer: Path, expected: str) -> str | None:
    for directory in [consumer.resolve().parent, *consumer.resolve().parent.parents]:
        override = directory / "AGENTS.override.md"
        if not override.is_file():
            continue
        try:
            if extract(override.read_text(encoding="utf-8")).strip() == expected:
                continue
        except ValueError:
            pass
        return f"{override} replaces AGENTS.md for Codex but does not carry the full resident core"
    return None


def check(consumer: Path, core: Path) -> str | None:
    expected = core.read_text(encoding="utf-8").strip()
    try:
        found = extract(consumer.read_text(encoding="utf-8"))
    except ValueError as exc:
        return f"{consumer}: {exc}"
    if found.strip() != expected:
        return f"{consumer}: resident core differs from {core}; copy it verbatim"
    return claude_shadow_problem(consumer, expected) or codex_override_problem(consumer, expected)


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

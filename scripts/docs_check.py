#!/usr/bin/env python3
"""Docs check: rules in AGENTS.md files, the commit-message blocks that go
with them, ratchet numbers, and the scope-review record.

Rule line (one line in an AGENTS.md):

    - <area>.R<n> <one sentence: where, what must hold> [lint: <check>] | [review] (<source>)

Exception line (indented, directly under the rule it opens):

      - exception: <what> (approved: <who> <YYYY-MM-DD>; review: <YYYY-MM-DD>; <PR or plan>)

Commit-message lines (read from every commit in <base>..HEAD):

    Rules-read:
    - <id>: applies; <how the change keeps it>
    - <id>: n/a; <why>
    Raises: <number> <old> -> <new> - <reason>
    Rules-removed: <id> - <reason>

Everything project-specific comes from the repo's config file,
`.agent-protocols/docs-check.json` (see `DEFAULTS`). Run it from inside the
repo on a committed tree; `--base` defaults to `origin/main`.

Subcommands:
  tags                 rule and exception lines are well formed; ids unique; [lint: X] resolves
  paths                every backquoted path in a rule, exception or routing row exists
  claude-md            every CLAUDE.md is a link to, or the one-line import of, its AGENTS.md
  routes               every doc under the current-docs dir is in the root routing table
  rule-ids             no rule id at base is missing now, unless `Rules-removed:` says so
  rules-read           the commit messages account for every [review] rule on the touched paths
  numbers              ratchet numbers do not exceed their value at base, unless `Raises:` says so
  scope                a change that hits a trigger carries a matching scope-review record
  gated [--log FILE]   what the merge agent must stop on, and whose answer it needs
                       (log default: SCOPE_REVIEW_LOG, then scope_review.log in the config)
  exceptions [--today DATE]  open exceptions; those past their review date are marked
  report --range A..B  the numbers of the measuring table
  rules-for PATH...    every rule that governs PATH (root down to the nearest AGENTS.md)
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any

CONFIG_PATH = ".agent-protocols/docs-check.json"
DEFAULTS: dict[str, Any] = {
    "system_prefix": "sys",
    "plans_dir": "docs/agent_plans",
    "changes_subdir": "changes",
    "archive_subdir": "archive",
    "current_docs_dir": "docs/current",
    "routing_heading": "## Read routing",
    "own_checks": {
        "incident_fixes_only": "docs-check:incident-fixes-only",
        "ratchet": "docs-check:ratchet",
    },
    "incident_only_marker": None,  # defaults to "[lint: <own_checks.incident_fixes_only>]"
    "lint_sources": [],
    "ratchets": {},
    "decision_boundary_paths": [],
    "ledger_paths": [],
    "placement_questions": None,
    "scope_review": {},
}
RATCHET_KINDS = {"file_lines", "glob_count", "regex_lines", "dirs_without_agents_md"}
VERDICTS = ("go", "cut", "ask", "no")

RULE = re.compile(
    r"^- (?P<id>[a-z][a-z0-9_]*\.R\d+) (?P<text>.+?) "
    r"(?P<tag>\[lint: [^\]]+\]|\[review\]) \((?P<source>.+)\)\s*$"
)
RULE_LIKE = re.compile(r"^- (?P<id>[a-z][a-z0-9_]*\.R\d+)\b")
EXC = re.compile(
    r"^\s+- exception: (?P<what>.+?) \(approved: (?P<who>\S+) (?P<on>\d{4}-\d\d-\d\d); "
    r"review: (?P<review>\d{4}-\d\d-\d\d); (?P<ref>[^)]+)\)\s*$"
)
EXC_LIKE = re.compile(r"^\s+- exception:")
RULE_ID = r"[a-z][a-z0-9_]*\.R\d+"
MASTER = "the master (ledger entry) or the human"
HUMAN = "the human"


class ConfigError(Exception):
    pass


def load_config(root: Path, path: str | None = None) -> dict[str, Any]:
    cfg_file = Path(path) if path else root / CONFIG_PATH
    data: dict[str, Any] = {}
    if cfg_file.is_file():
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{cfg_file}: not valid JSON: {exc}") from exc
    elif path:
        raise ConfigError(f"{cfg_file}: no such config file")
    cfg = {**DEFAULTS, **data}
    cfg["own_checks"] = {**DEFAULTS["own_checks"], **data.get("own_checks", {})}
    if not cfg["incident_only_marker"]:
        cfg["incident_only_marker"] = f"[lint: {cfg['own_checks']['incident_fixes_only']}]"
    for name, spec in cfg["ratchets"].items():
        if spec.get("kind") not in RATCHET_KINDS:
            raise ConfigError(f"ratchet {name}: kind is one of {sorted(RATCHET_KINDS)}")
    for src in cfg["lint_sources"]:
        if src.get("kind") not in {"toml_list", "regex"}:
            raise ConfigError("lint source: kind is toml_list or regex")
    return cfg


def git_root(cwd: Path) -> Path:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True)
    if out.returncode != 0:
        raise ConfigError(f"{cwd}: not inside a git repository")
    return Path(out.stdout.strip())


def glob_match(path: str, pattern: str) -> bool:
    """Segment-wise fnmatch: `*` stays inside one directory, `**` spans any number."""
    def rec(p: list[str], g: list[str]) -> bool:
        if not g:
            return not p
        if g[0] == "**":
            return any(rec(p[i:], g[1:]) for i in range(len(p) + 1))
        return bool(p) and fnmatch.fnmatchcase(p[0], g[0]) and rec(p[1:], g[1:])
    return rec(path.split("/"), pattern.split("/"))


class Repo:
    def __init__(self, root: Path, cfg: dict[str, Any], base: str = "origin/main"):
        self.root, self.cfg, self.base = root, cfg, base
        self._cache: dict[Any, Any] = {}

    # git access -----------------------------------------------------------
    def git(self, *args: str) -> str:
        out = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        if out.returncode != 0:
            raise ConfigError(f"git {' '.join(args)}: {out.stderr.strip()}")
        return out.stdout

    def show(self, ref: str | None, path: str) -> str | None:
        if ref is None:
            p = self.root / path
            return p.read_text(encoding="utf-8") if p.is_file() else None
        out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=self.root, capture_output=True, text=True)
        return out.stdout if out.returncode == 0 else None

    def tracked(self, ref: str | None) -> list[str]:
        key = ("tracked", ref)
        if key not in self._cache:
            if ref is None:
                files = [f for f in self.git("ls-files", "-z").split("\0") if f]
                self._cache[key] = [f for f in files if (self.root / f).exists() or (self.root / f).is_symlink()]
            else:
                self._cache[key] = [f for f in self.git("ls-tree", "-r", "-z", "--name-only", ref).split("\0") if f]
        return self._cache[key]

    def agents_files(self, ref: str | None) -> dict[str, str]:
        key = ("agents", ref)
        if key not in self._cache:
            self._cache[key] = {
                n: self.show(ref, n) or "" for n in self.tracked(ref) if PurePosixPath(n).name == "AGENTS.md"
            }
        return self._cache[key]

    def message(self) -> str:
        """The messages of every commit in base..HEAD (one commit at READY; a merge commit on a PR checkout)."""
        if "message" not in self._cache:
            self._cache["message"] = self.git("log", "--format=%B", f"{self.base}..HEAD")
        return self._cache["message"]

    def name_status(self) -> list[tuple[str, str]]:
        """(status, path) for the change base...HEAD; a rename gives its new path."""
        if "ns" not in self._cache:
            rows = []
            for line in self.git("diff", "--name-status", "-M", f"{self.base}...HEAD").splitlines():
                parts = line.split("\t")
                rows.append((parts[0], parts[-1]))
            self._cache["ns"] = rows
        return self._cache["ns"]

    def changed(self) -> list[str]:
        return [p for _, p in self.name_status()]

    def changed_any_side(self) -> list[str]:
        """Every path the change adds, edits or removes, both sides of a rename."""
        return [p for p in self.git("diff", "--name-only", "--no-renames", f"{self.base}...HEAD").splitlines() if p]

    def added(self) -> list[str]:
        return [p for p in self.git("diff", "--name-only", "--no-renames", "--diff-filter=A", f"{self.base}...HEAD").splitlines() if p]

    # rules ------------------------------------------------------------------
    @staticmethod
    def parse(files: dict[str, str]) -> tuple[list[dict], list[dict]]:
        rules: list[dict] = []
        exceptions: list[dict] = []
        for name, text in files.items():
            last = None
            for no, line in enumerate(text.splitlines(), 1):
                m = RULE.match(line)
                if m:
                    last = m["id"]
                    rules.append({"file": name, "line": no, **m.groupdict()})
                    continue
                m = RULE_LIKE.match(line)
                if m:
                    last = m["id"]
                    rules.append({"file": name, "line": no, "id": last, "bad": line.strip()})
                    continue
                if EXC_LIKE.match(line):
                    e = EXC.match(line)
                    fields = e.groupdict() if e else {"bad": line.strip()}
                    exceptions.append({"file": name, "line": no, "rule": last, **fields})
                else:
                    last = None  # an exception sits directly under its rule or another exception
        return rules, exceptions

    def rules(self, ref: str | None) -> list[dict]:
        return self.parse(self.agents_files(ref))[0]

    def chain(self, path: str, ref: str | None = None) -> list[str]:
        """AGENTS.md files at REF from the root down to the directory of PATH (PATH itself
        when it is a directory)."""
        tracked = self.tracked(ref)
        p = path.strip("/")
        is_dir = path.endswith("/") or any(f.startswith(p + "/") for f in tracked)
        parts = PurePosixPath(p).parts if is_dir else PurePosixPath(p).parts[:-1]
        names = set(tracked)
        return [c for c in ("/".join([*parts[:i], "AGENTS.md"]) for i in range(len(parts) + 1)) if c in names]

    def governing(self, paths: list[str], only_review: bool = False, ref: str | None = None) -> dict[str, str]:
        out: dict[str, str] = {}
        files = self.agents_files(ref)
        for path in paths:
            for name in self.chain(path, ref):
                for r in self.parse({name: files.get(name, "")})[0]:
                    if "bad" not in r and (not only_review or r["tag"] == "[review]"):
                        out[r["id"]] = name
        return out

    def touched_governing(self, only_review: bool = False) -> dict[str, str]:
        """Rules that govern the change: the AGENTS.md chains of every touched path (both
        sides of a rename, deleted paths included) at HEAD, plus those at base, so a rule
        whose directory the change deletes still counts."""
        paths = self.changed_any_side()
        out = self.governing(paths, only_review)
        for rid, name in self.governing(paths, only_review, self.base).items():
            out.setdefault(rid, f"{name} at {self.base}")
        return out

    def rules_for_lines(self, paths: list[str]) -> list[tuple[str, list[str]]]:
        files = self.agents_files(None)
        out = []
        for path in paths:
            lines = []
            for name in self.chain(path):
                rs, es = self.parse({name: files.get(name, "")})
                for r in rs:
                    if "bad" in r:
                        continue
                    lines.append(f"{r['id']:9} {r['text']} {r['tag']} ({r['source']})   <- {name}")
                    for e in es:
                        if e["rule"] == r["id"] and "bad" not in e:
                            lines.append(f"{'':9}   exception: {e['what']} (approved: {e['who']} {e['on']}; "
                                         f"review: {e['review']}; {e['ref']})")
            out.append((path, lines))
        return out

    def existing_checks(self) -> set[str]:
        names = set(self.cfg["own_checks"].values())
        for src in self.cfg["lint_sources"]:
            text = self.show(None, src["file"])
            if text is None:
                continue
            prefix = src.get("prefix", "")
            if src["kind"] == "toml_list":
                node: Any = tomllib.loads(text)
                for part in src["table"].split("."):
                    node = node.get(part, {}) if isinstance(node, dict) else {}
                items = node.values() if isinstance(node, dict) else node
                for item in items:
                    if isinstance(item, dict):
                        value = item.get(src.get("key", "name")) or item.get(src.get("fallback_key", "name"))
                        if value:
                            names.add(prefix + str(value))
            else:
                for found in re.findall(src["pattern"], text, re.M):
                    names.add(prefix + (found if isinstance(found, str) else found[0]))
        return names

    # numbers ----------------------------------------------------------------
    def measure(self, ref: str | None) -> dict[str, int]:
        files = self.tracked(ref)
        out: dict[str, int] = {}
        for name, spec in self.cfg["ratchets"].items():
            kind = spec["kind"]
            if kind == "file_lines":
                text = self.show(ref, spec["file"])
                if text is not None:
                    out[name] = len(text.splitlines())
            elif kind == "glob_count":
                exclude = set(spec.get("exclude", []))
                out[name] = sum(1 for f in files if f not in exclude and glob_match(f, spec["glob"]))
            elif kind == "regex_lines":
                text = self.show(ref, spec["file"])
                if text is not None:
                    out[name] = count_regex_lines(text, spec["pattern"], spec.get("start"), spec.get("end"))
            elif kind == "dirs_without_agents_md":
                d = spec["dir"].strip("/")
                depth = len(PurePosixPath(d).parts)
                fileset = set(files)
                tops = {PurePosixPath(f).parts[depth] for f in files
                        if f.startswith(d + "/") and len(PurePosixPath(f).parts) > depth + 1}
                if any(f.startswith(d + "/") for f in files):
                    out[name] = sum(1 for t in tops if f"{d}/{t}/AGENTS.md" not in fileset)
        return out

    def raises(self) -> list[tuple[str, int, int, bool]]:
        """(name, at base, now, declared) for every number above its value at base."""
        before, now = self.measure(self.base), self.measure(None)
        declared = {k: (int(a), int(b)) for k, a, b in
                    re.findall(r"^Raises: (\S+) (\d+) -> (\d+) - \S", self.message(), re.M)}
        return [(k, before[k], v, declared.get(k) == (before[k], v))
                for k, v in now.items() if k in before and v > before[k]]

    # rule changes -----------------------------------------------------------
    def rule_changes(self) -> list[str]:
        """Ids whose rule line was added, removed or reworded, or under which an exception
        was added or changed (a later review date included). An exception that is only
        deleted (it ended) is not a change: the rule is back to what was decided."""
        if "rule_changes" in self._cache:
            return self._cache["rule_changes"]
        r0, e0 = self.parse(self.agents_files(self.base))
        r1, e1 = self.parse(self.agents_files(None))
        def line(r: dict) -> tuple:
            return (r.get("text"), r.get("tag"), r.get("source"), r.get("bad"))
        t0, t1 = {r["id"]: line(r) for r in r0}, {r["id"]: line(r) for r in r1}
        ids = {i for i in set(t0) | set(t1) if t0.get(i) != t1.get(i)}
        def key(e: dict) -> tuple:
            return (e["rule"], e.get("what", e.get("bad")), e.get("who"), e.get("on"), e.get("review"), e.get("ref"))
        old = {key(e) for e in e0}
        ids |= {e["rule"] for e in e1 if e["rule"] and key(e) not in old}
        self._cache["rule_changes"] = sorted(ids)
        return self._cache["rule_changes"]

    def rule_moves(self) -> list[str]:
        """Ids whose line is unchanged but now sits in another AGENTS.md. A whole file that
        only moved with its directory (old file gone, new file new, same rule ids) is a
        rename, not a move."""
        f0, f1 = self.agents_files(self.base), self.agents_files(None)
        r0, r1 = self.parse(f0)[0], self.parse(f1)[0]
        w0 = {r["id"]: r["file"] for r in r0}
        w1 = {r["id"]: r["file"] for r in r1}
        ids_in = lambda rs, f: {r["id"] for r in rs if r["file"] == f}  # noqa: E731
        changed_ids = set(self.rule_changes())
        out = []
        for i, was in w0.items():
            now = w1.get(i)
            if not now or now == was or i in changed_ids:
                continue
            renamed = was not in f1 and now not in f0 and ids_in(r0, was) == ids_in(r1, now)
            if not renamed:
                out.append(f"{i} ({was} -> {now})")
        return sorted(out)

    def ended_exceptions(self) -> list[str]:
        e0 = self.parse(self.agents_files(self.base))[1]
        e1 = self.parse(self.agents_files(None))[1]
        now = {(e["rule"], e.get("what", e.get("bad"))) for e in e1}
        return sorted(f"{e['rule']}: {e.get('what', e.get('bad'))}" for e in e0
                      if (e["rule"], e.get("what", e.get("bad"))) not in now)

    # scope ------------------------------------------------------------------
    def changes_prefix(self) -> str:
        return f"{self.cfg['plans_dir'].strip('/')}/{self.cfg['changes_subdir'].strip('/')}/"

    def triggers(self) -> list[str]:
        hits = []
        ids = self.rule_changes()
        if ids:
            hits.append(f"a rule or an exception changed ({', '.join(ids)})")
        moved = self.rule_moves()
        if moved:
            hits.append(f"a rule moved to another file ({', '.join(moved)})")
        for key, was, value, _ in self.raises():
            hits.append(f"{key} goes up ({was} -> {value})")
        prefix = self.changes_prefix()
        if any(f.startswith(prefix) and PurePosixPath(f).name == "proposal.md" for f in self.added()):
            hits.append("a new plan")
        marker = self.cfg["incident_only_marker"]
        files = self.agents_files(None)
        for status, path in self.name_status():
            if status == "R100" or PurePosixPath(path).name == "AGENTS.md":
                continue
            for name in self.chain(path):
                if marker in files.get(name, ""):
                    hits.append(f"{path} is under {name}, which is marked incident-fixes-only")
                    break
        return hits

    def records(self) -> list[tuple[str, dict[str, str], str]]:
        out = []
        prefix = self.changes_prefix()
        for rec in self.changed():
            if (not rec.startswith(prefix) or PurePosixPath(rec).name != "scope-review.md"
                    or not (self.root / rec).is_file()):
                continue
            text = (self.root / rec).read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
            head = dict(re.findall(r"^(\w+): *(.*?)\s*$", m[1], re.M)) if m else {}
            out.append((rec, head, text))
        return out


def count_regex_lines(text: str, pattern: str, start: str | None, end: str | None) -> int:
    rx = re.compile(pattern)
    inside = start is None
    count = 0
    for line in text.splitlines():
        if start is not None and not inside:
            if start in line:
                inside = True
            continue
        if start is not None and end is not None and line.strip().startswith(end):
            inside = False
            continue
        if rx.search(line):
            count += 1
    return count


def sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


# commands ---------------------------------------------------------------------

def emit(bad: list[str], ok: str) -> int:
    print("\n".join(bad) if bad else ok)
    return 1 if bad else 0


def cmd_rules_for(repo: Repo, paths: list[str]) -> int:
    for path, lines in repo.rules_for_lines(paths):
        print(f"[rules: {path}]")
        for line in lines:
            print(line)
    return 0


def cmd_tags(repo: Repo) -> int:
    checks, seen, bad = repo.existing_checks(), {}, []
    rs, es = repo.parse(repo.agents_files(None))
    sources = ", ".join(s["file"] for s in repo.cfg["lint_sources"]) or "no lint sources configured"
    for r in rs:
        where = f"{r['file']}:{r['line']}"
        if "bad" in r:
            bad.append(f"{where} {r['id']}: a rule line needs `[lint: <check>]` or `[review]`, then `(source)`")
            continue
        if r["id"] in seen:
            bad.append(f"{where} {r['id']}: the same id is already at {seen[r['id']]}; one rule, one place")
        seen.setdefault(r["id"], where)
        if r["tag"].startswith("[lint:"):
            name = r["tag"][len("[lint:"):-1].strip()
            if name not in checks:
                bad.append(f"{where} {r['id']}: tagged {r['tag']}, but no check of that name exists "
                           f"(looked in {sources}, and the docs check's own checks). "
                           "Restore the check, or retag the rule [review], or delete the rule.")
    for e in es:
        if "bad" in e:
            bad.append(f"{e['file']}:{e['line']}: an exception line reads "
                       "`- exception: <what> (approved: <who> <date>; review: <date>; <PR or plan>)`")
        elif e["rule"] is None:
            bad.append(f"{e['file']}:{e['line']}: an exception sits under the rule it opens; no rule line above this one")
    return emit(bad, f"tags: ok ({len(seen)} rules, {len(es)} exceptions)")


def cmd_paths(repo: Repo) -> int:
    files = set(repo.tracked(None))
    known = files | {str(p) for f in files for p in PurePosixPath(f).parents}
    bad = []
    for name, text in repo.agents_files(None).items():
        here = PurePosixPath(name).parent
        for no, line in enumerate(text.splitlines(), 1):
            if not (RULE_LIKE.match(line) or EXC_LIKE.match(line) or line.lstrip().startswith("| `")):
                continue
            for quoted in re.findall(r"`([^`\s]+/[^`\s]*)`", line):
                if "://" in quoted or any(c in quoted for c in "*<>{}"):
                    continue
                p = quoted.strip("/")
                local = os.path.normpath(str(here / p))
                if not ({p, local} & known):
                    bad.append(f"{name}:{no}: `{quoted}` is named here and is not in the repo. Fix the path, or the line.")
    return emit(bad, "paths: ok")


def cmd_claude_md(repo: Repo) -> int:
    bad = []
    for name in repo.tracked(None):
        if PurePosixPath(name).name != "CLAUDE.md":
            continue
        p = repo.root / name
        if p.is_symlink():
            if PurePosixPath(os.readlink(p)).name == "AGENTS.md":
                continue
        elif p.read_text(encoding="utf-8").strip() == "@AGENTS.md":
            continue
        bad.append(f"{name}: must be a link to AGENTS.md or the single line `@AGENTS.md`; rules live in AGENTS.md only")
    return emit(bad, "claude-md: ok")


def cmd_routes(repo: Repo) -> int:
    current_dir = repo.cfg["current_docs_dir"].strip("/")
    current = {f for f in repo.tracked(None) if f.startswith(current_dir + "/") and f.endswith(".md")}
    if not current:
        print(f"routes: ok (no {current_dir}/ directory)")
        return 0
    heading = repo.cfg["routing_heading"]
    root = repo.show(None, "AGENTS.md") or ""
    section = root.split(heading, 1)[1].split("\n## ", 1)[0] if heading in root else ""
    listed = set(re.findall(r"^\| `([^`]+)` \|", section, re.M))
    bad = [f"{f}: a current doc that the routing table in AGENTS.md does not list; add a row saying when "
           f"to read it, or move the file out of {current_dir}/" for f in sorted(current - listed)]
    return emit(bad, f"routes: ok ({len(listed)} rows, {len(current)} current docs)")


def cmd_rule_ids(repo: Repo) -> int:
    before = {r["id"]: r["file"] for r in repo.rules(repo.base)}
    after = {r["id"] for r in repo.rules(None)}
    removed = set(re.findall(rf"^Rules-removed: ({RULE_ID}) - \S", repo.message(), re.M))
    lost = sorted(set(before) - after - removed)
    bad = [f"{rid}: was in {before[rid]} at {repo.base}, is in no AGENTS.md now. Move it with its code, "
           "or add a line `Rules-removed: <id> - <reason>` to the commit message." for rid in lost]
    return emit(bad, f"rule-ids: ok ({len(before)} at {repo.base}, {len(after)} now, {len(removed)} declared removed)")


def stated_rules(message: str) -> dict[str, str]:
    stated: dict[str, str] = {}
    for block in message.split("Rules-read:")[1:]:
        for rid, word in re.findall(rf"^- ({RULE_ID}): (applies|n/a); *\S", block, re.M):
            stated[rid] = word
    return stated


def cmd_rules_read(repo: Repo) -> int:
    expected = repo.touched_governing(only_review=True)
    stated = stated_rules(repo.message())
    missing = sorted(set(expected) - set(stated))
    bad = [f"{rid} ({expected[rid]}) governs a file this change touches, and the commit message does not account "
           f"for it. Add under `Rules-read:` a line `- {rid}: applies; <how the change keeps it>` or "
           f"`- {rid}: n/a; <why>`." for rid in missing]
    return emit(bad, f"rules-read: ok ({len(expected)} review-only rules govern the touched paths, all accounted for)")


def cmd_numbers(repo: Repo) -> int:
    before, now, bad = repo.measure(repo.base), repo.measure(None), []
    for key, was, value, declared in repo.raises():
        if declared:
            print(f"{key}: {was} at {repo.base}, {value} now, declared in the commit message. The merge agent will stop on it.")
        else:
            bad.append(f"{key}: {was} at {repo.base}, {value} now. This number only goes down. Undo the increase, "
                       f"or add a line `Raises: {key} {was} -> {value} - <reason>` to the commit message "
                       "(the merge agent then stops and asks).")
    for key, value in now.items():
        if key in before and value < before[key]:
            print(f"{key}: {before[key]} at {repo.base}, {value} now. Nothing to do: once this merges, "
                  f"{value} is the number to beat.")
    return emit(bad, f"numbers: ok {now}")


def cmd_scope(repo: Repo) -> int:
    hits = repo.triggers()
    if not hits:
        print("scope: no trigger, no record needed")
        return 0
    recs = repo.records()
    if not recs:
        print("This change needs a scope review before merge, because:")
        print("\n".join(f"  - {h}" for h in hits))
        print(f"Write {repo.changes_prefix()}<name>/proposal.md, run the scope review on it "
              "(it writes scope-review.md next to it) and commit both.")
        return 1
    bad = []
    need = set(repo.touched_governing())
    for rec, head, text in recs:
        proposal = (repo.root / rec).with_name("proposal.md")
        verdict = head.get("verdict")
        if verdict == "cut":
            bad.append(f"{rec}: verdict is `cut`. Take the listed parts out of the proposal and run the review again; "
                       "only `go`, or `ask` with an answer, can merge.")
        elif verdict == "no":
            bad.append(f"{rec}: verdict is `no`; this change does not merge.")
        elif verdict not in VERDICTS:
            bad.append(f"{rec}: verdict is `{verdict}`; it is one of {', '.join(VERDICTS)}")
        if not proposal.is_file():
            bad.append(f"{rec}: no proposal.md next to it; the record is about a proposal")
        elif head.get("proposal_sha") != sha12(proposal.read_bytes()):
            bad.append(f"{rec}: the proposal changed after the review (proposal_sha does not match); review again")
        answered = set(re.findall(rf"^- ({RULE_ID}): \S", text, re.M))
        if need - answered:
            bad.append(f"{rec}: no line for {sorted(need - answered)}; the review must say something about every "
                       "rule that governs the touched paths")
    asks = [rec for rec, head, _ in recs if head.get("verdict") == "ask"]
    if bad:
        return emit(bad, "")
    if asks:
        print(f"scope: record present, verdict `ask` ({asks[0]}). The check passes; the merge agent stops until "
              "the question is answered.")
    else:
        print(f"scope: ok ({len(hits)} trigger(s), record {recs[0][0]})")
    return 0


def cmd_gated(repo: Repo, log: str | None) -> int:
    sys_prefix = repo.cfg["system_prefix"] + "."
    items: list[str] = []
    for rid in repo.rule_changes():
        who = HUMAN if rid.startswith(sys_prefix) else MASTER
        items.append(f"rule {rid} or an exception under it changed -> needs the answer of {who}")
    for m in repo.rule_moves():
        items.append(f"rule {m} moved, wording unchanged -> needs the answer of {MASTER}")
    for key, was, value, _ in repo.raises():
        items.append(f"{key} goes up {was} -> {value} -> needs the answer of {MASTER}")
    touched = set(repo.changed_any_side())
    for label, key in (("the decision-boundary file", "decision_boundary_paths"), ("the authority ledger", "ledger_paths")):
        for path in repo.cfg[key]:
            if path in touched:
                items.append(f"{path}: {label} changed -> needs the answer of {HUMAN}")
    log = log or os.environ.get("SCOPE_REVIEW_LOG") or (repo.cfg.get("scope_review") or {}).get("log")
    logged: set[str] | None = None
    if log:
        log_path = Path(log).expanduser()
        logged = set(log_path.read_text(encoding="utf-8").split()) if log_path.is_file() else set()
    records = repo.records()
    if records and logged is None:
        items.append("scope-review records changed and no run log is set (--log, SCOPE_REVIEW_LOG or "
                     "scope_review.log in the config), so nobody checked they came from the runner -> "
                     "stop until checked with the log")
    for rec, head, text in records:
        if head.get("verdict") == "ask":
            conflicts = re.findall(rf"^- ({RULE_ID}): conflict", text, re.M)
            who = HUMAN if any(c.startswith(sys_prefix) for c in conflicts) else MASTER
            items.append(f"{rec}: verdict ask (conflict with {', '.join(conflicts) or 'no rule named'}) "
                         f"-> needs the answer of {who}")
            for label in ("Question", "Cut"):
                found = re.search(rf"^{label}: (.+)$", text, re.M)
                if found and found[1].strip().lower() != "nothing":
                    items.append(f"    {label.lower()} to answer: {found[1].strip()[:150]}")
        if logged is not None:
            digest = sha12(text.encode("utf-8"))
            if digest not in logged:
                items.append(f"{rec}: this record ({digest}) is not in the reviewer's run log; it was not written "
                             "by the scope-review runner -> send back to the author")
    for e in repo.ended_exceptions():
        print(f"note, no stop: an exception ended ({e})")
    if items:
        print("gated:\n" + "\n".join(f"  - {i}" if not i.startswith("    ") else f"  {i}" for i in items))
    else:
        print("gated: nothing to stop on")
    return 0


def cmd_exceptions(repo: Repo, today: str | None) -> int:
    today = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    es = sorted((e for e in repo.parse(repo.agents_files(None))[1] if "bad" not in e), key=lambda e: e["review"])
    due = 0
    for e in es:
        overdue = e["review"] <= today
        due += overdue
        mark = "OVERDUE" if overdue else "       "
        print(f"{mark} review {e['review']}  {e['rule']!s:8} {e['what']}  (approved {e['who']} {e['on']}; "
              f"{e['ref']})  <- {e['file']}:{e['line']}")
    print(f"exceptions: {len(es)} open, {due} past their review date as of {today}")
    return 0


def cmd_report(repo: Repo, rng: str) -> int:
    rs = [r for r in repo.rules(None) if "bad" not in r]
    lint = sum(1 for r in rs if r["tag"].startswith("[lint"))
    print(f"rules: {len(rs)} ({lint} program-checked, {len(rs) - lint} review-only)")
    seen: dict[str, list[int]] = {r["id"]: [0, 0] for r in rs if r["tag"] == "[review]"}
    commits = lines = 0
    for body in repo.git("log", "--format=%B%x00", rng).split("\0"):
        if "Rules-read:" not in body:
            continue
        commits += 1
        for rid, word in stated_rules(body).items():
            lines += 1
            seen.setdefault(rid, [0, 0])[0 if word == "applies" else 1] += 1
    print(f"commits with a Rules-read block in {rng}: {commits}; lines in those blocks: {lines}")
    print("review-only rule   governed a change   said applies   said n/a")
    for rid, (a, n) in sorted(seen.items()):
        print(f"{rid:18} {a + n:17} {a:14} {n:10}")
    plans = repo.cfg["plans_dir"].strip("/") + "/"
    verdicts: dict[str, int] = {}
    for f in repo.tracked(None):
        if f.startswith(plans) and PurePosixPath(f).name == "scope-review.md":
            m = re.search(r"^verdict: *(\S+)", repo.show(None, f) or "", re.M)
            v = m[1] if m else "?"
            verdicts[v] = verdicts.get(v, 0) + 1
    print(f"scope-review verdicts: {dict(sorted(verdicts.items()))}")
    print(f"measured numbers now: {repo.measure(None)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base", default="origin/main", help="the ref to compare with (default origin/main)")
    common.add_argument("--config", help=f"config file (default <repo>/{CONFIG_PATH})")
    parser = argparse.ArgumentParser(prog="docs_check.py", description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("tags", "paths", "claude-md", "routes", "rule-ids", "rules-read", "numbers", "scope"):
        sub.add_parser(name, parents=[common])
    sub.add_parser("gated", parents=[common]).add_argument("--log", help="the scope-review runner's log of record shas")
    sub.add_parser("exceptions", parents=[common]).add_argument("--today", help="YYYY-MM-DD (default: today, UTC)")
    sub.add_parser("report", parents=[common]).add_argument("--range", required=True, help="a git range, A..B")
    sub.add_parser("rules-for", parents=[common]).add_argument("paths", nargs="+")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = git_root(Path.cwd())
        repo = Repo(root, load_config(root, args.config), args.base)
        commands = {
            "tags": lambda: cmd_tags(repo),
            "paths": lambda: cmd_paths(repo),
            "claude-md": lambda: cmd_claude_md(repo),
            "routes": lambda: cmd_routes(repo),
            "rule-ids": lambda: cmd_rule_ids(repo),
            "rules-read": lambda: cmd_rules_read(repo),
            "numbers": lambda: cmd_numbers(repo),
            "scope": lambda: cmd_scope(repo),
            "gated": lambda: cmd_gated(repo, args.log),
            "exceptions": lambda: cmd_exceptions(repo, args.today),
            "report": lambda: cmd_report(repo, args.range),
            "rules-for": lambda: cmd_rules_for(repo, args.paths),
        }
        return commands[args.cmd]()
    except ConfigError as exc:
        print(f"docs_check.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

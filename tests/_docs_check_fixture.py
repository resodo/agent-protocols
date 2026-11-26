"""A tiny git repo laid out the way the docs check expects, for the docs-check tests.

Neutral names only: an app with `sources/` (data rules) and an incident-only
`sources/vendor_files/` directory, a fetch service named in the system rules,
an import-linter contract, a light-checks script and a plans directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_CHECK = REPO_ROOT / "scripts" / "docs_check.py"
RUNNER = REPO_ROOT / "scope-review" / "run_scope_review.py"

ROOT_AGENTS = """# Example repo

## System rules

- sys.R1 Outbound fetching lives in the fetch service; this repo adds no fetch code. [review] (decided 2026-11-09, data plan)
- sys.R2 The app's top-level packages import only the layers below them. [lint: importlinter:layers] (decided 2026-11-01, layout)
- sys.R3 Each data set has one writer; changing a writer or an entry rule needs the human. [review] (#100)

## Read routing

| Read | Before you write or review |
|---|---|
| `docs/current/data.md` | anything under `app/sources/`, or anything that fetches from outside |
"""

SOURCES_AGENTS = """# sources

- data.R1 Readers check time eligibility first, then choose the vendor. [review] (decided 2026-11-09, data plan 4.3)
"""

VENDOR_AGENTS = """# sources/vendor_files

- data.R2 This directory takes live-incident fixes only; every other change goes to the fetch service. [lint: docs-check:incident-fixes-only] (decided 2026-11-09; refines sys.R1)
"""

PYPROJECT = """[project]
name = "example"

[[tool.importlinter.contracts]]
id = "layers"
name = "Layers"
type = "layers"
layers = ["app.api", "app.nodes", "app.sources"]
ignore_imports = [
  "app.sources.a -> app.nodes.b",
  "app.sources.c -> app.nodes.d",
  "app.sources.e -> app.api.f",
]

[[tool.importlinter.contracts]]
name = "api-only"
type = "forbidden"
"""

LIGHT_CHECKS = """#!/usr/bin/env bash
check "lint" ruff check .
check "format" ruff format --check .
"""

CONFIG = {
    "lint_sources": [
        {"kind": "toml_list", "file": "pyproject.toml", "table": "tool.importlinter.contracts",
         "key": "id", "fallback_key": "name", "prefix": "importlinter:"},
        {"kind": "regex", "file": "scripts/light_checks.sh", "pattern": '^\\s*check "([^"]+)"', "prefix": "light:"},
    ],
    "ratchets": {
        "root_agents_md_lines": {"kind": "file_lines", "file": "AGENTS.md"},
        "layer_exemption_lines": {"kind": "regex_lines", "file": "pyproject.toml",
                                  "pattern": '^\\s*"app\\.[^"]+ -> [^"]+",?', "start": "ignore_imports = [", "end": "]"},
        "top_modules_without_agents_md": {"kind": "dirs_without_agents_md", "dir": "app"},
        "plan_index_lines": {"kind": "file_lines", "file": "docs/agent_plans/README.md"},
        "plans_outside_changes": {"kind": "glob_count", "glob": "docs/agent_plans/*",
                                  "exclude": ["docs/agent_plans/README.md"]},
    },
    "decision_boundary_paths": [".agent-protocols/decision-boundary.md"],
    "ledger_paths": [".agent-protocols/authority-ledger.md"],
    "placement_questions": "docs/placement.md",
}

PLACEMENT = """1. Is it about reading what the fetch service stored? `app/sources/<source>/`.
2. Is it a fixed step that runs on a schedule? `app/nodes/<node>/`.
"""

EXC_SEARCH = ("  - exception: Two web search clients live here while the main provider is down "
              "(approved: human 2026-11-22; review: 2026-11-30; docs/agent_plans/changes/search-vendor)")
EXC_RESULTS = ("  - exception: The results source is fetched here until the fetch service moves it "
               "(approved: human 2026-11-22; review: 2026-12-15; docs/agent_plans/changes/results-source)")

ALL_RULES = ["sys.R1", "sys.R2", "sys.R3", "data.R1", "data.R2"]


def sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


class Fixture:
    def __init__(self, tmp: str):
        self.tmp = Path(tmp)
        self.root = self.tmp / "repo"
        self.root.mkdir()
        home = self.tmp / "home"
        home.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.invalid",
        }
        for key in ("SCOPE_REVIEW_MODEL", "SCOPE_REVIEW_EFFORT", "SCOPE_REVIEW_LOG"):
            self.env.pop(key, None)
        self.git("init", "-q", "-b", "main")
        files = {
            "AGENTS.md": ROOT_AGENTS,
            "app/sources/AGENTS.md": SOURCES_AGENTS,
            "app/sources/__init__.py": "",
            "app/sources/vendor_files/AGENTS.md": VENDOR_AGENTS,
            "app/sources/vendor_files/reader.py": "def read():\n    return None\n",
            "app/nodes/__init__.py": "",
            "app/api/__init__.py": "",
            "pyproject.toml": PYPROJECT,
            "scripts/light_checks.sh": LIGHT_CHECKS,
            "docs/current/data.md": "# Data layer: how it works now\n",
            "docs/placement.md": PLACEMENT,
            "docs/agent_plans/README.md": "# Plan index\n- old one\n- old two\n",
            "docs/agent_plans/2026-10-01_old_one_plan.md": "# old one\n",
            "docs/agent_plans/2026-10-02_old_two_plan.md": "# old two\n",
            ".agent-protocols/docs-check.json": json.dumps(CONFIG, indent=2) + "\n",
            ".agent-protocols/decision-boundary.md": "# Decision boundary\n",
            ".agent-protocols/authority-ledger.md": "# Authority ledger\n",
        }
        for rel, text in files.items():
            self.write(rel, text)
        self.commit("base")
        self.mark_main()

    # files and git ---------------------------------------------------------
    def write(self, rel: str, text: str) -> None:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def read(self, rel: str) -> str:
        return (self.root / rel).read_text(encoding="utf-8")

    def append(self, rel: str, text: str) -> None:
        self.write(rel, self.read(rel) + text)

    def replace(self, rel: str, old: str, new: str) -> None:
        text = self.read(rel)
        assert old in text, (rel, old)
        self.write(rel, text.replace(old, new, 1))

    def insert_after(self, rel: str, prefix: str, *lines: str) -> None:
        rows = self.read(rel).splitlines()
        i = next(n for n, line in enumerate(rows) if line.startswith(prefix))
        rows[i + 1:i + 1] = list(lines)
        self.write(rel, "\n".join(rows) + "\n")

    def git(self, *args: str) -> str:
        out = subprocess.run(["git", *args], cwd=self.root, env=self.env, capture_output=True, text=True)
        if out.returncode != 0:
            raise AssertionError(f"git {args}: {out.stderr}")
        return out.stdout

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)

    def amend(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "--amend", "--allow-empty", "-m", message)

    def mark_main(self) -> None:
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def branch(self, name: str) -> None:
        self.git("checkout", "-q", "-b", name)

    # running ---------------------------------------------------------------
    def check(self, *args: str) -> tuple[int, str]:
        out = subprocess.run([sys.executable, str(DOCS_CHECK), *args], cwd=self.root, env=self.env,
                             capture_output=True, text=True)
        return out.returncode, out.stdout + out.stderr

    def runner(self, *args: str, env: dict[str, str] | None = None) -> tuple[int, str, str]:
        out = subprocess.run([sys.executable, str(RUNNER), *args], cwd=self.root, env={**self.env, **(env or {})},
                             capture_output=True, text=True)
        return out.returncode, out.stdout, out.stderr

    # scope-review helpers ----------------------------------------------------
    def proposal(self, name: str, touches: list[str], extra: str = "") -> str:
        rel = f"docs/agent_plans/changes/{name}/proposal.md"
        self.write(rel, "\n".join([
            f"# Proposal: {name}", "", f"Branch: {name}", "",
            "## Intent", "Since 2026-11-18 two-column tables fail to parse; 3 records have no text.", "",
            "## Scope", "Repair the table reader. No new fetch path." + extra, "",
            "## Touches", *[f"- `{t}`" for t in touches], "",
            "## Rule changes", "none", "",
        ]))
        return rel

    def record(self, name: str, verdict: str = "go", rules: list[str] | None = None,
               words: dict[str, str] | None = None, tail: list[str] | None = None) -> str:
        proposal = self.root / f"docs/agent_plans/changes/{name}/proposal.md"
        words = words or {}
        body = [f"- {r}: {words.get(r, 'holds')}. One sentence." for r in (ALL_RULES if rules is None else rules)]
        text = "\n".join([
            "---", f"verdict: {verdict}", "reviewer: test:model", "run_id: sr-20261126T000000Z-abcd",
            f"proposal_sha: {sha12(proposal.read_bytes())}", "---", *body,
            *(tail or ["Owner: data.R2", "Cut: nothing"]),
        ]) + "\n"
        rel = f"docs/agent_plans/changes/{name}/scope-review.md"
        self.write(rel, text)
        return rel

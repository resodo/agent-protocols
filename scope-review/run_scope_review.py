#!/usr/bin/env python3
"""Scope-review runner: one fresh, tool-less model session reviews one proposal.

    run_scope_review.py <name> [--repo DIR] [--config FILE] [--dry-run] [--timeout-sec N]

It reads `<plans>/<changes>/<name>/proposal.md` (directories from the repo's
docs-check config), collects the rules that govern the paths listed under the
proposal's `## Touches` heading (the docs check's `rules-for`), adds the
placement-questions file the config names, and gives the model exactly that
plus `reviewer_prompt.md`. The model runs from a new empty temp directory with
the prompt on stdin, so it sees no repo. The runner then writes
`scope-review.md` next to the proposal and appends the record's sha to the run
log, which the merge agent passes to `docs_check.py gated --log`.

Configuration (env wins over the config's `scope_review` object):
  SCOPE_REVIEW_MODEL   / "model"    model name (default gpt-6-sol)
  SCOPE_REVIEW_EFFORT  / "effort"   reasoning effort (default high)
  SCOPE_REVIEW_LOG     / "log"      run-log file; must be outside the repo
                         "command"  argv list; {model}, {effort}, {output} are filled in
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPT_FILE = HERE / "reviewer_prompt.md"
DOCS_CHECK_FILE = HERE.parent / "scripts" / "docs_check.py"
DEFAULT_MODEL = "gpt-6-sol"
DEFAULT_EFFORT = "high"
# Codex non-interactive, prompt on stdin (the structured-review runner's `exec -`
# pattern). Every tool family the CLI offers is switched off (shell, code mode,
# apps, plugins, sub-agents, goals, images, web search), the user config (and
# with it any MCP servers) is not loaded, the sandbox is read-only and the
# session is not saved. Checked against codex-cli 0.169: asked to run `ls /`,
# read a file, search the web and start a sub-agent, the model could do none.
DEFAULT_COMMAND = [
    "codex", "exec", "-",
    "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules",
    "--sandbox", "read-only",
    "--disable", "shell_tool", "--disable", "unified_exec", "--disable", "code_mode_host",
    "--disable", "apps", "--disable", "plugins", "--disable", "multi_agent",
    "--disable", "goals", "--disable", "image_generation", "--disable", "view_image",
    "-c", "web_search=disabled",
    "-m", "{model}", "-c", "model_reasoning_effort={effort}",
    "--color", "never", "--output-last-message", "{output}",
]


def load_docs_check():
    spec = importlib.util.spec_from_file_location("docs_check", DOCS_CHECK_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("docs_check", module)
    spec.loader.exec_module(module)
    return module


def touches(proposal: str) -> list[str]:
    m = re.search(r"^## Touches[ \t]*\n(.*?)(?=^## |\Z)", proposal, re.S | re.M)
    paths = []
    for line in (m[1] if m else "").splitlines():
        item = re.match(r"^\s*[-*] +(.+)$", line)
        if not item:
            continue
        quoted = re.search(r"`([^`]+)`", item[1])
        paths.append(quoted[1] if quoted else item[1].split()[0])
    return paths


def answer_body(text: str) -> tuple[str | None, list[str]]:
    """The verdict and the lines after it, from the first `verdict:` line on."""
    lines = [l for l in text.splitlines() if l.strip() != "```"]
    for i, line in enumerate(lines):
        m = re.match(r"^verdict:\s*(\S+)\s*$", line.strip())
        if m:
            return m[1], [l.rstrip() for l in lines[i + 1:]]
    return None, []


def fail(message: str) -> int:
    print(f"run_scope_review.py: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one scope review on a proposal.")
    parser.add_argument("name", help="the change name: <plans>/<changes>/<name>/proposal.md")
    parser.add_argument("--repo", default=".", help="a path inside the repo (default: the current directory)")
    parser.add_argument("--config", help="docs-check config file (default <repo>/.agent-protocols/docs-check.json)")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt and the command; call nothing")
    parser.add_argument("--timeout-sec", type=int, default=1800)
    args = parser.parse_args(argv)

    dc = load_docs_check()
    try:
        root = dc.git_root(Path(args.repo).resolve())
        cfg = dc.load_config(root, args.config)
    except dc.ConfigError as exc:
        return fail(str(exc))
    repo = dc.Repo(root, cfg)
    sr = cfg.get("scope_review") or {}

    change_dir = root / repo.changes_prefix() / args.name
    proposal_file = change_dir / "proposal.md"
    if not proposal_file.is_file():
        return fail(f"{proposal_file.relative_to(root)}: no such proposal")
    proposal_bytes = proposal_file.read_bytes()  # the sha is of exactly what the reviewer read
    proposal = proposal_bytes.decode("utf-8")
    paths = touches(proposal)
    if not paths:
        return fail(f"{proposal_file.relative_to(root)}: no paths listed under `## Touches`")

    rules: list[str] = []
    for _, lines in repo.rules_for_lines(paths):
        rules.extend(l for l in lines if l not in rules)
    sections = [PROMPT_FILE.read_text(encoding="utf-8").rstrip(),
                "## Rules that govern the touched paths\n" + ("\n".join(rules) or "(none)")]
    placement = cfg.get("placement_questions")
    if placement:
        placement_file = root / placement
        if not placement_file.is_file():
            return fail(f"{placement}: the placement-questions file the config names does not exist")
        sections.append(f"## Placement questions ({placement})\n" + placement_file.read_text(encoding="utf-8").rstrip())
    sections.append("## The proposal\n" + proposal.rstrip())
    prompt = "\n\n".join(sections) + "\n"

    model = os.environ.get("SCOPE_REVIEW_MODEL") or sr.get("model") or DEFAULT_MODEL
    effort = os.environ.get("SCOPE_REVIEW_EFFORT") or sr.get("effort") or DEFAULT_EFFORT
    template = sr.get("command") or DEFAULT_COMMAND
    log_value = os.environ.get("SCOPE_REVIEW_LOG") or sr.get("log")

    if args.dry_run:
        filled = [a.replace("{model}", model).replace("{effort}", effort).replace("{output}", "<output file>")
                  for a in template]
        print(prompt)
        print("command: " + " ".join(filled))
        print(f"log: {log_value or '(not set)'}")
        return 0

    if not log_value:
        return fail("no run log: set SCOPE_REVIEW_LOG or scope_review.log in the config (a file outside the repo)")
    log = Path(log_value).expanduser().resolve()
    if log == root or root in log.parents:
        return fail(f"{log}: the run log must be outside the repo")

    started = dt.datetime.now(dt.timezone.utc)
    with tempfile.TemporaryDirectory(prefix="scope-review-") as tmp_name:
        tmp = Path(tmp_name).resolve()  # the CLI refuses a non-normalized output path
        empty = tmp / "empty"
        empty.mkdir()
        output = tmp / "last-message.txt"
        command = [a.replace("{model}", model).replace("{effort}", effort).replace("{output}", str(output))
                   for a in template]
        try:
            run = subprocess.run(command, input=prompt, cwd=empty, capture_output=True, text=True,
                                 timeout=args.timeout_sec)
        except FileNotFoundError:
            return fail(f"{command[0]}: command not found")
        except subprocess.TimeoutExpired:
            return fail(f"the reviewer did not answer within {args.timeout_sec}s")
        if run.returncode != 0:
            return fail(f"the reviewer command exited {run.returncode}:\n{run.stderr[-2000:]}")
        answer = output.read_text(encoding="utf-8") if output.is_file() and output.stat().st_size else run.stdout
    seconds = int((dt.datetime.now(dt.timezone.utc) - started).total_seconds())

    verdict, body = answer_body(answer)
    if verdict not in dc.VERDICTS:
        print(answer, file=sys.stderr)
        return fail(f"the answer has no `verdict: <{'|'.join(dc.VERDICTS)}>` line; no record written")
    run_id = f"sr-{started:%Y%m%dT%H%M%SZ}-{hashlib.sha256(chr(10).join(body).encode()).hexdigest()[:4]}"
    record = "\n".join([
        "---",
        f"verdict: {verdict}",
        f"reviewer: {Path(command[0]).name}:{model}",
        f"run_id: {run_id}",
        f"proposal_sha: {dc.sha12(proposal_bytes)}",
        "---",
        *body,
    ]).rstrip("\n") + "\n"
    record_file = change_dir / "scope-review.md"
    record_file.write_text(record, encoding="utf-8")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(dc.sha12(record.encode("utf-8")) + "\n")
    print(f"scope review {run_id}: verdict {verdict}, {seconds}s, record {record_file.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

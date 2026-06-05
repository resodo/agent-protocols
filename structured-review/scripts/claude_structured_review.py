#!/usr/bin/env python3
"""Run Claude Code as a structured-review reviewer for a target worktree."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import selectors
import subprocess
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast

MODE_WRITE = "write-commit-to-plan"
MODE_PRINT = "print-review"
REVIEW_TYPES = ("other-plan", "impl-plan", "impl")
DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "xhigh"
DEFAULT_TIMEOUT_SEC = 1800
DEFAULT_HEARTBEAT_SEC = 30

CONTEXT_OVERLAY = Path(".agent-protocols/context.md")
STRUCTURED_REVIEW_OVERLAY = Path(".agent-protocols/structured-review.md")
REQUIRED_PROTOCOL_REFERENCES = (
    Path("references/review-lenses.md"),
    Path("references/collaboration.md"),
)
REVIEW_THREADS_RE = re.compile(r"^##\s+Review Threads\s*$", re.IGNORECASE | re.MULTILINE)
TOP_LEVEL_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)
REVIEW_HEADING_RE = re.compile(r"^###\s+.*(?:review|reviewer|thread)", re.IGNORECASE)

POSIX_MAC_HOME_PREFIX = "/" + "Users" + "/"
POSIX_LINUX_HOME_PREFIX = "/" + "home" + "/"
WINDOWS_HOME_SEGMENT = "Users"
LOCAL_HOME_RE = re.compile(
    "("
    + re.escape(POSIX_MAC_HOME_PREFIX)
    + r"[^/\s'\"`<>]+/"
    + "|"
    + re.escape(POSIX_LINUX_HOME_PREFIX)
    + r"(?!ubuntu(?:/|$))[^/\s'\"`<>]+/"
    + "|"
    + r"[A-Za-z]:[\\/]+"
    + re.escape(WINDOWS_HOME_SEGMENT)
    + r"[\\/]+[^\\/\s'\"`<>]+[\\/]+"
    + ")"
)
SECRET_RE = re.compile(
    r"BEGIN [A-Z ]*PRIVATE KEY"
    r"|AKIA[0-9A-Z]{16}"
    r"|ASIA[0-9A-Z]{16}"
    r"|ghp_[A-Za-z0-9]{36}"
    r"|xox[baprs]-[A-Za-z0-9-]+"
    r"|(?:secret|password|token|api[_-]?key)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{12,}",
    re.IGNORECASE,
)


class RunnerError(RuntimeError):
    """Structured review runner failure."""

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class ResolvedPath:
    rel: str
    abs: Path


@dataclass(frozen=True)
class RunConfig:
    protocol_dir: Path
    worktree: Path
    mode: str
    review_type: str
    artifacts: tuple[ResolvedPath, ...]
    focus: str
    thread_file: ResolvedPath | None
    topic: str | None
    model: str
    effort: str
    claude_bin: str
    timeout_sec: int
    heartbeat_sec: int
    run_log_dir: Path | None
    dry_run: bool


@dataclass(frozen=True)
class GitSnapshot:
    head: str
    status: str


@dataclass(frozen=True)
class RunLogs:
    root: Path
    prompt: Path
    stdout: Path
    stderr: Path
    metadata: Path
    review: Path


@dataclass(frozen=True)
class StreamLineResult:
    malformed: bool
    text_delta: str = ""
    message_text: str = ""


@dataclass
class ClaudeRunResult:
    returncode: int
    stdout: str
    stderr: str
    review_text: str
    malformed_stream_lines: int
    timed_out: bool
    started_at: str
    ended_at: str
    claude_version: str
    argv: list[str]


class Redactor:
    def __init__(self, paths: Iterable[Path]) -> None:
        replacements: list[tuple[str, str]] = []
        for path in paths:
            value = str(path)
            if value:
                replacements.append((value, "<PATH>"))
        home = str(Path.home())
        if home:
            replacements.append((home, "<HOME>"))
        replacements.sort(key=lambda item: len(item[0]), reverse=True)
        self._replacements = tuple(replacements)

    def redact(self, text: str) -> str:
        redacted = text
        for raw, marker in self._replacements:
            redacted = redacted.replace(raw, marker)
        return LOCAL_HOME_RE.sub("<LOCAL_HOME>/", redacted)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def run_git(
    args: Sequence[str],
    *,
    root: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, check=check, capture_output=True, text=True)


def normalize_rel(path: Path) -> str:
    return path.as_posix().removeprefix("./")


def git_root(path: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], root=path)
    root = Path(result.stdout.strip()).resolve()
    if not root.exists():
        raise RunnerError("resolved git root does not exist")
    return root


def resolve_worktree(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    if not path.exists():
        raise RunnerError("--worktree does not exist")
    root = git_root(path)
    if root != path:
        raise RunnerError("--worktree must point at the target repository root")
    return root


def resolve_repo_path(root: Path, raw: str) -> ResolvedPath:
    candidate = Path(raw).expanduser()
    absolute = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
    try:
        rel_path = absolute.relative_to(root)
    except ValueError as exc:
        raise RunnerError(f"path escapes worktree: {raw}") from exc
    rel = normalize_rel(rel_path)
    if not rel or rel == ".":
        raise RunnerError(f"path must identify a file or directory under worktree: {raw}")
    return ResolvedPath(rel=rel, abs=absolute)


def read_text(path: Path, *, required: bool = True) -> str:
    if not path.exists():
        if required:
            raise RunnerError(f"required file is missing: {normalize_rel(path)}")
        return ""
    return path.read_text(encoding="utf-8")


def default_protocol_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_protocol_dir(raw: str | None) -> Path:
    path = Path(raw).expanduser().resolve() if raw else default_protocol_dir()
    skill = path / "SKILL.md"
    if not skill.exists():
        raise RunnerError("--protocol-dir must contain SKILL.md")
    return path


def load_protocol_sections(config: RunConfig) -> list[tuple[str, str]]:
    sections = [("STRUCTURED REVIEW SKILL", read_text(config.protocol_dir / "SKILL.md"))]
    for rel in REQUIRED_PROTOCOL_REFERENCES:
        sections.append((f"STRUCTURED REVIEW REFERENCE {rel.as_posix()}", read_text(config.protocol_dir / rel)))
    for label, rel in (
        ("TARGET CONTEXT OVERLAY", CONTEXT_OVERLAY),
        ("TARGET STRUCTURED REVIEW OVERLAY", STRUCTURED_REVIEW_OVERLAY),
    ):
        path = config.worktree / rel
        if path.exists():
            sections.append((label, read_text(path)))
    return sections


def build_prompt(config: RunConfig) -> str:
    if str(config.worktree) in config.focus:
        raise RunnerError("focus text contains the real worktree path")
    thread_file = config.thread_file.rel if config.thread_file is not None else "none"
    lines = [
        "You are the reviewer for a structured-review gate.",
        "Role: reviewer",
        f"Type: {config.review_type}",
        "Worktree label: <WORKTREE>",
        "All relative paths are relative to <WORKTREE>.",
        "All repo-visible output, review threads, and commit messages must use relative paths only.",
        "Do not write local user-home absolute paths or the real worktree root into repo-visible content.",
        "",
        "Artifacts to review:",
    ]
    lines.extend(f"- {artifact.rel}" for artifact in config.artifacts)
    lines.extend(
        [
            "",
            f"Mode: {config.mode}",
            f"Thread file: {thread_file}",
            f"Topic: {config.topic or 'none'}",
            "",
            "Task-specific focus:",
            config.focus.strip(),
            "",
            "Instructions:",
            "- The structured-review protocol below is mandatory. Do not substitute a generic code review style.",
            "- Inspect the requested artifacts before judging readiness.",
        ]
    )
    if config.mode == MODE_WRITE:
        assert config.thread_file is not None
        assert config.topic is not None
        lines.extend(
            [
                "- Append review threads near the end of the thread file under its Review Threads section.",
                "- Commit only the thread-file change.",
                f"- Use commit message: structured-review: add reviewer comments for {config.topic}",
                "- Do not modify implementation files or any file other than the thread file.",
                "- If there are no blocking issues, say so explicitly in the review thread.",
            ]
        )
    else:
        lines.extend(
            [
                "- Print the review only. Do not write files and do not commit.",
                "- If there are no blocking issues, say so explicitly.",
            ]
        )
    for label, content in load_protocol_sections(config):
        lines.extend(["", f"--- BEGIN {label} ---", content.rstrip(), f"--- END {label} ---"])
    prompt = "\n".join(lines) + "\n"
    extra_paths = [config.worktree, *(artifact.abs for artifact in config.artifacts)]
    if config.thread_file is not None:
        extra_paths.append(config.thread_file.abs)
    if contains_local_path(prompt, extra_paths=extra_paths):
        raise RunnerError("prompt contains a local absolute path")
    return prompt


def git_snapshot(root: Path) -> GitSnapshot:
    head = run_git(["rev-parse", "HEAD"], root=root).stdout.strip()
    status = run_git(["status", "--porcelain"], root=root).stdout
    return GitSnapshot(head=head, status=status)


def require_clean(snapshot: GitSnapshot) -> None:
    if snapshot.status.strip():
        raise RunnerError("worktree must be clean before running structured review")


def changed_files(root: Path, commit: str) -> list[str]:
    result = run_git(["diff-tree", "--no-commit-id", "--name-only", "-r", commit], root=root)
    return [line for line in result.stdout.splitlines() if line]


def commit_subject(root: Path, commit: str) -> str:
    return run_git(["log", "-1", "--pretty=%s", commit], root=root).stdout.strip()


def commit_parent(root: Path, commit: str) -> str:
    result = run_git(["rev-parse", f"{commit}^"], root=root, check=False)
    if result.returncode != 0:
        raise RunnerError("review commit parent must be the pre-run HEAD")
    return result.stdout.strip()


def commits_between(root: Path, before: str, after: str) -> list[str]:
    result = run_git(["rev-list", "--reverse", f"{before}..{after}"], root=root)
    return [line for line in result.stdout.splitlines() if line]


def commit_diff(root: Path, commit: str, rel_path: str) -> str:
    return run_git(["show", "--format=", "--unified=0", commit, "--", rel_path], root=root).stdout


def diff_added_deleted(diff: str) -> tuple[list[str], list[str]]:
    added: list[str] = []
    deleted: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            deleted.append(line[1:])
    return added, deleted


def diff_added_line_numbers(diff: str) -> list[int]:
    line_numbers: list[int] = []
    new_line: int | None = None
    for line in diff.splitlines():
        if line.startswith("@@"):
            match = re.search(r"\+(\d+)(?:,\d+)?", line)
            new_line = int(match.group(1)) if match else None
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if new_line is None:
            continue
        if line.startswith("+"):
            line_numbers.append(new_line)
            new_line += 1
        elif line.startswith("-"):
            continue
        else:
            new_line += 1
    return line_numbers


def line_start_offsets(text: str) -> list[int]:
    starts = [0]
    offset = 0
    for line in text.splitlines(keepends=True):
        offset += len(line)
        starts.append(offset)
    return starts


def review_threads_bounds(text: str) -> tuple[int, int] | None:
    match = REVIEW_THREADS_RE.search(text)
    if match is None:
        return None
    next_heading = TOP_LEVEL_HEADING_RE.search(text, match.end())
    end = next_heading.start() if next_heading else len(text)
    return match.end(), end


def require_review_threads_anchor(path: Path) -> None:
    if review_threads_bounds(read_text(path)) is None:
        raise RunnerError("thread file must contain a top-level Review Threads section before running Claude")


def added_lines_under_review_threads(root: Path, rel_path: str, added_line_numbers: Sequence[int]) -> bool:
    text = (root / rel_path).read_text(encoding="utf-8")
    bounds = review_threads_bounds(text)
    if bounds is None:
        return False
    section_start, section_end = bounds
    starts = line_start_offsets(text)
    for line_number in added_line_numbers:
        if line_number <= 0 or line_number > len(starts):
            return False
        offset = starts[line_number - 1]
        if offset < section_start or offset >= section_end:
            return False
    return True


def added_content_is_review_like(added: Sequence[str]) -> bool:
    saw_review_heading = False
    for line in added:
        if REVIEW_HEADING_RE.search(line):
            saw_review_heading = True
            continue
        if saw_review_heading and line.strip() and not line.startswith("#"):
            return True
    return False


def contains_local_path(text: str, *, extra_paths: Iterable[Path] = ()) -> bool:
    if LOCAL_HOME_RE.search(text):
        return True
    return any(str(path) and str(path) in text for path in extra_paths)


def contains_secret_material(text: str) -> bool:
    return SECRET_RE.search(text) is not None


def verify_print_mode(config: RunConfig, before: GitSnapshot, after: GitSnapshot, result: ClaudeRunResult) -> None:
    if result.returncode != 0:
        raise RunnerError("claude review failed")
    if before.head != after.head:
        raise RunnerError("print-review changed HEAD")
    if before.status != after.status:
        raise RunnerError("print-review changed worktree status")
    if not result.review_text.strip():
        raise RunnerError("print-review produced no review text")
    if contains_local_path(result.review_text, extra_paths=(config.worktree,)):
        raise RunnerError("print-review output contains a local absolute path")


def verify_write_mode(config: RunConfig, before: GitSnapshot, after: GitSnapshot, result: ClaudeRunResult) -> None:
    if config.thread_file is None or config.topic is None:
        raise RunnerError("internal error: write mode missing thread file or topic")
    if result.returncode != 0:
        raise RunnerError("claude review failed")
    if after.status.strip():
        raise RunnerError("reviewer left uncommitted worktree changes")
    new_commits = commits_between(config.worktree, before.head, after.head)
    if len(new_commits) != 1:
        raise RunnerError("write mode must create exactly one new commit")
    commit = new_commits[0]
    if commit != after.head:
        raise RunnerError("new review commit must be the final HEAD")
    if commit_parent(config.worktree, commit) != before.head:
        raise RunnerError("review commit parent must be the pre-run HEAD")
    files = changed_files(config.worktree, commit)
    if files != [config.thread_file.rel]:
        raise RunnerError("review commit must touch only the thread file")
    subject = commit_subject(config.worktree, commit)
    if not subject.startswith("structured-review: "):
        raise RunnerError("review commit message must start with structured-review prefix")
    diff = commit_diff(config.worktree, commit, config.thread_file.rel)
    added, deleted = diff_added_deleted(diff)
    added_line_numbers = diff_added_line_numbers(diff)
    if not added:
        raise RunnerError("review commit must add non-empty review-thread content")
    if deleted:
        raise RunnerError("review commit must not delete existing thread-file content")
    if not added_lines_under_review_threads(config.worktree, config.thread_file.rel, added_line_numbers):
        raise RunnerError("review commit additions must be under a review-thread section")
    if not added_content_is_review_like(added):
        raise RunnerError("review commit additions do not look like review-thread content")
    if contains_local_path(diff, extra_paths=(config.worktree, config.thread_file.abs)):
        raise RunnerError("review commit diff contains a local absolute path")
    if contains_secret_material(diff):
        raise RunnerError("review commit diff contains possible secret material")


def text_from_content(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    parts: list[str] = []
    for item in value:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "".join(parts)


def stream_text_delta(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    if value.get("type") == "content_block_delta":
        delta = value.get("delta")
        if isinstance(delta, dict) and delta.get("type") == "text_delta" and isinstance(delta.get("text"), str):
            return delta["text"]
    return ""


def stream_message_text(value: Any) -> str:
    if not isinstance(value, dict) or value.get("type") != "assistant":
        return ""
    message = value.get("message")
    if isinstance(message, dict):
        return text_from_content(message.get("content"))
    return text_from_content(value.get("content"))


def process_stream_line(line: str) -> StreamLineResult:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return StreamLineResult(malformed=True)
    return StreamLineResult(malformed=False, text_delta=stream_text_delta(event), message_text=stream_message_text(event))


def claude_argv(config: RunConfig) -> list[str]:
    return [
        config.claude_bin,
        "-p",
        "--permission-mode",
        "auto",
        "--model",
        config.model,
        "--effort",
        config.effort,
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--include-hook-events",
        "--verbose",
    ]


def git_dir(root: Path) -> Path:
    result = run_git(["rev-parse", "--git-dir"], root=root)
    raw = Path(result.stdout.strip())
    return raw.resolve() if raw.is_absolute() else (root / raw).resolve()


def default_run_log_dir(config: RunConfig) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    suffix = secrets.token_hex(2)
    name = f"{timestamp}-{os.getpid()}-{suffix}-{config.mode}-{config.review_type}"
    return git_dir(config.worktree) / "structured-review-runs" / name


def prepare_run_logs(config: RunConfig) -> RunLogs:
    root = config.run_log_dir if config.run_log_dir is not None else default_run_log_dir(config)
    root.mkdir(parents=True, exist_ok=False)
    return RunLogs(
        root=root,
        prompt=root / "prompt.md",
        stdout=root / "stdout.stream.jsonl",
        stderr=root / "stderr.log",
        metadata=root / "metadata.json",
        review=root / "review.md",
    )


def claude_version(config: RunConfig) -> str:
    try:
        result = subprocess.run(
            [config.claude_bin, "--version"],
            cwd=config.worktree,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return "unknown: claude --version timed out"
    value = (result.stdout or result.stderr).strip()
    return value or f"unknown returncode={result.returncode}"


def write_metadata(
    config: RunConfig,
    logs: RunLogs,
    result: ClaudeRunResult | None,
    *,
    outcome: str,
    error: str | None = None,
    before: GitSnapshot | None = None,
    after: GitSnapshot | None = None,
) -> None:
    payload: dict[str, Any] = {
        "outcome": outcome,
        "error": error,
        "mode": config.mode,
        "type": config.review_type,
        "artifacts": [artifact.rel for artifact in config.artifacts],
        "thread_file": config.thread_file.rel if config.thread_file else None,
        "topic": config.topic,
        "model": config.model,
        "effort": config.effort,
        "timeout_sec": config.timeout_sec,
        "heartbeat_sec": config.heartbeat_sec,
        "run_log_dir": str(logs.root),
        "before": before.__dict__ if before else None,
        "after": after.__dict__ if after else None,
        "dirty_after": bool(after and after.status.strip()),
    }
    if result is not None:
        payload.update(
            {
                "argv": result.argv,
                "claude_version": result.claude_version,
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "malformed_stream_lines": result.malformed_stream_lines,
                "started_at": result.started_at,
                "ended_at": result.ended_at,
            }
        )
    logs.metadata.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_claude(config: RunConfig, prompt: str, logs: RunLogs, redactor: Redactor) -> ClaudeRunResult:
    argv = claude_argv(config)
    version = claude_version(config)
    logs.prompt.write_text(prompt, encoding="utf-8")
    started_at = utc_now()
    started = time.monotonic()
    last_event = started
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    text_delta_parts: list[str] = []
    message_text_candidate = ""
    malformed = 0
    print(
        f"claude review start mode={config.mode} type={config.review_type} model={config.model} effort={config.effort} artifacts={','.join(a.rel for a in config.artifacts)}",
        file=sys.stderr,
    )
    proc = subprocess.Popen(
        argv,
        cwd=config.worktree,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None
    proc.stdin.write(prompt)
    proc.stdin.close()
    assert proc.stdout is not None
    assert proc.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
    timed_out = False
    with logs.stdout.open("w", encoding="utf-8") as stdout_log, logs.stderr.open("w", encoding="utf-8") as stderr_log:
        while selector.get_map():
            now = time.monotonic()
            if now - started > config.timeout_sec:
                timed_out = True
                proc.kill()
                break
            events = selector.select(timeout=1.0)
            if not events:
                if now - last_event >= config.heartbeat_sec:
                    elapsed = int(now - started)
                    print(f"claude review heartbeat elapsed_sec={elapsed}", file=sys.stderr)
                    last_event = now
                continue
            for key, _ in events:
                stream = cast(TextIO, key.fileobj)
                line = stream.readline()
                if not line:
                    selector.unregister(stream)
                    continue
                last_event = time.monotonic()
                if key.data == "stdout":
                    stdout_parts.append(line)
                    stdout_log.write(line)
                    stdout_log.flush()
                    stream_result = process_stream_line(line)
                    if stream_result.malformed:
                        malformed += 1
                    if stream_result.text_delta:
                        text_delta_parts.append(stream_result.text_delta)
                    elif stream_result.message_text:
                        message_text_candidate = stream_result.message_text
                    print("claude review event", file=sys.stderr)
                else:
                    stderr_parts.append(line)
                    stderr_log.write(line)
                    stderr_log.flush()
                    print(redactor.redact(line.rstrip()), file=sys.stderr)
    selector.close()
    returncode = proc.wait()
    proc.stdout.close()
    proc.stderr.close()
    if timed_out:
        returncode = -9
    review_text = "".join(text_delta_parts) if text_delta_parts else message_text_candidate
    logs.review.write_text(review_text, encoding="utf-8")
    return ClaudeRunResult(
        returncode=returncode,
        stdout="".join(stdout_parts),
        stderr="".join(stderr_parts),
        review_text=review_text,
        malformed_stream_lines=malformed,
        timed_out=timed_out,
        started_at=started_at,
        ended_at=utc_now(),
        claude_version=version,
        argv=argv,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir")
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--mode", required=True, choices=(MODE_WRITE, MODE_PRINT))
    parser.add_argument("--type", required=True, choices=REVIEW_TYPES, dest="review_type")
    parser.add_argument("--artifact", action="append", required=True)
    focus = parser.add_mutually_exclusive_group(required=True)
    focus.add_argument("--focus")
    focus.add_argument("--focus-file")
    parser.add_argument("--thread-file")
    parser.add_argument("--topic")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--effort", default=DEFAULT_EFFORT)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--timeout-sec", type=int, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--heartbeat-sec", type=int, default=DEFAULT_HEARTBEAT_SEC)
    parser.add_argument("--run-log-dir")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> RunConfig:
    protocol_dir = resolve_protocol_dir(args.protocol_dir)
    worktree = resolve_worktree(args.worktree)
    focus = args.focus if args.focus else read_text(resolve_repo_path(worktree, args.focus_file).abs)
    artifacts = tuple(resolve_repo_path(worktree, raw) for raw in args.artifact)
    thread_file = resolve_repo_path(worktree, args.thread_file) if args.thread_file else None
    if args.mode == MODE_WRITE:
        if thread_file is None:
            raise RunnerError("--thread-file is required in write-commit-to-plan mode")
        if not args.topic:
            raise RunnerError("--topic is required in write-commit-to-plan mode")
    elif thread_file is not None:
        raise RunnerError("--thread-file is forbidden in print-review mode")
    if args.timeout_sec <= 0 or args.heartbeat_sec <= 0:
        raise RunnerError("timeout and heartbeat must be positive")
    run_log_dir = Path(args.run_log_dir).expanduser().resolve() if args.run_log_dir else None
    return RunConfig(
        protocol_dir=protocol_dir,
        worktree=worktree,
        mode=args.mode,
        review_type=args.review_type,
        artifacts=artifacts,
        focus=focus,
        thread_file=thread_file,
        topic=args.topic,
        model=args.model,
        effort=args.effort,
        claude_bin=args.claude_bin,
        timeout_sec=args.timeout_sec,
        heartbeat_sec=args.heartbeat_sec,
        run_log_dir=run_log_dir,
        dry_run=args.dry_run,
    )


def run(config: RunConfig) -> None:
    redactor_paths = [config.worktree, *(artifact.abs for artifact in config.artifacts)]
    if config.thread_file is not None:
        redactor_paths.append(config.thread_file.abs)
    redactor = Redactor(redactor_paths)
    prompt = build_prompt(config)
    if config.dry_run:
        print(redactor.redact(prompt))
        return
    before = git_snapshot(config.worktree)
    require_clean(before)
    if config.mode == MODE_WRITE:
        assert config.thread_file is not None
        require_review_threads_anchor(config.thread_file.abs)
    logs = prepare_run_logs(config)
    result: ClaudeRunResult | None = None
    after: GitSnapshot | None = None
    try:
        result = run_claude(config, prompt, logs, redactor)
        after = git_snapshot(config.worktree)
        if result.timed_out:
            dirty = " with uncommitted changes" if after.status.strip() else ""
            write_metadata(config, logs, result, outcome="timeout", error=f"claude review timed out{dirty}", before=before, after=after)
            raise RunnerError(f"claude review timed out{dirty}", exit_code=2)
        if config.mode == MODE_WRITE:
            verify_write_mode(config, before, after, result)
        else:
            verify_print_mode(config, before, after, result)
            print(redactor.redact(result.review_text).rstrip())
        write_metadata(config, logs, result, outcome="success", before=before, after=after)
        print(f"claude structured review completed run_log={redactor.redact(str(logs.root))}", file=sys.stderr)
    except RunnerError as exc:
        if result is not None and not result.timed_out:
            if after is None:
                after = git_snapshot(config.worktree)
            write_metadata(config, logs, result, outcome="failed", error=str(exc), before=before, after=after)
        raise
    except Exception as exc:
        after = git_snapshot(config.worktree)
        write_metadata(config, logs, result, outcome="error", error=str(exc), before=before, after=after)
        raise RunnerError(f"claude review errored: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(sys.argv[1:] if argv is None else argv)
        config = config_from_args(args)
        run(config)
        return 0
    except RunnerError as exc:
        redactor = Redactor([Path.cwd()])
        print(f"claude_structured_review.py: {redactor.redact(str(exc)).strip()}", file=sys.stderr)
        return exc.exit_code
    except subprocess.CalledProcessError as exc:
        message = exc.stderr or exc.stdout or str(exc)
        redactor = Redactor([Path.cwd()])
        print(f"claude_structured_review.py: {redactor.redact(message).strip()}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("claude_structured_review.py: interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run Claude Code, Codex, or Grok Build as a structured-review reviewer."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import signal
import uuid
from contextlib import contextmanager
import json
import os
import re
import secrets
import selectors
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO, cast

MODE_WRITE = "write-commit-to-plan"
MODE_PRINT = "print-review"
REVIEW_TYPES = ("other-plan", "impl-plan", "impl", "closeout-review")
DEFAULT_MODEL = "claude-opus-5"
HARD_CLAUDE_MODEL = "claude-fable-5-1"
DEFAULT_EFFORT = "xhigh"
DEFAULT_CODEX_MODEL = "gpt-5.6-terra"
HARD_CODEX_MODEL = "gpt-6-astra"
DEFAULT_CODEX_EFFORT = "xhigh"
DEFAULT_TIMEOUT_SEC = 1800
HARD_TIMEOUT_SEC = 3600
STOP_GRACE_SEC = 5.0
DEFAULT_HEARTBEAT_SEC = 30
HARD_REVIEW_LINE_THRESHOLD = 1000

BACKEND_AUTO = "auto"
BACKEND_CLAUDE = "claude"
BACKEND_CODEX = "codex"
BACKEND_GROK = "grok"
BACKEND_ORDER = (BACKEND_CLAUDE, BACKEND_CODEX, BACKEND_GROK)
REVIEW_TIER_AUTO = "auto"
REVIEW_TIER_NORMAL = "normal"
REVIEW_TIER_HARD = "hard"
TIER_SELECTION_EXPLICIT_DRIVER = "explicit-driver"
TIER_SELECTION_LEGACY_AUTO = "legacy-auto-compatibility"
LEGACY_AUTO_TIER_REASON = "legacy --review-tier auto compatibility selected normal"
CLAUDE_DRIVER_MARKERS = ("CLAUDECODE",)
CODEX_DRIVER_MARKERS = ("CODEX_THREAD_ID", "CODEX_SANDBOX")
CODEX_LAST_MESSAGE_NAME = "last-message.txt"

REVIEW_MODEL_MATRIX = {
    BACKEND_CLAUDE: {
        REVIEW_TIER_NORMAL: (DEFAULT_MODEL, DEFAULT_EFFORT),
        REVIEW_TIER_HARD: (HARD_CLAUDE_MODEL, DEFAULT_EFFORT),
    },
    BACKEND_CODEX: {
        REVIEW_TIER_NORMAL: (DEFAULT_CODEX_MODEL, DEFAULT_CODEX_EFFORT),
        REVIEW_TIER_HARD: (HARD_CODEX_MODEL, DEFAULT_CODEX_EFFORT),
    },
    BACKEND_GROK: {
        REVIEW_TIER_NORMAL: ("grok-4.6", "medium"),
        REVIEW_TIER_HARD: ("grok-4.6", "xhigh"),
    },
}

HARD_COMPLEXITY_SIGNAL_PHRASES = (
    (
        "production/runtime/deploy/rollout",
        (
            "production-facing",
            "production change",
            "production rollout",
            "runtime-facing",
            "runtime behavior",
            "deploy-facing",
            "deployment plan",
            "rollout plan",
        ),
    ),
    (
        "architecture/migration",
        (
            "architecture-facing",
            "architecture change",
            "system architecture",
            "data migration",
            "schema migration",
            "migration plan",
        ),
    ),
    (
        "security/data safety",
        (
            "security-sensitive",
            "security review",
            "security boundary",
            "data safety",
            "data loss",
            "destructive data",
        ),
    ),
    (
        "multi-repo/multi-agent/release",
        ("multi-repo", "multi-agent", "release plan", "release handoff"),
    ),
    (
        "broad protocol change",
        ("broad protocol change", "protocol-wide change", "protocol self-evolution"),
    ),
    (
        "explicit complexity",
        ("complex review", "high-risk", "hard review", "large review"),
    ),
)


def phrase_regex(phrase: str) -> re.Pattern[str]:
    body = r"\s+".join(re.escape(part) for part in phrase.split())
    return re.compile(rf"(?<!\w){body}(?!\w)", re.IGNORECASE)


HARD_COMPLEXITY_PATTERNS = tuple(
    (category, tuple(phrase_regex(phrase) for phrase in phrases))
    for category, phrases in HARD_COMPLEXITY_SIGNAL_PHRASES
)

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


class CreditExhausted(RunnerError):
    """Authoritative provider error, eligible for a fresh auto candidate."""

    attempt: Path | None = None


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
    backend: str
    selected_tier: str
    tier_selection_source: str
    driver_tier_reason: str | None
    recommended_tier: str
    recommendation_reasons: tuple[str, ...]
    model: str
    effort: str
    model_source: str
    effort_source: str
    claude_bin: str
    codex_bin: str
    codex_model: str
    codex_effort: str
    timeout_sec: int
    heartbeat_sec: int
    run_log_dir: Path | None
    dry_run: bool
    timeout_source: str = "profile"
    resume_run: Path | None = None
    resume_session_id: str | None = None
    grok_bin: str = "grok"
    grok_model: str = "grok-4.6"
    grok_effort: str = "medium"
    requested_backend: str = BACKEND_CLAUDE
    coding_agent: str = "unknown"
    profile_overrides: tuple[tuple[str, str | None, str | None], ...] = ()
    selection_history: tuple[dict[str, str], ...] = ()


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
    chain_root: Path | None = None
    signals: list[int] | None = None


@dataclass(frozen=True)
class StreamLineResult:
    malformed: bool
    text_delta: str = ""
    message_text: str = ""
    usage: dict[str, Any] | None = None


@dataclass
class ReviewState:
    text_deltas: list[str] = field(default_factory=list)
    final_message: str = ""
    messages: list[str] = field(default_factory=list)


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
    reviewer_version: str
    argv: list[str]
    token_usage: dict[str, Any] | None = None
    stop_reason: str | None = None
    stop_signal: int | None = None
    elapsed_sec: float = 0.0


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


def read_artifact_body(artifact: ResolvedPath) -> str:
    if not artifact.abs.is_file():
        raise RunnerError(f"artifact must be an existing regular file: {artifact.rel}")
    try:
        text = artifact.abs.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise RunnerError(f"artifact must be readable UTF-8: {artifact.rel}") from exc
    match = REVIEW_THREADS_RE.search(text)
    return text[: match.start()] if match else text


def recommend_review_tier(
    review_type: str,
    artifacts: Sequence[ResolvedPath],
    focus: str,
) -> tuple[str, tuple[str, ...]]:
    bodies = [read_artifact_body(artifact) for artifact in artifacts]
    reasons: list[str] = []
    if review_type == "closeout-review":
        reasons.append("review type closeout-review")

    total_lines = sum(len(body.splitlines()) for body in bodies)
    if total_lines > HARD_REVIEW_LINE_THRESHOLD:
        reasons.append(f"artifact body lines {total_lines} > {HARD_REVIEW_LINE_THRESHOLD}")

    if review_type == "impl" and len(artifacts) > 1:
        reasons.append(f"multi-artifact impl review ({len(artifacts)} artifacts)")

    scan_text = "\n".join((focus, *bodies))
    for category, patterns in HARD_COMPLEXITY_PATTERNS:
        if any(pattern.search(scan_text) for pattern in patterns):
            reasons.append(f"complexity signal: {category}")

    if reasons:
        return REVIEW_TIER_HARD, tuple(reasons)
    return REVIEW_TIER_NORMAL, ()


def resolve_review_tier(raw: str, tier_reason: str | None) -> tuple[str, str, str | None]:
    if raw == REVIEW_TIER_AUTO:
        if tier_reason is not None:
            raise RunnerError("--tier-reason is valid only with --review-tier hard")
        return REVIEW_TIER_NORMAL, TIER_SELECTION_LEGACY_AUTO, None

    if raw == REVIEW_TIER_NORMAL:
        if tier_reason is not None:
            raise RunnerError("--tier-reason is valid only with --review-tier hard")
        return REVIEW_TIER_NORMAL, TIER_SELECTION_EXPLICIT_DRIVER, None

    normalized_reason = tier_reason.strip() if tier_reason is not None else ""
    if not normalized_reason:
        raise RunnerError("--tier-reason must be non-empty with --review-tier hard")
    return REVIEW_TIER_HARD, TIER_SELECTION_EXPLICIT_DRIVER, normalized_reason


def legacy_review_tier_reasons(config: RunConfig) -> tuple[str, ...]:
    if config.tier_selection_source == TIER_SELECTION_LEGACY_AUTO:
        return (LEGACY_AUTO_TIER_REASON,)
    reasons = [f"explicit --review-tier {config.selected_tier}"]
    if config.driver_tier_reason is not None:
        reasons.append(f"driver tier reason: {config.driver_tier_reason}")
    return tuple(reasons)


def resolve_review_profile(
    backend: str,
    selected_tier: str,
    *,
    claude_model: str | None,
    claude_effort: str | None,
    codex_model: str | None,
    codex_effort: str | None,
    grok_model: str | None = None,
    grok_effort: str | None = None,
) -> tuple[str, str, str, str]:
    model, effort = REVIEW_MODEL_MATRIX[backend][selected_tier]
    model_override, effort_override = {
        BACKEND_CLAUDE: (claude_model, claude_effort),
        BACKEND_CODEX: (codex_model, codex_effort),
        BACKEND_GROK: (grok_model, grok_effort),
    }[backend]
    prefix = "--" if backend == BACKEND_CLAUDE else f"--{backend}-"
    model_flag, effort_flag = prefix + "model", prefix + "effort"
    model_source = "profile"
    effort_source = "profile"
    if model_override is not None:
        model = model_override
        model_source = f"explicit {model_flag}"
    if effort_override is not None:
        effort = effort_override
        effort_source = f"explicit {effort_flag}"
    return model, effort, model_source, effort_source


def require_hard_profile_model_has_hard_tier(backend: str, selected_tier: str, model: str) -> None:
    hard_model = REVIEW_MODEL_MATRIX[backend][REVIEW_TIER_HARD][0]
    normal_model = REVIEW_MODEL_MATRIX[backend][REVIEW_TIER_NORMAL][0]
    if hard_model != normal_model and selected_tier != REVIEW_TIER_HARD and model == hard_model:
        model_flag = "--model" if backend == BACKEND_CLAUDE else "--codex-model"
        raise RunnerError(
            f"{model_flag} cannot select pinned hard-profile model '{hard_model}' with "
            f"--review-tier {selected_tier}; pass --review-tier hard --tier-reason instead"
        )


def unused_profile_override_flags(
    backend: str,
    *,
    claude_model: str | None,
    claude_effort: str | None,
    codex_model: str | None,
    codex_effort: str | None,
    grok_model: str | None = None,
    grok_effort: str | None = None,
) -> tuple[str, ...]:
    providers = {BACKEND_CLAUDE: (claude_model, claude_effort),
                 BACKEND_CODEX: (codex_model, codex_effort),
                 BACKEND_GROK: (grok_model, grok_effort)}
    return tuple(("--" if name == BACKEND_CLAUDE else f"--{name}-") + kind
                 for name, values in providers.items() if name != backend
                 for kind, value in zip(("model", "effort"), values) if value is not None)


def select_profile(config: RunConfig, backend: str) -> RunConfig:
    overrides = {f"{name}_{kind}": value
                 for name, model, effort in config.profile_overrides
                 for kind, value in (("model", model), ("effort", effort))}
    for name in BACKEND_ORDER:
        overrides.setdefault(f"{name}_model", None)
        overrides.setdefault(f"{name}_effort", None)
    model, effort, model_source, effort_source = resolve_review_profile(backend, config.selected_tier, **overrides)
    require_hard_profile_model_has_hard_tier(backend, config.selected_tier, model)
    unused = unused_profile_override_flags(backend, **overrides)
    if unused:
        print(f"warning: reviewer backend '{backend}' ignores override flags for the non-selected provider: {', '.join(unused)}", file=sys.stderr)
    prefix = "" if backend == BACKEND_CLAUDE else backend + "_"
    return replace(config, backend=backend, model_source=model_source, effort_source=effort_source,
                   **{prefix + "model": model, prefix + "effort": effort})


def coding_identity(raw: str | None, env: Mapping[str, str], *, explicit_backend: bool = False) -> str:
    if raw is not None:
        value = raw.strip().lower()
        if not value:
            raise RunnerError("--coding-agent must be a nonempty name")
        return value
    claude, codex = detect_driver_markers(env)
    if claude and codex:
        if explicit_backend:
            return "unknown"  # Preserve intentional legacy explicit pin behavior.
        raise RunnerError("conflicting driver markers; pass --coding-agent (or --reviewer-backend to pin intentionally)")
    return BACKEND_CLAUDE if claude else (BACKEND_CODEX if codex else "unknown")


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
            "Reviewer selection:",
            f"- Backend: {config.backend}",
            f"- Selected review tier: {config.selected_tier}",
            f"- Tier selection source: {config.tier_selection_source}",
            f"- Driver tier reason: {config.driver_tier_reason or 'none'}",
            f"- Runner recommended tier: {config.recommended_tier}",
            f"- Recommendation reasons: {'; '.join(config.recommendation_reasons) or 'none'}",
            f"- Model: {active_model(config)}",
            f"- Model source: {config.model_source}",
            f"- Effort: {active_effort(config)}",
            f"- Effort source: {config.effort_source}",
            "- Review tier affects model routing and the default attempt time limit. Apply the same readiness standard at both tiers; do not invent scope or low-value findings for a hard review.",
            "- Normal is the default. Reserve hard for roughly the hardest 20% of the driver's tasks: major design, major architecture, or unusually difficult bugs. This is judgment, not a numerical quota. Mechanical recommendations and routine protocol edits alone do not qualify; do not evade this guidance with provider overrides.",
            "",
            "Task-specific focus:",
            config.focus.strip(),
            "",
            "Instructions:",
            "- The structured-review protocol below is mandatory. Do not substitute a generic code review style.",
            "- Inspect the requested artifacts before judging readiness.",
            f"- You are the {config.backend} reviewer backend. Name the backend in each reviewer pass heading, for example: ### Reviewer pass 1 ({config.review_type}, {config.backend} reviewer).",
        ]
    )
    if config.mode == MODE_WRITE:
        assert config.thread_file is not None
        assert config.topic is not None
        lines.extend(
            [
                "- Return the complete review threads as markdown in your final response.",
                "- Do not write files, stage changes, or commit anything; the runner appends your returned review to the thread file and creates the commit.",
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
        raise RunnerError("reviewer run failed")
    if before.head != after.head:
        raise RunnerError("print-review changed HEAD")
    if before.status != after.status:
        raise RunnerError("print-review changed worktree status")
    if not result.review_text.strip():
        raise RunnerError("print-review produced no review text")
    if contains_local_path(result.review_text, extra_paths=(config.worktree,)):
        raise RunnerError("print-review output contains a local absolute path")


def verify_reviewer_output(config: RunConfig, before: GitSnapshot, after: GitSnapshot, result: ClaudeRunResult) -> None:
    """Require a read-only reviewer run with committable review text."""
    if result.returncode != 0:
        raise RunnerError("reviewer run failed")
    if before.head != after.head:
        raise RunnerError("reviewer moved HEAD; write mode requires read-only reviewer output")
    if before.status != after.status:
        raise RunnerError("reviewer modified the worktree; write mode requires read-only reviewer output")
    text = result.review_text
    if not text.strip():
        raise RunnerError("reviewer produced no review text")
    if not added_content_is_review_like(text.splitlines()):
        raise RunnerError("review text does not look like review-thread content")
    if contains_local_path(text, extra_paths=(config.worktree,)):
        raise RunnerError("review text contains a local absolute path")
    if contains_secret_material(text):
        raise RunnerError("review text contains possible secret material")


def append_and_commit_review(config: RunConfig, review_text: str) -> None:
    """Append the reviewer's output under Review Threads and create the handoff commit."""
    if config.thread_file is None or config.topic is None:
        raise RunnerError("internal error: write mode missing thread file or topic")
    path = config.thread_file.abs
    text = read_text(path)
    bounds = review_threads_bounds(text)
    if bounds is None:
        raise RunnerError("thread file lost its Review Threads section during the run")
    _, section_end = bounds
    head = text[:section_end].rstrip("\n")
    tail = text[section_end:].lstrip("\n")
    block = review_text if review_text.endswith("\n") else review_text + "\n"
    updated = head + "\n\n" + block
    if tail:
        updated += "\n" + tail
    path.write_text(updated, encoding="utf-8")
    run_git(["add", config.thread_file.rel], root=config.worktree)
    run_git(
        ["commit", "-m", f"structured-review: add reviewer comments for {config.topic}"],
        root=config.worktree,
    )


def verify_write_mode(config: RunConfig, before: GitSnapshot, after: GitSnapshot, result: ClaudeRunResult) -> None:
    if config.thread_file is None or config.topic is None:
        raise RunnerError("internal error: write mode missing thread file or topic")
    if result.returncode != 0:
        raise RunnerError("reviewer run failed")
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


def codex_agent_message(value: Any) -> str:
    if not isinstance(value, dict) or value.get("type") != "item.completed":
        return ""
    item = value.get("item")
    if isinstance(item, dict) and item.get("type") == "agent_message" and isinstance(item.get("text"), str):
        return item["text"]
    return ""


def codex_turn_usage(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or value.get("type") != "turn.completed":
        return None
    usage = value.get("usage")
    return usage if isinstance(usage, dict) else None


def process_codex_stream_line(line: str) -> StreamLineResult:
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return StreamLineResult(malformed=True)
    return StreamLineResult(malformed=False, message_text=codex_agent_message(event), usage=codex_turn_usage(event))


def claude_argv(config: RunConfig) -> list[str]:
    return [
        config.claude_bin,
        "-p",
        *(["--resume", config.resume_session_id] if config.resume_session_id else []),
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


def codex_argv(config: RunConfig, logs: RunLogs) -> list[str]:
    if config.resume_session_id:
        return [
            config.codex_bin, "exec", "resume", config.resume_session_id, "-",
            "--json", "-m", config.codex_model,
            "-c", f"model_reasoning_effort={config.codex_effort}",
            "-c", 'sandbox_mode="workspace-write"',
            "--output-last-message", str(logs.root / CODEX_LAST_MESSAGE_NAME),
        ]
    # workspace-write (without any .git --add-dir grant) lets the reviewer run
    # tests, which need writable temp dirs, while commits stay impossible and
    # stray worktree writes are rejected by the runner's untouched-worktree
    # check before any append happens.
    return [
        config.codex_bin,
        "exec",
        "-",
        "--json",
        "--sandbox",
        "workspace-write",
        "-m",
        config.codex_model,
        "-c",
        f"model_reasoning_effort={config.codex_effort}",
        "--output-last-message",
        str(logs.root / CODEX_LAST_MESSAGE_NAME),
    ]


def grok_argv(config: RunConfig, logs: RunLogs) -> list[str]:
    return [
        config.grok_bin, "--model", config.grok_model,
        "--reasoning-effort", config.grok_effort, "--permission-mode", "plan",
        "--no-subagents", "--output-format", "streaming-messages-json",
        "--prompt-file", str(logs.prompt),
        *(["--resume", config.resume_session_id] if config.resume_session_id else []),
    ]


def message_session(event: dict[str, Any]) -> Any:
    return event.get("session_id")


def codex_session(event: dict[str, Any]) -> Any:
    return event.get("thread_id") if event.get("type") == "thread.started" else None


def grok_session(event: dict[str, Any]) -> Any:
    return event.get("session_id") if event.get("type") in ("system", "result") else None


def claude_failure(event: dict[str, Any]) -> str | None:
    if event.get("type") != "result" or not (event.get("is_error") or event.get("subtype", "success") != "success"):
        return None
    # Observed Claude CLI error envelope; never scan assistant/tool content.
    text = event.get("result")
    if event.get("is_error") is True and isinstance(text, str) and re.match(
        r"^You've hit your weekly limit\s*·\s*resets\s+\S", text
    ):
        return "credit_exhausted"
    return "provider_error"


def codex_failure(event: dict[str, Any]) -> str | None:
    if event.get("type") != "turn.failed":
        return None
    error = event.get("error")
    text = error.get("message") if isinstance(error, dict) else None
    # Upstream codex-rs/protocol/src/error.rs UsageLimitReached / QuotaExceeded.
    if isinstance(text, str) and (text.startswith(("You've hit your usage limit.", "You've hit your usage limit for "))
                                or text == "Quota exceeded. Check your plan and billing details."):
        return "credit_exhausted"
    return "provider_error"


def grok_failure(event: dict[str, Any]) -> str | None:
    if event.get("type") != "result":
        return None
    if (event.get("subtype") != "success" or event.get("is_error") is not False
            or event.get("stop_reason") != "end_turn"
            or not valid_session_id(event.get("session_id"))
            or not isinstance(event.get("result"), str) or not event["result"].strip()):
        return "provider_error"
    return None


def claude_finalize(state: ReviewState, logs: RunLogs) -> str:
    return state.final_message or "".join(state.text_deltas)


def codex_finalize(state: ReviewState, logs: RunLogs) -> str:
    last_message = logs.root / CODEX_LAST_MESSAGE_NAME
    if last_message.exists():
        file_text = last_message.read_text(encoding="utf-8")
        if file_text.strip():
            return file_text
    return "\n\n".join(message for message in state.messages if message.strip())


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
    root.mkdir(mode=0o700, parents=True, exist_ok=False)
    return RunLogs(
        root=root,
        prompt=root / "prompt.md",
        stdout=root / "stdout.stream.jsonl",
        stderr=root / "stderr.log",
        metadata=root / "metadata.json",
        review=root / "review.md",
    )


def binary_version(bin_path: str, label: str, cwd: Path) -> str:
    try:
        result = subprocess.run(
            [bin_path, "--version"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return f"unknown: {label} --version timed out"
    value = (result.stdout or result.stderr).strip()
    return value or f"unknown returncode={result.returncode}"


def claude_version(config: RunConfig) -> str:
    return binary_version(config.claude_bin, BACKEND_CLAUDE, config.worktree)


def codex_version(config: RunConfig) -> str:
    return binary_version(config.codex_bin, BACKEND_CODEX, config.worktree)


@dataclass(frozen=True)
class ReviewerBackend:
    name: str
    bin_for: Callable[[RunConfig], str]
    argv_for: Callable[[RunConfig, RunLogs], list[str]]
    parse_line: Callable[[str], StreamLineResult]
    finalize: Callable[[ReviewState, RunLogs], str]
    version_for: Callable[[RunConfig], str]
    driver_markers: tuple[str, ...]
    session_for: Callable[[dict[str, Any]], Any]
    failure_for: Callable[[dict[str, Any]], str | None]
    prompt_on_stdin: bool = True


BACKENDS: dict[str, ReviewerBackend] = {
    BACKEND_CLAUDE: ReviewerBackend(
        name=BACKEND_CLAUDE,
        bin_for=lambda config: config.claude_bin,
        argv_for=lambda config, logs: claude_argv(config),
        parse_line=process_stream_line,
        finalize=claude_finalize,
        version_for=claude_version,
        driver_markers=CLAUDE_DRIVER_MARKERS,
        session_for=message_session,
        failure_for=claude_failure,
    ),
    BACKEND_CODEX: ReviewerBackend(
        name=BACKEND_CODEX,
        bin_for=lambda config: config.codex_bin,
        argv_for=codex_argv,
        parse_line=process_codex_stream_line,
        finalize=codex_finalize,
        version_for=codex_version,
        driver_markers=CODEX_DRIVER_MARKERS,
        session_for=codex_session,
        failure_for=codex_failure,
    ),
    BACKEND_GROK: ReviewerBackend(
        name=BACKEND_GROK,
        bin_for=lambda config: config.grok_bin,
        argv_for=grok_argv,
        parse_line=process_stream_line,
        finalize=claude_finalize,
        version_for=lambda config: binary_version(config.grok_bin, BACKEND_GROK, config.worktree),
        driver_markers=(),
        session_for=grok_session,
        failure_for=grok_failure,
        prompt_on_stdin=False,
    ),
}


def detect_driver_markers(env: Mapping[str, str]) -> tuple[bool, bool]:
    claude_marker = any(name in env for name in CLAUDE_DRIVER_MARKERS)
    codex_marker = any(name in env for name in CODEX_DRIVER_MARKERS)
    return claude_marker, codex_marker


def resolve_reviewer_backend(raw: str, env: Mapping[str, str]) -> tuple[str, bool]:
    """Resolve the reviewer backend name and whether a driver marker chose it."""
    if raw != BACKEND_AUTO:
        return raw, False
    claude_marker, codex_marker = detect_driver_markers(env)
    if claude_marker and codex_marker:
        raise RunnerError(
            "driver environment carries both Claude and Codex markers; pass --reviewer-backend explicitly"
        )
    if claude_marker:
        return BACKEND_CODEX, True
    if codex_marker:
        return BACKEND_CLAUDE, True
    return BACKEND_CLAUDE, False


def active_model(config: RunConfig) -> str:
    return {BACKEND_CLAUDE: config.model, BACKEND_CODEX: config.codex_model, BACKEND_GROK: config.grok_model}[config.backend]


def active_effort(config: RunConfig) -> str:
    return {BACKEND_CLAUDE: config.effort, BACKEND_CODEX: config.codex_effort, BACKEND_GROK: config.grok_effort}[config.backend]


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
        "backend": config.backend,
        "requested_backend": config.requested_backend,
        "coding_agent": config.coding_agent,
        "selection_history": list(config.selection_history),
        "selected_tier": config.selected_tier,
        "tier_selection_source": config.tier_selection_source,
        "driver_tier_reason": config.driver_tier_reason,
        "recommended_tier": config.recommended_tier,
        "recommendation_reasons": list(config.recommendation_reasons),
        "review_tier": config.selected_tier,
        "review_tier_reasons": list(legacy_review_tier_reasons(config)),
        "model": active_model(config),
        "effort": active_effort(config),
        "model_source": config.model_source,
        "effort_source": config.effort_source,
        "timeout_sec": config.timeout_sec,
        "timeout_source": config.timeout_source,
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
                "reviewer_version": result.reviewer_version,
                "returncode": result.returncode,
                "timed_out": result.timed_out,
                "malformed_stream_lines": result.malformed_stream_lines,
                "started_at": result.started_at,
                "ended_at": result.ended_at,
                "token_usage": result.token_usage,
                "stop_reason": result.stop_reason,
                "stop_signal": result.stop_signal,
                "elapsed_sec": result.elapsed_sec,
                "cumulative_elapsed_sec": read_json(logs.metadata).get("prior_elapsed_sec", 0) + result.elapsed_sec,
            }
        )
    patch_metadata(logs, **payload)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise RunnerError(f"cannot read run state: {path}") from exc
    if not isinstance(value, dict):
        raise RunnerError(f"invalid run state: {path}")
    return value


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(6)}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as output:
            os.chmod(temporary, 0o600)
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def patch_metadata(logs: RunLogs, **fields: Any) -> None:
    atomic_json(logs.metadata, {**read_json(logs.metadata), **fields})


def chain_for(attempt: Path) -> Path:
    metadata = read_json(attempt / "metadata.json")
    root = Path(metadata.get("chain_root", str(attempt))).resolve()
    if attempt != root and root not in attempt.parents:
        raise RunnerError("attempt is outside its recorded run chain")
    if not (root / "chain.json").is_file():
        raise RunnerError("run has no recovery chain metadata")
    return root


def require_latest(root: Path, attempt: Path) -> None:
    latest = read_json(root / "chain.json").get("latest_attempt")
    if latest != str(attempt):
        raise RunnerError(f"stale attempt; latest attempt is {latest}")


@contextmanager
def chain_lock(root: Path):
    with (root / "chain.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunnerError("review chain is already running; concurrent resume refused") from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def attempt_diagnostics(metadata: dict[str, Any]) -> str:
    return (
        f"runner_pid={metadata.get('runner_pid')} "
        f"reviewer_pgid={metadata.get('reviewer_pgid')} "
        f"started_at={metadata.get('started_at', metadata.get('created_at'))}"
    )


def request_stop(attempt: Path, reason: str) -> None:
    attempt = attempt.resolve()
    if not reason.strip():
        raise RunnerError("--stop-reason must be non-empty")
    root = chain_for(attempt)
    require_latest(root, attempt)
    if read_json(attempt / "metadata.json").get("outcome") != "running":
        raise RunnerError("attempt is not running; stop request not queued")
    # Probe the lock, never signal a PID loaded from disk (it may be reused).
    try:
        with chain_lock(root):
            raise RunnerError("no live runner owns the chain; inspect before a fresh review: " + attempt_diagnostics(read_json(attempt / "metadata.json")))
    except RunnerError as exc:
        if "already running" not in str(exc):
            raise
    atomic_json(attempt / "stop-request.json", {"reason": reason.strip(), "requested_at": utc_now()})
    print(f"Stop request queued for {attempt}; this is not an acknowledgement. Poll metadata.json for a terminal outcome.")


def review_fingerprint(config: RunConfig, prompt: str, before: GitSnapshot) -> dict[str, Any]:
    paths = {a.rel: a.abs for a in config.artifacts}
    if config.thread_file:
        paths[config.thread_file.rel] = config.thread_file.abs
    binary = BACKENDS[config.backend].bin_for(config)
    try:
        version = BACKENDS[config.backend].version_for(config)
    except OSError as exc:
        raise RunnerError(f"reviewer binary unavailable: {binary}; install it or check the explicit backend binary flag") from exc
    return {
        "worktree": str(config.worktree), "head": before.head,
        "files": {rel: hashlib.sha256(path.read_bytes()).hexdigest() for rel, path in paths.items()},
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "mode": config.mode, "type": config.review_type, "topic": config.topic,
        "backend": config.backend, "model": active_model(config), "effort": active_effort(config),
        "coding_agent": config.coding_agent,
        "tier": config.selected_tier, "reason": config.driver_tier_reason,
        "binary": str(Path(shutil.which(binary) or binary).resolve()),
        "version": version,
    }


def valid_session_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value.lower()
    except ValueError:
        return False


@contextmanager
def attempt_context(config: RunConfig, prompt: str, before: GitSnapshot):
    source = config.resume_run.resolve() if config.resume_run else None
    if source is None:
        logs = prepare_run_logs(config)
        root = logs.root
    else:
        if config.run_log_dir is not None:
            raise RunnerError("--run-log-dir cannot accompany --resume-run; attempt logs are allocated in the chain")
        root = chain_for(source)
    with chain_lock(root):
        fingerprint = review_fingerprint(config, prompt, before)
        previous: dict[str, Any] = {}
        if source is not None:
            require_latest(root, source)
            previous = read_json(source / "metadata.json")
            if previous.get("outcome") not in ("timeout", "stopped", "interrupted"):
                raise RunnerError(f"attempt is not resumable: outcome={previous.get('outcome')}; only cleaned timeout/stopped/interrupted attempts can resume; {attempt_diagnostics(previous)}")
            if previous.get("cleanup_complete") is not True:
                raise RunnerError("attempt is not resumable: process cleanup was not verified")
            if previous.get("fingerprint") != fingerprint:
                raise RunnerError("resume target or reviewer constraints changed; start a fresh review")
            session_id = previous.get("session_id")
            if not valid_session_id(session_id):
                raise RunnerError("attempt has no valid captured session ID; start a fresh review")
            config = replace(config, resume_session_id=session_id)
            attempt_dir = root / "attempts" / f"{previous['attempt_number'] + 1}-{secrets.token_hex(4)}"
            logs = prepare_run_logs(replace(config, run_log_dir=attempt_dir))
        logs = replace(logs, chain_root=root)
        write_metadata(config, logs, None, outcome="running", before=before)
        patch_metadata(
            logs, phase="created", chain_root=str(root), fingerprint=fingerprint,
            attempt_number=previous.get("attempt_number", 0) + 1,
            resumed_from=str(source) if source else None,
            session_id=config.resume_session_id, session_observed=False,
            runner_pid=os.getpid(), created_at=utc_now(), cleanup_complete=False,
            prior_elapsed_sec=previous.get("cumulative_elapsed_sec", 0),
        )
        atomic_json(root / "chain.json", {"latest_attempt": str(logs.root)})
        print(f"review run_log={logs.root} metadata={logs.metadata}", file=sys.stderr)
        yield config, logs


def group_is_executing(pgid: int) -> bool:
    # killpg(0) also sees unreaped zombies. ps distinguishes those from writers.
    result = subprocess.run(["ps", "-eo", "pgid=,stat="], capture_output=True, text=True, timeout=5)
    if result.returncode:
        raise RunnerError("cannot verify reviewer process-group cleanup")
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == str(pgid) and not fields[1].startswith("Z"):
            return True
    return False


def cleanup_process(proc: subprocess.Popen) -> None:
    def finished() -> bool:
        proc.poll()
        return not group_is_executing(proc.pid)

    def send(sig: int) -> None:
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass
        except PermissionError:
            # Some process sandboxes return EPERM for an already-gone group.
            # Only accept it when the independent process-table check agrees.
            if group_is_executing(proc.pid):
                raise

    if finished():
        proc.wait(timeout=5)
        return
    send(signal.SIGTERM)
    deadline = time.monotonic() + STOP_GRACE_SEC
    while time.monotonic() < deadline:
        if finished():
            proc.wait(timeout=5)
            return
        time.sleep(0.05)
    send(signal.SIGKILL)
    proc.wait(timeout=5)
    deadline = time.monotonic() + 5
    while not finished():
        if time.monotonic() > deadline:
            raise RunnerError("reviewer process group still executing after cleanup; resume refused")
        time.sleep(0.05)


@contextmanager
def captured_signals(received: list[int] | None = None):
    if received is None:
        received = []
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in previous:
        signal.signal(sig, lambda number, frame: received.append(number))
    try:
        yield received
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def run_claude(config: RunConfig, prompt: str, logs: RunLogs, redactor: Redactor) -> ClaudeRunResult:
    """Run either reviewer, retaining recoverable state and owning its process group."""
    backend = BACKENDS[config.backend]
    argv = backend.argv_for(config, logs)
    version = backend.version_for(config)
    if config.resume_session_id:
        prompt = (
            "Continue the interrupted review in this same conversation. Previously completed "
            "reads and tool results remain evidence; an interrupted command may be incomplete. "
            "Do not assume it succeeded or repeat side effects blindly. Complete the remaining "
            "review and return ONE complete final review, not a delta. The original scope, "
            "read-only role, and write-back restrictions still apply.\n\n" + prompt
        )
    logs.prompt.write_text(prompt, encoding="utf-8")
    started_at = utc_now()
    started = time.monotonic()
    last_event = started
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    state = ReviewState()
    token_usage = None
    malformed = 0
    stop_reason = None
    stop_signal = None
    timed_out = False
    observed_session = False
    completed_result = False
    captured_session = config.resume_session_id
    protocol_error = None
    failure_category = None
    print(
        f"{config.backend} review start mode={config.mode} type={config.review_type} "
        f"selected_tier={config.selected_tier} tier_source={config.tier_selection_source} "
        f"driver_tier_reason={json.dumps(config.driver_tier_reason)} "
        f"recommended_tier={config.recommended_tier} "
        f"recommendation_reasons={json.dumps(list(config.recommendation_reasons), separators=(',', ':'))} "
        f"timeout_sec={config.timeout_sec} timeout_source={config.timeout_source} "
        f"model={active_model(config)} effort={active_effort(config)} "
        f"artifacts={','.join(a.rel for a in config.artifacts)}", file=sys.stderr,
    )
    proc = None
    selector = selectors.DefaultSelector()
    buffers = {"stdout": b"", "stderr": b""}
    with captured_signals(logs.signals) as received, logs.stdout.open("w", encoding="utf-8") as stdout_log, logs.stderr.open("w", encoding="utf-8") as stderr_log:
        def consume(label: str, raw: bytes) -> None:
            nonlocal malformed, token_usage, observed_session, captured_session, protocol_error, last_event, completed_result, failure_category
            line = raw.decode("utf-8", errors="replace")
            last_event = time.monotonic()
            if label == "stderr":
                stderr_parts.append(line)
                stderr_log.write(line)
                stderr_log.flush()
                print(redactor.redact(line.rstrip()), file=sys.stderr)
                return
            stdout_parts.append(line)
            stdout_log.write(line)
            stdout_log.flush()
            try:
                event = json.loads(line)
            except ValueError:
                event = {}
            if isinstance(event, dict):
                session = backend.session_for(event)
                if session is not None:
                    if not valid_session_id(session):
                        protocol_error = "backend emitted an invalid session ID"
                    elif config.resume_session_id and session != config.resume_session_id:
                        protocol_error = "backend did not resume the recorded session ID; fresh-session fallback refused"
                    elif captured_session not in (None, session):
                        protocol_error = "backend changed session ID during attempt"
                    elif not observed_session:
                        observed_session = True
                        captured_session = session
                        patch_metadata(logs, session_id=session, session_observed=True, phase="session_captured")
                category = backend.failure_for(event)
                if category:
                    failure_category = category
                    if protocol_error is None:
                        protocol_error = f"{config.backend} session failed; consult private stderr and stream logs"
                if event.get("type") == "result" and not category:
                    completed_result = True
                    if isinstance(event.get("result"), str):
                        state.final_message = event["result"]
                    if isinstance(event.get("usage"), dict):
                        token_usage = event["usage"]
            parsed = backend.parse_line(line)
            malformed += int(parsed.malformed)
            if parsed.text_delta:
                state.text_deltas.append(parsed.text_delta)
            elif parsed.message_text:
                state.final_message = parsed.message_text
                state.messages.append(parsed.message_text)
            if parsed.usage is not None:
                token_usage = parsed.usage
            print(f"{config.backend} review event", file=sys.stderr)

        try:
            proc = subprocess.Popen(argv, cwd=config.worktree, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
            patch_metadata(logs, outcome="running", phase="launched", reviewer_pid=proc.pid, reviewer_pgid=proc.pid, started_at=started_at, argv=argv, reviewer_version=version)
            assert proc.stdin and proc.stdout and proc.stderr
            pending = memoryview(prompt.encode() if backend.prompt_on_stdin else b"")
            for stream, label, mask in ((proc.stdin, "stdin", selectors.EVENT_WRITE), (proc.stdout, "stdout", selectors.EVENT_READ), (proc.stderr, "stderr", selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, mask, label)
            while selector.get_map() or proc.poll() is None:
                now = time.monotonic()
                if received:
                    stop_signal = received[0]
                    stop_reason = signal.Signals(stop_signal).name
                    break
                request = read_json(logs.root / "stop-request.json")
                if request:
                    stop_reason = str(request.get("reason", "driver stop"))
                    break
                if now - started >= config.timeout_sec:
                    timed_out = True
                    break
                if protocol_error:
                    break
                events = selector.select(timeout=0.2)
                for key, _ in events:
                    stream = key.fileobj
                    label = key.data
                    if label == "stdin":
                        try:
                            written = os.write(stream.fileno(), pending[:65536])
                            pending = pending[written:]
                        except BrokenPipeError:
                            pending = memoryview(b"")
                        if not pending:
                            selector.unregister(stream)
                            stream.close()
                        continue
                    try:
                        chunk = os.read(stream.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(stream)
                        if buffers[label]:
                            consume(label, buffers[label])
                            buffers[label] = b""
                        stream.close()
                    else:
                        buffers[label] += chunk
                        while b"\n" in buffers[label]:
                            line, buffers[label] = buffers[label].split(b"\n", 1)
                            consume(label, line + b"\n")
                if now - last_event >= config.heartbeat_sec:
                    print(f"{config.backend} review heartbeat elapsed_sec={int(now - started)}", file=sys.stderr)
                    last_event = now
            cleanup_process(proc)
            patch_metadata(logs, cleanup_complete=True, phase="reviewer_exited")
        finally:
            selector.close()
            if proc is not None:
                if not read_json(logs.metadata).get("cleanup_complete"):
                    try:
                        cleanup_process(proc)
                    except BaseException:
                        # Best-effort termination even when process-table verification
                        # itself fails. The attempt remains non-resumable.
                        try:
                            os.killpg(proc.pid, signal.SIGKILL)
                        except (ProcessLookupError, PermissionError):
                            pass
                        proc.wait(timeout=5)
                        raise
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()
    if protocol_error:
        patch_metadata(logs, reason_category=failure_category or "provider_error")
        if failure_category == "credit_exhausted" and not (timed_out or stop_reason or malformed):
            # Session/protocol inconsistencies never qualify for availability fallback.
            if protocol_error == f"{config.backend} session failed; consult private stderr and stream logs":
                raise CreditExhausted(f"{config.backend} credit allowance exhausted")
        raise RunnerError(protocol_error)
    if config.resume_session_id and not observed_session and not (timed_out or stop_reason):
        raise RunnerError("resumed backend did not confirm the recorded session; session state may be missing")
    if config.backend == BACKEND_GROK and not (timed_out or stop_reason) and (not completed_result or not observed_session or malformed):
        raise RunnerError("Grok review lacks a valid complete result/session or has malformed output")
    assert proc is not None
    returncode = proc.returncode
    if timed_out:
        returncode = -9
    elif stop_reason:
        returncode = -(stop_signal or signal.SIGTERM)
    review_text = backend.finalize(state, logs)
    logs.review.write_text(review_text, encoding="utf-8")
    return ClaudeRunResult(
        returncode=returncode, stdout="".join(stdout_parts), stderr="".join(stderr_parts),
        review_text=review_text, malformed_stream_lines=malformed, timed_out=timed_out,
        started_at=started_at, ended_at=utc_now(), reviewer_version=version, argv=argv,
        token_usage=token_usage, stop_reason=stop_reason, stop_signal=stop_signal,
        elapsed_sec=time.monotonic() - started,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, epilog="Stop: --stop-run ATTEMPT_DIRECTORY --stop-reason REASON. Poll metadata.json for acknowledgement.")
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
    parser.add_argument(
        "--reviewer-backend",
        default=BACKEND_AUTO,
        choices=(BACKEND_AUTO, *BACKEND_ORDER),
        dest="reviewer_backend",
    )
    parser.add_argument(
        "--review-tier",
        default=REVIEW_TIER_AUTO,
        choices=(REVIEW_TIER_AUTO, REVIEW_TIER_NORMAL, REVIEW_TIER_HARD),
        dest="review_tier",
        help=(
            "driver-selected review tier; pass normal or hard explicitly. Normal is the default; "
            "reserve hard for roughly the hardest 20%% of tasks (major design/architecture or difficult bugs), not a quota. "
            "Legacy auto compatibility always selects normal and is deprecated"
        ),
    )
    parser.add_argument(
        "--tier-reason",
        help="required non-empty driver rationale for --review-tier hard; forbidden otherwise",
    )
    parser.add_argument("--model", help="explicit Claude model override")
    parser.add_argument("--effort", help="explicit Claude effort override")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--codex-model", help="explicit Codex model override")
    parser.add_argument("--codex-effort", help="explicit Codex reasoning-effort override")
    parser.add_argument("--grok-bin", default="grok")
    parser.add_argument("--grok-model", help="explicit Grok model override")
    parser.add_argument("--grok-effort", help="explicit Grok reasoning-effort override; do not evade rare-hard guidance")
    parser.add_argument("--coding-agent", help="current coding agent name; explicit identity wins markers. Grok drivers must pass grok")
    parser.add_argument("--timeout-sec", type=int, help="positive attempt limit; default normal/auto 1800, hard 3600 seconds")
    parser.add_argument("--resume-run", help="resume the exact latest interrupted attempt directory with the same scope/profile arguments")
    parser.add_argument("--heartbeat-sec", type=int, default=DEFAULT_HEARTBEAT_SEC)
    parser.add_argument("--run-log-dir")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace, env: Mapping[str, str] | None = None) -> RunConfig:
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
    if (args.timeout_sec is not None and args.timeout_sec <= 0) or args.heartbeat_sec <= 0:
        raise RunnerError("timeout and heartbeat must be positive")
    run_log_dir = Path(args.run_log_dir).expanduser().resolve() if args.run_log_dir else None
    identity = coding_identity(args.coding_agent, os.environ if env is None else env,
                               explicit_backend=args.reviewer_backend != BACKEND_AUTO)
    backend = args.reviewer_backend
    if args.resume_run:
        previous = read_json(Path(args.resume_run).expanduser().resolve() / "metadata.json")
        recorded = previous.get("backend")
        if recorded not in BACKENDS or (backend != BACKEND_AUTO and backend != recorded):
            raise RunnerError("resume reviewer backend disagrees with recorded attempt")
        if previous.get("coding_agent") != identity:
            raise RunnerError("resume coding identity changed or legacy handle lacks identity; start a fresh review")
        backend = recorded
    elif backend == BACKEND_AUTO:
        backend = next(name for name in BACKEND_ORDER if name != identity)
    if identity == "unknown" and args.reviewer_backend == BACKEND_AUTO:
        print("warning: unknown coding agent cannot guarantee same-agent exclusion; pass --coding-agent NAME (required for Grok drivers)", file=sys.stderr)
    recommended_tier, recommendation_reasons = recommend_review_tier(
        args.review_type, artifacts, focus
    )
    selected_tier, tier_selection_source, driver_tier_reason = resolve_review_tier(
        args.review_tier, args.tier_reason
    )
    if tier_selection_source == TIER_SELECTION_LEGACY_AUTO:
        print(
            "warning: --review-tier auto compatibility is deprecated and always selects "
            "normal; pass --review-tier normal or hard explicitly",
            file=sys.stderr,
        )
    if recommended_tier == REVIEW_TIER_HARD and selected_tier == REVIEW_TIER_NORMAL:
        print(
            "notice: runner recommends hard from mechanical signals "
            f"({'; '.join(recommendation_reasons)}); selected tier and model remain normal",
            file=sys.stderr,
        )
        print("notice: mechanical hints do not qualify for hard; reserve it for roughly the hardest 20% of tasks", file=sys.stderr)
    claude_model, claude_effort = REVIEW_MODEL_MATRIX[BACKEND_CLAUDE][selected_tier]
    codex_model, codex_effort = REVIEW_MODEL_MATRIX[BACKEND_CODEX][selected_tier]
    grok_model, grok_effort = REVIEW_MODEL_MATRIX[BACKEND_GROK][selected_tier]
    config = RunConfig(
        protocol_dir=protocol_dir,
        worktree=worktree,
        mode=args.mode,
        review_type=args.review_type,
        artifacts=artifacts,
        focus=focus,
        thread_file=thread_file,
        topic=args.topic,
        backend=backend,
        selected_tier=selected_tier,
        tier_selection_source=tier_selection_source,
        driver_tier_reason=driver_tier_reason,
        recommended_tier=recommended_tier,
        recommendation_reasons=recommendation_reasons,
        model=claude_model,
        effort=claude_effort,
        model_source="profile",
        effort_source="profile",
        claude_bin=args.claude_bin,
        codex_bin=args.codex_bin,
        codex_model=codex_model,
        codex_effort=codex_effort,
        grok_bin=args.grok_bin,
        grok_model=grok_model,
        grok_effort=grok_effort,
        requested_backend=args.reviewer_backend,
        coding_agent=identity,
        profile_overrides=(("claude", args.model, args.effort),
                           ("codex", args.codex_model, args.codex_effort),
                           ("grok", args.grok_model, args.grok_effort)),
        timeout_sec=args.timeout_sec if args.timeout_sec is not None else (HARD_TIMEOUT_SEC if selected_tier == REVIEW_TIER_HARD else DEFAULT_TIMEOUT_SEC),
        timeout_source="explicit --timeout-sec" if args.timeout_sec is not None else "profile",
        resume_run=Path(args.resume_run).expanduser().resolve() if args.resume_run else None,
        heartbeat_sec=args.heartbeat_sec,
        run_log_dir=run_log_dir,
        dry_run=args.dry_run,
    )
    return select_profile(config, backend)


def run_attempt(config: RunConfig) -> None:
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
    with attempt_context(config, prompt, before) as (config, logs), captured_signals() as signals:
        logs = replace(logs, signals=signals)
        result = None
        after = None
        try:
            result = run_claude(config, prompt, logs, redactor)
            after = git_snapshot(config.worktree)
            if result.timed_out or result.stop_reason:
                dirty = " with uncommitted changes" if after.status.strip() else ""
                outcome = "timeout" if result.timed_out else ("interrupted" if result.stop_signal else "stopped")
                message = f"{config.backend} review timed out{dirty}" if result.timed_out else f"{config.backend} review {outcome}{dirty}: {result.stop_reason}"
                write_metadata(config, logs, result, outcome=outcome, error=message, before=before, after=after)
                patch_metadata(logs, phase=outcome)
                print(f"Review incomplete. Attempt: {logs.root}. Resume with --resume-run and the same scope/profile arguments after checking metadata.json.", file=sys.stderr)
                raise RunnerError(message, exit_code=2 if result.timed_out else (128 + result.stop_signal if result.stop_signal else 3))
            with captured_signals(signals) as late_signals:
                write_metadata(config, logs, result, outcome="finalizing", before=before, after=after)
                patch_metadata(logs, phase="finalizing")
                if config.mode == MODE_WRITE:
                    verify_reviewer_output(config, before, after, result)
                    append_and_commit_review(config, result.review_text)
                    after = git_snapshot(config.worktree)
                    verify_write_mode(config, before, after, result)
                else:
                    verify_print_mode(config, before, after, result)
                    print(redactor.redact(result.review_text).rstrip())
                write_metadata(config, logs, result, outcome="success", before=before, after=after)
                patch_metadata(logs, phase="success", late_signals=list(late_signals), late_stop_request=read_json(logs.root / "stop-request.json") or None)
            print(f"{config.backend} structured review completed run_log={redactor.redact(str(logs.root))}", file=sys.stderr)
        except BaseException as exc:
            # Never turn an error or a finalization crash into a resumable attempt.
            current = read_json(logs.metadata).get("outcome")
            if current not in ("timeout", "stopped", "interrupted", "success"):
                after = git_snapshot(config.worktree)
                outcome = "failed" if isinstance(exc, RunnerError) else "error"
                write_metadata(config, logs, result, outcome=outcome, error=str(exc), before=before, after=after)
                patch_metadata(logs, phase=outcome)
            if isinstance(exc, CreditExhausted):
                exc.attempt = logs.root
                if (after != before or not read_json(logs.metadata).get("cleanup_complete")
                        or signals or read_json(logs.root / "stop-request.json")):
                    raise RunnerError("credit failure is not safe to advance: changed target, stop request, or unverified cleanup") from exc
            if isinstance(exc, (RunnerError, KeyboardInterrupt, SystemExit)):
                raise
            raise RunnerError(f"reviewer run errored: {exc}") from exc


def run(config: RunConfig) -> None:
    if config.requested_backend != BACKEND_AUTO or config.resume_run or config.dry_run:
        run_attempt(config)
        return
    before = git_snapshot(config.worktree)
    require_clean(before)
    history: list[dict[str, str]] = []
    previous_attempt: Path | None = None
    for backend in BACKEND_ORDER:
        if backend == config.coding_agent:
            history.append({"backend": backend, "reason": "coding_agent_excluded"})
            print(f"review selection skip backend={backend} reason=coding_agent_excluded", file=sys.stderr)
            continue
        binary = BACKENDS[backend].bin_for(config)
        if shutil.which(binary) is None:
            history.append({"backend": backend, "reason": "binary_unavailable"})
            print(f"review selection skip backend={backend} reason=binary_unavailable", file=sys.stderr)
            continue
        if git_snapshot(config.worktree) != before:
            raise RunnerError("review target changed between candidates; fallback refused")
        candidate = select_profile(config, backend) if backend != config.backend else config
        candidate = replace(candidate, selection_history=tuple(history))
        if previous_attempt is not None:
            next_dir = previous_attempt / "fallback" / backend
            atomic_json(previous_attempt / "selection.json", {"next_backend": backend, "next_attempt": str(next_dir)})
            candidate = replace(candidate, run_log_dir=next_dir)
        try:
            run_attempt(candidate)
            return
        except CreditExhausted as exc:
            assert exc.attempt is not None
            previous_attempt = exc.attempt
            history.append({"backend": backend, "reason": "credit_exhausted", "attempt": str(exc.attempt)})
            print(f"review selection unavailable backend={backend} reason=credit_exhausted; trying next eligible backend", file=sys.stderr)
    if previous_attempt is not None:
        atomic_json(previous_attempt / "selection.json", {"outcome": "exhausted", "selection_history": history})
    summary = ", ".join(f"{item['backend']}:{item['reason']}" for item in history)
    raise RunnerError(f"no eligible reviewer available ({summary}); all three backends unavailable or excluded; human assistance required")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        raw = list(sys.argv[1:] if argv is None else argv)
        if "--stop-run" in raw:
            parser = argparse.ArgumentParser(description="Queue a cooperative review stop; poll metadata for acknowledgement")
            parser.add_argument("--stop-run", required=True)
            parser.add_argument("--stop-reason", required=True)
            stop = parser.parse_args(raw)
            request_stop(Path(stop.stop_run).expanduser().resolve(), stop.stop_reason)
            return 0
        args = parse_args(raw)
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

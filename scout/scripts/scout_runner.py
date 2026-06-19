#!/usr/bin/env python3
"""Mechanical helper for Scout runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by environment, not logic
    raise SystemExit("PyYAML is required. Install with: python -m pip install PyYAML") from exc


SUBSKILL_REFERENCES = {
    "script-lifecycle": Path("references/script-lifecycle.md"),
    "code-reachability": Path("references/code-reachability-backend-python.md"),
    "document-structure": Path("references/document-structure.md"),
    "document-lifecycle-drift": Path("references/document-lifecycle-drift.md"),
    "code-structure": Path("references/code-structure.md"),
}
CORE_FIELDS = (
    "version",
    "enabled_subskills",
    "report",
    "repo_context",
)
REPORT_HEADINGS = (
    "# Scout Report",
    "## Run Metadata",
    "## Executive Summary",
    "## Proposed Backlog Changes",
    "## Human Review Queue",
    "## Subskill Results",
    "## Tool Commands",
    "## Runner Validation",
)
RUNNER_CHECK_PROVENANCE_TOKENS = ("scout_runner.py", "check")
WRITE_ENABLED_BACKLOG_PROVENANCE_TOKEN = "backlog"
SUBSKILL_SUBHEADINGS = (
    "#### Context And Tools Used",
    "#### Candidate Proposals",
    "#### Candidate Refinements",
    "#### Report-Only Observations",
    "#### Ignored Noise",
    "#### Inconclusive Items",
)
DOCUMENT_STRUCTURE_THRESHOLDS = (
    "index_review_lines",
    "doc_review_lines",
    "doc_large_lines",
)
CODE_STRUCTURE_ADAPTERS = ("python", "typescript_react")
CODE_STRUCTURE_THRESHOLDS = {
    "python": ("review_lines", "large_lines", "script_review_lines"),
    "typescript_react": ("review_lines", "large_lines", "route_large_lines"),
    "shared": ("churn_since_days", "high_churn_commits"),
}


class RunnerError(RuntimeError):
    pass


def load_yaml(path: Path, *, label: str = "YAML") -> dict[str, Any]:
    if not path.exists():
        raise RunnerError(f"{label} is missing: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RunnerError(f"{label} parse failed: {exc}") from exc
    if not isinstance(data, dict):
        raise RunnerError(f"{label} must be a mapping")
    return data


def require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunnerError(f"{label} must be a mapping")
    return value


def require_list(value: Any, label: str, *, non_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise RunnerError(f"{label} must be a list")
    if non_empty and not value:
        raise RunnerError(f"{label} must not be empty")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunnerError(f"{label} must be a non-empty string")
    return value


def require_string_list(value: Any, label: str, *, non_empty: bool = False) -> list[str]:
    raw = require_list(value, label, non_empty=non_empty)
    for index, item in enumerate(raw):
        require_string(item, f"{label}[{index}]")
    return list(raw)


def require_positive_int(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RunnerError(f"{label} must be a positive integer")


def validate_known_thresholds(raw: Any, label: str, fields: tuple[str, ...]) -> None:
    thresholds = require_mapping(raw, label)
    for field in fields:
        if field in thresholds:
            require_positive_int(thresholds[field], f"{label}.{field}")


def require_adapter_roots(raw: Any, label: str) -> dict[str, list[str]]:
    adapters = require_mapping(raw, label)
    if not adapters:
        raise RunnerError(f"{label} must declare at least one adapter")
    parsed: dict[str, list[str]] = {}
    for adapter, roots in adapters.items():
        if adapter not in CODE_STRUCTURE_ADAPTERS:
            raise RunnerError(f"{label}.{adapter} is not a supported adapter")
        parsed[adapter] = require_string_list(roots, f"{label}.{adapter}", non_empty=True)
    return parsed


def validate_adapter_string_lists(raw: Any, label: str) -> None:
    adapters = require_mapping(raw, label)
    for adapter, values in adapters.items():
        if adapter not in CODE_STRUCTURE_ADAPTERS:
            raise RunnerError(f"{label}.{adapter} is not a supported adapter")
        require_string_list(values, f"{label}.{adapter}")


def validate_code_structure_thresholds(raw: Any, label: str) -> None:
    thresholds = require_mapping(raw, label)
    for category, fields in CODE_STRUCTURE_THRESHOLDS.items():
        if category in thresholds:
            validate_known_thresholds(thresholds[category], f"{label}.{category}", fields)


def validate_version_pin(value: str, label: str) -> None:
    lowered = value.lower()
    if (
        any(marker in lowered for marker in ("<", ">", "*", "pinned-by-adopting-repo"))
        or lowered.endswith(".x")
        or lowered == "x"
    ):
        raise RunnerError(f"{label} must be an exact version pin, not a range or placeholder")


def protocol_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_path(repo_root: Path, raw: str, label: str) -> Path:
    path = (repo_root / raw).resolve()
    try:
        path.relative_to(repo_root)
    except ValueError as exc:
        raise RunnerError(f"{label} must stay inside repo: {raw}") from exc
    return path


def validate_overlay(repo_root: Path, overlay_path: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    data = load_yaml(overlay_path, label="overlay YAML")
    missing = [field for field in CORE_FIELDS if field not in data]
    if missing:
        raise RunnerError(f"overlay missing fields: {', '.join(missing)}")
    if data["version"] != 1:
        raise RunnerError("overlay version must be 1")

    enabled = require_string_list(data["enabled_subskills"], "enabled_subskills", non_empty=True)
    report = require_mapping(data["report"], "report")
    output_root = require_string(report.get("output_root"), "report.output_root")
    repo_path(repo_root, output_root, "report.output_root")

    repo_context = require_mapping(data["repo_context"], "repo_context")
    require_string_list(repo_context.get("entry_files"), "repo_context.entry_files")
    backlog_path = require_string(repo_context.get("backlog_path"), "repo_context.backlog_path")
    repo_path(repo_root, backlog_path, "repo_context.backlog_path")
    require_string_list(repo_context.get("active_docs"), "repo_context.active_docs")
    require_string_list(repo_context.get("archive_paths"), "repo_context.archive_paths")

    subskills = require_mapping(data.get("subskills"), "subskills")
    for subskill in enabled:
        ref = SUBSKILL_REFERENCES.get(subskill)
        if ref is None:
            raise RunnerError(f"enabled subskill has no shared protocol: {subskill}")
        if not (protocol_root() / ref).exists():
            raise RunnerError(f"subskill reference is missing: {ref}")
        if subskill not in subskills:
            raise RunnerError(f"subskills.{subskill} is required")

    if "script-lifecycle" in enabled:
        script = require_mapping(subskills["script-lifecycle"], "subskills.script-lifecycle")
        require_string_list(script.get("script_roots"), "subskills.script-lifecycle.script_roots", non_empty=True)
        require_string_list(
            script.get("script_entrypoint_sources"),
            "subskills.script-lifecycle.script_entrypoint_sources",
            non_empty=True,
        )
        if "known_manual_entrypoints" in script:
            require_string_list(script["known_manual_entrypoints"], "subskills.script-lifecycle.known_manual_entrypoints")
        if "historical_script_contexts" in script:
            require_string_list(script["historical_script_contexts"], "subskills.script-lifecycle.historical_script_contexts")
        if "repo_notes" in script:
            require_string(script["repo_notes"], "subskills.script-lifecycle.repo_notes")

    if "code-reachability" in enabled:
        code = require_mapping(subskills["code-reachability"], "subskills.code-reachability")
        python = require_mapping(code.get("python"), "subskills.code-reachability.python")
        require_string_list(python.get("production_roots"), "subskills.code-reachability.python.production_roots", non_empty=True)
        require_string_list(python.get("test_roots"), "subskills.code-reachability.python.test_roots")
        require_string_list(python.get("active_contract_sources"), "subskills.code-reachability.python.active_contract_sources")
        require_string_list(python.get("dynamic_entrypoint_sources"), "subskills.code-reachability.python.dynamic_entrypoint_sources")
        if "known_false_positive_classes" in python:
            require_string_list(
                python["known_false_positive_classes"],
                "subskills.code-reachability.python.known_false_positive_classes",
            )
        if "repo_notes" in code:
            require_string(code["repo_notes"], "subskills.code-reachability.repo_notes")
        if "vulture" in python:
            vulture = require_mapping(python["vulture"], "subskills.code-reachability.python.vulture")
            require_string_list(vulture.get("roots"), "subskills.code-reachability.python.vulture.roots", non_empty=True)
            version = require_string(vulture.get("version"), "subskills.code-reachability.python.vulture.version")
            validate_version_pin(version, "subskills.code-reachability.python.vulture.version")
            if "min_confidence" in vulture:
                min_confidence = vulture["min_confidence"]
                if not isinstance(min_confidence, int) or min_confidence < 0 or min_confidence > 100:
                    raise RunnerError("subskills.code-reachability.python.vulture.min_confidence must be 0..100")
            if "ignore_decorators" in vulture:
                require_string_list(vulture["ignore_decorators"], "subskills.code-reachability.python.vulture.ignore_decorators")
            if "ignore_names" in vulture:
                require_string_list(vulture["ignore_names"], "subskills.code-reachability.python.vulture.ignore_names")

    if "document-structure" in enabled:
        document = require_mapping(subskills["document-structure"], "subskills.document-structure")
        require_string_list(document.get("entry_docs"), "subskills.document-structure.entry_docs", non_empty=True)
        require_string_list(document.get("index_docs"), "subskills.document-structure.index_docs")
        require_string_list(document.get("doc_roots"), "subskills.document-structure.doc_roots", non_empty=True)
        if "archive_paths" in document:
            require_string_list(document["archive_paths"], "subskills.document-structure.archive_paths")
        if "thresholds" in document:
            validate_known_thresholds(
                document["thresholds"],
                "subskills.document-structure.thresholds",
                DOCUMENT_STRUCTURE_THRESHOLDS,
            )
        if "repo_notes" in document:
            require_string(document["repo_notes"], "subskills.document-structure.repo_notes")

    if "document-lifecycle-drift" in enabled:
        drift = require_mapping(subskills["document-lifecycle-drift"], "subskills.document-lifecycle-drift")
        require_string_list(drift.get("entry_docs"), "subskills.document-lifecycle-drift.entry_docs", non_empty=True)
        require_string_list(drift.get("current_docs"), "subskills.document-lifecycle-drift.current_docs", non_empty=True)
        require_string_list(drift.get("doc_roots"), "subskills.document-lifecycle-drift.doc_roots", non_empty=True)
        if "archive_paths" in drift:
            require_string_list(drift["archive_paths"], "subskills.document-lifecycle-drift.archive_paths")
        if "status_sources" in drift:
            require_string_list(drift["status_sources"], "subskills.document-lifecycle-drift.status_sources")
        if "runbook_roots" in drift:
            require_string_list(drift["runbook_roots"], "subskills.document-lifecycle-drift.runbook_roots")
        if "repo_notes" in drift:
            require_string(drift["repo_notes"], "subskills.document-lifecycle-drift.repo_notes")

    if "code-structure" in enabled:
        structure = require_mapping(subskills["code-structure"], "subskills.code-structure")
        require_adapter_roots(structure.get("roots"), "subskills.code-structure.roots")
        if "test_roots" in structure:
            validate_adapter_string_lists(structure["test_roots"], "subskills.code-structure.test_roots")
        if "active_contract_sources" in structure:
            require_string_list(
                structure["active_contract_sources"],
                "subskills.code-structure.active_contract_sources",
            )
        if "thresholds" in structure:
            validate_code_structure_thresholds(
                structure["thresholds"],
                "subskills.code-structure.thresholds",
            )
        if "repo_notes" in structure:
            require_string(structure["repo_notes"], "subskills.code-structure.repo_notes")

    backlog = repo_path(repo_root, repo_context["backlog_path"], "repo_context.backlog_path")
    if not backlog.exists():
        raise RunnerError(f"configured backlog is missing: {repo_context['backlog_path']}")
    load_yaml(backlog, label="backlog YAML")
    return data


def git_value(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def next_run_dir(root: Path, date: str, slug: str) -> Path:
    base = root / f"{date}_{slug}"
    if not base.exists():
        return base
    index = 2
    while True:
        candidate = root / f"{date}_{slug}_{index}"
        if not candidate.exists():
            return candidate
        index += 1


def report_skeleton(data: dict[str, Any], repo_root: Path, overlay: Path, run_dir: Path, mode: str) -> str:
    enabled = data["enabled_subskills"]
    branch = git_value(repo_root, "branch", "--show-current") or git_value(repo_root, "rev-parse", "--short", "HEAD")
    lines = [
        "# Scout Report",
        "",
        "## Run Metadata",
        f"- Repo: {repo_root.name}",
        f"- Branch/worktree: {branch}",
        f"- Date: {datetime.now(UTC).date().isoformat()}",
        f"- Mode: {mode}",
        f"- Overlay: {overlay.as_posix()}",
        f"- Enabled subskills: {', '.join(enabled)}",
        f"- Backlog path: {data['repo_context']['backlog_path']}",
        f"- Report output dir: {run_dir.as_posix()}",
        "",
        "## Executive Summary",
        "- Proposed candidate count: 0",
        "- Proposed refinement count: 0",
        "- Report-only observation count: 0",
        "- Ignored noise count: 0",
        "- Inconclusive count: 0",
        "- Summary: None.",
        "",
        "## Proposed Backlog Changes",
        "",
        "### Candidate Proposals",
        "None.",
        "",
        "### Candidate Refinements",
        "None.",
        "",
        "## Human Review Queue",
        "None.",
        "",
        "## Subskill Results",
    ]
    for subskill in enabled:
        lines.extend(["", f"### {subskill}"])
        for heading in SUBSKILL_SUBHEADINGS:
            lines.extend(["", heading, "None."])
    lines.extend(
        [
            "",
            "## Tool Commands",
            "None.",
            "",
            "## Runner Validation",
            "- Setup: completed.",
        ]
    )
    return "\n".join(lines) + "\n"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_skeleton(mode: str, backlog_sha256: str) -> str:
    if mode == "dry-run":
        backlog_lines = [
            "- Dry-run reports do not modify backlog YAML.",
            f"- Backlog baseline sha256: {backlog_sha256}",
        ]
        note = "- Candidate proposals require explicit human approval before backlog writes."
    else:
        backlog_lines = [
            "- Write-enabled runs may modify backlog YAML.",
            "- Backlog/report changes must be validated and committed separately per subskill.",
        ]
        note = "- Candidate proposals/refinements written to backlog must follow backlog-maintenance."

    return "\n".join(
        [
            "# Scout Run Output Manifest",
            "",
            "Status: open; Scout run report generated",
            "Owner: Scout run driver",
            "PR: pending",
            f"Created: {datetime.now(UTC).date().isoformat()}",
            "Closed: pending",
            "",
            "## Primary Plans",
            "",
            "- None. This folder records Scout run evidence.",
            "",
            "## Artifacts",
            "",
            "| Path | Type | Keep / delete / archive policy | Owner | Referenced by | Notes |",
            "| --- | --- | --- | --- | --- | --- |",
            "| `MANIFEST.md` | manifest | Keep permanently with this Scout output folder. | Scout run driver | output-manifest check | Owns the lifecycle of artifacts in this folder. |",
            "| `SCOUT_REPORT.md` | Scout report | Keep permanently as repo-safe Scout discovery evidence. | Scout run driver | backlog candidates / closeout | Records subskill findings, commands, validation, and backlog write behavior. |",
            "",
            "## Lifecycle Rules",
            "",
            "- This folder stores repo-safe Scout run evidence only.",
            "- Every committed artifact in this folder must appear in the Artifacts table above.",
            "- Scratch/debug/temp artifacts must be deleted before closeout or moved to ignored private storage.",
            "- Do not add secrets, tokens, credentials, provider balances, raw production rows, private host identifiers, or local environment files.",
            "",
            "## Human Acceptance",
            "",
            "- Human review is required before promoted Scout candidates become accepted backlog work.",
            "",
            "## Next / Backlog",
            "",
            "- Review candidate proposals/refinements in `SCOUT_REPORT.md` and update backlog state according to the owning repo's backlog protocol.",
            "",
            "## Validation",
            "",
            "- Report skeleton created by Scout runner.",
            "- Overlay parsed by Scout runner.",
            "",
            "## Backlog Write Mode",
            "",
            f"- Mode: {mode}",
            *backlog_lines,
            "",
            "## Notes",
            "",
            note,
        ]
    ) + "\n"


def cmd_setup(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    overlay = (repo_root / args.overlay).resolve()
    data = validate_overlay(repo_root, overlay)
    output_root = repo_root / data["report"]["output_root"]
    run_date = args.date or datetime.now(UTC).date().isoformat()
    run_dir = next_run_dir(output_root, run_date, args.slug)
    run_dir.mkdir(parents=True)
    backlog_sha256 = file_sha256(repo_root / data["repo_context"]["backlog_path"])
    (run_dir / "SCOUT_REPORT.md").write_text(report_skeleton(data, repo_root, Path(args.overlay), run_dir.relative_to(repo_root), args.mode), encoding="utf-8")
    (run_dir / "MANIFEST.md").write_text(manifest_skeleton(args.mode, backlog_sha256), encoding="utf-8")
    print(run_dir.relative_to(repo_root).as_posix())
    return 0


def contains_heading(text: str, heading: str) -> bool:
    return re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE) is not None


def section_text(text: str, heading: str, next_level_prefix: str, *, artifact: str = "SCOUT_REPORT.md") -> str:
    pattern = re.compile(rf"^{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        raise RunnerError(f"{artifact} missing section: {heading}")
    next_heading = re.search(rf"^{re.escape(next_level_prefix)}\s+", text[match.end() :], re.MULTILINE)
    if next_heading is None:
        return text[match.end() :]
    return text[match.end() : match.end() + next_heading.start()]


def manifest_backlog_baseline(manifest: str) -> str | None:
    match = re.search(r"^- Backlog baseline sha256: ([0-9a-f]{64})\s*$", manifest, re.MULTILINE)
    return match.group(1) if match else None


def contains_all_tokens(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(token.lower() in lowered for token in tokens)


def require_validation_provenance(report: str, manifest: str, mode: str) -> None:
    report_validation = section_text(report, "## Runner Validation", "##")
    manifest_validation = section_text(manifest, "## Validation", "##", artifact="MANIFEST.md")
    if not contains_all_tokens(report_validation, RUNNER_CHECK_PROVENANCE_TOKENS):
        raise RunnerError("SCOUT_REPORT.md Runner Validation must record the scout_runner.py check command")
    if not contains_all_tokens(manifest_validation, RUNNER_CHECK_PROVENANCE_TOKENS):
        raise RunnerError("MANIFEST.md Validation must record the scout_runner.py check command")
    if mode == "write-enabled":
        backlog_tokens = (WRITE_ENABLED_BACKLOG_PROVENANCE_TOKEN,)
        if not contains_all_tokens(report_validation, backlog_tokens):
            raise RunnerError("SCOUT_REPORT.md Runner Validation must record repo backlog checker provenance in write-enabled mode")
        if not contains_all_tokens(manifest_validation, backlog_tokens):
            raise RunnerError("MANIFEST.md Validation must record repo backlog checker provenance in write-enabled mode")


def cmd_check(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    overlay = (repo_root / args.overlay).resolve()
    data = validate_overlay(repo_root, overlay)
    run_dir = (repo_root / args.run_dir).resolve()
    report_path = run_dir / "SCOUT_REPORT.md"
    manifest_path = run_dir / "MANIFEST.md"
    if not report_path.exists():
        raise RunnerError("SCOUT_REPORT.md is missing")
    if not manifest_path.exists():
        raise RunnerError("MANIFEST.md is missing")
    report = report_path.read_text(encoding="utf-8")
    manifest = manifest_path.read_text(encoding="utf-8")
    for heading in REPORT_HEADINGS:
        if not contains_heading(report, heading):
            raise RunnerError(f"SCOUT_REPORT.md missing heading: {heading}")
    for subskill in data["enabled_subskills"]:
        if not contains_heading(report, f"### {subskill}"):
            raise RunnerError(f"SCOUT_REPORT.md missing subskill section: {subskill}")
        subskill_text = section_text(report, f"### {subskill}", "###")
        for heading in SUBSKILL_SUBHEADINGS:
            if heading not in subskill_text:
                raise RunnerError(f"SCOUT_REPORT.md missing {subskill} subsection: {heading}")
    if re.search(r"\bTODO\b", report) or re.search(r"\bTODO\b", manifest):
        raise RunnerError("report artifacts contain TODO placeholders")
    for heading in ("# Scout Run Output Manifest", "## Primary Plans", "## Artifacts", "## Lifecycle Rules", "## Human Acceptance", "## Next / Backlog", "## Validation", "## Backlog Write Mode"):
        if not contains_heading(manifest, heading):
            raise RunnerError(f"MANIFEST.md missing heading: {heading}")
    require_validation_provenance(report, manifest, args.mode)
    if args.mode == "dry-run":
        baseline = manifest_backlog_baseline(manifest)
        if baseline is None:
            raise RunnerError("MANIFEST.md missing backlog baseline sha256")
        current = file_sha256(repo_root / data["repo_context"]["backlog_path"])
        if current != baseline:
            raise RunnerError("dry-run mode must not modify backlog YAML")
    print("ok")
    return 0


def canonical_list(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(values))


def toml_string(value: str) -> str:
    return json.dumps(value)


def toml_list(values: list[str]) -> str:
    return "[" + ", ".join(toml_string(value) for value in canonical_list(values)) + "]"


def vulture_config_text(data: dict[str, Any]) -> str:
    vulture = data["subskills"]["code-reachability"]["python"]["vulture"]
    min_confidence = vulture.get("min_confidence", 60)
    lines = [
        "[tool.vulture]",
        f"paths = {toml_list(require_string_list(vulture.get('roots'), 'vulture.roots', non_empty=True))}",
        f"min_confidence = {min_confidence}",
        f"ignore_decorators = {toml_list(require_string_list(vulture.get('ignore_decorators', []), 'vulture.ignore_decorators'))}",
        f"ignore_names = {toml_list(require_string_list(vulture.get('ignore_names', []), 'vulture.ignore_names'))}",
    ]
    return "\n".join(lines) + "\n"


def cmd_vulture_config(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    overlay = (repo_root / args.overlay).resolve()
    data = validate_overlay(repo_root, overlay)
    output = args.output.resolve()
    try:
        output.relative_to(repo_root)
    except ValueError:
        pass
    else:
        if not args.allow_repo_output:
            raise RunnerError("vulture adapter output must be outside the repo unless --allow-repo-output is set")
    text = vulture_config_text(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(hashlib.sha256(text.encode("utf-8")).hexdigest())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--overlay", default=".agent-protocols/scout.yml")
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup")
    setup.add_argument("--mode", choices=("dry-run", "write-enabled"), default="dry-run")
    setup.add_argument("--date")
    setup.add_argument("--slug", default="scout_run")
    setup.set_defaults(func=cmd_setup)

    check = sub.add_parser("check")
    check.add_argument("--run-dir", required=True)
    check.add_argument("--mode", choices=("dry-run", "write-enabled"), default="dry-run")
    check.set_defaults(func=cmd_check)

    vulture = sub.add_parser("vulture-config")
    vulture.add_argument("--output", type=Path, required=True)
    vulture.add_argument("--allow-repo-output", action="store_true")
    vulture.set_defaults(func=cmd_vulture_config)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except RunnerError as exc:
        print(f"scout_runner.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

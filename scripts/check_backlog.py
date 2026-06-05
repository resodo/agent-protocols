#!/usr/bin/env python3
"""Validate docs/backlog.yml against the shared backlog-maintenance contract."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by environment, not logic
    raise SystemExit("PyYAML is required. Install with: python -m pip install PyYAML") from exc


VALID_STATUSES = {"open", "closed"}
VALID_PRIORITIES = {"P0", "P1", "P2"}
VALID_RESOLUTIONS = {"completed", "cancelled", "transferred"}
OPEN_REQUIRED = {"id", "status", "priority", "kind", "title", "why", "next", "done_when"}
CLOSED_REQUIRED = {
    "id",
    "status",
    "priority",
    "kind",
    "title",
    "resolution",
    "closed_at",
    "outcome",
    "refs",
}
TOP_LEVEL_REQUIRED = {"version", "repo", "id_prefix", "kinds", "items"}


class ValidationError(Exception):
    pass


def _load_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise ValidationError(f"YAML parse failed: {exc}") from exc


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must be a mapping")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{label} must be a list")
    return value


def _require_nonempty_string(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a non-empty string")


def validate_backlog(root: Path) -> None:
    backlog_path = root / "docs/backlog.yml"
    retired_markdown = root / "docs/backlog.md"

    if not backlog_path.exists():
        raise ValidationError("docs/backlog.yml is missing")
    if retired_markdown.exists():
        raise ValidationError("active docs/backlog.md must not exist")

    data = _require_mapping(_load_yaml(backlog_path), "docs/backlog.yml")
    missing_top = sorted(TOP_LEVEL_REQUIRED - data.keys())
    if missing_top:
        raise ValidationError(f"missing top-level fields: {', '.join(missing_top)}")

    if data["version"] != 1:
        raise ValidationError("version must be 1")
    _require_nonempty_string(data["repo"], "repo")
    _require_nonempty_string(data["id_prefix"], "id_prefix")

    kinds = _require_list(data["kinds"], "kinds")
    if not kinds or any(not isinstance(kind, str) or not kind.strip() for kind in kinds):
        raise ValidationError("kinds must contain non-empty strings")
    kind_set = set(kinds)
    if len(kind_set) != len(kinds):
        raise ValidationError("kinds must be unique")

    items = _require_list(data["items"], "items")
    id_prefix = data["id_prefix"]
    id_re = re.compile(rf"^{re.escape(id_prefix)}-\d{{4}}$")
    seen_ids: set[str] = set()

    for index, raw_item in enumerate(items):
        item = _require_mapping(raw_item, f"items[{index}]")
        item_id = item.get("id")
        _require_nonempty_string(item_id, f"items[{index}].id")
        if not id_re.fullmatch(item_id):
            raise ValidationError(f"{item_id} does not match {id_prefix}-NNNN")
        if item_id in seen_ids:
            raise ValidationError(f"duplicate backlog id: {item_id}")
        seen_ids.add(item_id)

        status = item.get("status")
        priority = item.get("priority")
        kind = item.get("kind")
        title = item.get("title")
        if status not in VALID_STATUSES:
            raise ValidationError(f"{item_id} status must be open or closed")
        if priority not in VALID_PRIORITIES:
            raise ValidationError(f"{item_id} priority must be P0, P1, or P2")
        if kind not in kind_set:
            raise ValidationError(f"{item_id} kind must be listed in top-level kinds")
        _require_nonempty_string(title, f"{item_id}.title")

        if status == "open":
            missing_open = sorted(OPEN_REQUIRED - item.keys())
            if missing_open:
                raise ValidationError(f"{item_id} missing open fields: {', '.join(missing_open)}")
            for field in ("why", "next", "done_when"):
                _require_nonempty_string(item[field], f"{item_id}.{field}")
        else:
            missing_closed = sorted(CLOSED_REQUIRED - item.keys())
            if missing_closed:
                raise ValidationError(f"{item_id} missing closed fields: {', '.join(missing_closed)}")
            if item.get("resolution") not in VALID_RESOLUTIONS:
                raise ValidationError(f"{item_id} resolution is invalid")
            if type(item.get("closed_at")) is not date:
                raise ValidationError(f"{item_id}.closed_at must be YYYY-MM-DD")
            _require_nonempty_string(item.get("outcome"), f"{item_id}.outcome")
            _require_list(item.get("refs"), f"{item_id}.refs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    args = parser.parse_args(argv)

    try:
        validate_backlog(args.root)
    except ValidationError as exc:
        print(f"check_backlog.py: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

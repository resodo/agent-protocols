from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_backlog.py"
SPEC = importlib.util.spec_from_file_location("check_backlog", SCRIPT)
assert SPEC is not None
check_backlog = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["check_backlog"] = check_backlog
SPEC.loader.exec_module(check_backlog)


def valid_backlog() -> dict[str, Any]:
    return {
        "version": 1,
        "repo": "resodo/agent-protocols",
        "id_prefix": "AP-BL",
        "kinds": ["bug", "feature", "ops", "debt", "research", "process"],
        "items": [
            {
                "id": "AP-BL-0001",
                "status": "open",
                "priority": "P1",
                "kind": "process",
                "title": "Example open item",
                "why": "The reason is known.",
                "next": "Do the next thing.",
                "done_when": "The acceptance condition is met.",
            }
        ],
    }


class BacklogCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_backlog(self, data: dict[str, Any]) -> None:
        path = self.root / "docs/backlog.yml"
        path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def assert_invalid(self, message: str) -> None:
        with self.assertRaisesRegex(check_backlog.ValidationError, message):
            check_backlog.validate_backlog(self.root)

    def test_valid_backlog_passes(self) -> None:
        self.write_backlog(valid_backlog())

        check_backlog.validate_backlog(self.root)

    def test_duplicate_id_fails(self) -> None:
        data = valid_backlog()
        data["items"].append(dict(data["items"][0]))
        self.write_backlog(data)

        self.assert_invalid("duplicate backlog id")

    def test_bad_priority_fails(self) -> None:
        data = valid_backlog()
        data["items"][0]["priority"] = "P9"
        self.write_backlog(data)

        self.assert_invalid("priority")

    def test_missing_open_required_field_fails(self) -> None:
        data = valid_backlog()
        del data["items"][0]["done_when"]
        self.write_backlog(data)

        self.assert_invalid("missing open fields")

    def test_retired_markdown_backlog_fails(self) -> None:
        self.write_backlog(valid_backlog())
        (self.root / "docs/backlog.md").write_text("# Retired\n", encoding="utf-8")

        self.assert_invalid("docs/backlog.md")

    def test_invalid_id_prefix_fails(self) -> None:
        data = valid_backlog()
        data["items"][0]["id"] = "OTHER-BL-0001"
        self.write_backlog(data)

        self.assert_invalid("does not match")


if __name__ == "__main__":
    unittest.main()

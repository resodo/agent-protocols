from __future__ import annotations

import importlib.util
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/scout_runner.py"
SPEC = importlib.util.spec_from_file_location("scout_runner", SCRIPT)
assert SPEC is not None
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["scout_runner"] = runner
SPEC.loader.exec_module(runner)


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class ScoutRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        run_git(self.root, "init")
        run_git(self.root, "config", "user.email", "test@example.invalid")
        run_git(self.root, "config", "user.name", "Test User")
        (self.root / ".agent-protocols").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs/agent_plans").mkdir(parents=True)
        (self.root / "docs/backlog.yml").write_text(
            "version: 1\nrepo: example/repo\nid_prefix: EX-BL\nkinds: [debt]\nitems: []\n",
            encoding="utf-8",
        )
        self.write_overlay(self.overlay())
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-m", "initial")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def overlay(self) -> dict[str, Any]:
        return {
            "version": 1,
            "enabled_subskills": ["script-lifecycle", "code-reachability"],
            "report": {"output_root": "docs/agent_plans/outputs"},
            "repo_context": {
                "entry_files": ["AGENTS.md"],
                "backlog_path": "docs/backlog.yml",
                "active_docs": ["README.md"],
                "archive_paths": ["docs/agent_plans/outputs"],
            },
            "subskills": {
                "script-lifecycle": {
                    "script_roots": ["scripts"],
                    "script_entrypoint_sources": ["README.md", ".github/workflows"],
                    "known_manual_entrypoints": [],
                    "historical_script_contexts": ["docs/agent_plans/outputs"],
                },
                "code-reachability": {
                    "python": {
                        "production_roots": ["backend/app", "scripts"],
                        "test_roots": ["backend/tests"],
                        "active_contract_sources": ["README.md"],
                        "dynamic_entrypoint_sources": ["backend/pyproject.toml"],
                        "vulture": {
                            "roots": ["scripts", "backend/app"],
                            "version": "2.14.0",
                            "min_confidence": 60,
                            "ignore_decorators": ["@router.get", "@app.get", "@app.get"],
                            "ignore_names": ["model_config", "cls"],
                        },
                    },
                    "repo_notes": "Treat test-only production helpers as seam questions.",
                },
            },
        }

    def write_overlay(self, data: dict[str, Any]) -> None:
        (self.root / ".agent-protocols/scout.yml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    def test_validate_overlay_accepts_slice1_schema(self) -> None:
        data = runner.validate_overlay(self.root, self.root / ".agent-protocols/scout.yml")

        self.assertEqual(data["enabled_subskills"], ["script-lifecycle", "code-reachability"])

    def test_placeholder_vulture_version_is_rejected(self) -> None:
        data = self.overlay()
        data["subskills"]["code-reachability"]["python"]["vulture"]["version"] = "<exact-version-pinned-by-adopting-repo>"
        self.write_overlay(data)

        with self.assertRaisesRegex(runner.RunnerError, "exact version pin"):
            runner.validate_overlay(self.root, self.root / ".agent-protocols/scout.yml")

    def test_vulture_version_range_is_rejected(self) -> None:
        data = self.overlay()
        data["subskills"]["code-reachability"]["python"]["vulture"]["version"] = "2.x"
        self.write_overlay(data)

        with self.assertRaisesRegex(runner.RunnerError, "exact version pin"):
            runner.validate_overlay(self.root, self.root / ".agent-protocols/scout.yml")

    def test_output_root_escape_is_rejected(self) -> None:
        data = self.overlay()
        data["report"]["output_root"] = "../outside"
        self.write_overlay(data)

        with self.assertRaisesRegex(runner.RunnerError, "inside repo"):
            runner.validate_overlay(self.root, self.root / ".agent-protocols/scout.yml")

    def test_malformed_backlog_is_rejected(self) -> None:
        (self.root / "docs/backlog.yml").write_text("version: 1\nitems: [\n", encoding="utf-8")

        with self.assertRaisesRegex(runner.RunnerError, "backlog YAML parse failed"):
            runner.validate_overlay(self.root, self.root / ".agent-protocols/scout.yml")

    def test_setup_and_check_report_artifacts(self) -> None:
        setup_args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            mode="dry-run",
            date="2026-06-06",
            slug="scout_run",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.cmd_setup(setup_args), 0)
        run_dir = self.root / "docs/agent_plans/outputs/2026-06-06_scout_run"

        check_args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            run_dir="docs/agent_plans/outputs/2026-06-06_scout_run",
            mode="dry-run",
        )
        self.assertTrue((run_dir / "SCOUT_REPORT.md").exists())
        self.assertTrue((run_dir / "MANIFEST.md").exists())
        self.assertIn("Backlog baseline sha256:", (run_dir / "MANIFEST.md").read_text(encoding="utf-8"))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.cmd_check(check_args), 0)

    def test_check_requires_subsections_under_each_subskill(self) -> None:
        setup_args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            mode="dry-run",
            date="2026-06-06",
            slug="scout_run",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            runner.cmd_setup(setup_args)
        report_path = self.root / "docs/agent_plans/outputs/2026-06-06_scout_run/SCOUT_REPORT.md"
        report = report_path.read_text(encoding="utf-8")
        report = report.replace("### code-reachability\n\n#### Context And Tools Used", "### code-reachability\n\nContext omitted", 1)
        report_path.write_text(report, encoding="utf-8")

        args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            run_dir="docs/agent_plans/outputs/2026-06-06_scout_run",
            mode="dry-run",
        )
        with self.assertRaisesRegex(runner.RunnerError, "code-reachability subsection"):
            runner.cmd_check(args)

    def test_check_rejects_dry_run_backlog_change(self) -> None:
        self.test_setup_and_check_report_artifacts()
        (self.root / "docs/backlog.yml").write_text(
            "version: 1\nrepo: example/repo\nid_prefix: EX-BL\nkinds: [debt]\nitems: []\n# changed\n",
            encoding="utf-8",
        )

        args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            run_dir="docs/agent_plans/outputs/2026-06-06_scout_run",
            mode="dry-run",
        )
        with self.assertRaisesRegex(runner.RunnerError, "dry-run"):
            runner.cmd_check(args)

    def test_dry_run_allows_backlog_dirty_before_setup_when_unchanged(self) -> None:
        (self.root / "docs/backlog.yml").write_text(
            "version: 1\nrepo: example/repo\nid_prefix: EX-BL\nkinds: [debt]\nitems:\n"
            "  - id: EX-BL-0001\n"
            "    status: candidate\n"
            "    priority: P2\n"
            "    kind: debt\n"
            "    title: Existing candidate\n"
            "    why: >\n"
            "      Existing human-approved candidate before this dry-run.\n"
            "    next: >\n"
            "      Review later.\n"
            "    done_when: >\n"
            "      Reviewed.\n"
            "    refs:\n"
            "      - docs/agent_plans/outputs/previous/SCOUT_REPORT.md#candidate-proposal-001\n",
            encoding="utf-8",
        )

        setup_args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            mode="dry-run",
            date="2026-06-06",
            slug="scout_run",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            runner.cmd_setup(setup_args)

        args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            run_dir="docs/agent_plans/outputs/2026-06-06_scout_run",
            mode="dry-run",
        )
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.cmd_check(args), 0)

    def test_vulture_config_is_canonical_and_outside_repo(self) -> None:
        out1 = Path(self.tmp.name) / "vulture1.toml"
        out2 = Path(self.tmp.name) / "vulture2.toml"
        args1 = SimpleNamespace(repo_root=self.root, overlay=".agent-protocols/scout.yml", output=out1, allow_repo_output=False)
        args2 = SimpleNamespace(repo_root=self.root, overlay=".agent-protocols/scout.yml", output=out2, allow_repo_output=False)

        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runner.cmd_vulture_config(args1), 0)
            self.assertEqual(runner.cmd_vulture_config(args2), 0)

        self.assertEqual(out1.read_text(encoding="utf-8"), out2.read_text(encoding="utf-8"))
        self.assertIn('ignore_decorators = ["@app.get", "@router.get"]', out1.read_text(encoding="utf-8"))
        self.assertIn('paths = ["backend/app", "scripts"]', out1.read_text(encoding="utf-8"))

    def test_vulture_config_rejects_repo_output_by_default(self) -> None:
        args = SimpleNamespace(
            repo_root=self.root,
            overlay=".agent-protocols/scout.yml",
            output=self.root / "vulture.toml",
            allow_repo_output=False,
        )

        with self.assertRaisesRegex(runner.RunnerError, "outside the repo"):
            runner.cmd_vulture_config(args)


if __name__ == "__main__":
    unittest.main()

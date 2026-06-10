from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/claude_structured_review.py"
SPEC = importlib.util.spec_from_file_location("claude_structured_review", SCRIPT)
assert SPEC is not None
csr = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["claude_structured_review"] = csr
SPEC.loader.exec_module(csr)


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class ClaudeStructuredReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def init_target_repo(self) -> Path:
        repo = self.root / "repo"
        repo.mkdir()
        run_git(repo, "init")
        run_git(repo, "config", "user.email", "test@example.invalid")
        run_git(repo, "config", "user.name", "Test User")
        docs = repo / "docs"
        docs.mkdir()
        (docs / "plan.md").write_text("# Plan\n\n## Review Threads\n\nExisting.\n", encoding="utf-8")
        run_git(repo, "add", ".")
        run_git(repo, "commit", "-m", "initial")
        return repo

    def init_protocol_dir(self) -> Path:
        protocol = self.root / "structured-review"
        protocol.mkdir()
        references = protocol / "references"
        references.mkdir()
        (protocol / "SKILL.md").write_text("# Structured Review\n\nReviewer protocol.\n", encoding="utf-8")
        (references / "review-lenses.md").write_text("# Review Lenses\n\nValidation sentinel.\n", encoding="utf-8")
        (references / "collaboration.md").write_text("# Collaboration\n\nDriver checkpoint sentinel.\n", encoding="utf-8")
        return protocol

    def config_for(
        self,
        repo: Path,
        protocol: Path,
        *,
        mode: str = csr.MODE_WRITE,
        topic: str | None = "plan",
        extra: list[str] | None = None,
    ) -> csr.RunConfig:
        args = [
            "--protocol-dir",
            str(protocol),
            "--worktree",
            str(repo),
            "--mode",
            mode,
            "--type",
            "impl-plan",
            "--artifact",
            "docs/plan.md",
            "--focus",
            "Review the plan.",
            "--reviewer-backend",
            "claude",
        ]
        if mode == csr.MODE_WRITE:
            args.extend(["--thread-file", "docs/plan.md"])
        if topic is not None:
            args.extend(["--topic", topic])
        if extra:
            args.extend(extra)
        return csr.config_from_args(csr.parse_args(args))

    def append_review_commit(
        self,
        repo: Path,
        text: str,
        *,
        message: str = "structured-review: add reviewer comments for plan",
    ) -> None:
        plan = repo / "docs/plan.md"
        plan.write_text(plan.read_text(encoding="utf-8") + text, encoding="utf-8")
        run_git(repo, "add", "docs/plan.md")
        run_git(repo, "commit", "-m", message)

    def test_missing_generic_skill_fails(self) -> None:
        repo = self.init_target_repo()
        protocol = self.root / "missing"
        with self.assertRaisesRegex(csr.RunnerError, "SKILL.md"):
            self.config_for(repo, protocol)

    def test_target_overlays_load_from_target_worktree(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        overlay = repo / ".agent-protocols/structured-review.md"
        overlay.parent.mkdir()
        overlay.write_text("Target overlay text.\n", encoding="utf-8")
        config = self.config_for(repo, protocol)

        prompt = csr.build_prompt(config)

        self.assertIn("STRUCTURED REVIEW SKILL", prompt)
        self.assertIn("TARGET STRUCTURED REVIEW OVERLAY", prompt)
        self.assertIn("Target overlay text.", prompt)

    def test_required_protocol_references_load_into_prompt(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)

        prompt = csr.build_prompt(config)

        self.assertIn("STRUCTURED REVIEW REFERENCE references/review-lenses.md", prompt)
        self.assertIn("Validation sentinel.", prompt)
        self.assertIn("STRUCTURED REVIEW REFERENCE references/collaboration.md", prompt)
        self.assertIn("Driver checkpoint sentinel.", prompt)

    def test_closeout_review_type_loads_into_prompt(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, extra=["--type", "closeout-review"])

        prompt = csr.build_prompt(config)

        self.assertEqual(config.review_type, "closeout-review")
        self.assertIn("Type: closeout-review", prompt)

    def test_missing_required_protocol_reference_fails(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        (protocol / "references/review-lenses.md").unlink()
        config = self.config_for(repo, protocol)

        with self.assertRaisesRegex(csr.RunnerError, "required file is missing"):
            csr.build_prompt(config)

    def test_path_escape_is_rejected(self) -> None:
        repo = self.init_target_repo()
        with self.assertRaisesRegex(csr.RunnerError, "escapes worktree"):
            csr.resolve_repo_path(repo, "../outside.md")

    def test_unknown_mode_is_rejected(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        with self.assertRaises(SystemExit):
            csr.parse_args(
                [
                    "--protocol-dir",
                    str(protocol),
                    "--worktree",
                    str(repo),
                    "--mode",
                    "write",
                    "--type",
                    "impl-plan",
                    "--artifact",
                    "docs/plan.md",
                    "--focus",
                    "Review.",
                ]
            )

    def test_focus_and_focus_file_are_exactly_one(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        base = [
            "--protocol-dir",
            str(protocol),
            "--worktree",
            str(repo),
            "--mode",
            csr.MODE_PRINT,
            "--type",
            "impl-plan",
            "--artifact",
            "docs/plan.md",
        ]
        with self.assertRaises(SystemExit):
            csr.parse_args(base)
        with self.assertRaises(SystemExit):
            csr.parse_args([*base, "--focus", "a", "--focus-file", "docs/plan.md"])

    def test_multiple_artifacts_are_preserved_in_prompt(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        (repo / "docs/other.md").write_text("# Other\n", encoding="utf-8")
        config = self.config_for(repo, protocol, extra=["--artifact", "docs/other.md"])

        prompt = csr.build_prompt(config)

        self.assertIn("- docs/plan.md", prompt)
        self.assertIn("- docs/other.md", prompt)

    def test_prompt_excludes_real_worktree_root(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)

        prompt = csr.build_prompt(config)

        self.assertNotIn(str(repo), prompt)
        self.assertIn("docs/plan.md", prompt)

    def test_prompt_rejects_local_path_from_overlay(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        overlay = repo / ".agent-protocols/structured-review.md"
        overlay.parent.mkdir()
        overlay.write_text(f"Leaked path: {config.worktree}\n", encoding="utf-8")

        with self.assertRaisesRegex(csr.RunnerError, "local absolute path"):
            csr.build_prompt(config)

    def test_claude_argv_uses_auto_mode_without_outer_tool_restrictions(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, extra=["--claude-bin", "custom-claude"])

        argv = csr.claude_argv(config)

        self.assertEqual(argv[0], "custom-claude")
        self.assertIn("--permission-mode", argv)
        self.assertIn("auto", argv)
        self.assertNotIn("--disallowedTools", argv)
        self.assertNotIn("--allowedTools", argv)
        self.assertNotIn("--allowed-tools", argv)
        self.assertNotIn("--disallowed-tools", argv)

    def test_skill_removed_legacy_human_interaction_mechanics(self) -> None:
        skill = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")

        forbidden = (
            "Human Shorthand",
            "[O]",
            "[H]",
            "[V]",
            "[R]",
            "[X]",
            "Write review comments into the artifact and commit",
            "numbered decision menu",
            "action menu",
        )
        for text in forbidden:
            self.assertNotIn(text, skill)

        self.assertIn("Default Runner Rule", skill)
        self.assertIn("accepted", skill)
        self.assertIn("rejected", skill)
        self.assertIn("deferred", skill)
        self.assertIn("escalation-needed", skill)

    def test_skill_separates_review_readiness_from_closeout_handoff(self) -> None:
        skill = (SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Boundary With Closeout", skill)
        self.assertIn("closeout-review", skill)
        self.assertIn("is not part of this default gate list", skill)
        self.assertIn("ready for implementation", skill)
        self.assertIn("ready for closeout", skill)
        self.assertIn("ready to resume closeout", skill)
        self.assertIn(
            "Plan and implementation reviews must not make final merge-readiness handoffs",
            skill,
        )
        self.assertNotIn("ready for human merge", skill)

    def test_default_claude_bin_uses_path_lookup(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)

        self.assertEqual(csr.claude_argv(config)[0], "claude")

    def test_claude_version_timeout_is_recorded_as_unknown(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)

        with mock.patch.object(csr.subprocess, "run", side_effect=subprocess.TimeoutExpired("claude", 10)):
            self.assertEqual(csr.claude_version(config), "unknown: claude --version timed out")

    def test_stream_line_command_content_is_not_classified(self) -> None:
        result = csr.process_stream_line('{"event":{"input":{"command":"git push origin HEAD"}}}')

        self.assertFalse(result.malformed)
        self.assertEqual(result.text_delta, "")
        self.assertEqual(result.message_text, "")

    def test_malformed_stream_line_is_recorded(self) -> None:
        result = csr.process_stream_line("{not json")

        self.assertTrue(result.malformed)

    def test_stream_line_extracts_assistant_text_delta(self) -> None:
        result = csr.process_stream_line('{"type":"content_block_delta","delta":{"type":"text_delta","text":"No blockers."}}')

        self.assertFalse(result.malformed)
        self.assertEqual(result.text_delta, "No blockers.")

    def test_stream_line_extracts_final_message_text(self) -> None:
        result = csr.process_stream_line('{"type":"assistant","message":{"content":[{"type":"text","text":"Looks good."}]}}')

        self.assertFalse(result.malformed)
        self.assertEqual(result.message_text, "Looks good.")

    def test_redactor_covers_paths_and_home_prefixes(self) -> None:
        repo = self.init_target_repo()
        thread = repo / "docs/plan.md"
        redactor = csr.Redactor([repo, thread])
        mac_home = "/" + "Users" + "/alice/project"
        linux_home = "/" + "home" + "/alice/project"
        windows_home = "C:" + "\\" + "Users" + "\\alice\\project"

        redacted = redactor.redact(f"{repo} {thread} {Path.home()} {mac_home} {linux_home} {windows_home}")

        self.assertNotIn(str(repo), redacted)
        self.assertNotIn(str(thread), redacted)
        self.assertNotIn(str(Path.home()), redacted)
        self.assertIn("<LOCAL_HOME>/project", redacted)

    def test_print_mode_rejects_head_change(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Pass\n\nNo blockers.\n")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "changed HEAD"):
            csr.verify_print_mode(config, before, after, self.result(review_text="No blockers."))

    def test_print_mode_rejects_empty_review_text(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None)
        before = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "no review text"):
            csr.verify_print_mode(config, before, before, self.result(review_text=""))

    def test_print_mode_run_outputs_rendered_review_text(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None)

        def fake_run_claude(config: csr.RunConfig, prompt: str, logs: csr.RunLogs, redactor: csr.Redactor) -> csr.ClaudeRunResult:
            logs.prompt.write_text(prompt, encoding="utf-8")
            logs.stdout.write_text("{}", encoding="utf-8")
            logs.stderr.write_text("", encoding="utf-8")
            logs.review.write_text("### Review\n\nNo blockers.\n", encoding="utf-8")
            return self.result(review_text="### Review\n\nNo blockers.\n")

        with mock.patch.object(csr, "run_claude", fake_run_claude), mock.patch("sys.stdout", new_callable=lambda: __import__("io").StringIO()) as stdout:
            csr.run(config)

        self.assertIn("No blockers.", stdout.getvalue())

    def test_require_clean_rejects_dirty_worktree(self) -> None:
        repo = self.init_target_repo()
        (repo / "docs/plan.md").write_text("# Plan\n\nDirty.\n", encoding="utf-8")

        with self.assertRaisesRegex(csr.RunnerError, "clean"):
            csr.require_clean(csr.git_snapshot(repo))

    def test_missing_review_threads_anchor_rejects_before_claude(self) -> None:
        repo = self.init_target_repo()
        (repo / "docs/plan.md").write_text("# Plan\n\nNo anchor.\n", encoding="utf-8")

        with self.assertRaisesRegex(csr.RunnerError, "Review Threads"):
            csr.require_review_threads_anchor(repo / "docs/plan.md")

    def test_write_mode_accepts_exact_single_review_commit(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Pass\n\nNo blockers.\n")
        after = csr.git_snapshot(repo)

        csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_no_commit(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "exactly one"):
            csr.verify_write_mode(config, before, before, self.result())

    def test_write_mode_rejects_multiple_commits(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Pass 1\n\nNo blockers.\n")
        self.append_review_commit(repo, "\n### Reviewer Pass 2\n\nStill no blockers.\n")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "exactly one"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_amended_parent(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        plan = repo / "docs/plan.md"
        plan.write_text(plan.read_text(encoding="utf-8") + "\n### Reviewer Pass\n\nNo blockers.\n", encoding="utf-8")
        run_git(repo, "add", "docs/plan.md")
        run_git(repo, "commit", "--amend", "-m", "structured-review: add reviewer comments for plan")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "parent"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_wrong_file(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        (repo / "docs/other.md").write_text("### Reviewer Pass\n\nNo blockers.\n", encoding="utf-8")
        run_git(repo, "add", "docs/other.md")
        run_git(repo, "commit", "-m", "structured-review: add reviewer comments for plan")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "thread file"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_wrong_prefix(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Pass\n\nNo blockers.\n", message="review comments")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "structured-review prefix"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_deleted_thread_content(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        (repo / "docs/plan.md").write_text("# Plan\n\n## Review Threads\n\n### Reviewer Pass\n\nNo blockers.\n", encoding="utf-8")
        run_git(repo, "add", "docs/plan.md")
        run_git(repo, "commit", "-m", "structured-review: add reviewer comments for plan")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "delete"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_additions_outside_review_threads(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        plan = repo / "docs/plan.md"
        plan.write_text("review stray\n" + plan.read_text(encoding="utf-8"), encoding="utf-8")
        run_git(repo, "add", "docs/plan.md")
        run_git(repo, "commit", "-m", "structured-review: add reviewer comments for plan")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "under a review-thread section"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_accepts_nested_thread_heading_inside_review_section(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Follow-up Review\n\n#### Thread C resolution\n\nNo blockers remain.\n")
        after = csr.git_snapshot(repo)

        csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_additions_without_review_like_content(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Notes\n\nNo blockers.\n")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "look like"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_local_absolute_path_in_diff(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        local_path = "/" + "Users/example/work/repo/"
        self.append_review_commit(repo, f"\n### Reviewer Pass\n\nPath leaked: {local_path}\n")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "local absolute path"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_write_mode_rejects_secret_like_material(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol)
        before = csr.git_snapshot(repo)
        self.append_review_commit(repo, "\n### Reviewer Pass\n\nsecret = 'abcdefghijklmnop'\n")
        after = csr.git_snapshot(repo)

        with self.assertRaisesRegex(csr.RunnerError, "secret"):
            csr.verify_write_mode(config, before, after, self.result())

    def test_run_claude_writes_logs_metadata_and_review_text(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        fake_bin = self.root / "bin"
        fake_bin.mkdir()
        fake_claude = fake_bin / "claude"
        fake_claude.write_text(
            """#!/usr/bin/env python3
import sys

if '--version' in sys.argv:
    print('2.1.143 (Claude Code)')
    raise SystemExit(0)

sys.stdin.read()
print('{"type":"content_block_delta","delta":{"type":"text_delta","text":"Review "}}', flush=True)
print('{not json', flush=True)
print('{"type":"content_block_delta","delta":{"type":"text_delta","text":"done."}}', flush=True)
print('stderr path', file=sys.stderr, flush=True)
""",
            encoding="utf-8",
        )
        fake_claude.chmod(0o755)
        config = self.config_for(
            repo,
            protocol,
            mode=csr.MODE_PRINT,
            topic=None,
            extra=["--claude-bin", str(fake_claude), "--run-log-dir", str(self.root / "logs")],
        )
        logs = csr.prepare_run_logs(config)

        result = csr.run_claude(config, "prompt", logs, csr.Redactor([repo]))
        csr.write_metadata(config, logs, result, outcome="success")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.review_text, "Review done.")
        self.assertEqual(result.malformed_stream_lines, 1)
        self.assertIn("prompt", logs.prompt.read_text(encoding="utf-8"))
        self.assertIn("{not json", logs.stdout.read_text(encoding="utf-8"))
        self.assertIn("stderr path", logs.stderr.read_text(encoding="utf-8"))
        self.assertEqual(logs.review.read_text(encoding="utf-8"), "Review done.")
        metadata = json.loads(logs.metadata.read_text(encoding="utf-8"))
        self.assertEqual(metadata["reviewer_version"], "2.1.143 (Claude Code)")
        self.assertEqual(metadata["backend"], "claude")
        self.assertEqual(metadata["malformed_stream_lines"], 1)

    def test_run_reports_timeout_with_dirty_state(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None, extra=["--run-log-dir", str(self.root / "timeout-logs")])

        def fake_run_claude(config: csr.RunConfig, prompt: str, logs: csr.RunLogs, redactor: csr.Redactor) -> csr.ClaudeRunResult:
            (config.worktree / "docs/plan.md").write_text("# Plan\n\nDirty after timeout.\n", encoding="utf-8")
            return self.result(timed_out=True, returncode=-9)

        with mock.patch.object(csr, "run_claude", fake_run_claude):
            with self.assertRaisesRegex(csr.RunnerError, "timed out with uncommitted changes") as ctx:
                csr.run(config)

        self.assertEqual(ctx.exception.exit_code, 2)
        metadata = json.loads((self.root / "timeout-logs/metadata.json").read_text(encoding="utf-8"))
        self.assertTrue(metadata["dirty_after"])
        self.assertEqual(metadata["outcome"], "timeout")

    def test_run_records_metadata_for_unexpected_errors(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None, extra=["--run-log-dir", str(self.root / "error-logs")])

        def fake_run_claude(config: csr.RunConfig, prompt: str, logs: csr.RunLogs, redactor: csr.Redactor) -> csr.ClaudeRunResult:
            raise ValueError("boom")

        with mock.patch.object(csr, "run_claude", fake_run_claude):
            with self.assertRaisesRegex(csr.RunnerError, "errored"):
                csr.run(config)

        metadata = json.loads((self.root / "error-logs/metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["outcome"], "error")
        self.assertEqual(metadata["error"], "boom")

    def logs_for(self, root: Path) -> csr.RunLogs:
        return csr.RunLogs(
            root=root,
            prompt=root / "prompt.md",
            stdout=root / "stdout.stream.jsonl",
            stderr=root / "stderr.log",
            metadata=root / "metadata.json",
            review=root / "review.md",
        )

    def write_fake_codex(self, body: str) -> Path:
        fake_bin = self.root / "bin"
        fake_bin.mkdir(exist_ok=True)
        fake_codex = fake_bin / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "import subprocess, sys\n"
            "\n"
            "if '--version' in sys.argv:\n"
            "    print('codex-cli 0.137.0')\n"
            "    raise SystemExit(0)\n"
            "\n"
            "out_path = sys.argv[sys.argv.index('--output-last-message') + 1]\n"
            "sys.stdin.read()\n" + body,
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        return fake_codex

    def test_resolve_reviewer_backend_cross_vendor_auto(self) -> None:
        self.assertEqual(csr.resolve_reviewer_backend("auto", {"CLAUDECODE": "1"}), ("codex", True))
        self.assertEqual(csr.resolve_reviewer_backend("auto", {"CODEX_THREAD_ID": "t"}), ("claude", True))
        self.assertEqual(csr.resolve_reviewer_backend("auto", {"CODEX_SANDBOX": "seatbelt"}), ("claude", True))
        self.assertEqual(csr.resolve_reviewer_backend("auto", {}), ("claude", False))
        self.assertEqual(csr.resolve_reviewer_backend("codex", {"CLAUDECODE": "1"}), ("codex", False))

    def test_resolve_reviewer_backend_both_markers_error(self) -> None:
        with self.assertRaisesRegex(csr.RunnerError, "--reviewer-backend"):
            csr.resolve_reviewer_backend("auto", {"CLAUDECODE": "1", "CODEX_SANDBOX": "seatbelt"})

    def test_auto_marker_resolved_missing_binary_errors(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        args = csr.parse_args(
            [
                "--protocol-dir",
                str(protocol),
                "--worktree",
                str(repo),
                "--mode",
                csr.MODE_PRINT,
                "--type",
                "impl-plan",
                "--artifact",
                "docs/plan.md",
                "--focus",
                "Review.",
            ]
        )
        with mock.patch.object(csr.shutil, "which", return_value=None):
            with self.assertRaisesRegex(csr.RunnerError, "--reviewer-backend"):
                csr.config_from_args(args, env={"CLAUDECODE": "1"})

    def test_auto_neither_marker_skips_preflight(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        args = csr.parse_args(
            [
                "--protocol-dir",
                str(protocol),
                "--worktree",
                str(repo),
                "--mode",
                csr.MODE_PRINT,
                "--type",
                "impl-plan",
                "--artifact",
                "docs/plan.md",
                "--focus",
                "Review.",
            ]
        )
        with mock.patch.object(csr.shutil, "which", return_value=None):
            config = csr.config_from_args(args, env={})
        self.assertEqual(config.backend, "claude")

    def test_explicit_backend_skips_preflight(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        with mock.patch.object(csr.shutil, "which", return_value=None):
            config = self.config_for(repo, protocol, extra=["--reviewer-backend", "codex"])
        self.assertEqual(config.backend, "codex")

    def test_codex_argv_write_mode_sandbox_git_dirs_and_defaults(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, extra=["--reviewer-backend", "codex"])
        logs = self.logs_for(self.root / "codex-logs")

        argv = csr.codex_argv(config, logs)

        self.assertEqual(argv[:4], ["codex", "exec", "-", "--json"])
        self.assertIn("workspace-write", argv)
        add_dirs = [argv[i + 1] for i, flag in enumerate(argv) if flag == "--add-dir"]
        self.assertEqual(add_dirs, [str((repo / ".git").resolve())])
        self.assertIn("gpt-5.5", argv)
        self.assertIn("model_reasoning_effort=xhigh", argv)
        self.assertEqual(argv[argv.index("--output-last-message") + 1], str(logs.root / "last-message.txt"))

    def test_codex_argv_linked_worktree_adds_both_git_dirs(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        linked = self.root / "linked"
        run_git(repo, "worktree", "add", str(linked), "-b", "linked")
        config = self.config_for(linked, protocol, extra=["--reviewer-backend", "codex"])
        logs = self.logs_for(self.root / "codex-logs")

        argv = csr.codex_argv(config, logs)

        add_dirs = [argv[i + 1] for i, flag in enumerate(argv) if flag == "--add-dir"]
        self.assertEqual(len(add_dirs), 2)
        self.assertIn(str((repo / ".git").resolve()), add_dirs)

    def test_codex_argv_print_mode_is_read_only_without_add_dir(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, mode=csr.MODE_PRINT, topic=None, extra=["--reviewer-backend", "codex"])
        logs = self.logs_for(self.root / "codex-logs")

        argv = csr.codex_argv(config, logs)

        self.assertIn("read-only", argv)
        self.assertNotIn("workspace-write", argv)
        self.assertNotIn("--add-dir", argv)

    def test_codex_model_and_effort_overrides(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(
            repo,
            protocol,
            extra=["--reviewer-backend", "codex", "--codex-model", "gpt-9", "--codex-effort", "high"],
        )
        logs = self.logs_for(self.root / "codex-logs")

        argv = csr.codex_argv(config, logs)

        self.assertIn("gpt-9", argv)
        self.assertIn("model_reasoning_effort=high", argv)
        self.assertNotIn("gpt-5.5", argv)

    def test_codex_stream_line_extracts_agent_message_and_usage(self) -> None:
        message = csr.process_codex_stream_line(
            '{"type":"item.completed","item":{"id":"i1","type":"agent_message","text":"No blockers."}}'
        )
        usage = csr.process_codex_stream_line('{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}')
        other = csr.process_codex_stream_line('{"type":"item.completed","item":{"id":"i2","type":"command_execution","command":"ls"}}')
        malformed = csr.process_codex_stream_line("{not json")

        self.assertEqual(message.message_text, "No blockers.")
        self.assertEqual(usage.usage, {"input_tokens": 10, "output_tokens": 5})
        self.assertEqual(other.message_text, "")
        self.assertTrue(malformed.malformed)

    def test_prompt_names_reviewer_backend_for_both_backends(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        claude_config = self.config_for(repo, protocol)
        codex_config = self.config_for(repo, protocol, extra=["--reviewer-backend", "codex"])

        self.assertIn("You are the claude reviewer backend", csr.build_prompt(claude_config))
        self.assertIn("claude reviewer).", csr.build_prompt(claude_config))
        self.assertIn("You are the codex reviewer backend", csr.build_prompt(codex_config))

    def test_run_codex_prefers_last_message_file_and_records_metadata(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        fake_codex = self.write_fake_codex(
            "print('{\"type\":\"item.completed\",\"item\":{\"id\":\"i1\",\"type\":\"agent_message\",\"text\":\"Partial note.\"}}', flush=True)\n"
            "print('{not json', flush=True)\n"
            "print('{\"type\":\"turn.completed\",\"usage\":{\"input_tokens\":10,\"output_tokens\":5}}', flush=True)\n"
            "with open(out_path, 'w') as fh:\n"
            "    fh.write('Codex review done.')\n"
            "print('codex stderr path', file=sys.stderr, flush=True)\n"
        )
        config = self.config_for(
            repo,
            protocol,
            mode=csr.MODE_PRINT,
            topic=None,
            extra=["--reviewer-backend", "codex", "--codex-bin", str(fake_codex), "--run-log-dir", str(self.root / "logs")],
        )
        logs = csr.prepare_run_logs(config)

        result = csr.run_claude(config, "prompt", logs, csr.Redactor([repo]))
        csr.write_metadata(config, logs, result, outcome="success")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.review_text, "Codex review done.")
        self.assertEqual(result.malformed_stream_lines, 1)
        self.assertEqual(result.reviewer_version, "codex-cli 0.137.0")
        metadata = json.loads(logs.metadata.read_text(encoding="utf-8"))
        self.assertEqual(metadata["backend"], "codex")
        self.assertEqual(metadata["model"], "gpt-5.5")
        self.assertEqual(metadata["effort"], "xhigh")
        self.assertEqual(metadata["reviewer_version"], "codex-cli 0.137.0")
        self.assertEqual(metadata["token_usage"], {"input_tokens": 10, "output_tokens": 5})

    def test_run_codex_falls_back_to_accumulated_messages(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        fake_codex = self.write_fake_codex(
            "print('{\"type\":\"item.completed\",\"item\":{\"id\":\"i1\",\"type\":\"agent_message\",\"text\":\"First note.\"}}', flush=True)\n"
            "print('{\"type\":\"item.completed\",\"item\":{\"id\":\"i2\",\"type\":\"agent_message\",\"text\":\"Second note.\"}}', flush=True)\n"
        )
        config = self.config_for(
            repo,
            protocol,
            mode=csr.MODE_PRINT,
            topic=None,
            extra=["--reviewer-backend", "codex", "--codex-bin", str(fake_codex), "--run-log-dir", str(self.root / "logs")],
        )
        logs = csr.prepare_run_logs(config)

        result = csr.run_claude(config, "prompt", logs, csr.Redactor([repo]))

        self.assertEqual(result.review_text, "First note.\n\nSecond note.")

    def test_run_codex_write_mode_end_to_end(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        fake_codex = self.write_fake_codex(
            "with open('docs/plan.md', 'a') as fh:\n"
            "    fh.write('\\n### Reviewer pass 1 (impl-plan, codex reviewer)\\n\\nNo blocking issues.\\n')\n"
            "subprocess.run(['git', 'add', 'docs/plan.md'], check=True)\n"
            "subprocess.run(['git', 'commit', '-m', 'structured-review: add reviewer comments for plan'], check=True)\n"
            "print('{\"type\":\"item.completed\",\"item\":{\"id\":\"i1\",\"type\":\"agent_message\",\"text\":\"Committed review.\"}}', flush=True)\n"
            "with open(out_path, 'w') as fh:\n"
            "    fh.write('Committed review.')\n"
        )
        config = self.config_for(
            repo,
            protocol,
            extra=["--reviewer-backend", "codex", "--codex-bin", str(fake_codex), "--run-log-dir", str(self.root / "logs")],
        )
        head_before = run_git(repo, "rev-parse", "HEAD")

        csr.run(config)

        self.assertNotEqual(run_git(repo, "rev-parse", "HEAD"), head_before)
        self.assertEqual(run_git(repo, "log", "-1", "--pretty=%s"), "structured-review: add reviewer comments for plan")
        self.assertIn("codex reviewer", (repo / "docs/plan.md").read_text(encoding="utf-8"))
        metadata = json.loads((self.root / "logs/metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["outcome"], "success")
        self.assertEqual(metadata["backend"], "codex")

    def test_codex_version_timeout_is_recorded_as_unknown(self) -> None:
        repo = self.init_target_repo()
        protocol = self.init_protocol_dir()
        config = self.config_for(repo, protocol, extra=["--reviewer-backend", "codex"])

        with mock.patch.object(csr.subprocess, "run", side_effect=subprocess.TimeoutExpired("codex", 10)):
            self.assertEqual(csr.codex_version(config), "unknown: codex --version timed out")

    def result(
        self,
        *,
        review_text: str = "### Review\n\nNo blockers.\n",
        returncode: int = 0,
        timed_out: bool = False,
    ) -> csr.ClaudeRunResult:
        return csr.ClaudeRunResult(
            returncode=returncode,
            stdout="",
            stderr="",
            review_text=review_text,
            malformed_stream_lines=0,
            timed_out=timed_out,
            started_at="2026-06-04T00:00:00Z",
            ended_at="2026-06-04T00:00:01Z",
            reviewer_version="2.1.143 (Claude Code)",
            argv=["claude", "-p"],
        )


if __name__ == "__main__":
    unittest.main()

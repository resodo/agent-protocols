"""Tests for scope-review/run_scope_review.py, with a fake model command in place of the CLI."""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _docs_check_fixture import ALL_RULES, RUNNER, Fixture, sha12  # noqa: E402

SPEC = importlib.util.spec_from_file_location("run_scope_review", RUNNER)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

INCIDENT = "app/sources/vendor_files/reader.py"

FAKE_MODEL = """import json, os, sys
output, side, model, answer = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
prompt = sys.stdin.read()
json.dump({"cwd": os.getcwd(), "listing": os.listdir("."), "prompt": prompt, "model": model}, open(side, "w"))
open(output, "w").write(open(answer).read())
"""


def answer_text(verdict: str = "go", fence: bool = False) -> str:
    lines = [f"verdict: {verdict}", *[f"- {r}: holds. One sentence." for r in ALL_RULES],
             "Owner: data.R2", "Cut: nothing"]
    text = "\n".join(lines) + "\n"
    return f"Here is the review.\n```\n{text}```\n" if fence else text


class RunnerCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.f = Fixture(self._tmp.name)
        self.f.branch("work")
        self.tmp = Path(self._tmp.name)
        self.fake = self.tmp / "fake_model.py"
        self.fake.write_text(FAKE_MODEL)
        self.side = self.tmp / "side.json"
        self.answer = self.tmp / "answer.txt"
        self.answer.write_text(answer_text())
        self.log = self.tmp / "state" / "scope-reviews.log"
        cfg = json.loads(self.f.read(".agent-protocols/docs-check.json"))
        cfg["scope_review"] = {"model": "config-model",
                               "command": [sys.executable, str(self.fake), "{output}", str(self.side), "{model}",
                                           str(self.answer)]}
        self.f.write(".agent-protocols/docs-check.json", json.dumps(cfg, indent=2) + "\n")
        self.f.write(INCIDENT, "def read():\n    return []\n")
        self.proposal = self.f.proposal("ir-fix", [INCIDENT])
        self.record = "docs/agent_plans/changes/ir-fix/scope-review.md"

    def run_ok(self, *args: str, env: dict[str, str] | None = None) -> str:
        code, out, err = self.f.runner(*args, env=env)
        self.assertEqual(code, 0, out + err)
        return out

    def run_fails(self, *args: str, env: dict[str, str] | None = None) -> str:
        code, out, err = self.f.runner(*args, env=env)
        self.assertEqual(code, 2, out + err)
        return err


class WritesTheRecord(RunnerCase):
    def test_record_log_and_isolation(self) -> None:
        out = self.run_ok("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log)})
        self.assertRegex(out, r"scope review sr-\d{8}T\d{6}Z-[0-9a-f]{4}: verdict go, \d+s, record "
                         + re.escape(self.record))
        record = self.f.read(self.record)
        head = dict(re.findall(r"^(\w+): (.+)$", record.split("---")[1], re.M))
        self.assertEqual(head["verdict"], "go")
        self.assertTrue(head["reviewer"].endswith(":config-model"), head)
        self.assertRegex(head["run_id"], r"^sr-\d{8}T\d{6}Z-[0-9a-f]{4}$")
        self.assertEqual(head["proposal_sha"], sha12((self.f.root / self.proposal).read_bytes()))
        self.assertIn("- data.R2: holds. One sentence.\nOwner: data.R2\nCut: nothing\n", record)
        self.assertNotIn("verdict: go\n- ", record)  # the verdict line went into the front matter
        self.assertEqual(self.log.read_text().split(), [sha12(record.encode())])

        side = json.loads(self.side.read_text())
        self.assertEqual(side["listing"], [])  # an empty working directory
        self.assertNotIn(str(self.f.root), side["cwd"])
        self.assertEqual(side["model"], "config-model")
        prompt = side["prompt"]
        self.assertTrue(prompt.startswith("You are the scope reviewer."))
        self.assertIn("## Rules that govern the touched paths\nsys.R1 ", prompt)
        for rid in ALL_RULES:
            self.assertEqual(prompt.count(f"\n{rid} "), 1, rid)
        self.assertIn("[review] (decided 2026-11-09, data plan)   <- AGENTS.md", prompt)
        self.assertIn("[lint: docs-check:incident-fixes-only] (decided 2026-11-09; refines sys.R1)", prompt)
        self.assertIn("## Placement questions (docs/placement.md)\n1. Is it about reading", prompt)
        self.assertIn("## The proposal\n# Proposal: ir-fix", prompt)

        # The record and the log pass the docs check's scope and gated steps.
        self.f.commit("IR fix\n\nRules-read:\n- sys.R1: applies; x\n- sys.R3: n/a; x\n- data.R1: n/a; x\n")
        code, text = self.f.check("scope")
        self.assertEqual(code, 0, text)
        self.assertIn("scope: ok (2 trigger(s)", text)
        code, text = self.f.check("gated", "--log", str(self.log))
        self.assertIn("gated: nothing to stop on", text)

    def test_env_overrides_the_model(self) -> None:
        self.run_ok("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log), "SCOPE_REVIEW_MODEL": "env-model"})
        self.assertEqual(json.loads(self.side.read_text())["model"], "env-model")
        self.assertIn("reviewer: ", self.f.read(self.record))
        self.assertIn(":env-model\n", self.f.read(self.record))

    def test_answer_inside_a_code_fence(self) -> None:
        self.answer.write_text(answer_text("ask", fence=True))
        self.run_ok("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log)})
        record = self.f.read(self.record)
        self.assertIn("verdict: ask\n", record)
        self.assertNotIn("```", record)


class Refuses(RunnerCase):
    def test_log_inside_the_repo(self) -> None:
        err = self.run_fails("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.f.root / "reviews.log")})
        self.assertIn("the run log must be outside the repo", err)
        self.assertFalse((self.f.root / self.record).exists())

    def test_no_log(self) -> None:
        self.assertIn("no run log", self.run_fails("ir-fix"))

    def test_bad_verdict(self) -> None:
        self.answer.write_text("I think it is fine.\n")
        err = self.run_fails("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log)})
        self.assertIn("no record written", err)
        self.assertFalse((self.f.root / self.record).exists())
        self.assertFalse(self.log.exists())

    def test_missing_proposal(self) -> None:
        self.assertIn("no such proposal", self.run_fails("nope", env={"SCOPE_REVIEW_LOG": str(self.log)}))

    def test_proposal_without_touches(self) -> None:
        self.f.write(self.proposal, "# Proposal\n\n## Intent\nx\n")
        self.assertIn("no paths listed under `## Touches`", self.run_fails("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log)}))

    def test_failing_command(self) -> None:
        self.fake.write_text("import sys\nsys.stderr.write('quota exhausted')\nsys.exit(3)\n")
        err = self.run_fails("ir-fix", env={"SCOPE_REVIEW_LOG": str(self.log)})
        self.assertIn("exited 3", err)
        self.assertIn("quota exhausted", err)


class DryRunAndDefaults(RunnerCase):
    def test_dry_run_calls_nothing(self) -> None:
        out = self.run_ok("ir-fix", "--dry-run", env={"SCOPE_REVIEW_MODEL": "env-model"})
        self.assertIn("You are the scope reviewer.", out)
        self.assertIn("command: ", out)
        self.assertIn("env-model", out)
        self.assertFalse(self.side.exists())
        self.assertFalse((self.f.root / self.record).exists())

    def test_default_command_is_codex_without_tools(self) -> None:
        cmd = runner.DEFAULT_COMMAND
        self.assertEqual(cmd[:3], ["codex", "exec", "-"])
        pairs = {cmd[i + 1] for i, a in enumerate(cmd) if a == "--disable"}
        for feature in ("shell_tool", "unified_exec", "code_mode_host", "apps", "plugins", "multi_agent"):
            self.assertIn(feature, pairs)
        self.assertIn("web_search=disabled", cmd)
        self.assertIn("--ignore-user-config", cmd)
        self.assertEqual(cmd[cmd.index("--sandbox") + 1], "read-only")
        for placeholder in ("{model}", "{output}", "model_reasoning_effort={effort}"):
            self.assertIn(placeholder, cmd)
        self.assertEqual(runner.DEFAULT_MODEL, "gpt-6-sol")

    def test_touches_parsing(self) -> None:
        text = "# P\n\n## Touches\n- `app/a.py` (the reader)\n* app/b/\n  - app/c.py\nnot a bullet\n\n## Rule changes\n- none\n"
        self.assertEqual(runner.touches(text), ["app/a.py", "app/b/", "app/c.py"])

    def test_answer_body(self) -> None:
        verdict, body = runner.answer_body("noise\nverdict: cut\n- sys.R1: holds. x\nCut: y\n")
        self.assertEqual(verdict, "cut")
        self.assertEqual(body, ["- sys.R1: holds. x", "Cut: y"])
        self.assertEqual(runner.answer_body("nothing here"), (None, []))


if __name__ == "__main__":
    unittest.main()

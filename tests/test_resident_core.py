from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CORE = REPO_ROOT / "decision-boundary" / "CORE.md"
SCRIPT = REPO_ROOT / "scripts" / "check_resident_core.py"


def run(consumer_text: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        consumer = Path(tmp) / "AGENTS.md"
        consumer.write_text(consumer_text, encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(consumer), str(CORE)],
                              capture_output=True, text=True)


class ResidentCoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.core = CORE.read_text(encoding="utf-8")

    def test_core_is_short_and_names_every_gate(self) -> None:
        self.assertLessEqual(len(self.core.splitlines()), 40)
        for gate in range(1, 11):
            self.assertIn(f"G{gate} ", self.core)

    def test_exact_copy_passes(self) -> None:
        result = run("# Project\n\nintro\n\n" + self.core + "\nmore text\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_block_fails(self) -> None:
        result = run("# Project\n\nno core here\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing", result.stderr)

    def test_duplicate_block_fails(self) -> None:
        result = run(self.core + "\n" + self.core)
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected one", result.stderr)

    def test_one_changed_line_fails(self) -> None:
        lines = self.core.splitlines()
        lines[5] = lines[5] + " (edited)"
        result = run("\n".join(lines) + "\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("differs", result.stderr)

    def test_unclosed_block_fails(self) -> None:
        result = run(self.core.split("<!-- /agent-protocols")[0])
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_skill_mounts.sh"


def run(*args, cwd):
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


class SyncSkillMountsTest(unittest.TestCase):
    def test_creates_refreshes_and_prunes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run("git", "init", "-q", cwd=root)
            base = root / "external" / "agent-protocols"
            for name in ("alpha", "beta"):
                (base / name).mkdir(parents=True)
                (base / name / "SKILL.md").write_text("x")
            (base / "docs").mkdir()  # no SKILL.md: must not be mounted
            for d in (".claude/skills", ".agents/skills"):
                (root / d).mkdir(parents=True)
                (root / d / "gone").symlink_to("../../external/agent-protocols/gone")
                (root / d / "own").mkdir()  # unrelated entry stays
            run("bash", str(SCRIPT), cwd=root)
            for d in (".claude/skills", ".agents/skills"):
                for name in ("alpha", "beta"):
                    link = root / d / name
                    self.assertTrue(link.is_symlink())
                    self.assertTrue((link / "SKILL.md").is_file())
                self.assertFalse((root / d / "gone").is_symlink())
                self.assertFalse((root / d / "docs").exists())
                self.assertTrue((root / d / "own").is_dir())
            before = run("bash", str(SCRIPT), cwd=root).stdout
            self.assertEqual(before, "")  # idempotent


if __name__ == "__main__":
    unittest.main()

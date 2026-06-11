from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def skill_files() -> list[Path]:
    return sorted(REPO_ROOT.glob("*/SKILL.md"))


def frontmatter_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path}: SKILL.md must start with a '---' frontmatter block")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise AssertionError(f"{path}: frontmatter block is not closed with '---'")
    return parts[1]


class SkillFrontmatterTest(unittest.TestCase):
    def test_skill_files_exist(self) -> None:
        self.assertGreater(len(skill_files()), 0, "no */SKILL.md files found at repo root")

    def test_frontmatter_parses_with_strict_yaml(self) -> None:
        for path in skill_files():
            with self.subTest(skill=str(path.relative_to(REPO_ROOT))):
                try:
                    data = yaml.safe_load(frontmatter_text(path))
                except yaml.YAMLError as exc:
                    self.fail(
                        f"{path}: frontmatter is not strict YAML; lenient loaders may "
                        f"accept it but strict skill loaders (e.g. Codex CLI) refuse to "
                        f"load the skill: {exc}"
                    )
                self.assertIsInstance(data, dict, f"{path}: frontmatter must be a mapping")

    def test_frontmatter_has_name_and_description(self) -> None:
        for path in skill_files():
            with self.subTest(skill=str(path.relative_to(REPO_ROOT))):
                data = yaml.safe_load(frontmatter_text(path))
                for key in ("name", "description"):
                    value = data.get(key)
                    self.assertIsInstance(value, str, f"{path}: '{key}' must be a string")
                    self.assertTrue(value.strip(), f"{path}: '{key}' must be non-empty")
                self.assertEqual(
                    data["name"],
                    path.parent.name,
                    f"{path}: frontmatter 'name' must match the protocol directory name",
                )


if __name__ == "__main__":
    unittest.main()

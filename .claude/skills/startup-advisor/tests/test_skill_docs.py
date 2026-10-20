import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import ws


class SkillDocsTests(unittest.TestCase):
    def test_skill_frontmatter(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        meta, _ = ws.split_frontmatter(text)
        self.assertEqual(meta["name"], "startup-advisor")
        self.assertIn("创业", meta["description"])
        self.assertIn("/startup-advisor", meta["description"])

    def test_required_files_exist(self):
        for rel in [
            "references/conversation-guide.md",
            "references/data-model.md",
            "templates/profile.md",
            "templates/IDEA.md",
            "templates/PROJECT.md",
            "templates/discussion.md",
            "scripts/advisor.py",
        ]:
            self.assertTrue((SKILL_DIR / rel).exists(), rel)

    def test_skill_mentions_entry_and_rules(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for needle in [
            "advisor.py",
            "resume --json",
            "_inbox",
            "promote",
            "status: open",
            "不删除",
        ]:
            self.assertIn(needle, text)

    def test_skill_links_references(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for rel in [
            "references/conversation-guide.md",
            "references/data-model.md",
        ]:
            self.assertIn(rel, text, rel)

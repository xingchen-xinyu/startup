import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class SkillDocTests(unittest.TestCase):
    def test_skill_protocol_mentions_required_behaviors(self):
        text = (BASE / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "顾问档",
            "参谋档",
            "brief",
            "execution-assistant",
            "init",
            "context",
            "validate",
            "按需访谈",
            "收尾",
        ):
            self.assertIn(token, text)


class CoachingPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/coaching-playbook.md").read_text(encoding="utf-8")
        for token in ("访谈模块", "提问法", "阶段剧本", "Lean Canvas", "失败模式"):
            self.assertIn(token, text)

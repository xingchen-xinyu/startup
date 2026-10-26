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
            "BLOCKED",
        ):
            self.assertIn(token, text)


class CoachingPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/coaching-playbook.md").read_text(encoding="utf-8")
        for token in ("访谈模块", "提问法", "阶段剧本", "Lean Canvas", "失败模式"):
            self.assertIn(token, text)


class ExecutionPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/execution-playbook.md").read_text(encoding="utf-8")
        for token in (
            "brief 写法",
            "交付物类型与结构",
            "文风适配",
            "验收清单",
            "执行助手返回格式",
            "正例与反例",
        ):
            self.assertIn(token, text)


class MemoryModelTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/memory-model.md").read_text(encoding="utf-8")
        for token in ("目录结构", "frontmatter", "更新规则", "读写策略", "命名"):
            self.assertIn(token, text)


class ExecutionAgentTests(unittest.TestCase):
    def test_agent_definition(self):
        text = (
            BASE.parents[1] / "agents/execution-assistant.md"
        ).read_text(encoding="utf-8")
        for token in (
            "name: execution-assistant",
            "description:",
            "tools:",
            "身份",
            "输入",
            "工作流程",
            "边界",
            "execution-playbook.md",
            "截止时间",
            "文风",
            "使用材料",
            "BLOCKED",
        ):
            self.assertIn(token, text)

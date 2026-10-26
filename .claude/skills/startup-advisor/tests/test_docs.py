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
            "文风：",
            "使用材料",
            "使用材料：",
            "## 缺失信息返回格式",
            "BLOCKED",
        ):
            self.assertIn(token, text)
        blocked_section = text.split("## 缺失信息返回格式", 1)[1]
        self.assertIn("BLOCKED", blocked_section)


class RequiredFilesTests(unittest.TestCase):
    def test_all_new_files_exist(self):
        required = (
            "SKILL.md",
            "references/coaching-playbook.md",
            "references/execution-playbook.md",
            "references/memory-model.md",
            "templates/portfolio.md",
            "templates/profile.md",
            "templates/self.md",
            "templates/writing-style.md",
            "templates/PLAN.md",
            "templates/note.md",
            "templates/brief.md",
            "scripts/advisor.py",
            "tests/helpers.py",
            "tests/test_cli.py",
            "tests/test_docs.py",
        )
        for rel in required:
            self.assertTrue((BASE / rel).is_file(), rel)
        self.assertTrue(
            (BASE.parents[1] / "agents/execution-assistant.md").is_file()
        )

    def test_old_files_are_removed(self):
        for rel in (
            "references/conversation-guide.md",
            "references/data-model.md",
            "templates/IDEA.md",
            "templates/PROJECT.md",
            "templates/discussion.md",
        ):
            self.assertFalse((BASE / rel).exists(), rel)

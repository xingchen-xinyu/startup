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
            "项目根目录",
        ):
            self.assertIn(token, text)

    def test_skill_mentions_understanding_protocol(self):
        text = (BASE / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "理解档",
            "方案门槛",
            "反馈回环",
            "给方案前核对上下文",
            "发送前自检",
        ):
            self.assertIn(token, text)

    def test_skill_omits_removed_commands_and_files(self):
        text = (BASE / "SKILL.md").read_text(encoding="utf-8")
        for token in ("resume", "doctor", "project promote", "_inbox"):
            self.assertNotIn(token, text)


TEMPLATE_HEADINGS = {
    "portfolio.md": (
        "# 创业组合",
        "## 当前主攻",
        "## 孵化池",
        "## 已归档",
    ),
    "PLAN.md": (
        "## 一句话",
        "## 愿景",
        "## 目标用户与痛点",
        "## 价值主张",
        "## 解决方案",
        "## 关键假设与证据",
        "## 当前阶段与目标",
        "## 主要风险",
        "## 下一步",
        "## 方向起源",
    ),
    "note.md": (
        "## 议题",
        "## 关键原话",
        "## 讨论要点",
        "## 结论",
        "## 未决问题",
        "## 决定",
        "## 行动项",
        "## 下一步",
    ),
    "brief.md": (
        "## 目标",
        "## 读者与渠道",
        "## 交付物",
        "## 必须包含",
        "## 不能出现",
        "## 文风与格式",
        "## 参考材料",
        "## 验收标准",
        "## 截止时间",
    ),
    "profile.md": (
        "## 基本信息",
        "## 背景与能力",
        "## 资源与约束",
        "## 创业偏好",
        "## 变更记录",
    ),
    "self.md": (
        "## 性格与决策风格",
        "## 能量来源与压力反应",
        "## 优势",
        "## 短板与盲区",
        "## 核心价值观",
        "## 为什么创业",
        "## 长期愿景",
        "## 未来 12 个月目标",
        "## 协作偏好",
        "## 待确认",
    ),
    "writing-style.md": (
        "## 语气与人称",
        "## 结构偏好",
        "## 用词",
        "## 平台差异",
        "## 代表性样本",
        "## 反馈日志",
        "## 待确认",
    ),
}


class TemplateHeadingTests(unittest.TestCase):
    def test_required_headings(self):
        for name, headings in TEMPLATE_HEADINGS.items():
            text = (BASE / "templates" / name).read_text(encoding="utf-8")
            for heading in headings:
                self.assertIn(heading, text, f"{name} 缺少章节：{heading}")


class CoachingPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/coaching-playbook.md").read_text(encoding="utf-8")
        for token in (
            "访谈模块",
            "提问法",
            "阶段剧本",
            "Lean Canvas",
            "失败模式",
            "诊断先于方案",
            "方案门槛",
            "反馈四步",
            "最小答案",
        ):
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

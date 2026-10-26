import json
import tempfile
import unittest
from pathlib import Path

from helpers import advisor, init_workspace, run_cli, write


class InitTests(unittest.TestCase):
    def test_init_creates_workspace_and_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            ventures = root / "ventures"
            for rel in (
                "portfolio.md",
                "me/profile.md",
                "me/self.md",
                "me/writing-style.md",
            ):
                self.assertTrue((ventures / rel).is_file(), rel)
            self.assertIn("created: ventures/portfolio.md", out)

    def test_init_is_idempotent_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(run_cli(root, "init")[0], 0)
            profile = root / "ventures/me/profile.md"
            profile.write_text(
                profile.read_text(encoding="utf-8") + "\n- 称呼：星辰\n",
                encoding="utf-8",
                newline="\n",
            )
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            self.assertIn("称呼：星辰", profile.read_text(encoding="utf-8"))
            self.assertIn("skipped: ventures/me/profile.md", out)

    def test_init_migrates_legacy_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "ventures/profile.md"
            write(legacy, "---\nupdated: 2026-10-20\n---\n\n## 基本信息\n- 称呼：星辰\n")
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            new_profile = root / "ventures/me/profile.md"
            self.assertTrue(new_profile.is_file())
            self.assertIn("称呼：星辰", new_profile.read_text(encoding="utf-8"))
            self.assertTrue(legacy.is_file())
            self.assertIn("migrated:", out)


class ProfileBomTests(unittest.TestCase):
    def test_bom_profile_parses_frontmatter_and_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "profile.md"
            path.write_text(
                "---\nupdated: 2026-10-26\n---\n\n## 基本信息\n- 称呼：\n",
                encoding="utf-8-sig",
                newline="\n",
            )
            text = advisor.read_text(path)
            self.assertIsNotNone(text)
            self.assertFalse(text.startswith(chr(0xFEFF)))
            meta, _, _ = advisor.parse_frontmatter(text)
            self.assertEqual(meta.get("updated"), "2026-10-26")
            self.assertEqual(advisor.profile_state(path), "empty")


def make_plan(name="AI 知识库", stage="validating"):
    return (
        "---\n"
        f"name: {name}\n"
        f"stage: {stage}\n"
        "one_liner: 帮小团队做内部知识库\n"
        "created: 2026-10-20\n"
        "updated: 2026-10-26\n"
        "next_action: 访谈 3 家团队\n"
        "---\n\n"
        f"# 方向：{name}\n"
    )


class ContextTests(unittest.TestCase):
    def test_context_on_empty_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out, err = run_cli(root, "context")
            self.assertEqual(code, 0, out + err)
            self.assertIn("主攻：未设置", out)
            self.assertIn("最近未结束：无", out)
            self.assertIn("警告：", out)

    def test_context_json_populated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(ventures / "pet-social/PLAN.md", make_plan("宠物社交", "idea"))
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating: pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n\n# 创业组合\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step: 访谈 3 家\n---\n\n"
                "# 讨论：定价\n\n## 未决问题\n- 企业版定价锚点是多少？\n- 谁做付费决策？\n",
            )
            write(ventures / "ai-kb/TODO.md", "- [ ] 访谈 3 家\n- [ ] 整理竞品\n")
            write(
                ventures / "me/self.md",
                "---\nupdated: 2026-10-26\n---\n\n# 星辰画像\n\n"
                "## 性格与决策风格\n- 偏好小步验证\n",
            )
            code, out, err = run_cli(root, "context", "--json")
            self.assertEqual(code, 0, out + err)
            data = json.loads(out)
            self.assertEqual(data["main"]["slug"], "ai-kb")
            self.assertEqual(data["main"]["name"], "AI 知识库")
            self.assertEqual(data["main"]["stage"], "validating")
            self.assertEqual(
                data["latest_open_note"]["path"],
                "ventures/ai-kb/notes/2026-10-26-定价.md",
            )
            self.assertEqual(
                data["open_questions"],
                ["企业版定价锚点是多少？", "谁做付费决策？"],
            )
            self.assertEqual(data["todos"], ["访谈 3 家", "整理竞品"])
            self.assertEqual(data["me"]["self"], "filled")
            self.assertEqual(data["me"]["profile"], "empty")
            self.assertEqual(len(data["incubating"]), 1)
            self.assertEqual(data["incubating"][0]["name"], "宠物社交")

    def test_context_ignores_closed_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\nupdated: 2026-10-26\n---\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-25-旧.md",
                "---\ntitle: 旧\ndate: 2026-10-25\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step: 继续\n---\n\n"
                "## 未决问题\n- 旧问题\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-26-新.md",
                "---\ntitle: 新\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: closed\nnext_step:\n---\n\n"
                "## 未决问题\n- 新问题\n",
            )
            code, out, err = run_cli(root, "context", "--json")
            self.assertEqual(code, 0, out + err)
            data = json.loads(out)
            self.assertEqual(data["latest_open_note"]["title"], "旧")
            self.assertEqual(data["open_questions"], ["旧问题"])

    def test_context_human_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\nupdated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "context")
            self.assertEqual(code, 0, out + err)
            self.assertIn("主攻：AI 知识库（validating）", out)
            self.assertIn("下一步：访谈 3 家团队", out)


def valid_workspace(root: Path) -> Path:
    ventures = init_workspace(root)
    write(
        ventures / "portfolio.md",
        "---\nmain: ai-kb\nincubating: pet-social\narchived:\n"
        "updated: 2026-10-26\n---\n\n# 创业组合\n",
    )
    write(
        ventures / "ai-kb/PLAN.md",
        "---\nname: AI 知识库\nstage: validating\n"
        "one_liner: 帮小团队做内部知识库\n"
        "created: 2026-10-20\nupdated: 2026-10-26\n"
        "next_action: 访谈 3 家团队\n---\n",
    )
    write(
        ventures / "pet-social/PLAN.md",
        "---\nname: 宠物社交\nstage: idea\none_liner: 宠物主人社交\n"
        "created: 2026-10-20\nupdated: 2026-10-26\n"
        "next_action: 访谈 5 位宠物主\n---\n",
    )
    write(
        ventures / "ai-kb/notes/2026-10-26-定价.md",
        "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
        "mode: coach\nstatus: open\nnext_step: 访谈 3 家\n---\n\n"
        "## 未决问题\n- 定价锚点？\n",
    )
    write(
        ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
        "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
        "output_type: launch-copy\nstatus: approved\ndue: 2026-10-28\n---\n\n"
        "## 参考材料\n- `PLAN.md`\n",
    )
    write(
        ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
        "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
        "brief: briefs/2026-10-26-发布文案.md\nversion: 1\nstatus: draft\n"
        "author: execution-assistant\n---\n\n# 发布文案\n",
    )
    write(ventures / "ai-kb/TODO.md", "- [ ] 访谈 3 家\n")
    return ventures


class ValidateTests(unittest.TestCase):
    def test_valid_workspace_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_workspace(root)
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)
            self.assertIn("校验通过", out)

    def test_optional_files_may_be_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)

    def test_main_points_to_missing_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: missing\nincubating: pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("main 指向不存在的方向：missing", out)

    def test_unregistered_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("方向未在 portfolio.md 登记：pet-social", out)

    def test_duplicate_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating: ai-kb, pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("main 与 incubating 重复：ai-kb", out)

    def test_invalid_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/PLAN.md",
                "---\nname: AI 知识库\nstage: foo\none_liner: x\n"
                "created: 2026-10-20\nupdated: 2026-10-26\nnext_action: x\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("非法 stage: foo", out)

    def test_note_direction_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: other\n"
                "mode: coach\nstatus: open\nnext_step: 继续\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("direction=other 与目录不一致", out)

    def test_open_note_missing_next_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step:\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("open 纪要缺少 next_step", out)

    def test_brief_invalid_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "output_type: launch-copy\nstatus: unknown\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("非法 status: unknown", out)

    def test_brief_missing_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "output_type: launch-copy\nstatus: approved\n---\n\n"
                "## 参考材料\n- `notes/missing.md`\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("参考材料不存在：notes/missing.md", out)

    def test_output_missing_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "brief: briefs/missing.md\nversion: 1\nstatus: draft\n"
                "author: execution-assistant\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("brief 不存在：briefs/missing.md", out)

    def test_output_bad_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "brief: briefs/2026-10-26-发布文案.md\nversion: 0\n"
                "status: draft\nauthor: execution-assistant\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("version 必须是 >=1 的整数", out)

    def test_missing_required_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            (ventures / "me/profile.md").unlink()
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("缺少必填文件：ventures/me/profile.md", out)

    def test_legacy_state_file_is_warning_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(ventures / ".state.json", "{}\n")
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)
            self.assertIn("WARNING: 发现旧 ventures/.state.json", out)

    def test_direction_name_rejects_comma(self):
        from helpers import advisor

        self.assertTrue(advisor.name_errors("bad,name", allow_comma=False))
        self.assertFalse(advisor.name_errors("bad,name", allow_comma=True))

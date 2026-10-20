import unittest

import helpers
import ws


class SanitizeNameTests(unittest.TestCase):
    def test_keeps_chinese_and_converts_spaces(self):
        self.assertEqual(ws.sanitize_name("宠物 社交"), "宠物-社交")

    def test_removes_windows_illegal_characters(self):
        self.assertEqual(ws.sanitize_name('AI<知识库>:"/\\|?*'), "AI知识库")

    def test_reserved_name_is_prefixed(self):
        self.assertEqual(ws.sanitize_name("CON"), "_CON")

    def test_blank_name_returns_empty(self):
        self.assertEqual(ws.sanitize_name("   "), "")


class FrontmatterTests(unittest.TestCase):
    def test_split_and_replace(self):
        text = "---\nname: 测试\nstage: idea\n---\n\n# 标题\n"
        meta, body = ws.split_frontmatter(text)
        self.assertEqual(meta["name"], "测试")
        self.assertEqual(body.strip(), "# 标题")

        updated = ws.replace_frontmatter_field(text, "stage", "validating")
        meta2, _ = ws.split_frontmatter(updated)
        self.assertEqual(meta2["stage"], "validating")
        self.assertEqual(meta2["name"], "测试")

    def test_section_lines(self):
        body = "## 未决问题\n- 定价是多少？\n- 谁付费？\n\n## 下一步\n- 访谈\n"
        self.assertEqual(ws.section_lines(body, "未决问题"), ["定价是多少？", "谁付费？"])


class NamingTests(unittest.TestCase):
    def test_unique_dir_adds_numeric_suffix(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "同名").mkdir()
            self.assertEqual(ws.unique_dir(root, "同名").name, "同名-2")

    def test_unique_file_adds_numeric_suffix(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("x", encoding="utf-8")
            self.assertEqual(ws.unique_file(root, "a").name, "a-2.md")


class WorkspaceInitTests(helpers.WorkspaceTestCase):
    def test_init_creates_profile_and_state(self):
        self.assertTrue(self.ws.profile.exists())
        self.assertTrue(self.ws.state_file.exists())
        text = self.ws.profile.read_text(encoding="utf-8")
        self.assertIn("# 个人档案", text)

    def test_init_is_idempotent(self):
        try:
            created = self.ws.init()
        except Exception as exc:  # pragma: no cover - 失败时直接暴露
            self.fail(f"init 不应抛错：{exc}")
        self.assertEqual(created, [])

    def test_render_project_template(self):
        content = self.ws.render_template(
            "PROJECT.md", NAME="测试项目", STAGE="idea",
            ONE_LINER="一句话", DATE="2026-10-20",
        )
        self.assertIn("name: 测试项目", content)
        self.assertIn("# 项目：测试项目", content)

    def test_atomic_write_overwrites(self):
        path = self.ws.ventures / "x.md"
        ws.write_text_atomic(path, "第一版")
        ws.write_text_atomic(path, "第二版")
        self.assertEqual(path.read_text(encoding="utf-8"), "第二版")

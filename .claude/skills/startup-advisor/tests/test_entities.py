import unittest
from unittest import mock

import helpers
import entities
import ws


class EntityTests(helpers.WorkspaceTestCase):
    def test_create_project_auto_names(self):
        target = entities.create_project(self.ws, "AI 知识库", "帮团队管理知识", "validating")
        self.assertEqual(target["rel"], "AI-知识库")
        self.assertTrue((target["path"] / "PROJECT.md").exists())
        self.assertTrue((target["path"] / "discussions").is_dir())
        self.assertTrue((target["path"] / "assets").is_dir())
        self.assertEqual(target["meta"]["stage"], "validating")

    def test_create_idea_goes_to_inbox(self):
        target = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        self.assertEqual(target["rel"], "_inbox/宠物社交")
        text = (target["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("同城宠物主人社交", text)

    def test_create_idea_flattens_multiline_one_liner(self):
        target = entities.create_idea(self.ws, "注入测试", "第一行\n## 伪造标题\n第二行")
        text = (target["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("第一行 ## 伪造标题 第二行", text)
        self.assertNotIn("\n## 伪造标题", text)

    def test_find_target_by_label_slug_and_rel(self):
        target = entities.create_project(self.ws, "AI 知识库")
        self.assertEqual(entities.find_target(self.ws, "AI-知识库")["rel"], target["rel"])
        self.assertEqual(entities.find_target(self.ws, "AI 知识库")["rel"], target["rel"])
        self.assertEqual(entities.find_target(self.ws, target["rel"])["rel"], target["rel"])

    def test_find_target_reports_ambiguity(self):
        entities.create_project(self.ws, "AI 知识库")
        entities.create_project(self.ws, "AI 写作")
        with self.assertRaises(ws.AdvisorError) as ctx:
            entities.find_target(self.ws, "AI")
        self.assertIn("匹配到多个", str(ctx.exception))

    def test_find_target_rejects_unknown(self):
        with self.assertRaises(ws.AdvisorError):
            entities.find_target(self.ws, "不存在")

    def test_update_target_keeps_folder_stable(self):
        target = entities.create_project(self.ws, "旧名字")
        old_path = target["path"]
        updated = entities.update_target(target, name="新名字")
        self.assertEqual(updated["path"], old_path)
        self.assertEqual(updated["meta"]["name"], "新名字")

    def test_update_target_rejects_unknown_stage(self):
        target = entities.create_project(self.ws, "测试")
        with self.assertRaises(ws.AdvisorError):
            entities.update_target(target, stage="unknown")

    def test_update_project_syncs_body_heading_and_one_liner(self):
        target = entities.create_project(self.ws, "旧名字", "旧的一句话")
        updated = entities.update_target(target, name="新名字", one_liner="新的一句话")
        text = (updated["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("# 项目：新名字", text)
        self.assertNotIn("# 项目：旧名字", text)
        self.assertIn("## 愿景", text)
        self.assertNotIn("旧的一句话", text)
        self.assertEqual(ws.section_lines(updated["body"], "一句话"), ["新的一句话"])
        self.assertEqual(updated["meta"]["name"], "新名字")
        self.assertEqual(updated["meta"]["one_liner"], "新的一句话")

    def test_update_idea_syncs_title_and_one_liner(self):
        target = entities.create_idea(self.ws, "旧标题", "旧的说明")
        updated = entities.update_target(target, title="新标题", one_liner="新的说明")
        text = (updated["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("# 想法：新标题", text)
        self.assertNotIn("# 想法：旧标题", text)
        self.assertIn("## 初步观察", text)
        self.assertNotIn("旧的说明", text)
        self.assertEqual(ws.section_lines(updated["body"], "一句话"), ["新的说明"])
        self.assertEqual(entities.idea_one_liner(updated), "新的说明")
        self.assertEqual(updated["meta"]["title"], "新标题")

    def test_repeated_update_does_not_grow_blank_lines(self):
        target = entities.create_project(self.ws, "测试项目", "第一版")
        target = entities.update_target(target, one_liner="第二版")
        target = entities.update_target(target, one_liner="第三版")
        text = (target["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("## 一句话\n\n第三版\n\n## 愿景", text)
        self.assertNotIn("## 一句话\n\n\n", text)

    def test_update_flattens_multiline_values(self):
        target = entities.create_project(self.ws, "测试项目", "第一版")
        target = entities.update_target(target, one_liner="第一行\n## 伪造标题\n第二行")
        text = (target["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("第一行 ## 伪造标题 第二行", text)
        self.assertNotIn("\n## 伪造标题", text)
        self.assertEqual(target["meta"]["one_liner"], "第一行 ## 伪造标题 第二行")

    def test_reserved_name_project_is_reachable(self):
        target = entities.create_project(self.ws, "CON")
        self.assertEqual(target["rel"], "_CON")
        rels = [item["rel"] for item in entities.iter_targets(self.ws)]
        self.assertIn("_CON", rels)
        self.assertEqual(entities.find_target(self.ws, "_CON")["rel"], "_CON")

    def test_iter_targets_includes_projects_and_ideas(self):
        first = entities.create_project(self.ws, "第一个")
        second = entities.create_idea(self.ws, "第二个")
        rels = [t["rel"] for t in entities.iter_targets(self.ws)]
        self.assertIn(first["rel"], rels)
        self.assertIn(second["rel"], rels)


class PromoteTests(helpers.WorkspaceTestCase):
    def test_promote_moves_and_preserves_history(self):
        idea = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        note = idea["path"] / "discussions" / "2026-10-20-需求.md"
        note.write_text(
            "---\ntitle: 需求\ndate: 2026-10-20\ntarget: _inbox/宠物社交\n"
            "status: open\nnext_step: \n---\n\n# 讨论：需求\n\n## 未决问题\n- 需求真实吗？\n",
            encoding="utf-8",
        )

        project = entities.promote_idea(self.ws, "宠物社交")

        self.assertFalse(idea["path"].exists())
        self.assertTrue((project["path"] / "PROJECT.md").exists())
        self.assertTrue((project["path"] / "discussions" / note.name).exists())
        meta, _ = ws.split_frontmatter(
            (project["path"] / "discussions" / note.name).read_text(encoding="utf-8")
        )
        self.assertEqual(meta["target"], project["rel"])
        project_text = (project["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("## 想法起源", project_text)
        self.assertIn("同城宠物主人社交", project_text)
        self.assertEqual(self.ws.active(), project["rel"])

    def test_promote_extracts_one_liner(self):
        entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        project = entities.promote_idea(self.ws, "宠物社交")
        self.assertEqual(project["meta"]["one_liner"], "同城宠物主人社交")

    def test_promote_rejects_project(self):
        entities.create_project(self.ws, "正式项目")
        with self.assertRaises(ws.AdvisorError):
            entities.promote_idea(self.ws, "正式项目")

    def test_promote_rolls_back_destination_on_conversion_failure(self):
        idea = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        with mock.patch.object(entities, "write_text_atomic", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                entities.promote_idea(self.ws, "宠物社交")
        self.assertFalse((self.ws.ventures / "宠物社交").exists())
        self.assertTrue(idea["path"].exists())

    def test_promote_keeps_destination_when_source_cleanup_fails(self):
        idea = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        with mock.patch.object(entities.shutil, "rmtree", side_effect=OSError("locked")):
            with self.assertRaises(ws.AdvisorError) as ctx:
                entities.promote_idea(self.ws, "宠物社交")
        self.assertIn("清理", str(ctx.exception))
        self.assertTrue((self.ws.ventures / "宠物社交" / "PROJECT.md").exists())
        self.assertTrue(idea["path"].exists())

    def test_promote_flattens_new_name(self):
        entities.create_idea(self.ws, "宠物社交")
        project = entities.promote_idea(self.ws, "宠物社交", new_name="新项目\n## 伪造标题")
        text = (project["path"] / "PROJECT.md").read_text(encoding="utf-8")
        h1_lines = [line for line in text.splitlines() if line.startswith("# ")]
        self.assertEqual(h1_lines, ["# 项目：新项目 ## 伪造标题"])
        self.assertNotIn("\n## 伪造标题", text)

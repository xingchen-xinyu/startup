import unittest

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

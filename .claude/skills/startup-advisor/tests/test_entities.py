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

    def test_iter_targets_includes_projects_and_ideas(self):
        first = entities.create_project(self.ws, "第一个")
        second = entities.create_idea(self.ws, "第二个")
        rels = [t["rel"] for t in entities.iter_targets(self.ws)]
        self.assertIn(first["rel"], rels)
        self.assertIn(second["rel"], rels)

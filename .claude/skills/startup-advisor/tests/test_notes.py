import unittest

import helpers
import entities
import notes
import ws


class NoteTests(helpers.WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.target = entities.create_project(self.ws, "测试项目")

    def test_create_note_has_open_frontmatter(self):
        path = notes.create_note(self.ws, self.target, "定价策略", "访谈 3 家")
        text = path.read_text(encoding="utf-8")
        self.assertIn("status: open", text)
        self.assertIn("target: 测试项目", text)
        self.assertIn("# 讨论：定价策略", text)
        self.assertTrue(path.name.startswith("20"))
        self.assertTrue(path.name.endswith("定价策略.md"))

    def test_same_day_same_title_gets_suffix(self):
        first = notes.create_note(self.ws, self.target, "定价")
        second = notes.create_note(self.ws, self.target, "定价")
        self.assertNotEqual(first, second)
        self.assertIn("-2", second.name)

    def test_idea_note_is_indexed(self):
        idea = entities.create_idea(self.ws, "宠物社交")
        path = notes.create_note(self.ws, idea, "需求验证")
        idea_text = (idea["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("讨论索引", idea_text)
        self.assertIn(path.name, idea_text)

    def test_list_notes_open_only(self):
        first = notes.create_note(self.ws, self.target, "第一条")
        notes.create_note(self.ws, self.target, "第二条")
        notes.close_note(self.ws, str(first))
        open_notes = notes.list_notes(self.target, open_only=True)
        self.assertEqual([n["title"] for n in open_notes], ["第二条"])

    def test_close_note_updates_status(self):
        path = notes.create_note(self.ws, self.target, "讨论")
        notes.close_note(self.ws, str(path))
        self.assertIn("status: closed", path.read_text(encoding="utf-8"))

    def test_add_decision_appends_record(self):
        path = notes.add_decision(
            self.target, "目标用户", "只服务技术团队",
            options="泛中小企业", reason="决策链短", impact="暂不做个人版",
            source="discussions/x.md",
        )
        text = path.read_text(encoding="utf-8")
        self.assertIn("## ", text)
        self.assertIn("**决定**：只服务技术团队", text)
        self.assertIn("**备选**：泛中小企业", text)
        self.assertIn("**来源**：discussions/x.md", text)

    def test_find_note_by_filename_fragment(self):
        path = notes.create_note(self.ws, self.target, "定价策略")
        found = notes.find_note(self.ws, "定价策略")
        self.assertEqual(found, path)

    def test_create_note_flattens_frontmatter_inputs(self):
        path = notes.create_note(
            self.ws,
            self.target,
            "标题\n---\ninjected: yes",
            "下一步\n---\nstatus: closed",
        )
        text = path.read_text(encoding="utf-8")
        meta, _ = ws.split_frontmatter(text)
        self.assertEqual(meta["status"], "open")
        self.assertNotIn("injected", meta)
        self.assertNotIn("\n", meta["title"])
        self.assertNotIn("\n", meta["next_step"])

    def test_find_note_rejects_non_discussion_files(self):
        project_md = self.target["path"] / "PROJECT.md"
        with self.assertRaises(ws.AdvisorError):
            notes.find_note(self.ws, str(project_md))
        self.assertNotIn("status: closed", project_md.read_text(encoding="utf-8"))

    def test_find_note_empty_ref_raises(self):
        with self.assertRaises(ws.AdvisorError):
            notes.find_note(self.ws, "")

    def test_find_note_rejects_empty_fragment(self):
        notes.create_note(self.ws, self.target, "讨论")
        with self.assertRaises(ws.AdvisorError) as ctx:
            notes.find_note(self.ws, ".")
        self.assertIn("有效", str(ctx.exception))

    def test_add_decision_flattens_fields(self):
        path = notes.add_decision(
            self.target,
            "标题\n## 伪造",
            "决定\n## 伪造",
            options="备选\n## 伪造",
            reason="理由\n## 伪造",
            impact="影响\n## 伪造",
            source="来源\n## 伪造",
        )
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("\n## 伪造", text)
        self.assertIn("- **决定**：决定 ## 伪造", text)
        self.assertIn("- **备选**：备选 ## 伪造", text)

    def test_list_notes_negative_limit_returns_empty(self):
        notes.create_note(self.ws, self.target, "限制")
        self.assertEqual(notes.list_notes(self.target, limit=-1), [])


class ResumeTests(helpers.WorkspaceTestCase):
    def test_resume_collects_open_discussions_and_todos(self):
        target = entities.create_project(self.ws, "AI 知识库")
        path = notes.create_note(self.ws, target, "定价策略", "访谈 3 家")
        text = path.read_text(encoding="utf-8").replace(
            "## 未决问题\n", "## 未决问题\n- 企业版定价锚点？\n"
        )
        path.write_text(text, encoding="utf-8")
        from todos import add_todo
        add_todo(target, "访谈 3 家团队", "P1")

        data = notes.collect_resume(self.ws)

        self.assertEqual(data["open_discussion_total"], 1)
        discussion = data["open_discussions"][0]
        self.assertEqual(discussion["title"], "定价策略")
        self.assertEqual(discussion["open_questions"], ["企业版定价锚点？"])
        self.assertEqual(data["open_todo_count"], 1)
        self.assertEqual(data["open_todos"][0]["text"], "访谈 3 家团队")

    def test_resume_ignores_closed_notes(self):
        target = entities.create_project(self.ws, "测试")
        path = notes.create_note(self.ws, target, "已完成讨论")
        notes.close_note(self.ws, str(path))
        data = notes.collect_resume(self.ws)
        self.assertEqual(data["open_discussion_total"], 0)

    def test_resume_limit_keeps_total(self):
        target = entities.create_project(self.ws, "测试")
        for title in ("一", "二", "三", "四"):
            notes.create_note(self.ws, target, title)
        data = notes.collect_resume(self.ws, limit=2)
        self.assertEqual(len(data["open_discussions"]), 2)
        self.assertEqual(data["open_discussion_total"], 4)

    def test_resume_negative_limit_returns_no_discussions(self):
        target = entities.create_project(self.ws, "测试")
        notes.create_note(self.ws, target, "讨论")
        data = notes.collect_resume(self.ws, limit=-1)
        self.assertEqual(data["open_discussions"], [])
        self.assertEqual(data["open_discussion_total"], 1)

    def test_resume_reads_next_step_from_body(self):
        target = entities.create_project(self.ws, "测试")
        path = notes.create_note(self.ws, target, "讨论")
        text = path.read_text(encoding="utf-8").replace(
            "## 下一步\n", "## 下一步\n- 访谈 5 位用户\n"
        )
        path.write_text(text, encoding="utf-8")
        data = notes.collect_resume(self.ws)
        self.assertEqual(data["open_discussions"][0]["next_step"], "访谈 5 位用户")

    def test_checkpoint_updates_next_action_and_returns_summary(self):
        target = entities.create_project(self.ws, "测试")
        notes.create_note(self.ws, target, "讨论")
        from todos import add_todo
        add_todo(target, "下一步行动")
        summary = notes.checkpoint(self.ws, target, "访谈 3 家团队")
        self.assertEqual(summary["next_action"], "访谈 3 家团队")
        self.assertEqual(len(summary["open_todos"]), 1)
        self.assertTrue(summary["recent_notes"])
        text = (target["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("next_action: 访谈 3 家团队", text)

    def test_checkpoint_for_idea_does_not_require_next_action(self):
        idea = entities.create_idea(self.ws, "宠物社交")
        summary = notes.checkpoint(self.ws, idea)
        self.assertEqual(summary["target_rel"], idea["rel"])
        self.assertEqual(self.ws.active(), idea["rel"])

    def test_checkpoint_sets_active(self):
        first = entities.create_project(self.ws, "项目甲")
        second = entities.create_project(self.ws, "项目乙")
        self.ws.set_active(second["rel"])
        self.assertEqual(self.ws.active(), second["rel"])
        notes.checkpoint(self.ws, first)
        self.assertEqual(self.ws.active(), first["rel"])

    def test_checkpoint_finds_older_open_note(self):
        target = entities.create_project(self.ws, "测试")
        old = notes.create_note(self.ws, target, "旧讨论")
        text = old.read_text(encoding="utf-8").replace(
            "## 未决问题\n", "## 未决问题\n- 旧问题仍然成立？\n"
        )
        text = ws.replace_frontmatter_field(text, "date", "2026-01-01")
        old.write_text(text, encoding="utf-8")
        for title in ("新讨论一", "新讨论二", "新讨论三"):
            path = notes.create_note(self.ws, target, title)
            notes.close_note(self.ws, str(path))

        summary = notes.checkpoint(self.ws, target)

        self.assertIn("旧问题仍然成立？", summary["open_questions"])

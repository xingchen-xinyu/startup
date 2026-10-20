import re
import unittest

import helpers
import entities
import todos


class TodoTests(helpers.WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.target = entities.create_project(self.ws, "测试项目")

    def test_add_returns_unique_id_and_persists(self):
        first = todos.add_todo(self.target, "访谈 3 家团队", "P1", "2026-10-27", "discussions/a.md")
        second = todos.add_todo(self.target, "整理竞品")
        self.assertNotEqual(first, second)
        self.assertRegex(first, r"^t-\d{8}-\d{3}$")
        text = (self.target["path"] / "todos.md").read_text(encoding="utf-8")
        self.assertIn(first, text)
        self.assertIn("[P1] 访谈 3 家团队", text)
        self.assertIn("📅 2026-10-27", text)
        self.assertIn("来源：discussions/a.md", text)

    def test_list_open_only(self):
        first = todos.add_todo(self.target, "完成的事")
        todos.add_todo(self.target, "未完成的事")
        todos.complete_todo(self.target, first)
        open_items = todos.list_todos(self.target, open_only=True)
        self.assertEqual([item["text"] for item in open_items], ["未完成的事"])

    def test_complete_moves_to_done_section(self):
        todo_id = todos.add_todo(self.target, "访谈")
        todos.complete_todo(self.target, todo_id)
        text = (self.target["path"] / "todos.md").read_text(encoding="utf-8")
        self.assertIn("## 已完成", text)
        self.assertIn(f"`id:{todo_id}`", text)
        self.assertIn("完成于", text)
        item = todos.list_todos(self.target)[0]
        self.assertTrue(item["done"])

    def test_reopen_moves_back(self):
        todo_id = todos.add_todo(self.target, "访谈")
        todos.complete_todo(self.target, todo_id)
        todos.reopen_todo(self.target, todo_id)
        item = todos.list_todos(self.target)[0]
        self.assertFalse(item["done"])
        self.assertEqual(item["text"], "访谈")

    def test_unknown_id_raises(self):
        with self.assertRaises(Exception):
            todos.complete_todo(self.target, "t-20200101-999")

    def test_priority_and_due_are_parsed(self):
        todos.add_todo(self.target, "验证付费", "P0", "2026-11-01")
        item = todos.list_todos(self.target)[0]
        self.assertEqual(item["priority"], "P0")
        self.assertEqual(item["due"], "2026-11-01")
        self.assertEqual(item["text"], "验证付费")

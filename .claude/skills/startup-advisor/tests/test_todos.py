import unittest

import helpers
import entities
import todos
import ws


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
        self.assertNotIn("- [ ]", text)
        self.assertEqual(text.count(f"`id:{todo_id}`"), 1)
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
        with self.assertRaises(ws.AdvisorError):
            todos.complete_todo(self.target, "t-20200101-999")

    def test_priority_and_due_are_parsed(self):
        todos.add_todo(self.target, "验证付费", "P0", "2026-11-01")
        item = todos.list_todos(self.target)[0]
        self.assertEqual(item["priority"], "P0")
        self.assertEqual(item["due"], "2026-11-01")
        self.assertEqual(item["text"], "验证付费")

    def test_add_flattens_multiline_text_and_source_with_spaces(self):
        source = "discussions/带 空格 的目录/纪要.md"
        todo_id = todos.add_todo(self.target, "第一行\n第二行", source=source)
        text = (self.target["path"] / "todos.md").read_text(encoding="utf-8")
        self.assertIn("第一行 第二行", text)
        self.assertIn(source, text)
        item = next(item for item in todos.list_todos(self.target) if item["id"] == todo_id)
        self.assertEqual(item["text"], "第一行 第二行")
        self.assertEqual(item["source"], source)

    def test_text_with_id_like_fragment_is_rejected(self):
        with self.assertRaises(ws.AdvisorError):
            todos.add_todo(self.target, "伪造 `id:t-20200101-001` 片段")

    def test_invalid_due_is_rejected(self):
        with self.assertRaises(ws.AdvisorError):
            todos.add_todo(self.target, "访谈", due="2026/10/27")

    def test_complete_handles_file_without_trailing_newline(self):
        path = self.target["path"] / "todos.md"
        todo_id = "t-20200101-001"
        path.write_text(
            f"# 待办\n\n## 进行中\n- [ ] 末尾项 `id:{todo_id}`\n\n## 已完成",
            encoding="utf-8",
        )
        todos.complete_todo(self.target, todo_id)
        text = path.read_text(encoding="utf-8")
        self.assertEqual(text.count(f"`id:{todo_id}`"), 1)
        items = todos.list_todos(self.target)
        self.assertEqual(len(items), 1)
        self.assertTrue(items[0]["done"])
        self.assertEqual(items[0]["text"], "末尾项")

    def test_duplicate_id_lookup_raises(self):
        path = self.target["path"] / "todos.md"
        todo_id = "t-20200101-001"
        path.write_text(
            f"# 待办\n\n## 进行中\n- [ ] 甲 `id:{todo_id}`\n- [ ] 乙 `id:{todo_id}`\n\n## 已完成\n",
            encoding="utf-8",
        )
        with self.assertRaises(ws.AdvisorError):
            todos.complete_todo(self.target, todo_id)

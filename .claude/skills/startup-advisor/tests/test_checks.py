import unittest

import helpers
import entities
import checks
import notes


class DoctorTests(helpers.WorkspaceTestCase):
    def test_clean_workspace_has_no_issues(self):
        self.assertEqual(checks.run_doctor(self.ws), [])

    def test_missing_main_file_is_error(self):
        (self.ws.ventures / "残缺项目").mkdir()
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "缺少 PROJECT.md" in issue["message"]
            for issue in issues
        ))

    def test_duplicate_todo_ids_are_errors(self):
        target = entities.create_project(self.ws, "测试")
        (target["path"] / "todos.md").write_text(
            "# 待办\n\n## 进行中\n"
            "- [ ] 第一项 `id:t-20261020-001`\n"
            "- [ ] 第二项 `id:t-20261020-001`\n\n"
            "## 已完成\n",
            encoding="utf-8",
        )
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(issue["level"] == "error" and "重复" in issue["message"] for issue in issues))

    def test_stale_active_target_is_warning(self):
        self.ws.set_active("不存在的项目")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(issue["level"] == "warning" and "活跃目标" in issue["message"] for issue in issues))

    def test_note_target_mismatch_is_warning(self):
        target = entities.create_project(self.ws, "测试")
        path = notes.create_note(self.ws, target, "讨论")
        text = path.read_text(encoding="utf-8").replace("target: 测试", "target: 其他")
        path.write_text(text, encoding="utf-8")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "warning" and "target" in issue["message"]
            for issue in issues
        ))

    def test_missing_source_is_warning(self):
        target = entities.create_project(self.ws, "测试")
        from todos import add_todo
        add_todo(target, "行动", source="discussions/不存在.md")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "warning" and "来源不存在" in issue["message"]
            for issue in issues
        ))

    def test_corrupt_state_returns_error_not_crash(self):
        self.ws.state_file.write_text("{ 坏掉的 JSON", encoding="utf-8")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "状态" in issue["message"]
            for issue in issues
        ))

    def test_non_object_state_returns_error_not_crash(self):
        self.ws.state_file.write_text("[]", encoding="utf-8")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "状态" in issue["message"]
            for issue in issues
        ))

    def test_missing_profile_and_state_are_reported(self):
        self.ws.profile.unlink()
        self.ws.state_file.unlink()
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "个人档案" in issue["message"]
            for issue in issues
        ))
        self.assertTrue(any(
            issue["level"] == "warning" and "状态文件" in issue["message"]
            for issue in issues
        ))

    def test_reserved_name_and_inbox_missing_main_are_reported(self):
        (self.ws.ventures / "_CON").mkdir()
        (self.ws.inbox / "坏想法").mkdir()
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error"
            and "缺少 PROJECT.md" in issue["message"]
            and issue["path"] == "_CON"
            for issue in issues
        ))
        self.assertTrue(any(
            issue["level"] == "error"
            and "缺少 IDEA.md" in issue["message"]
            and issue["path"] == "_inbox/坏想法"
            for issue in issues
        ))
        self.assertFalse(any(
            "缺少 PROJECT.md" in issue["message"] and issue["path"] == "_inbox"
            for issue in issues
        ))

    def test_non_utf8_state_is_reported_not_crash(self):
        self.ws.state_file.write_bytes(b"\xff\xfe")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "状态" in issue["message"]
            for issue in issues
        ))

    def test_non_utf8_project_main_does_not_crash(self):
        target = entities.create_project(self.ws, "测试")
        self.ws.set_active(target["rel"])
        (target["path"] / "PROJECT.md").write_bytes(b"\xff\xfe")
        issues = checks.run_doctor(self.ws)
        self.assertIsInstance(issues, list)

    def test_non_utf8_note_is_reported(self):
        target = entities.create_project(self.ws, "测试")
        note = notes.create_note(self.ws, target, "讨论")
        note.write_bytes(b"\xff\xfe")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(
            issue["level"] == "error" and "纪要" in issue["message"]
            for issue in issues
        ))

    def test_doctor_does_not_create_todos_file(self):
        target = entities.create_project(self.ws, "测试")
        todos_path = target["path"] / "todos.md"
        self.assertFalse(todos_path.exists())
        checks.run_doctor(self.ws)
        self.assertFalse(todos_path.exists())

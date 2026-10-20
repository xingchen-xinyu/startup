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
        self.assertTrue(any("缺少 PROJECT.md" in issue["message"] for issue in issues))

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
        self.assertTrue(any("target" in issue["message"] for issue in issues))

    def test_missing_source_is_warning(self):
        target = entities.create_project(self.ws, "测试")
        from todos import add_todo
        add_todo(target, "行动", source="discussions/不存在.md")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any("来源不存在" in issue["message"] for issue in issues))

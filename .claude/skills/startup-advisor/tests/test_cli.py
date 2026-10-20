import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "scripts" / "advisor.py"


def run_cli(root, *args):
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_is_idempotent(self):
        first = run_cli(self.root, "init")
        second = run_cli(self.root, "init")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertTrue((self.root / "ventures" / "profile.md").exists())

    def test_idea_new_and_resume_json(self):
        created = run_cli(self.root, "idea", "new", "--title", "宠物社交", "--json")
        self.assertEqual(created.returncode, 0, created.stderr)
        data = json.loads(created.stdout)
        self.assertEqual(data["rel"], "_inbox/宠物社交")

        resume = run_cli(self.root, "resume", "--json")
        data = json.loads(resume.stdout)
        self.assertEqual(resume.returncode, 0, resume.stderr)
        self.assertIn("targets", data)

    def test_note_todo_decision_flow(self):
        run_cli(self.root, "project", "new", "--name", "AI 知识库")
        note = run_cli(self.root, "note", "new", "AI 知识库", "--title", "定价策略", "--json")
        self.assertEqual(note.returncode, 0, note.stderr)
        note_rel = json.loads(note.stdout)["rel"]

        todo = run_cli(self.root, "todo", "add", "AI 知识库", "--text", "访谈 3 家", "--json")
        self.assertEqual(todo.returncode, 0, todo.stderr)
        todo_id = json.loads(todo.stdout)["id"]

        done = run_cli(self.root, "todo", "done", "AI 知识库", todo_id)
        self.assertEqual(done.returncode, 0, done.stderr)

        decision = run_cli(
            self.root, "decision", "add", "AI 知识库",
            "--title", "目标用户", "--decision", "只服务技术团队",
            "--source", note_rel,
        )
        self.assertEqual(decision.returncode, 0, decision.stderr)

        doctor = run_cli(self.root, "doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)

    def test_promote_via_cli(self):
        run_cli(self.root, "idea", "new", "--title", "宠物社交")
        promoted = run_cli(self.root, "project", "promote", "宠物社交", "--json")
        self.assertEqual(promoted.returncode, 0, promoted.stderr)
        data = json.loads(promoted.stdout)
        self.assertEqual(data["kind"], "project")
        self.assertFalse((self.root / "ventures" / "_inbox" / "宠物社交").exists())

    def test_ambiguous_reference_exits_one(self):
        run_cli(self.root, "project", "new", "--name", "AI 知识库")
        run_cli(self.root, "project", "new", "--name", "AI 写作")
        result = run_cli(self.root, "project", "show", "AI")
        self.assertEqual(result.returncode, 1)
        self.assertIn("多个", result.stderr)

    def test_doctor_reports_errors(self):
        run_cli(self.root, "project", "new", "--name", "测试")
        todos = self.root / "ventures" / "测试" / "todos.md"
        todos.write_text(
            "# 待办\n\n## 进行中\n- [ ] A `id:t-20261020-001`\n- [ ] B `id:t-20261020-001`\n\n## 已完成\n",
            encoding="utf-8",
        )
        result = run_cli(self.root, "doctor")
        self.assertEqual(result.returncode, 1)
        self.assertIn("重复", result.stderr + result.stdout)

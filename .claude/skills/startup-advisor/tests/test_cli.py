import tempfile
import unittest
from pathlib import Path

from helpers import run_cli, write


class InitTests(unittest.TestCase):
    def test_init_creates_workspace_and_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            ventures = root / "ventures"
            for rel in (
                "portfolio.md",
                "me/profile.md",
                "me/self.md",
                "me/writing-style.md",
            ):
                self.assertTrue((ventures / rel).is_file(), rel)
            self.assertIn("created: ventures/portfolio.md", out)

    def test_init_is_idempotent_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(run_cli(root, "init")[0], 0)
            profile = root / "ventures/me/profile.md"
            profile.write_text(
                profile.read_text(encoding="utf-8") + "\n- 称呼：星辰\n",
                encoding="utf-8",
                newline="\n",
            )
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            self.assertIn("称呼：星辰", profile.read_text(encoding="utf-8"))
            self.assertIn("skipped: ventures/me/profile.md", out)

    def test_init_migrates_legacy_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "ventures/profile.md"
            write(legacy, "---\nupdated: 2026-10-20\n---\n\n## 基本信息\n- 称呼：星辰\n")
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            new_profile = root / "ventures/me/profile.md"
            self.assertTrue(new_profile.is_file())
            self.assertIn("称呼：星辰", new_profile.read_text(encoding="utf-8"))
            self.assertTrue(legacy.is_file())
            self.assertIn("migrated:", out)

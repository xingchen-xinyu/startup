import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ws


class WorkspaceTestCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="advisor-test-"))
        (self.root / ".claude").mkdir()
        self.ws = ws.Workspace(self.root)
        self.ws.init()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

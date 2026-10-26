import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import advisor  # noqa: E402


def run_cli(root: Path, *args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = advisor.main(["--root", str(root), *args])
    return code, stdout.getvalue(), stderr.getvalue()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def init_workspace(root: Path) -> Path:
    code, stdout, stderr = run_cli(root, "init")
    if code != 0:
        raise AssertionError(stdout + stderr)
    return root / "ventures"

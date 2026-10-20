"""工作区路径、文本 IO、frontmatter 与命名工具。"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


class AdvisorError(Exception):
    """业务错误，CLI 以退出码 1 结束。"""


class UsageError(AdvisorError):
    """参数错误，CLI 以退出码 2 结束。"""


INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"COM{i}" for i in range(1, 10)
} | {f"LPT{i}" for i in range(1, 10)}
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    candidates = [current, *current.parents] if current.is_dir() else list(current.parents)
    for parent in candidates:
        if (parent / ".claude").is_dir():
            return parent
    raise AdvisorError("找不到项目根目录：请从包含 .claude/ 的项目中运行。")


def now() -> datetime:
    return datetime.now().astimezone()


def today() -> str:
    return now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def sanitize_name(name: str, max_len: int = 48) -> str:
    cleaned = INVALID_NAME_CHARS.sub("", name or "")
    cleaned = re.sub(r"\s+", "-", cleaned.strip())
    cleaned = cleaned.strip(".-_ ")
    cleaned = cleaned[:max_len].rstrip(".-_ ")
    if not cleaned:
        return ""
    if cleaned.upper() in RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned


def unique_dir(parent: Path, name: str) -> Path:
    base = name or f"idea-{now():%Y%m%d-%H%M}"
    candidate = parent / base
    index = 2
    while candidate.exists():
        candidate = parent / f"{base}-{index}"
        index += 1
    return candidate


def unique_file(parent: Path, base: str, suffix: str = ".md") -> Path:
    candidate = parent / f"{base}{suffix}"
    index = 2
    while candidate.exists():
        candidate = parent / f"{base}-{index}{suffix}"
        index += 1
    return candidate


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise AdvisorError(
            f"无法读取文件（编码或权限问题）：{path}。请运行 ADVISOR doctor 检查。"
        ) from exc


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition(":")
        if separator:
            meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def render_frontmatter(meta: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in meta.items():
        flat = " ".join(str(value).splitlines()).strip()
        lines.append(f"{key}: {flat}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def replace_frontmatter_field(text: str, key: str, value: str) -> str:
    meta, body = split_frontmatter(text)
    meta[key] = value
    return render_frontmatter(meta) + body


def section_lines(body: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.M | re.S,
    )
    match = pattern.search(body)
    if not match:
        return []
    lines: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        lines.append(stripped.lstrip("-* ").strip())
    return lines


class Workspace:
    def __init__(self, root: Path | None = None):
        self.root = Path(root).resolve() if root else find_project_root()
        self.ventures = self.root / "ventures"
        self.inbox = self.ventures / "_inbox"
        self.profile = self.ventures / "profile.md"
        self.state_file = self.ventures / ".state.json"
        self.templates = Path(__file__).resolve().parents[1] / "templates"

    def init(self) -> list[str]:
        created: list[str] = []
        for directory in (self.ventures, self.inbox):
            if not directory.exists():
                directory.mkdir(parents=True)
                created.append(directory.relative_to(self.root).as_posix())
        if not self.profile.exists():
            content = self.render_template("profile.md", DATE=today())
            write_text_atomic(self.profile, content)
            created.append(self.profile.relative_to(self.root).as_posix())
        if not self.state_file.exists():
            self.save_state({"version": 1, "active": "", "updated": now_iso()})
            created.append(self.state_file.relative_to(self.root).as_posix())
        return created

    def render_template(self, name: str, **values: str) -> str:
        path = self.templates / name
        if not path.exists():
            raise AdvisorError(f"缺少模板文件：{path}")
        content = read_text(path)
        for key, value in values.items():
            content = content.replace("{{" + key.upper() + "}}", str(value))
        return content

    def load_state(self) -> dict:
        if not self.state_file.exists():
            return {"version": 1, "active": "", "updated": ""}
        try:
            raw = read_text(self.state_file)
        except (OSError, UnicodeDecodeError) as exc:
            raise AdvisorError(f"状态文件无法读取：{self.state_file}") from exc
        try:
            state = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AdvisorError(f"状态文件格式损坏：{self.state_file}") from exc
        if not isinstance(state, dict):
            raise AdvisorError(f"状态文件格式损坏：{self.state_file}")
        return state

    def save_state(self, state: dict) -> None:
        content = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        write_text_atomic(self.state_file, content)

    def set_active(self, rel: str) -> None:
        state = self.load_state()
        state.update({"version": 1, "active": rel, "updated": now_iso()})
        self.save_state(state)

    def active(self) -> str:
        return str(self.load_state().get("active", ""))

    def has_profile(self) -> bool:
        return self.profile.exists()

"""待办清单的解析与增删改查。"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from ws import AdvisorError, read_text, today, write_text_atomic

TODO_RE = re.compile(
    r"^- \[(?P<mark>[ xX])\]\s+(?P<body>.*?)\s*`id:(?P<id>t-\d{8}-\d{3})`"
    r"(?P<tail>(?:\s*—\s*来源：.*?)?(?:\s*—\s*完成于\s*\d{4}-\d{2}-\d{2})?)\s*$"
)
PRIORITY_RE = re.compile(r"^\[(?P<priority>P[0-3])\]\s*")
DUE_RE = re.compile(r"📅\s*(\d{4}-\d{2}-\d{2})")
ID_FRAGMENT_RE = re.compile(r"`id:t-\d{8}-\d{3}`")
DUE_FORMAT_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

EMPTY = "# 待办\n\n## 进行中\n\n## 已完成\n"


def _parse_source(tail: str) -> str:
    tail = re.sub(r"\s*—\s*完成于\s*\d{4}-\d{2}-\d{2}\s*$", "", tail)
    match = re.match(r"\s*—\s*来源：(?P<source>.*)$", tail, re.S)
    return match.group("source").strip() if match else ""


def parse_todo_line(line: str) -> dict | None:
    match = TODO_RE.match(line.rstrip())
    if not match:
        return None
    body = match.group("body")
    priority = "P2"
    priority_match = PRIORITY_RE.match(body)
    if priority_match:
        priority = priority_match.group("priority")
        body = body[priority_match.end():]
    due_match = DUE_RE.search(body)
    text = body
    if due_match:
        text = text[: due_match.start()].rstrip(" —-")
    return {
        "id": match.group("id"),
        "done": match.group("mark").lower() == "x",
        "text": text.strip(),
        "priority": priority,
        "due": due_match.group(1) if due_match else "",
        "source": _parse_source(match.group("tail")),
        "raw": line,
    }


def parse_todos(text: str) -> list[dict]:
    items = []
    for line in text.splitlines():
        item = parse_todo_line(line)
        if item:
            items.append(item)
    return items


def _path(target: dict) -> Path:
    return target["path"] / "todos.md"


def _load(target: dict) -> str:
    path = _path(target)
    if not path.exists():
        write_text_atomic(path, EMPTY)
        return EMPTY
    return read_text(path)


def list_todos(target: dict, open_only: bool = False) -> list[dict]:
    items = parse_todos(_load(target))
    if open_only:
        items = [item for item in items if not item["done"]]
    return items


def _next_id(existing: list[dict]) -> str:
    prefix = f"t-{today().replace('-', '')}-"
    used = {item["id"] for item in existing}
    index = 1
    while f"{prefix}{index:03d}" in used:
        index += 1
    return f"{prefix}{index:03d}"


def _insert_after_heading(text: str, heading: str, line: str) -> str:
    match = re.search(rf"^{re.escape(heading)}[ \t]*$", text, re.M)
    if match is None:
        raise AdvisorError(f"待办文件缺少分区：{heading}")
    insert_at = text.find("\n", match.end())
    if insert_at == -1:
        return text + "\n" + line + "\n"
    return text[: insert_at + 1] + line + "\n" + text[insert_at + 1:]


def _remove_line(text: str, raw: str) -> str:
    updated, count = re.compile(rf"^{re.escape(raw)}\n?", re.M).subn("", text, count=1)
    if count == 0:
        raise AdvisorError("待办文件内容已变化，请重试。")
    return updated


def add_todo(target: dict, text: str, priority: str = "P2", due: str = "", source: str = "") -> str:
    text = " ".join((text or "").split())
    source = " ".join((source or "").split())
    if not text:
        raise AdvisorError("待办内容不能为空。")
    if priority not in {"P0", "P1", "P2", "P3"}:
        raise AdvisorError(f"未知优先级：{priority}")
    if ID_FRAGMENT_RE.search(text) or ID_FRAGMENT_RE.search(source):
        raise AdvisorError("待办内容或来源不能包含形如 `id:t-YYYYMMDD-NNN` 的片段，请改写后重试。")
    if due:
        if not DUE_FORMAT_RE.fullmatch(due):
            raise AdvisorError(f"截止日期格式不正确：{due}，请使用 YYYY-MM-DD 格式。")
        try:
            datetime.date.fromisoformat(due)
        except ValueError as exc:
            raise AdvisorError(f"截止日期不是有效日期：{due}") from exc
    content = _load(target)
    todo_id = _next_id(parse_todos(content))
    line = f"- [ ] [{priority}] {text}"
    if due:
        line += f" — 📅 {due}"
    line += f" `id:{todo_id}`"
    if source:
        line += f" — 来源：{source}"
    content = _insert_after_heading(content, "## 进行中", line)
    write_text_atomic(_path(target), content)
    return todo_id


def _find(target: dict, todo_id: str) -> dict:
    matches = [item for item in parse_todos(_load(target)) if item["id"] == todo_id]
    if len(matches) > 1:
        raise AdvisorError(f"待办中存在重复 ID：{todo_id}，请运行 doctor 检查待办文件。")
    if not matches:
        raise AdvisorError(f"找不到待办：{todo_id}")
    return matches[0]


def complete_todo(target: dict, todo_id: str) -> None:
    item = _find(target, todo_id)
    if item["done"]:
        return
    content = _load(target)
    content = _remove_line(content, item["raw"])
    completed = item["raw"].replace("- [ ]", "- [x]", 1).rstrip()
    completed += f" — 完成于 {today()}"
    content = _insert_after_heading(content, "## 已完成", completed)
    write_text_atomic(_path(target), content)


def reopen_todo(target: dict, todo_id: str) -> None:
    item = _find(target, todo_id)
    if not item["done"]:
        return
    content = _load(target)
    content = _remove_line(content, item["raw"])
    reopened = re.sub(r"\s*—\s*完成于\s*\d{4}-\d{2}-\d{2}\s*$", "", item["raw"])
    reopened = reopened.replace("- [x]", "- [ ]", 1).replace("- [X]", "- [ ]", 1)
    content = _insert_after_heading(content, "## 进行中", reopened)
    write_text_atomic(_path(target), content)

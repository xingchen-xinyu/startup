"""待办清单的解析与增删改查。"""

from __future__ import annotations

import re
from pathlib import Path

from ws import AdvisorError, read_text, today, write_text_atomic

TODO_RE = re.compile(
    r"^- \[(?P<mark>[ xX])\]\s+(?P<body>.*?)\s*`id:(?P<id>t-\d{8}-\d{3})`\s*(?P<tail>.*)$"
)
PRIORITY_RE = re.compile(r"^\[(?P<priority>P[0-3])\]\s*")
DUE_RE = re.compile(r"📅\s*(\d{4}-\d{2}-\d{2})")
SOURCE_RE = re.compile(r"来源：\s*(\S+)")

EMPTY = "# 待办\n\n## 进行中\n\n## 已完成\n"


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
    source_match = SOURCE_RE.search(match.group("tail"))
    text = body
    if due_match:
        text = text[: due_match.start()].rstrip(" —-")
    return {
        "id": match.group("id"),
        "done": match.group("mark").lower() == "x",
        "text": text.strip(),
        "priority": priority,
        "due": due_match.group(1) if due_match else "",
        "source": source_match.group(1) if source_match else "",
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
    match = re.search(rf"^{re.escape(heading)}\s*$", text, re.M)
    if match is None:
        raise AdvisorError(f"待办文件缺少分区：{heading}")
    insert_at = text.find("\n", match.end())
    insert_at = len(text) if insert_at == -1 else insert_at + 1
    return text[:insert_at] + line + "\n" + text[insert_at:]


def _remove_line(text: str, raw: str) -> str:
    return text.replace(raw.rstrip("\n") + "\n", "", 1)


def add_todo(target: dict, text: str, priority: str = "P2", due: str = "", source: str = "") -> str:
    text = (text or "").strip()
    if not text:
        raise AdvisorError("待办内容不能为空。")
    if priority not in {"P0", "P1", "P2", "P3"}:
        raise AdvisorError(f"未知优先级：{priority}")
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
    for item in parse_todos(_load(target)):
        if item["id"] == todo_id:
            return item
    raise AdvisorError(f"找不到待办：{todo_id}")


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

"""讨论纪要、决策记录、续接扫描与收尾。"""

from __future__ import annotations

from pathlib import Path

from entities import append_idea_note_index, iter_targets, target_label, touch_target
from todos import list_todos
from ws import (
    AdvisorError,
    Workspace,
    read_text,
    replace_frontmatter_field,
    sanitize_name,
    section_lines,
    split_frontmatter,
    today,
    unique_file,
    write_text_atomic,
)


def _read_note(path: Path) -> dict:
    text = read_text(path)
    meta, body = split_frontmatter(text)
    return {
        "path": path,
        "meta": meta,
        "body": body,
        "title": meta.get("title", path.stem),
        "date": meta.get("date", ""),
        "status": meta.get("status", "open"),
        "next_step": meta.get("next_step", ""),
        "open_questions": section_lines(body, "未决问题"),
    }


def create_note(ws: Workspace, target: dict, title: str, next_step: str = "") -> Path:
    title = (title or "").strip()
    if not title:
        raise AdvisorError("讨论主题不能为空。")
    discussions = target["path"] / "discussions"
    discussions.mkdir(parents=True, exist_ok=True)
    base = f"{today()}-{sanitize_name(title, 40) or '讨论'}"
    path = unique_file(discussions, base)
    content = ws.render_template(
        "discussion.md", TITLE=title, DATE=today(),
        TARGET=target["rel"], NEXT_STEP=next_step,
    )
    write_text_atomic(path, content)
    touch_target(target)
    if target["kind"] == "idea":
        rel = path.relative_to(target["path"]).as_posix()
        append_idea_note_index(target, title, today(), rel)
    return path


def list_notes(target: dict, open_only: bool = False, limit: int | None = None) -> list[dict]:
    directory = target["path"] / "discussions"
    paths = sorted(directory.glob("*.md")) if directory.is_dir() else []
    items = []
    for path in paths:
        note = _read_note(path)
        note["rel"] = path.relative_to(target["path"]).as_posix()
        items.append(note)
    if open_only:
        items = [note for note in items if note["status"] == "open"]
    items.sort(key=lambda note: (note["date"], note["path"].name), reverse=True)
    return items[:limit] if limit is not None else items


def find_note(ws: Workspace, ref: str) -> Path:
    candidate = Path(ref)
    if not candidate.is_absolute():
        candidate = ws.root / candidate
    resolved = candidate.resolve()
    ventures = ws.ventures.resolve()
    if resolved.is_file() and resolved.is_relative_to(ventures):
        return resolved

    needle = Path(ref).name
    matches = [
        path for path in ws.ventures.rglob("*.md")
        if path.parent.name == "discussions" and needle in path.name
    ]
    if not matches:
        raise AdvisorError(f"找不到讨论纪要：{ref}")
    if len(matches) > 1:
        listing = "\n".join(f"- {path.relative_to(ws.ventures).as_posix()}" for path in matches)
        raise AdvisorError(f"“{ref}”匹配到多个纪要：\n{listing}")
    return matches[0]


def close_note(ws: Workspace, ref: str) -> Path:
    path = find_note(ws, ref)
    text = read_text(path)
    write_text_atomic(path, replace_frontmatter_field(text, "status", "closed"))
    return path


def add_decision(
    target: dict,
    title: str,
    decision: str,
    options: str = "",
    reason: str = "",
    impact: str = "",
    source: str = "",
) -> Path:
    if not title.strip() or not decision.strip():
        raise AdvisorError("决策标题和决定内容不能为空。")
    path = target["path"] / "decisions.md"
    if not path.exists():
        write_text_atomic(path, "# 决策记录\n")
    text = read_text(path)
    lines = [
        f"## {today()} · {title.strip()}",
        "",
        f"- **决定**：{decision.strip()}",
    ]
    if options.strip():
        lines.append(f"- **备选**：{options.strip()}")
    if reason.strip():
        lines.append(f"- **理由**：{reason.strip()}")
    if impact.strip():
        lines.append(f"- **影响**：{impact.strip()}")
    if source.strip():
        lines.append(f"- **来源**：{source.strip()}")
    write_text_atomic(path, text.rstrip() + "\n\n" + "\n".join(lines) + "\n")
    touch_target(target)
    return path

"""项目与临时想法的创建、查询、更新。"""

from __future__ import annotations

import re
from pathlib import Path

from ws import (
    AdvisorError,
    Workspace,
    now,
    read_text,
    render_frontmatter,
    sanitize_name,
    section_lines,
    split_frontmatter,
    today,
    unique_dir,
    write_text_atomic,
)

STAGES = {"idea", "validating", "building", "operating", "paused", "archived"}


def load_target(ws: Workspace, path: Path, kind: str) -> dict:
    main = path / ("PROJECT.md" if kind == "project" else "IDEA.md")
    if not main.exists():
        raise AdvisorError(f"缺少主档文件：{main}")
    meta, body = split_frontmatter(read_text(main))
    return {
        "kind": kind,
        "slug": path.name,
        "rel": path.relative_to(ws.ventures).as_posix(),
        "path": path,
        "main": main,
        "meta": meta,
        "body": body,
    }


def iter_targets(ws: Workspace) -> list[dict]:
    targets: list[dict] = []
    if ws.ventures.is_dir():
        for path in sorted(ws.ventures.iterdir()):
            if path.is_dir() and (path / "PROJECT.md").exists():
                targets.append(load_target(ws, path, "project"))
    if ws.inbox.is_dir():
        for path in sorted(ws.inbox.iterdir()):
            if path.is_dir() and (path / "IDEA.md").exists():
                targets.append(load_target(ws, path, "idea"))
    targets.sort(key=lambda item: (item["meta"].get("updated", ""), item["rel"]), reverse=True)
    return targets


def target_label(target: dict) -> str:
    return target["meta"].get("name") or target["meta"].get("title") or target["slug"]


def find_target(ws: Workspace, ref: str) -> dict:
    ref = (ref or "").strip()
    if not ref:
        raise AdvisorError("请提供项目名或想法名。")
    targets = iter_targets(ws)
    normalized = ref.replace("\\", "/")
    matches = [target for target in targets if target["rel"] == normalized]
    if not matches:
        matches = [target for target in targets if target["slug"].lower() == ref.lower()]
    if not matches:
        matches = [target for target in targets if target_label(target).lower() == ref.lower()]
    if not matches:
        matches = [
            target for target in targets
            if ref.lower() in target["slug"].lower()
            or ref.lower() in target_label(target).lower()
        ]
    if not matches:
        available = "、".join(target_label(target) for target in targets) or "（暂无项目）"
        raise AdvisorError(f"找不到“{ref}”。可用的项目/想法：{available}")
    if len(matches) > 1:
        candidates = "\n".join(
            f"- [{'项目' if target['kind'] == 'project' else '想法'}] "
            f"{target_label(target)}（{target['rel']}）"
            for target in matches
        )
        raise AdvisorError(f"“{ref}”匹配到多个目标，请说得更具体：\n{candidates}")
    return matches[0]


def _replace_heading(body: str, keyword: str, value: str) -> str:
    pattern = re.compile(rf"^#\s*{re.escape(keyword)}\s*[:：].*$", re.M)
    return pattern.sub(lambda match: f"# {keyword}：{value}", body, count=1)


def _replace_section(body: str, heading: str, value: str) -> str:
    pattern = re.compile(
        rf"^(##[ \t]*{re.escape(heading)}[ \t]*)$(.*?)(?=^##[ \t]|\Z)",
        re.M | re.S,
    )
    updated, count = pattern.subn(
        lambda match: f"{match.group(1)}\n\n{value}\n\n", body, count=1,
    )
    if count == 0:
        updated = body.rstrip() + f"\n\n## {heading}\n\n{value}\n"
    return updated


def touch_target(target: dict, updates: dict[str, str] | None = None) -> dict:
    meta, body = split_frontmatter(read_text(target["main"]))
    normalized: dict[str, str] = {}
    if updates:
        normalized = {key: str(value) for key, value in updates.items()}
        for key in ("name", "title", "one_liner"):
            if key in normalized:
                normalized[key] = " ".join(normalized[key].split())
        meta.update(normalized)
    meta["updated"] = today()
    if target["kind"] == "project" and "name" in normalized:
        body = _replace_heading(body, "项目", normalized["name"])
    elif target["kind"] == "idea" and "title" in normalized:
        body = _replace_heading(body, "想法", normalized["title"])
    if "one_liner" in normalized:
        body = _replace_section(body, "一句话", normalized["one_liner"])
    write_text_atomic(target["main"], render_frontmatter(meta) + body)
    target["meta"] = meta
    target["body"] = body
    return target


def create_project(ws: Workspace, name: str, one_liner: str = "", stage: str = "idea") -> dict:
    name = " ".join((name or "").split())
    one_liner = " ".join((one_liner or "").split())
    if not name:
        raise AdvisorError("项目名称不能为空。")
    if stage not in STAGES:
        raise AdvisorError(f"未知阶段：{stage}")
    slug = sanitize_name(name) or f"project-{now():%Y%m%d-%H%M}"
    path = unique_dir(ws.ventures, slug)
    (path / "discussions").mkdir(parents=True, exist_ok=True)
    (path / "assets").mkdir(exist_ok=True)
    content = ws.render_template(
        "PROJECT.md", NAME=name, STAGE=stage, ONE_LINER=one_liner, DATE=today(),
    )
    write_text_atomic(path / "PROJECT.md", content)
    return load_target(ws, path, "project")


def create_idea(ws: Workspace, title: str, one_liner: str = "") -> dict:
    title = " ".join((title or "").split())
    slug = sanitize_name(title)
    if not slug:
        slug = f"idea-{now():%Y%m%d-%H%M}"
        title = title or f"新想法 {today()}"
    path = unique_dir(ws.inbox, slug)
    (path / "discussions").mkdir(parents=True, exist_ok=True)
    (path / "assets").mkdir(exist_ok=True)
    content = ws.render_template("IDEA.md", TITLE=title, DATE=today())
    if one_liner:
        content = content.replace("## 一句话\n", f"## 一句话\n\n{one_liner}\n", 1)
    write_text_atomic(path / "IDEA.md", content)
    return load_target(ws, path, "idea")


def update_target(target: dict, **changes: str | None) -> dict:
    allowed = {"name", "title", "stage", "one_liner", "next_action"}
    updates = {key: value for key, value in changes.items() if value is not None}
    unknown = set(updates) - allowed
    if unknown:
        raise AdvisorError(f"不支持的更新字段：{', '.join(sorted(unknown))}")
    if "stage" in updates and updates["stage"] not in STAGES:
        raise AdvisorError(f"未知阶段：{updates['stage']}")
    return touch_target(target, updates)


def append_idea_note_index(target: dict, title: str, date: str, note_rel: str) -> None:
    if target["kind"] != "idea":
        return
    text = read_text(target["main"])
    line = f"- {date} [{title}]({note_rel})"
    if line in text:
        return
    heading = "## 讨论索引"
    match = re.search(rf"^##\s*讨论索引\s*$", text, re.M)
    if match is None:
        text = text.rstrip() + f"\n\n{heading}\n\n{line}\n"
    else:
        insert_at = text.find("\n", match.end())
        insert_at = len(text) if insert_at == -1 else insert_at + 1
        text = text[:insert_at] + line + "\n" + text[insert_at:]
    write_text_atomic(target["main"], text)


def idea_one_liner(target: dict) -> str:
    lines = section_lines(target["body"], "一句话")
    return lines[0] if lines else ""

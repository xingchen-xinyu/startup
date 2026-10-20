"""工作区一致性自检。"""

from __future__ import annotations

from collections import Counter

from entities import find_target, iter_targets
from todos import list_todos
from ws import AdvisorError, Workspace, read_text, split_frontmatter


def run_doctor(ws: Workspace) -> list[dict]:
    issues: list[dict] = []

    if not ws.profile.exists():
        issues.append({
            "level": "error",
            "message": "缺少个人档案",
            "path": "ventures/profile.md",
        })

    if not ws.state_file.exists():
        issues.append({
            "level": "warning",
            "message": "缺少状态文件",
            "path": "ventures/.state.json",
        })
    else:
        try:
            ws.load_state()
        except AdvisorError as exc:
            issues.append({
                "level": "error",
                "message": str(exc),
                "path": "ventures/.state.json",
            })

    if ws.active():
        try:
            find_target(ws, ws.active())
        except AdvisorError:
            issues.append({
                "level": "warning",
                "message": f"活跃目标已失效：{ws.active()}",
                "path": "ventures/.state.json",
            })

    if ws.ventures.is_dir():
        for path in ws.ventures.iterdir():
            if path.is_dir() and path.name != "_inbox" and not (path / "PROJECT.md").exists():
                issues.append({
                    "level": "error",
                    "message": "项目目录缺少 PROJECT.md",
                    "path": path.relative_to(ws.ventures).as_posix(),
                })
    if ws.inbox.is_dir():
        for path in ws.inbox.iterdir():
            if path.is_dir() and not (path / "IDEA.md").exists():
                issues.append({
                    "level": "error",
                    "message": "临时想法目录缺少 IDEA.md",
                    "path": path.relative_to(ws.ventures).as_posix(),
                })

    for target in iter_targets(ws):
        todo_items = list_todos(target)
        duplicates = [
            todo_id for todo_id, count in Counter(item["id"] for item in todo_items).items()
            if count > 1
        ]
        for todo_id in duplicates:
            issues.append({
                "level": "error",
                "message": f"待办 ID 重复：{todo_id}",
                "path": target["rel"],
            })

        discussions = target["path"] / "discussions"
        if discussions.is_dir():
            for note in discussions.glob("*.md"):
                meta, _ = split_frontmatter(read_text(note))
                note_target = meta.get("target", "")
                if note_target and note_target != target["rel"]:
                    issues.append({
                        "level": "warning",
                        "message": f"纪要 target 指向 {note_target}，与所在目录不一致",
                        "path": f"{target['rel']}/discussions/{note.name}",
                    })

        for item in todo_items:
            if item["source"]:
                source = target["path"] / item["source"]
                if not source.exists():
                    issues.append({
                        "level": "warning",
                        "message": f"待办 {item['id']} 的来源不存在：{item['source']}",
                        "path": target["rel"],
                    })

    return issues

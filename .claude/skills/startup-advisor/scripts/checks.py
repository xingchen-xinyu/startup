"""工作区一致性自检。"""

from __future__ import annotations

from collections import Counter

from entities import find_target, iter_targets
from todos import parse_todos
from ws import AdvisorError, Workspace, read_text, split_frontmatter


def run_doctor(ws: Workspace) -> list[dict]:
    issues: list[dict] = []

    if not ws.profile.exists():
        issues.append({
            "level": "error",
            "message": "缺少个人档案",
            "path": "ventures/profile.md",
        })

    state = None
    if not ws.state_file.exists():
        issues.append({
            "level": "warning",
            "message": "缺少状态文件",
            "path": "ventures/.state.json",
        })
    else:
        try:
            state = ws.load_state()
        except (AdvisorError, OSError, UnicodeDecodeError) as exc:
            issues.append({
                "level": "error",
                "message": str(exc),
                "path": "ventures/.state.json",
            })

    if state is not None:
        active = str(state.get("active", "") or "")
        if active:
            try:
                find_target(ws, active)
            except (AdvisorError, OSError, UnicodeDecodeError) as exc:
                issues.append({
                    "level": "warning",
                    "message": f"活跃目标已失效：{active}（{exc}）",
                    "path": "ventures/.state.json",
                })

    inbox_resolved = ws.inbox.resolve()
    if ws.ventures.is_dir():
        try:
            venture_paths = list(ws.ventures.iterdir())
        except OSError as exc:
            issues.append({
                "level": "error",
                "message": f"无法读取项目目录：{exc}",
                "path": "ventures",
            })
            venture_paths = []
        for path in venture_paths:
            if (
                path.is_dir()
                and path.resolve() != inbox_resolved
                and not (path / "PROJECT.md").exists()
            ):
                issues.append({
                    "level": "error",
                    "message": "项目目录缺少 PROJECT.md",
                    "path": path.relative_to(ws.ventures).as_posix(),
                })
    if ws.inbox.is_dir():
        try:
            inbox_paths = list(ws.inbox.iterdir())
        except OSError as exc:
            issues.append({
                "level": "error",
                "message": f"无法读取临时想法目录：{exc}",
                "path": "ventures/_inbox",
            })
            inbox_paths = []
        for path in inbox_paths:
            if path.is_dir() and not (path / "IDEA.md").exists():
                issues.append({
                    "level": "error",
                    "message": "临时想法目录缺少 IDEA.md",
                    "path": path.relative_to(ws.ventures).as_posix(),
                })

    try:
        targets = iter_targets(ws)
    except (OSError, UnicodeDecodeError, AdvisorError) as exc:
        issues.append({
            "level": "error",
            "message": f"无法枚举项目与想法：{exc}",
            "path": "ventures",
        })
        targets = []

    for target in targets:
        todos_path = target["path"] / "todos.md"
        try:
            todo_items = parse_todos(read_text(todos_path)) if todos_path.exists() else []
        except (OSError, UnicodeDecodeError) as exc:
            issues.append({
                "level": "error",
                "message": f"无法读取待办：{exc}",
                "path": target["rel"],
            })
            todo_items = []

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
            try:
                note_paths = sorted(discussions.glob("*.md"))
            except OSError as exc:
                issues.append({
                    "level": "error",
                    "message": f"无法读取纪要目录：{exc}",
                    "path": f"{target['rel']}/discussions",
                })
                note_paths = []
            for note in note_paths:
                note_rel = f"{target['rel']}/discussions/{note.name}"
                try:
                    meta, _ = split_frontmatter(read_text(note))
                except (OSError, UnicodeDecodeError) as exc:
                    issues.append({
                        "level": "error",
                        "message": f"无法读取纪要：{exc}",
                        "path": note_rel,
                    })
                    continue
                note_target = meta.get("target", "")
                if note_target and note_target != target["rel"]:
                    issues.append({
                        "level": "warning",
                        "message": f"纪要 target 指向 {note_target}，与所在目录不一致",
                        "path": note_rel,
                    })

        for item in todo_items:
            if item["source"]:
                source = target["path"] / item["source"]
                if not source.exists():
                    source = ws.ventures / item["source"]
                if not source.exists():
                    issues.append({
                        "level": "warning",
                        "message": f"待办 {item['id']} 的来源不存在：{item['source']}",
                        "path": target["rel"],
                    })

    return issues

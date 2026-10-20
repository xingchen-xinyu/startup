#!/usr/bin/env python3
"""创业顾问工作区 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import checks
import entities
import notes
import todos
from ws import AdvisorError, UsageError, Workspace

READ_ONLY_COMMANDS = {"resume", "status", "doctor"}
READ_ONLY_SUBCOMMANDS = {
    ("idea", "list"),
    ("project", "list"),
    ("project", "show"),
    ("note", "list"),
    ("todo", "list"),
}


def _is_read_only(args) -> bool:
    if args.command in READ_ONLY_COMMANDS:
        return True
    sub = getattr(args, f"{args.command}_cmd", None)
    return (args.command, sub) in READ_ONLY_SUBCOMMANDS


def _print_json(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _summary(target: dict) -> dict:
    return {
        "kind": target["kind"],
        "rel": target["rel"],
        "label": entities.target_label(target),
        "stage": target["meta"].get("stage", ""),
        "next_action": target["meta"].get("next_action", ""),
        "path": str(target["path"]),
    }


def _render_resume(data: dict) -> str:
    lines = ["上次停在这里："]
    discussions = data["open_discussions"]
    if discussions:
        for index, item in enumerate(discussions, 1):
            lines.append(f"{index}. [{item['target_label']}] {item['date']}「{item['title']}」")
            for question in item["open_questions"][:2]:
                lines.append(f"   未决：{question}")
            if item["next_step"]:
                lines.append(f"   下一步：{item['next_step']}")
        remaining = data["open_discussion_total"] - len(discussions)
        if remaining > 0:
            lines.append(f"…还有 {remaining} 条未结束讨论。")
    else:
        lines.append("还没有未结束的讨论。可以开一个新话题，或先聊聊一个想法。")
    if data["open_todo_count"]:
        lines.append(f"\n另有 {data['open_todo_count']} 个进行中的待办。")
    if data["active"]:
        lines.append(f"当前活跃目标：{data['active']}")
    lines.append("\n接着上次继续，还是开新话题？")
    return "\n".join(lines)


def _render_status(data: dict) -> str:
    lines = []
    if data["active"]:
        lines.append(f"当前活跃目标：{data['active']}")
    lines.append(f"个人档案：{'已建立' if data['profile_path'] else '未建立'}")
    lines.append(f"未结束讨论：{data['open_discussion_total']}，进行中待办：{data['open_todo_count']}")
    lines.append("")
    if not data["targets"]:
        lines.append("（暂无项目或想法）")
    for target in data["targets"]:
        tag = "项目" if target["kind"] == "project" else "想法"
        extra = f" · {target['stage']}" if target["stage"] else ""
        lines.append(f"- [{tag}] {target['label']}（{target['rel']}）{extra}")
        if target["next_action"]:
            lines.append(f"    下一步：{target['next_action']}")
    return "\n".join(lines)


def _render_project(target: dict, open_todos: list[dict], recent: list[dict]) -> str:
    lines = [
        f"{entities.target_label(target)}（{target['rel']}）",
        f"阶段：{target['meta'].get('stage', '') or '（未设置）'}",
        f"下一步：{target['meta'].get('next_action', '') or '（未设置）'}",
        f"未完成待办：{len(open_todos)}",
    ]
    for item in open_todos:
        lines.append(f"- {item['id']} [{item['priority']}] {item['text']}")
    lines.append("最近讨论：")
    if not recent:
        lines.append("- （暂无）")
    for note in recent:
        lines.append(f"- {note['date']}「{note['title']}」{note['status']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="advisor.py", description="创业顾问工作区管理")
    parser.add_argument("--root", type=Path, default=None, help="项目根目录（默认自动查找）")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="初始化工作区")

    p = sub.add_parser("resume", help="查看未结束的讨论")
    p.add_argument("--json", action="store_true")
    p.add_argument("--limit", type=int, default=3)

    p = sub.add_parser("status", help="工作区概览")
    p.add_argument("--json", action="store_true")

    idea = sub.add_parser("idea", help="临时想法")
    idea_sub = idea.add_subparsers(dest="idea_cmd", required=True)
    p = idea_sub.add_parser("new")
    p.add_argument("--title", required=True)
    p.add_argument("--one-liner", default="")
    p.add_argument("--json", action="store_true")
    p = idea_sub.add_parser("list")
    p.add_argument("--json", action="store_true")

    project = sub.add_parser("project", help="正式项目")
    project_sub = project.add_subparsers(dest="project_cmd", required=True)
    p = project_sub.add_parser("new")
    p.add_argument("--name", required=True)
    p.add_argument("--one-liner", default="")
    p.add_argument("--stage", default="idea", choices=sorted(entities.STAGES))
    p.add_argument("--json", action="store_true")
    p = project_sub.add_parser("list")
    p.add_argument("--json", action="store_true")
    p.add_argument("--include-archived", action="store_true")
    p = project_sub.add_parser("show")
    p.add_argument("ref")
    p.add_argument("--json", action="store_true")
    p = project_sub.add_parser("update")
    p.add_argument("ref")
    p.add_argument("--name")
    p.add_argument("--stage", choices=sorted(entities.STAGES))
    p.add_argument("--one-liner")
    p.add_argument("--next-action")
    p.add_argument("--json", action="store_true")
    p = project_sub.add_parser("use")
    p.add_argument("ref")
    p = project_sub.add_parser("promote")
    p.add_argument("ref")
    p.add_argument("--name", default=None)
    p.add_argument("--json", action="store_true")

    note = sub.add_parser("note", help="讨论纪要")
    note_sub = note.add_subparsers(dest="note_cmd", required=True)
    p = note_sub.add_parser("new")
    p.add_argument("ref")
    p.add_argument("--title", required=True)
    p.add_argument("--next-step", default="")
    p.add_argument("--json", action="store_true")
    p = note_sub.add_parser("list")
    p.add_argument("ref")
    p.add_argument("--open", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--json", action="store_true")
    p = note_sub.add_parser("close")
    p.add_argument("note")
    p.add_argument("--json", action="store_true")

    decision = sub.add_parser("decision", help="决策记录")
    decision_sub = decision.add_subparsers(dest="decision_cmd", required=True)
    p = decision_sub.add_parser("add")
    p.add_argument("ref")
    p.add_argument("--title", required=True)
    p.add_argument("--decision", required=True)
    p.add_argument("--options", default="")
    p.add_argument("--reason", default="")
    p.add_argument("--impact", default="")
    p.add_argument("--source", default="")
    p.add_argument("--json", action="store_true")

    todo = sub.add_parser("todo", help="待办")
    todo_sub = todo.add_subparsers(dest="todo_cmd", required=True)
    p = todo_sub.add_parser("add")
    p.add_argument("ref")
    p.add_argument("--text", required=True)
    p.add_argument("--priority", default="P2", choices=["P0", "P1", "P2", "P3"])
    p.add_argument("--due", default="")
    p.add_argument("--source", default="")
    p.add_argument("--json", action="store_true")
    p = todo_sub.add_parser("list")
    p.add_argument("ref")
    p.add_argument("--open", action="store_true")
    p.add_argument("--json", action="store_true")
    p = todo_sub.add_parser("done")
    p.add_argument("ref")
    p.add_argument("id")
    p = todo_sub.add_parser("reopen")
    p.add_argument("ref")
    p.add_argument("id")

    p = sub.add_parser("checkpoint", help="收尾")
    p.add_argument("ref")
    p.add_argument("--next-action", default=None)
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("doctor", help="一致性自检")
    p.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        ws = Workspace(args.root)
        created = [] if _is_read_only(args) else ws.init()

        if args.command == "init":
            if created:
                print("已初始化工作区：")
                for item in created:
                    print(f"- {item}")
            else:
                print("工作区已存在，无需初始化。")
            return 0

        if args.command == "resume":
            data = notes.collect_resume(ws, limit=args.limit)
            if args.json:
                _print_json(data)
            else:
                print(_render_resume(data))
            return 0

        if args.command == "status":
            data = notes.collect_resume(ws, limit=0)
            if args.json:
                _print_json(data)
            else:
                print(_render_status(data))
            return 0

        if args.command == "idea":
            if args.idea_cmd == "new":
                target = entities.create_idea(ws, args.title, args.one_liner)
                ws.set_active(target["rel"])
                if args.json:
                    _print_json(_summary(target))
                else:
                    print(f"已创建临时想法：{entities.target_label(target)}")
                    print(f"路径：{target['rel']}")
                return 0
            items = [
                {**_summary(target), "status": target["meta"].get("status", "")}
                for target in entities.iter_targets(ws) if target["kind"] == "idea"
            ]
            if args.json:
                _print_json(items)
            else:
                for item in items:
                    print(f"- [{item['status']}] {item['label']}（{item['rel']}）")
                if not items:
                    print("（暂无临时想法）")
            return 0

        if args.command == "project":
            if args.project_cmd == "new":
                target = entities.create_project(ws, args.name, args.one_liner, args.stage)
                ws.set_active(target["rel"])
                if args.json:
                    _print_json(_summary(target))
                else:
                    print(f"已创建项目：{entities.target_label(target)}")
                    print(f"路径：{target['rel']}")
                return 0

            if args.project_cmd == "list":
                items = [
                    _summary(target) for target in entities.iter_targets(ws)
                    if target["kind"] == "project"
                    and (args.include_archived or target["meta"].get("stage") != "archived")
                ]
                if args.json:
                    _print_json(items)
                else:
                    for item in items:
                        print(f"- {item['label']}（{item['rel']}）· {item['stage']}")
                    if not items:
                        print("（暂无项目）")
                return 0

            if args.project_cmd == "show":
                target = entities.find_target(ws, args.ref)
                open_items = todos.list_todos(target, open_only=True)
                recent = notes.list_notes(target, limit=3)
                data = {
                    "target": _summary(target),
                    "meta": target["meta"],
                    "open_todos": open_items,
                    "recent_notes": [
                        {
                            "title": note["title"],
                            "date": note["date"],
                            "status": note["status"],
                            "path": f"{target['rel']}/discussions/{note['path'].name}",
                        }
                        for note in recent
                    ],
                }
                if args.json:
                    _print_json(data)
                else:
                    print(_render_project(target, open_items, recent))
                return 0

            if args.project_cmd == "update":
                target = entities.find_target(ws, args.ref)
                target = entities.update_target(
                    target,
                    name=args.name,
                    stage=args.stage,
                    one_liner=args.one_liner,
                    next_action=args.next_action,
                )
                if args.json:
                    _print_json(_summary(target))
                else:
                    print(f"已更新：{entities.target_label(target)}")
                return 0

            if args.project_cmd == "use":
                target = entities.find_target(ws, args.ref)
                ws.set_active(target["rel"])
                print(f"当前目标：{target['rel']}")
                return 0

            target = entities.promote_idea(ws, args.ref, args.name)
            if args.json:
                _print_json(_summary(target))
            else:
                print(f"已转正为项目：{entities.target_label(target)}")
                print(f"路径：{target['rel']}")
            return 0

        if args.command == "note":
            if args.note_cmd == "new":
                target = entities.find_target(ws, args.ref)
                path = notes.create_note(ws, target, args.title, args.next_step)
                data = {
                    "path": str(path),
                    "rel": f"{target['rel']}/discussions/{path.name}",
                    "source": f"discussions/{path.name}",
                }
                if args.json:
                    _print_json(data)
                else:
                    print(data["rel"])
                return 0
            if args.note_cmd == "list":
                target = entities.find_target(ws, args.ref)
                items = notes.list_notes(target, open_only=args.open, limit=args.limit)
                data = [
                    {
                        "title": note["title"],
                        "date": note["date"],
                        "status": note["status"],
                        "path": f"{target['rel']}/discussions/{note['path'].name}",
                        "open_questions": note["open_questions"],
                    }
                    for note in items
                ]
                if args.json:
                    _print_json(data)
                else:
                    for item in data:
                        print(f"- {item['date']}「{item['title']}」{item['status']}")
                    if not data:
                        print("（暂无讨论）")
                return 0
            path = notes.close_note(ws, args.note)
            if args.json:
                _print_json({"path": str(path), "status": "closed"})
            else:
                print(f"已关闭讨论：{path.name}")
            return 0

        if args.command == "decision":
            target = entities.find_target(ws, args.ref)
            path = notes.add_decision(
                target, args.title, args.decision,
                args.options, args.reason, args.impact, args.source,
            )
            if args.json:
                _print_json({"path": str(path)})
            else:
                print(f"已记录决策：{args.title}")
            return 0

        if args.command == "todo":
            target = entities.find_target(ws, args.ref)
            if args.todo_cmd == "add":
                source = args.source
                prefix = f"{target['rel']}/"
                if source.startswith(prefix):
                    source = source[len(prefix):]
                todo_id = todos.add_todo(target, args.text, args.priority, args.due, source)
                if args.json:
                    _print_json({"id": todo_id})
                else:
                    print(todo_id)
                return 0
            if args.todo_cmd == "list":
                items = todos.list_todos(target, open_only=args.open)
                if args.json:
                    _print_json(items)
                else:
                    for item in items:
                        mark = "x" if item["done"] else " "
                        print(f"- [{mark}] {item['id']} [{item['priority']}] {item['text']}")
                    if not items:
                        print("（暂无待办）")
                return 0
            if args.todo_cmd == "done":
                todos.complete_todo(target, args.id)
                print(f"已完成：{args.id}")
                return 0
            todos.reopen_todo(target, args.id)
            print(f"已重新打开：{args.id}")
            return 0

        if args.command == "checkpoint":
            target = entities.find_target(ws, args.ref)
            summary = notes.checkpoint(ws, target, args.next_action)
            if args.json:
                _print_json(summary)
            else:
                print(f"已收尾：{summary['target_label']}")
                if summary["next_action"]:
                    print(f"下一步：{summary['next_action']}")
                print(f"未完成待办：{len(summary['open_todos'])}")
                for item in summary["open_todos"]:
                    print(f"- {item['id']} {item['text']}")
                if summary["open_questions"]:
                    print("未决问题：")
                    for question in summary["open_questions"]:
                        print(f"- {question}")
            return 0

        issues = checks.run_doctor(ws)
        if args.json:
            _print_json(issues)
        else:
            if not issues:
                print("自检通过，未发现问题。")
            for issue in issues:
                print(f"[{issue['level']}] {issue['message']}（{issue['path']}）")
        return 1 if any(issue["level"] == "error" for issue in issues) else 0

    except UsageError as exc:
        print(f"参数错误：{exc}", file=sys.stderr)
        return 2
    except AdvisorError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

#!/usr/bin/env python3
"""startup-advisor 最小 CLI：init / context / validate。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

PLACEHOLDER_VALUES = {
    "（待确认）",
    "(待确认)",
    "待确认",
    "（尚未确认）",
    "(尚未确认)",
    "（尚未验证的判断）",
    "(尚未验证的判断)",
    "（尚未确认的信息）",
    "(尚未确认的信息)",
}


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, []
    meta: dict[str, str] = {}
    errors: list[str] = []
    end = None
    for index in range(1, len(lines)):
        line = lines[index]
        if line.strip() == "---":
            end = index
            break
        if not line.strip():
            continue
        if ":" not in line:
            errors.append(f"frontmatter 第 {index + 1} 行无法解析：{line}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if not key:
            errors.append(f"frontmatter 第 {index + 1} 行缺少键名")
            continue
        meta[key] = value.strip()
    if end is None:
        return {}, text, ["frontmatter 缺少结束的 ---"]
    return meta, "\n".join(lines[end + 1 :]), errors


def split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def body_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    in_section = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_section:
                break
            in_section = stripped[3:].strip() == heading
            continue
        if in_section:
            output.append(line)
    return "\n".join(output)


def section_items(body: str, heading: str) -> list[str]:
    items = []
    for line in body_section(body, heading).splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            item = stripped[2:].strip()
            if item:
                items.append(item)
    return items


def body_without_section(body: str, heading: str) -> str:
    lines = body.splitlines()
    skipping = False
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == f"## {heading}":
            skipping = True
            continue
        if skipping and stripped.startswith("## "):
            skipping = False
        if not skipping:
            output.append(line)
    return "\n".join(output)


def profile_state(path: Path) -> str:
    text = read_text(path)
    if text is None:
        return "empty"
    _, body, _ = parse_frontmatter(text)
    body = body_without_section(body, "变更记录")
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("<!--"):
            continue
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if "：" in item:
                value = item.split("：", 1)[1].strip()
            elif ":" in item:
                value = item.split(":", 1)[1].strip()
            else:
                value = item
        else:
            value = stripped
        if value and value not in PLACEHOLDER_VALUES:
            return "filled"
    return "empty"


def templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def cmd_init(root: Path) -> int:
    ventures = root / "ventures"
    me_dir = ventures / "me"
    old_profile = ventures / "profile.md"
    new_profile = me_dir / "profile.md"
    migrate = old_profile.is_file() and not new_profile.exists()
    ventures.mkdir(parents=True, exist_ok=True)
    me_dir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "portfolio.md": ventures / "portfolio.md",
        "profile.md": new_profile,
        "self.md": me_dir / "self.md",
        "writing-style.md": me_dir / "writing-style.md",
    }
    today = date.today().isoformat()
    created: list[str] = []
    skipped: list[str] = []
    for template_name, target in mapping.items():
        if target.exists():
            skipped.append(target.relative_to(root).as_posix())
            continue
        template = templates_dir() / template_name
        text = read_text(template)
        if text is None:
            print(f"ERROR: 缺少模板 {template}", file=sys.stderr)
            return 1
        text = text.replace("{{DATE}}", today)
        if template_name == "profile.md" and migrate:
            old_text = read_text(old_profile) or ""
            _, old_body, _ = parse_frontmatter(old_text)
            text = text.rstrip() + "\n\n## 迁移内容\n\n" + old_body.strip() + "\n"
        write_atomic(target, text)
        created.append(target.relative_to(root).as_posix())
    for item in created:
        print(f"created: {item}")
    for item in skipped:
        print(f"skipped: {item}")
    if migrate:
        print("migrated: ventures/profile.md -> ventures/me/profile.md")
    return 0


def list_direction_dirs(ventures: Path) -> list[Path]:
    if not ventures.is_dir():
        return []
    return sorted(
        path
        for path in ventures.iterdir()
        if path.is_dir() and path.name != "me" and not path.name.startswith(".")
    )


def read_plan(direction: Path) -> tuple[dict[str, str], str, list[str]]:
    path = direction / "PLAN.md"
    text = read_text(path)
    if text is None:
        return {}, "", [f"{direction.name}/PLAN.md 缺失或无法读取"]
    return parse_frontmatter(text)


def read_portfolio(ventures: Path) -> tuple[dict[str, str], str, list[str]]:
    path = ventures / "portfolio.md"
    text = read_text(path)
    if text is None:
        return {}, "", ["缺少或无法读取 ventures/portfolio.md"]
    return parse_frontmatter(text)


def latest_open_note(direction: Path) -> tuple[Path, dict[str, str], str] | None:
    notes = direction / "notes"
    if not notes.is_dir():
        return None
    candidates = []
    for path in notes.glob("*.md"):
        text = read_text(path)
        if text is None:
            continue
        meta, body, _ = parse_frontmatter(text)
        if meta.get("status") == "open":
            candidates.append((meta.get("date", ""), path.name, path, meta, body))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    _, _, path, meta, body = candidates[0]
    return path, meta, body


def open_todos(direction: Path, limit: int = 3) -> list[str]:
    text = read_text(direction / "TODO.md")
    if not text:
        return []
    items: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ] "):
            items.append(stripped[6:].strip())
            if len(items) >= limit:
                break
    return items


def collect_context(ventures: Path) -> dict:
    warnings: list[str] = []
    meta, _body, portfolio_errors = read_portfolio(ventures)
    warnings.extend(portfolio_errors)
    main_slug = meta.get("main", "").strip()
    incubating_slugs = split_csv(meta.get("incubating", ""))
    main = None
    if main_slug:
        direction = ventures / main_slug
        if not direction.is_dir():
            warnings.append(f"主攻方向不存在：{main_slug}")
        else:
            plan, _plan_body, plan_errors = read_plan(direction)
            warnings.extend(f"{main_slug}: {error}" for error in plan_errors)
            main = {
                "slug": main_slug,
                "name": plan.get("name", main_slug),
                "stage": plan.get("stage", ""),
                "one_liner": plan.get("one_liner", ""),
                "next_action": plan.get("next_action", ""),
            }
    incubating = []
    for slug in incubating_slugs:
        direction = ventures / slug
        plan: dict[str, str] = {}
        if direction.is_dir():
            plan, _plan_body, plan_errors = read_plan(direction)
            warnings.extend(f"{slug}: {error}" for error in plan_errors)
        else:
            warnings.append(f"孵化方向不存在：{slug}")
        incubating.append(
            {
                "slug": slug,
                "name": plan.get("name", slug),
                "stage": plan.get("stage", ""),
            }
        )
    latest = None
    open_questions: list[str] = []
    todos: list[str] = []
    if main_slug and (ventures / main_slug).is_dir():
        found = latest_open_note(ventures / main_slug)
        if found:
            path, note_meta, note_body = found
            latest = {
                "path": path.relative_to(ventures.parent).as_posix(),
                "title": note_meta.get("title", ""),
                "date": note_meta.get("date", ""),
                "next_step": note_meta.get("next_step", ""),
            }
            open_questions = section_items(note_body, "未决问题")
        todos = open_todos(ventures / main_slug)
    me = {
        "profile": profile_state(ventures / "me" / "profile.md"),
        "self": profile_state(ventures / "me" / "self.md"),
        "writing_style": profile_state(ventures / "me" / "writing-style.md"),
    }
    empty_files = {
        "profile": "ventures/me/profile.md",
        "self": "ventures/me/self.md",
        "writing_style": "ventures/me/writing-style.md",
    }
    for key, label in (
        ("profile", "个人档案"),
        ("self", "星辰画像"),
        ("writing_style", "文风档案"),
    ):
        if me[key] == "empty":
            warnings.append(f"{label}为空：{empty_files[key]}")
    return {
        "main": main,
        "incubating": incubating,
        "latest_open_note": latest,
        "open_questions": open_questions,
        "todos": todos,
        "me": me,
        "warnings": warnings,
    }


def print_context(context: dict) -> None:
    main = context["main"]
    if main:
        print(f"主攻：{main['name']}（{main['stage']}）")
        if main["one_liner"]:
            print(f"一句话：{main['one_liner']}")
        print(f"下一步：{main['next_action'] or '未设置'}")
    else:
        print("主攻：未设置")
    latest = context["latest_open_note"]
    if latest:
        print(f"最近未结束：{latest['path']} — {latest['title']}")
        if context["open_questions"]:
            print("未决问题：")
            for question in context["open_questions"]:
                print(f"- {question}")
    else:
        print("最近未结束：无")
    if context["todos"]:
        print("待办：")
        for todo in context["todos"]:
            print(f"- {todo}")
    if context["incubating"]:
        names = "、".join(
            f"{item['name']}（{item['slug']}）" for item in context["incubating"]
        )
        print(f"孵化：{names}")
    me = context["me"]
    print(
        f"档案：profile {me['profile']}；self {me['self']}；"
        f"writing-style {me['writing_style']}"
    )
    if context["warnings"]:
        print("警告：")
        for warning in context["warnings"]:
            print(f"- {warning}")


def cmd_context(root: Path, as_json: bool) -> int:
    context = collect_context(root / "ventures")
    if as_json:
        print(json.dumps(context, ensure_ascii=False, indent=2))
    else:
        print_context(context)
    return 0


def cmd_validate(root: Path) -> int:
    print("validate 尚未实现", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(prog="advisor")
    parser.add_argument("--root", type=Path, default=None, help="项目根目录，默认当前目录")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="初始化工作区")
    context_parser = subparsers.add_parser("context", help="输出当前上下文")
    context_parser.add_argument("--json", action="store_true", help="输出 JSON")
    subparsers.add_parser("validate", help="校验工作区一致性")
    args = parser.parse_args(argv)
    base = (Path(root) if root is not None else args.root) or Path.cwd()
    base = base.resolve()
    if args.command == "init":
        return cmd_init(base)
    if args.command == "context":
        return cmd_context(base, args.json)
    if args.command == "validate":
        return cmd_validate(base)
    parser.error("未知命令")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

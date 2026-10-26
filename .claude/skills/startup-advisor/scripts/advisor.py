#!/usr/bin/env python3
"""startup-advisor 最小 CLI：init / context / validate。"""

from __future__ import annotations

import argparse
import json
import os
import re
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
    "（尚未确认的文风判断）",
    "(尚未确认的文风判断)",
}
STAGES = {"explore", "idea", "validating", "building", "operating", "paused", "archived"}
NOTE_MODES = {"coach", "exec", "mixed"}
NOTE_STATUSES = {"open", "closed"}
BRIEF_STATUSES = {"draft", "approved", "delivered"}
OUTPUT_STATUSES = {"draft", "review", "final"}
REQUIRED_PLAN_KEYS = (
    "name",
    "stage",
    "one_liner",
    "created",
    "updated",
    "next_action",
)
WINDOWS_ILLEGAL = set('<>:"/\\|?*')
RESERVED_NAMES = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


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


def name_errors(name: str, allow_comma: bool) -> list[str]:
    errors: list[str] = []
    if not name:
        return ["名称为空"]
    illegal = set(WINDOWS_ILLEGAL)
    if not allow_comma:
        illegal.add(",")
    found = sorted({char for char in name if char in illegal or ord(char) < 32})
    if found:
        errors.append("包含非法字符：" + "".join(found))
    stem = name.split(".")[0].upper()
    if stem in RESERVED_NAMES:
        errors.append("使用了 Windows 保留名")
    if name != name.strip(" ."):
        errors.append("首尾包含空白或点")
    return errors


def validate_note(
    direction: Path, path: Path, errors: list[str], warnings: list[str]
) -> None:
    rel = path.relative_to(direction).as_posix()
    text = read_text(path)
    if text is None:
        errors.append(f"{direction.name}/{rel}: 无法读取或不是 UTF-8")
        return
    meta, _body, fm_errors = parse_frontmatter(text)
    for error in fm_errors:
        errors.append(f"{direction.name}/{rel}: {error}")
    for key in ("title", "date", "direction", "mode", "status"):
        if key not in meta:
            errors.append(f"{direction.name}/{rel}: 缺少 frontmatter: {key}")
    for key in ("title", "date", "direction"):
        if key in meta and not meta[key].strip():
            errors.append(f"{direction.name}/{rel}: {key} 为空")
    if meta.get("direction") and meta["direction"] != direction.name:
        errors.append(
            f"{direction.name}/{rel}: direction={meta['direction']} 与目录不一致"
        )
    if meta.get("mode") and meta["mode"] not in NOTE_MODES:
        errors.append(f"{direction.name}/{rel}: 非法 mode: {meta['mode']}")
    if meta.get("status") and meta["status"] not in NOTE_STATUSES:
        errors.append(f"{direction.name}/{rel}: 非法 status: {meta['status']}")
    if meta.get("status") == "open" and not meta.get("next_step", "").strip():
        errors.append(f"{direction.name}/{rel}: open 纪要缺少 next_step")
    if not re.match(r"^\d{4}-\d{2}-\d{2}-", path.name):
        warnings.append(f"{direction.name}/{rel}: 文件名不是 YYYY-MM-DD- 开头")
    for error in name_errors(path.name, allow_comma=True):
        errors.append(f"{direction.name}/{rel}: 文件名 {error}")


def validate_brief(
    direction: Path, path: Path, errors: list[str], warnings: list[str]
) -> None:
    rel = path.relative_to(direction).as_posix()
    text = read_text(path)
    if text is None:
        errors.append(f"{direction.name}/{rel}: 无法读取或不是 UTF-8")
        return
    meta, body, fm_errors = parse_frontmatter(text)
    for error in fm_errors:
        errors.append(f"{direction.name}/{rel}: {error}")
    for key in ("title", "date", "direction", "output_type", "status"):
        if key not in meta:
            errors.append(f"{direction.name}/{rel}: 缺少 frontmatter: {key}")
    if meta.get("direction") and meta["direction"] != direction.name:
        errors.append(
            f"{direction.name}/{rel}: direction={meta['direction']} 与目录不一致"
        )
    if meta.get("status") and meta["status"] not in BRIEF_STATUSES:
        errors.append(f"{direction.name}/{rel}: 非法 status: {meta['status']}")
    for ref in re.findall(r"`([^`]+)`", body_section(body, "参考材料")):
        if ref.endswith(".md") and "/" in ref and not (direction / ref).is_file():
            errors.append(f"{direction.name}/{rel}: 参考材料不存在：{ref}")
    for error in name_errors(path.name, allow_comma=True):
        errors.append(f"{direction.name}/{rel}: 文件名 {error}")


def validate_output(
    direction: Path, path: Path, errors: list[str], warnings: list[str]
) -> None:
    rel = path.relative_to(direction).as_posix()
    text = read_text(path)
    if text is None:
        errors.append(f"{direction.name}/{rel}: 无法读取或不是 UTF-8")
        return
    meta, _body, fm_errors = parse_frontmatter(text)
    for error in fm_errors:
        errors.append(f"{direction.name}/{rel}: {error}")
    for key in ("title", "date", "direction", "brief", "version", "status", "author"):
        if key not in meta:
            errors.append(f"{direction.name}/{rel}: 缺少 frontmatter: {key}")
    if meta.get("direction") and meta["direction"] != direction.name:
        errors.append(
            f"{direction.name}/{rel}: direction={meta['direction']} 与目录不一致"
        )
    if meta.get("status") and meta["status"] not in OUTPUT_STATUSES:
        errors.append(f"{direction.name}/{rel}: 非法 status: {meta['status']}")
    version = meta.get("version", "")
    if not version.isdigit() or int(version) < 1:
        errors.append(f"{direction.name}/{rel}: version 必须是 >=1 的整数")
    brief = meta.get("brief", "").strip()
    if not brief:
        errors.append(f"{direction.name}/{rel}: 缺少 brief 引用")
    elif not (direction / brief).is_file():
        errors.append(f"{direction.name}/{rel}: brief 不存在：{brief}")
    for error in name_errors(path.name, allow_comma=True):
        errors.append(f"{direction.name}/{rel}: 文件名 {error}")


def validate_workspace(ventures: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not ventures.is_dir():
        return [f"工作区不存在：{ventures}"], warnings
    required = (
        "portfolio.md",
        "me/profile.md",
        "me/self.md",
        "me/writing-style.md",
    )
    for rel in required:
        path = ventures / rel
        if not path.is_file():
            errors.append(f"缺少必填文件：ventures/{rel}")
        elif read_text(path) is None:
            errors.append(f"无法读取或不是 UTF-8：ventures/{rel}")
    if (ventures / ".state.json").exists():
        warnings.append("发现旧 ventures/.state.json；新设计已不再读取，可手工删除")
    portfolio_path = ventures / "portfolio.md"
    meta: dict[str, str] = {}
    if portfolio_path.is_file():
        text = read_text(portfolio_path)
        if text is None:
            errors.append("无法读取或不是 UTF-8：ventures/portfolio.md")
        else:
            meta, _body, fm_errors = parse_frontmatter(text)
            for error in fm_errors:
                errors.append(f"portfolio.md: {error}")
            if "updated" not in meta:
                errors.append("portfolio.md 缺少 frontmatter: updated")
    main = meta.get("main", "").strip()
    incubating = split_csv(meta.get("incubating", ""))
    archived = split_csv(meta.get("archived", ""))
    dirs = list_direction_dirs(ventures)
    dir_names = {path.name for path in dirs}

    def check_registered(label: str, items: list[str]) -> None:
        seen: set[str] = set()
        for item in items:
            if item in seen:
                errors.append(f"{label} 重复登记：{item}")
            seen.add(item)
            if item not in dir_names:
                errors.append(f"{label} 指向不存在的方向：{item}")

    check_registered("incubating", incubating)
    check_registered("archived", archived)
    if main:
        if main not in dir_names:
            errors.append(f"main 指向不存在的方向：{main}")
        if main in incubating:
            errors.append(f"main 与 incubating 重复：{main}")
        if main in archived:
            errors.append(f"main 与 archived 重复：{main}")
    registered = set(incubating) | set(archived) | ({main} if main else set())
    for direction in dirs:
        slug = direction.name
        if slug not in registered:
            errors.append(f"方向未在 portfolio.md 登记：{slug}")
        for error in name_errors(slug, allow_comma=False):
            errors.append(f"方向目录名 {slug}: {error}")
        if len(slug) > 48:
            errors.append(f"方向目录名 {slug}: 超过 48 字符")
        plan_path = direction / "PLAN.md"
        if not plan_path.is_file():
            errors.append(f"{slug}: 缺少 PLAN.md")
            continue
        plan_text = read_text(plan_path)
        if plan_text is None:
            errors.append(f"{slug}/PLAN.md: 无法读取或不是 UTF-8")
            continue
        plan, _plan_body, fm_errors = parse_frontmatter(plan_text)
        for error in fm_errors:
            errors.append(f"{slug}/PLAN.md: {error}")
        for key in REQUIRED_PLAN_KEYS:
            if key not in plan:
                errors.append(f"{slug}/PLAN.md: 缺少 frontmatter: {key}")
        if not plan.get("name", "").strip():
            errors.append(f"{slug}/PLAN.md: name 为空")
        stage = plan.get("stage", "").strip()
        if stage not in STAGES:
            errors.append(f"{slug}/PLAN.md: 非法 stage: {stage}")
        if slug in archived and stage != "archived":
            errors.append(
                f"{slug}: 已登记为归档，但 PLAN.md stage 不是 archived"
            )
        notes_dir = direction / "notes"
        if notes_dir.is_dir():
            for note_path in sorted(notes_dir.glob("*.md")):
                validate_note(direction, note_path, errors, warnings)
        briefs_dir = direction / "briefs"
        if briefs_dir.is_dir():
            for brief_path in sorted(briefs_dir.glob("*.md")):
                validate_brief(direction, brief_path, errors, warnings)
        outputs_dir = direction / "outputs"
        if outputs_dir.is_dir():
            for output_path in sorted(outputs_dir.glob("*.md")):
                validate_output(direction, output_path, errors, warnings)
    return errors, warnings


def cmd_context(root: Path, as_json: bool) -> int:
    context = collect_context(root / "ventures")
    if as_json:
        print(json.dumps(context, ensure_ascii=False, indent=2))
    else:
        print_context(context)
    return 0


def cmd_validate(root: Path) -> int:
    errors, warnings = validate_workspace(root / "ventures")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"校验失败：{len(errors)} 个错误，{len(warnings)} 个警告")
        return 1
    print(f"校验通过：0 个错误，{len(warnings)} 个警告")
    return 0


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

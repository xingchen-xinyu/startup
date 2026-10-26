#!/usr/bin/env python3
"""startup-advisor 最小 CLI：init / context / validate。"""

from __future__ import annotations

import argparse
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


def cmd_context(root: Path, as_json: bool) -> int:
    print("context 尚未实现", file=sys.stderr)
    return 1


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

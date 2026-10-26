# 创业顾问 Skill 重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有 startup-advisor 重构为“主对话顾问 + 按需执行助手 subagent”的双角色技能，用三层记忆维护星辰的个人认知、创业组合和每个方向的活方案。

**Architecture:** 顾问由 `SKILL.md` 定义，始终留在主对话；执行助手由 `.claude/agents/execution-assistant.md` 定义，按 brief 产出正式文档。数据分创始人层 `ventures/me/`、组合层 `ventures/portfolio.md`、方向层 `ventures/<方向>/`。CLI 只保留 `init`、`context`、`validate` 三条命令，其余内容由模型按模板编辑。

**Tech Stack:** Python 3 标准库（argparse、json、pathlib、unittest）、Markdown、Claude Code skill + custom agent。

## Global Constraints

- 工作分支：`feature/startup-advisor`；不要提交到 `main`。
- Python 3 标准库，不引入第三方依赖。
- 所有用户可见输出、文档、测试断言使用中文。
- 文件统一 UTF-8、`\n` 换行；Windows 路径用 `pathlib`。
- CLI 只有 `init`、`context [--json]`、`validate` 三条命令；不要新增命令。
- `ventures/` 是私人数据，已被 `.gitignore` 忽略；不要提交。
- 不要修改、暂存或还原 `.gitignore` 现有的未提交修改。
- 测试命令：`python -m unittest discover -s .claude/skills/startup-advisor/tests -v`。
- 每次提交只包含本任务的文件；提交信息用中文，并带 `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。
- 顾问不写成 subagent；执行助手只通过 brief 接收任务。
- 正式方案和对外文案只能由执行助手写入 `outputs/`；顾问只写 brief 和验收意见。
- 不代写代码、不做外部调研、不做视觉设计。

## File Structure

| 文件 | 职责 |
|---|---|
| `.claude/skills/startup-advisor/SKILL.md` | 顾问身份、双档、启动、记录、收尾、派发与验收规则 |
| `.claude/skills/startup-advisor/references/coaching-playbook.md` | 访谈、提问、阶段剧本、框架、失败模式 |
| `.claude/skills/startup-advisor/references/execution-playbook.md` | brief 写法、产出模板、文风适配、验收清单 |
| `.claude/skills/startup-advisor/references/memory-model.md` | 数据模型、更新规则、读写策略、命名规则 |
| `.claude/skills/startup-advisor/templates/portfolio.md` | 组合层模板 |
| `.claude/skills/startup-advisor/templates/profile.md` | 个人事实模板 |
| `.claude/skills/startup-advisor/templates/self.md` | 个人画像模板 |
| `.claude/skills/startup-advisor/templates/writing-style.md` | 文风档案模板 |
| `.claude/skills/startup-advisor/templates/PLAN.md` | 方向活方案模板 |
| `.claude/skills/startup-advisor/templates/note.md` | 讨论纪要模板 |
| `.claude/skills/startup-advisor/templates/brief.md` | 工作简报模板 |
| `.claude/skills/startup-advisor/scripts/advisor.py` | 最小 CLI：init / context / validate |
| `.claude/skills/startup-advisor/tests/helpers.py` | 测试辅助：临时工作区、运行 CLI |
| `.claude/skills/startup-advisor/tests/test_cli.py` | CLI 单元测试 |
| `.claude/skills/startup-advisor/tests/test_docs.py` | 技能文档一致性测试 |
| `.claude/agents/execution-assistant.md` | 执行助手 subagent 定义 |

---

### Task 1: 工作区模板与 `init`

**Files:**
- Delete: `.claude/skills/startup-advisor/scripts/checks.py`
- Delete: `.claude/skills/startup-advisor/scripts/entities.py`
- Delete: `.claude/skills/startup-advisor/scripts/notes.py`
- Delete: `.claude/skills/startup-advisor/scripts/todos.py`
- Delete: `.claude/skills/startup-advisor/scripts/ws.py`
- Delete: `.claude/skills/startup-advisor/scripts/advisor.py`
- Delete: `.claude/skills/startup-advisor/tests/helpers.py`
- Delete: `.claude/skills/startup-advisor/tests/test_checks.py`
- Delete: `.claude/skills/startup-advisor/tests/test_cli.py`
- Delete: `.claude/skills/startup-advisor/tests/test_entities.py`
- Delete: `.claude/skills/startup-advisor/tests/test_notes.py`
- Delete: `.claude/skills/startup-advisor/tests/test_skill_docs.py`
- Delete: `.claude/skills/startup-advisor/tests/test_todos.py`
- Delete: `.claude/skills/startup-advisor/tests/test_ws.py`
- Delete: `.claude/skills/startup-advisor/templates/profile.md`
- Create: `.claude/skills/startup-advisor/scripts/advisor.py`
- Create: `.claude/skills/startup-advisor/tests/helpers.py`
- Create: `.claude/skills/startup-advisor/tests/test_cli.py`
- Create: `.claude/skills/startup-advisor/templates/portfolio.md`
- Create: `.claude/skills/startup-advisor/templates/profile.md`
- Create: `.claude/skills/startup-advisor/templates/self.md`
- Create: `.claude/skills/startup-advisor/templates/writing-style.md`
- Create: `.claude/skills/startup-advisor/templates/PLAN.md`
- Create: `.claude/skills/startup-advisor/templates/note.md`
- Create: `.claude/skills/startup-advisor/templates/brief.md`

**Interfaces:**
- Consumes: none.
- Produces:
  - `advisor.main(argv: list[str] | None = None, root: Path | None = None) -> int`
  - `advisor.cmd_init(root: Path) -> int`
  - `advisor.cmd_context(root: Path, as_json: bool) -> int`（Task 1 为占位，Task 2 实现）
  - `advisor.cmd_validate(root: Path) -> int`（Task 1 为占位，Task 3 实现）
  - `advisor.read_text(path: Path) -> str | None`
  - `advisor.write_atomic(path: Path, text: str) -> None`
  - `advisor.parse_frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]`
  - `advisor.split_csv(value: str) -> list[str]`
  - `advisor.body_section(body: str, heading: str) -> str`
  - `advisor.section_items(body: str, heading: str) -> list[str]`
  - `advisor.body_without_section(body: str, heading: str) -> str`
  - `advisor.profile_state(path: Path) -> str`（返回 `"filled"` 或 `"empty"`）
  - `helpers.run_cli(root: Path, *args: str) -> tuple[int, str, str]`
  - `helpers.write(path: Path, text: str) -> None`
  - `helpers.init_workspace(root: Path) -> Path`

- [ ] **Step 1: 删除旧实现文件**

```bash
git rm .claude/skills/startup-advisor/scripts/checks.py
git rm .claude/skills/startup-advisor/scripts/entities.py
git rm .claude/skills/startup-advisor/scripts/notes.py
git rm .claude/skills/startup-advisor/scripts/todos.py
git rm .claude/skills/startup-advisor/scripts/ws.py
git rm .claude/skills/startup-advisor/scripts/advisor.py
git rm .claude/skills/startup-advisor/tests/helpers.py
git rm .claude/skills/startup-advisor/tests/test_checks.py
git rm .claude/skills/startup-advisor/tests/test_cli.py
git rm .claude/skills/startup-advisor/tests/test_entities.py
git rm .claude/skills/startup-advisor/tests/test_notes.py
git rm .claude/skills/startup-advisor/tests/test_skill_docs.py
git rm .claude/skills/startup-advisor/tests/test_todos.py
git rm .claude/skills/startup-advisor/tests/test_ws.py
git rm .claude/skills/startup-advisor/templates/profile.md
```

- [ ] **Step 2: 创建七个模板**

`.claude/skills/startup-advisor/templates/portfolio.md`：

```markdown
---
main:
incubating:
archived:
updated: {{DATE}}
---

# 创业组合

## 当前主攻
- 方向：
- 为什么是它：
- 当前阶段：
- 下一个里程碑：

## 孵化池

## 已归档
```

`.claude/skills/startup-advisor/templates/profile.md`：

```markdown
---
updated: {{DATE}}
---

# 个人档案

## 基本信息
- 称呼：
- 所在地/时区：

## 背景与能力
- 职业经历：
- 专业技能：
- 擅长：
- 不擅长：

## 资源与约束
- 可投入时间：
- 可投入资金：
- 人脉/渠道/行业资源：

## 创业偏好
- 感兴趣的方向：
- 偏好的商业模式：
- 风险承受度：
- 期望角色（全职创始人/合伙人/副业）：

## 变更记录
- {{DATE}} 创建档案
```

`.claude/skills/startup-advisor/templates/self.md`：

```markdown
---
updated: {{DATE}}
---

# 星辰画像

## 性格与决策风格
- （待确认）

## 能量来源与压力反应
- （待确认）

## 优势
- （待确认）

## 短板与盲区
- （待确认）

## 核心价值观
- （待确认）

## 为什么创业
- （待确认）

## 长期愿景
- （待确认）

## 未来 12 个月目标
- （待确认）

## 协作偏好
- 希望顾问怎么帮：
- 不希望怎么做：

## 待确认
- （尚未验证的判断）
```

`.claude/skills/startup-advisor/templates/writing-style.md`：

```markdown
---
updated: {{DATE}}
---

# 星辰文风档案

## 语气与人称
- （待确认）

## 结构偏好
- （待确认）

## 用词
- 偏好词：
- 禁用词：
- 口头禅：
- 英文术语习惯：

## 平台差异
- 对内方案：
- 公众号：
- 小红书：
- 邮件：
- 落地页：

## 代表性样本
<!-- 粘贴星辰自己写过的 3–5 段文字 -->

## 反馈日志

## 待确认
- （尚未确认的文风判断）
```

`.claude/skills/startup-advisor/templates/PLAN.md`：

```markdown
---
name: {{NAME}}
stage: idea
one_liner: {{ONE_LINER}}
created: {{DATE}}
updated: {{DATE}}
next_action:
---

# 方向：{{NAME}}

## 一句话

{{ONE_LINER}}

## 愿景

## 目标用户与痛点

## 价值主张

## 解决方案

## 关键假设与证据

| 假设 | 状态 | 证据 | 来源 | 下一步 |
|---|---|---|---|---|
|  | 待验证 |  |  |  |

## 当前阶段与目标

## 主要风险

## 下一步

## 方向起源
```

`.claude/skills/startup-advisor/templates/note.md`：

```markdown
---
title: {{TITLE}}
date: {{DATE}}
direction: {{DIRECTION}}
mode: mixed
status: open
next_step:
---

# 讨论：{{TITLE}}

## 议题

## 关键原话

## 讨论要点

## 结论

## 未决问题

## 决定

## 行动项

## 下一步
```

`.claude/skills/startup-advisor/templates/brief.md`：

```markdown
---
title: {{TITLE}}
date: {{DATE}}
direction: {{DIRECTION}}
output_type: {{OUTPUT_TYPE}}
status: draft
due:
---

# 工作简报：{{TITLE}}

## 目标

## 读者与渠道

## 交付物

## 必须包含

## 不能出现

## 文风与格式

## 参考材料
- `PLAN.md`

## 验收标准

## 截止时间
```

- [ ] **Step 3: 写失败的 init 测试**

`.claude/skills/startup-advisor/tests/helpers.py`：

```python
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import advisor  # noqa: E402


def run_cli(root: Path, *args: str) -> tuple[int, str, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = advisor.main(["--root", str(root), *args])
    return code, stdout.getvalue(), stderr.getvalue()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def init_workspace(root: Path) -> Path:
    code, stdout, stderr = run_cli(root, "init")
    if code != 0:
        raise AssertionError(stdout + stderr)
    return root / "ventures"
```

`.claude/skills/startup-advisor/tests/test_cli.py`：

```python
import tempfile
import unittest
from pathlib import Path

from helpers import run_cli, write


class InitTests(unittest.TestCase):
    def test_init_creates_workspace_and_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            ventures = root / "ventures"
            for rel in (
                "portfolio.md",
                "me/profile.md",
                "me/self.md",
                "me/writing-style.md",
            ):
                self.assertTrue((ventures / rel).is_file(), rel)
            self.assertIn("created: ventures/portfolio.md", out)

    def test_init_is_idempotent_and_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(run_cli(root, "init")[0], 0)
            profile = root / "ventures/me/profile.md"
            profile.write_text(
                profile.read_text(encoding="utf-8") + "\n- 称呼：星辰\n",
                encoding="utf-8",
                newline="\n",
            )
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            self.assertIn("称呼：星辰", profile.read_text(encoding="utf-8"))
            self.assertIn("skipped: ventures/me/profile.md", out)

    def test_init_migrates_legacy_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "ventures/profile.md"
            write(legacy, "---\nupdated: 2026-10-20\n---\n\n## 基本信息\n- 称呼：星辰\n")
            code, out, err = run_cli(root, "init")
            self.assertEqual(code, 0, out + err)
            new_profile = root / "ventures/me/profile.md"
            self.assertTrue(new_profile.is_file())
            self.assertIn("称呼：星辰", new_profile.read_text(encoding="utf-8"))
            self.assertTrue(legacy.is_file())
            self.assertIn("migrated:", out)
```

- [ ] **Step 4: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: FAIL / ERROR，提示 `ModuleNotFoundError: No module named 'advisor'`。

- [ ] **Step 5: 写最小 `advisor.py`（init 版本）**

`.claude/skills/startup-advisor/scripts/advisor.py`：

```python
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
        return path.read_text(encoding="utf-8")
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
```

- [ ] **Step 6: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 3 个测试全部 PASS。

- [ ] **Step 7: 提交**

```bash
git add -A .claude/skills/startup-advisor
git commit -m "feat: 重建创业顾问工作区与 init 命令" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `context` 命令

**Files:**
- Modify: `.claude/skills/startup-advisor/scripts/advisor.py`
- Modify: `.claude/skills/startup-advisor/tests/test_cli.py`

**Interfaces:**
- Consumes: Task 1 的 `read_text`、`parse_frontmatter`、`split_csv`、`section_items`、`profile_state`、`main`。
- Produces:
  - `advisor.list_direction_dirs(ventures: Path) -> list[Path]`
  - `advisor.read_plan(direction: Path) -> tuple[dict[str, str], str, list[str]]`
  - `advisor.read_portfolio(ventures: Path) -> tuple[dict[str, str], str, list[str]]`
  - `advisor.latest_open_note(direction: Path) -> tuple[Path, dict[str, str], str] | None`
  - `advisor.open_todos(direction: Path, limit: int = 3) -> list[str]`
  - `advisor.collect_context(ventures: Path) -> dict`
  - `advisor.print_context(context: dict) -> None`
  - `advisor.cmd_context(root: Path, as_json: bool) -> int`

- [ ] **Step 1: 追加失败的 context 测试**

在 `test_cli.py` 顶部补充 `import json`，并把 `from helpers import run_cli, write` 改为 `from helpers import init_workspace, run_cli, write`。然后在文件末尾追加：

```python
def make_plan(name="AI 知识库", stage="validating"):
    return (
        "---\n"
        f"name: {name}\n"
        f"stage: {stage}\n"
        "one_liner: 帮小团队做内部知识库\n"
        "created: 2026-10-20\n"
        "updated: 2026-10-26\n"
        "next_action: 访谈 3 家团队\n"
        "---\n\n"
        f"# 方向：{name}\n"
    )


class ContextTests(unittest.TestCase):
    def test_context_on_empty_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            code, out, err = run_cli(root, "context")
            self.assertEqual(code, 0, out + err)
            self.assertIn("主攻：未设置", out)
            self.assertIn("最近未结束：无", out)
            self.assertIn("警告：", out)

    def test_context_json_populated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(ventures / "pet-social/PLAN.md", make_plan("宠物社交", "idea"))
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating: pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n\n# 创业组合\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step: 访谈 3 家\n---\n\n"
                "# 讨论：定价\n\n## 未决问题\n- 企业版定价锚点是多少？\n- 谁做付费决策？\n",
            )
            write(ventures / "ai-kb/TODO.md", "- [ ] 访谈 3 家\n- [ ] 整理竞品\n")
            write(
                ventures / "me/self.md",
                "---\nupdated: 2026-10-26\n---\n\n# 星辰画像\n\n"
                "## 性格与决策风格\n- 偏好小步验证\n",
            )
            code, out, err = run_cli(root, "context", "--json")
            self.assertEqual(code, 0, out + err)
            data = json.loads(out)
            self.assertEqual(data["main"]["slug"], "ai-kb")
            self.assertEqual(data["main"]["name"], "AI 知识库")
            self.assertEqual(data["main"]["stage"], "validating")
            self.assertEqual(
                data["latest_open_note"]["path"],
                "ventures/ai-kb/notes/2026-10-26-定价.md",
            )
            self.assertEqual(
                data["open_questions"],
                ["企业版定价锚点是多少？", "谁做付费决策？"],
            )
            self.assertEqual(data["todos"], ["访谈 3 家", "整理竞品"])
            self.assertEqual(data["me"]["self"], "filled")
            self.assertEqual(data["me"]["profile"], "empty")
            self.assertEqual(len(data["incubating"]), 1)
            self.assertEqual(data["incubating"][0]["name"], "宠物社交")

    def test_context_ignores_closed_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\nupdated: 2026-10-26\n---\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-25-旧.md",
                "---\ntitle: 旧\ndate: 2026-10-25\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step: 继续\n---\n\n"
                "## 未决问题\n- 旧问题\n",
            )
            write(
                ventures / "ai-kb/notes/2026-10-26-新.md",
                "---\ntitle: 新\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: closed\nnext_step:\n---\n\n"
                "## 未决问题\n- 新问题\n",
            )
            code, out, err = run_cli(root, "context", "--json")
            self.assertEqual(code, 0, out + err)
            data = json.loads(out)
            self.assertEqual(data["latest_open_note"]["title"], "旧")
            self.assertEqual(data["open_questions"], ["旧问题"])

    def test_context_human_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = init_workspace(root)
            write(ventures / "ai-kb/PLAN.md", make_plan())
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\nupdated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "context")
            self.assertEqual(code, 0, out + err)
            self.assertIn("主攻：AI 知识库（validating）", out)
            self.assertIn("下一步：访谈 3 家团队", out)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 4 个 context 测试 FAIL，提示 `AssertionError: 1 != 0`（`main` 仍返回占位错误）。

- [ ] **Step 3: 实现 context**

在 `advisor.py` 顶部加入 `import json`。

在 `cmd_init` 之后、`main` 之前加入：

```python
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
```

在 `print_context` 之后加入 `cmd_context`，并用它替换 Task 1 的占位定义：

```python
def cmd_context(root: Path, as_json: bool) -> int:
    context = collect_context(root / "ventures")
    if as_json:
        print(json.dumps(context, ensure_ascii=False, indent=2))
    else:
        print_context(context)
    return 0
```

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 7 个测试全部 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/advisor.py .claude/skills/startup-advisor/tests/test_cli.py
git commit -m "feat: 添加 context 上下文摘要命令" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: `validate` 命令

**Files:**
- Modify: `.claude/skills/startup-advisor/scripts/advisor.py`
- Modify: `.claude/skills/startup-advisor/tests/test_cli.py`

**Interfaces:**
- Consumes: Task 1、Task 2 的解析与读取函数。
- Produces:
  - `advisor.name_errors(name: str, allow_comma: bool) -> list[str]`
  - `advisor.validate_note(direction: Path, path: Path, errors: list[str], warnings: list[str]) -> None`
  - `advisor.validate_brief(direction: Path, path: Path, errors: list[str], warnings: list[str]) -> None`
  - `advisor.validate_output(direction: Path, path: Path, errors: list[str], warnings: list[str]) -> None`
  - `advisor.validate_workspace(ventures: Path) -> tuple[list[str], list[str]]`
  - `advisor.cmd_validate(root: Path) -> int`

- [ ] **Step 1: 追加失败的 validate 测试**

在 `.claude/skills/startup-advisor/tests/test_cli.py` 末尾追加：

```python
def valid_workspace(root: Path) -> Path:
    ventures = init_workspace(root)
    write(
        ventures / "portfolio.md",
        "---\nmain: ai-kb\nincubating: pet-social\narchived:\n"
        "updated: 2026-10-26\n---\n\n# 创业组合\n",
    )
    write(
        ventures / "ai-kb/PLAN.md",
        "---\nname: AI 知识库\nstage: validating\n"
        "one_liner: 帮小团队做内部知识库\n"
        "created: 2026-10-20\nupdated: 2026-10-26\n"
        "next_action: 访谈 3 家团队\n---\n",
    )
    write(
        ventures / "pet-social/PLAN.md",
        "---\nname: 宠物社交\nstage: idea\none_liner: 宠物主人社交\n"
        "created: 2026-10-20\nupdated: 2026-10-26\n"
        "next_action: 访谈 5 位宠物主\n---\n",
    )
    write(
        ventures / "ai-kb/notes/2026-10-26-定价.md",
        "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
        "mode: coach\nstatus: open\nnext_step: 访谈 3 家\n---\n\n"
        "## 未决问题\n- 定价锚点？\n",
    )
    write(
        ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
        "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
        "output_type: launch-copy\nstatus: approved\ndue: 2026-10-28\n---\n\n"
        "## 参考材料\n- `PLAN.md`\n",
    )
    write(
        ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
        "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
        "brief: briefs/2026-10-26-发布文案.md\nversion: 1\nstatus: draft\n"
        "author: execution-assistant\n---\n\n# 发布文案\n",
    )
    write(ventures / "ai-kb/TODO.md", "- [ ] 访谈 3 家\n")
    return ventures


class ValidateTests(unittest.TestCase):
    def test_valid_workspace_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid_workspace(root)
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)
            self.assertIn("校验通过", out)

    def test_optional_files_may_be_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            init_workspace(root)
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)

    def test_main_points_to_missing_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: missing\nincubating: pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("main 指向不存在的方向：missing", out)

    def test_unregistered_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating:\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("方向未在 portfolio.md 登记：pet-social", out)

    def test_duplicate_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "portfolio.md",
                "---\nmain: ai-kb\nincubating: ai-kb, pet-social\narchived:\n"
                "updated: 2026-10-26\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("main 与 incubating 重复：ai-kb", out)

    def test_invalid_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/PLAN.md",
                "---\nname: AI 知识库\nstage: foo\none_liner: x\n"
                "created: 2026-10-20\nupdated: 2026-10-26\nnext_action: x\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("非法 stage: foo", out)

    def test_note_direction_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: other\n"
                "mode: coach\nstatus: open\nnext_step: 继续\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("direction=other 与目录不一致", out)

    def test_open_note_missing_next_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/notes/2026-10-26-定价.md",
                "---\ntitle: 定价\ndate: 2026-10-26\ndirection: ai-kb\n"
                "mode: coach\nstatus: open\nnext_step:\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("open 纪要缺少 next_step", out)

    def test_brief_invalid_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "output_type: launch-copy\nstatus: unknown\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("非法 status: unknown", out)

    def test_brief_missing_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/briefs/2026-10-26-发布文案.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "output_type: launch-copy\nstatus: approved\n---\n\n"
                "## 参考材料\n- `notes/missing.md`\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("参考材料不存在：notes/missing.md", out)

    def test_output_missing_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "brief: briefs/missing.md\nversion: 1\nstatus: draft\n"
                "author: execution-assistant\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("brief 不存在：briefs/missing.md", out)

    def test_output_bad_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(
                ventures / "ai-kb/outputs/2026-10-26-发布文案-v1.md",
                "---\ntitle: 发布文案\ndate: 2026-10-26\ndirection: ai-kb\n"
                "brief: briefs/2026-10-26-发布文案.md\nversion: 0\n"
                "status: draft\nauthor: execution-assistant\n---\n",
            )
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("version 必须是 >=1 的整数", out)

    def test_missing_required_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            (ventures / "me/profile.md").unlink()
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 1, out + err)
            self.assertIn("缺少必填文件：ventures/me/profile.md", out)

    def test_legacy_state_file_is_warning_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ventures = valid_workspace(root)
            write(ventures / ".state.json", "{}\n")
            code, out, err = run_cli(root, "validate")
            self.assertEqual(code, 0, out + err)
            self.assertIn("WARNING: 发现旧 ventures/.state.json", out)

    def test_direction_name_rejects_comma(self):
        from helpers import advisor

        self.assertTrue(advisor.name_errors("bad,name", allow_comma=False))
        self.assertFalse(advisor.name_errors("bad,name", allow_comma=True))
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: ValidateTests 全部 FAIL，提示 `AttributeError` 或 `AssertionError: 1 != 0`。

- [ ] **Step 3: 实现 validate**

在 `advisor.py` 顶部加入 `import re`，并在 `PLACEHOLDER_VALUES` 下方加入常量：

```python
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
```

在 `print_context` 之后加入 `name_errors`、`validate_note`、`validate_brief`、`validate_output`、`validate_workspace`；用代码块中的 `cmd_validate` 替换 Task 1 的占位定义：

```python
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
```

用上面代码块中的 `cmd_validate` 替换 Task 1 的占位定义。`main` 已经在 Task 1 中改为调用 `cmd_validate(base)`，不需要再改。

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/advisor.py .claude/skills/startup-advisor/tests/test_cli.py
git commit -m "feat: 添加 validate 一致性校验命令" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: `SKILL.md` 顾问协议

**Files:**
- Create: `.claude/skills/startup-advisor/SKILL.md`
- Create: `.claude/skills/startup-advisor/tests/test_docs.py`

**Interfaces:**
- Consumes: Task 1 的模板和 Task 2/3 的 CLI 命令。
- Produces: 顾问身份、双档规则、启动、记录、收尾、派发与验收协议。

- [ ] **Step 1: 写失败的文档测试**

`.claude/skills/startup-advisor/tests/test_docs.py`：

```python
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


class SkillDocTests(unittest.TestCase):
    def test_skill_protocol_mentions_required_behaviors(self):
        text = (BASE / "SKILL.md").read_text(encoding="utf-8")
        for token in (
            "顾问档",
            "参谋档",
            "brief",
            "execution-assistant",
            "init",
            "context",
            "validate",
            "按需访谈",
            "收尾",
        ):
            self.assertIn(token, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: `FileNotFoundError`，找不到 `SKILL.md`。

- [ ] **Step 3: 写 `SKILL.md`**

`.claude/skills/startup-advisor/SKILL.md`：

````markdown
---
name: startup-advisor
description: 作为星辰的长期创业顾问，通过对话梳理创业方向、维护活方案与个人认知，并在需要时派发执行助手产出正式方案与文案。当用户提到创业想法、方向、验证、方案、个人访谈，或调用 /startup-advisor 时使用。
---

# 创业顾问

你是星辰的长期创业顾问。你的职责不是给漂亮建议，而是帮星辰想清楚、守住主线，并在该动手时组织产出。

## 身份与职责

- 通过提问和访谈理解星辰的想法、背景、性格、价值观、优劣势和愿景。
- 帮星辰把模糊方向收敛成可验证的假设和可执行方案。
- 维护每个方向的 `PLAN.md`、讨论纪要、决策和下一步。
- 判断阶段，决定用顾问档还是参谋档。
- 基于星辰的性格、优劣势、资源约束和风险偏好调整建议，不套用通用模板。
- 需要正式产出时，写清楚 brief，派发执行助手，并验收结果。
- 维护记忆：稳定信息写进正确文件，不把猜测写成事实。

## 气质

- 中文交流，直接、具体、不迎合。
- 先复述理解，再给判断；一次只问一个最关键的问题。
- 关键节点给 2–3 条路径或框架对比，并说明推荐与理由。
- 区分事实、假设和观点；不确定就标“待确认”。
- 建议结合 `ventures/me/self.md` 中星辰的性格、优劣势、资源和风险偏好，不套通用模板。

## 边界

- 不替星辰做重大决定；给选项、权衡和推荐，由星辰拍板。
- 不编造信息、数据或案例。
- 不越权写正式交付物；正式方案和对外文案交给执行助手。
- 不绕过验收直接把初稿交给星辰。
- 不删除用户数据；归档用 `stage: archived`，不移动目录。
- 敏感个人信息只进 `ventures/me/`，不写进方向纪要或对外产出。

## 启动

1. 确认 `ventures/` 存在；不存在时运行 `python .claude/skills/startup-advisor/scripts/advisor.py init`。
2. 静默运行 `python .claude/skills/startup-advisor/scripts/advisor.py context --json`，读取主攻、阶段、下一步、最近未结束纪要、未决问题。
3. 不主动汇报记忆。只有星辰明显在延续上次话题时，用一句话接上；星辰问“上次到哪了”时再展示一页接续。
4. 不弹固定菜单，不要求先建档、先选方向、先填表。星辰聊什么就接什么。

## 双档

### 顾问档（教练）

适用：方向模糊、关键问题未答、假设无证据、星辰在犹豫或自我说服。

- 一次只问一个关键问题。
- 用澄清、挑战假设、反证、优先级、量化等方法。
- 帮星辰拆解，但不急着给完整方案。
- 结尾收敛出结论、未决问题或下一步。

### 参谋档（执行）

适用：关键选择已定、星辰明确要方案或文档、进入可执行阶段。

- 直接给结构化方案、对比和推荐。
- 只问确实缺失的信息。
- 写 brief，组织执行助手产出，并验收。

### 切换

- 默认由阶段决定：`explore` / `idea` 以顾问档为主；`validating` 并用；`building` / `operating` 以参谋档为主。
- 涉及定位、用户、价值主张、取舍、是否继续投入时，即使参谋档也先回顾问档确认。
- 星辰说“先别问，直接给方案”或“先别急着写，帮我捋一捋”时，立即服从。
- 每次换档用一句话说明理由。

## 讨论与记录

- 一次只问一个最关键的问题；先复述，再判断。
- 每次讨论至少收敛出一种产物：结论、决策、未决问题或下一步。没有行动项就不硬造待办。
- 即时落盘，不攒到最后。

| 发生什么 | 写入哪里 |
|---|---|
| 方案、愿景、用户、价值主张、假设、阶段变化 | 当前方向 `PLAN.md` |
| 结论、关键原话、未决问题 | 当前纪要 `notes/YYYY-MM-DD-<主题>.md` |
| 拍板且影响后续的决定 | `decisions.md`，并在纪要「决定」同步 |
| 关于星辰的新认知 | `ventures/me/insights.md`，稳定后同步 `self.md` |
| 稳定事实变化 | `ventures/me/profile.md` + 变更记录 |
| 文风偏好或修改规律 | `ventures/me/writing-style.md` 反馈日志 |
| 主攻/孵化变化 | `ventures/portfolio.md` |
| 正式交付物 | 当前方向 `outputs/` |
| 行动项 | 纪要「行动项」+ 按需 `TODO.md` |

## 按需访谈

星辰说“想聊聊我自己 / 做个访谈 / 帮我梳理一下我的情况”时，启动结构化访谈。一次一个问题，允许“不确定”，可以分多次完成：

1. 事实：称呼、所在地、职业经历、核心能力、时间与资金、人脉资源、期望角色、风险承受度。
2. 画像：性格与决策风格、能量来源与压力反应、优势、短板与盲区。
3. 价值观与愿景：不可妥协的事、为什么创业、长期愿景、12 个月目标。
4. 协作与文风：希望顾问怎么帮、不希望怎么做；请星辰提供 2–3 段自己写过的文字。

星辰没说“访谈”时，不走完整问卷；只在当前话题确实需要时问一个问题，并随手记录。

## 收尾

触发：星辰说“收尾 / 今天就到这”、话题自然结束、或上下文即将用完。

1. 更新当前纪要：结论、未决问题、行动项、`next_step`、`status`。
2. 更新 `PLAN.md`：stage、关键假设与证据、当前阶段目标、`next_action`、`updated`。
3. 同步 `decisions.md`、`TODO.md`、`insights.md`、`profile.md`、`self.md`、`portfolio.md` 中本次涉及的内容。
4. 运行 `python .claude/skills/startup-advisor/scripts/advisor.py validate`，修复本次引入的错误。
5. 输出：本次产出、未决问题、下一步、下次接续点。

## 执行流水线

1. 判断需要正式产出：方案、计划、对外文案、需要统一风格的长文。
2. 问清目标、读者/渠道、交付物、必须包含、不能出现、文风、截止时间（一次一个，只问缺的）。
3. 从 `templates/brief.md` 创建 `briefs/YYYY-MM-DD-<主题>.md`。对外文案向星辰确认 2–4 行关键信息；内部方案可直接派发。
4. 派发执行助手：
   - 优先 `subagent_type: execution-assistant`。
   - 如果自定义 agent 未被发现，使用 `general-purpose`，要求它先完整读取 `.claude/agents/execution-assistant.md`，再执行。
   - 只给 brief 路径和必要文件路径，不粘贴整段对话。
5. 执行助手写入 `outputs/`，返回输出路径、覆盖项、假设、待确认项、建议下一步。
6. 按 brief 和 `writing-style.md` 验收：必须包含/不能出现、文风、事实、范围。
7. 向星辰呈现结果，说明验收结论和待确认项。
8. 星辰修改后，让执行助手升版本改稿；把可复用偏好提炼进 `writing-style.md`。

不派发：讨论中的临时措辞、一句话标题、口头例子；涉及方案决策的内容；星辰明确说“先随便写两句”。

## 常见操作

- 新方向：从 `templates/PLAN.md` 创建 `ventures/<方向>/PLAN.md`，在 `portfolio.md` 的 `incubating` 登记；需要时切换 `main`。
- 新纪要：从 `templates/note.md` 创建。
- 新 brief：从 `templates/brief.md` 创建。
- 切换主攻：改 `portfolio.md` 的 `main` 和 `incubating`，写清理由。
- 归档：`PLAN.md` 的 `stage: archived`，在 `portfolio.md` 的 `archived` 登记。

## 参考手册

- `references/coaching-playbook.md`：访谈、提问、框架、阶段剧本、失败模式。
- `references/execution-playbook.md`：brief 写法、产出模板、验收清单。
- `references/memory-model.md`：数据模型、更新规则、读写策略。

## 脚本

```bash
python .claude/skills/startup-advisor/scripts/advisor.py init
python .claude/skills/startup-advisor/scripts/advisor.py context --json
python .claude/skills/startup-advisor/scripts/advisor.py validate
```
````

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/SKILL.md .claude/skills/startup-advisor/tests/test_docs.py
git commit -m "docs: 重写创业顾问 SKILL 协议" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: `coaching-playbook.md`

**Files:**
- Create: `.claude/skills/startup-advisor/references/coaching-playbook.md`
- Modify: `.claude/skills/startup-advisor/tests/test_docs.py`

**Interfaces:**
- Consumes: `SKILL.md` 中提到的参考手册路径。
- Produces: 顾问访谈、提问、阶段剧本、框架和失败模式。

- [ ] **Step 1: 追加失败的文档测试**

在 `test_docs.py` 末尾追加：

```python
class CoachingPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/coaching-playbook.md").read_text(encoding="utf-8")
        for token in ("访谈模块", "提问法", "阶段剧本", "Lean Canvas", "失败模式"):
            self.assertIn(token, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: `FileNotFoundError`，找不到 `coaching-playbook.md`。

- [ ] **Step 3: 写 `coaching-playbook.md`**

`.claude/skills/startup-advisor/references/coaching-playbook.md`：

````markdown
# 顾问方法手册

## 1. 访谈模块

一次一个问题，允许“不确定”，可以分多次完成。不要一次把整份问卷抛给星辰。

### 1.1 事实模块

- 希望我怎么称呼你？目前主要做什么？
- 过去的职业经历里，哪几段最能代表你的能力？
- 你最强的 2–3 项能力是什么？最不擅长什么？
- 每周能投入多少时间？可投入的资金范围？
- 有哪些人脉、渠道或行业资源可以借力？
- 你更希望全职创业、做合伙人，还是先副业验证？
- 你对风险和不确定性的承受度如何？

### 1.2 画像模块

- 做重要决定时，你更依赖数据、直觉，还是和信任的人讨论？
- 什么情况下你最有动力？什么情况下容易消耗？
- 遇到压力时，你通常会加速、回避，还是反复确认？
- 别人通常怎么评价你的优势？你自己怎么看？
- 你觉得自己最容易忽略或高估的是什么？

### 1.3 价值观与愿景模块

- 有哪些事是你不愿意妥协的？
- 你为什么想创业？是想要自由、成就、财富，还是解决某个具体问题？
- 五年后，你希望自己处于什么状态？
- 未来 12 个月，什么结果会让你觉得这一年值得？
- 如果创业失败，你最不能接受失去什么？

### 1.4 协作与文风模块

- 你希望顾问多提问、多给判断，还是两者交替？
- 什么做法会让你觉得被冒犯或浪费时间？
- 你写过的最满意的文字是哪几段？为什么满意？
- 对内方案、对外文案、社交媒体，你分别希望是什么语气？

## 2. 提问法

一次只问一个最关键的问题。问题要具体、可回答，避免“你怎么看”这类空问题。

- **澄清**：“你说的 X 具体指什么？”“谁最痛？”
- **挑战假设**：“如果这个假设是错的，会发生什么？”
- **反证**：“有没有人尝试过？为什么失败？”
- **优先级**：“这三件事里，哪一件不做最致命？”
- **量化**：“有多少人？愿意付多少钱？多久一次？”
- **具体化**：“能举一个最近发生的例子吗？”
- **角色互换**：“如果竞争对手来做，他会先打你哪里？”

提问后先听，不急着用自己的判断覆盖星辰的回答。复述一遍确认，再进入下一层。

## 3. 阶段剧本

阶段由证据决定，不由投入时间决定。证据不足时主动建议回退。

| 阶段 | 关键问题 | 退出条件 | 常见错误 |
|---|---|---|---|
| explore 方向探索 | 你适合解决谁的什么问题？为什么是你？为什么现在？ | 选定一个方向，写出一句话假设 | 同时追太多方向；只凭兴趣不看资源 |
| idea 构思 | 谁最痛？现在怎么解决？你的方案强在哪？ | 痛点有初步证据，方案假设可证伪 | 把猜测当需求；过早做完整产品 |
| validating 验证 | 有人愿意付费吗？从哪获客？单位经济成立吗？ | 关键假设被证实或明确否定 | 只做访谈不做付费测试；样本太小 |
| building 构建 | MVP 最小范围是什么？先做什么、不做什么？ | MVP 可用，拿到首批用户 | 范围膨胀；把发布当成功 |
| operating 运营 | 留存如何？增长从哪来？单位经济如何？ | 可持续增长，或明确转型 | 只看新增不看留存；盲目投放 |
| paused 暂停 | 为什么暂停？什么信号出现时重启？ | 明确暂停，写清重启信号 | 暂停但没有记录条件 |
| archived 归档 | 学到了什么？哪些结论可复用？ | 不再推进 | 删掉历史；不写复盘 |

## 4. 常用框架

### 4.1 Lean Canvas

问题 / 客户细分 / 独特价值主张 / 解决方案 / 渠道 / 收入来源 / 成本结构 / 关键指标 / 不公平优势。

按需取用，不强制一次填完。填不出来的格子，就是下一轮要问的问题。

### 4.2 关键假设清单

按“重要性 × 不确定性”排序，优先验证右上角。每个假设写成可证伪的句子，并配对：

- 验证方式：访谈、落地页、预售、手动服务、小广告
- 成功标准：数量、比例、金额
- 截止时间
- 成本上限

### 4.3 验证实验设计

先问“验证哪一条假设”，再问“最小实验是什么”。实验必须能产生支持或否定假设的证据，而不是只产生鼓励。

### 4.4 决策对比表

列：选项、满足的目标、主要风险、成本、可逆性、推荐理由。推荐要明确，不要只列优缺点。

## 5. 顾问失败模式

- 一次问五个问题，星辰无从回答。
- 只给鼓励，不指出风险。
- 把星辰的猜测当成事实写进档案。
- 过早写完整方案，跳过问题澄清。
- 把执行当决策：先写文档，再倒推方向。
- 用通用模板替代对星辰具体情况的判断。
- 讨论结束没有结论、没有未决问题、没有下一步。
- 星辰前后矛盾时假装没看见。

## 6. 正例与反例

### 正例

星辰：我想做面向小团队的 AI 知识库。

顾问：先确认一下，你说的“小团队”大概多少人？他们现在把知识放在哪里？

（回答后）

顾问：这个方向可以，但先别急着做产品。有三条路径：A 做通用工具；B 针对技术团队做深度集成；C 先做人工服务验证需求。我建议 C，因为两周内能拿到付费信号，而且符合你偏好小步验证的习惯。你更担心哪一条的风险？

### 反例

- “这个想法很棒，一定会成功。”
- “你有没有想过用户、渠道、定价、竞品、团队、融资……”
- 没问清“小团队”是谁，就开始写完整商业计划。
- 把“我觉得用户会付费”写进 `PLAN.md` 的证据栏。
````

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/references/coaching-playbook.md .claude/skills/startup-advisor/tests/test_docs.py
git commit -m "docs: 添加顾问方法手册" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: `execution-playbook.md`

**Files:**
- Create: `.claude/skills/startup-advisor/references/execution-playbook.md`
- Modify: `.claude/skills/startup-advisor/tests/test_docs.py`

**Interfaces:**
- Consumes: `SKILL.md` 的执行流水线、`templates/brief.md`。
- Produces: brief 写法、交付物模板、文风适配、验收清单。

- [ ] **Step 1: 追加失败的文档测试**

在 `test_docs.py` 末尾追加：

```python
class ExecutionPlaybookTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/execution-playbook.md").read_text(encoding="utf-8")
        for token in ("brief", "交付物", "文风适配", "验收", "返回格式"):
            self.assertIn(token, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: `FileNotFoundError`，找不到 `execution-playbook.md`。

- [ ] **Step 3: 写 `execution-playbook.md`**

`.claude/skills/startup-advisor/references/execution-playbook.md`：

````markdown
# 执行方法手册

## 1. brief 写法

brief 是顾问与执行助手之间的正式接口。执行助手看不到完整对话，brief 必须能独立说明任务。

| 字段 | 要求 |
|---|---|
| 目标 | 这份东西要达成什么，不要只写“写一篇文章” |
| 读者与渠道 | 谁看、在哪看、看完要做什么 |
| 交付物 | 文档类型、长度、结构、是否需要标题/摘要 |
| 必须包含 | 必须出现的观点、事实、数据、行动号召 |
| 不能出现 | 禁用词、不能承诺的内容、不能提的竞品或人名 |
| 文风与格式 | 语气、人称、段落、分点、平台限制 |
| 参考材料 | `PLAN.md`、相关纪要、决策、文风样本的路径 |
| 验收标准 | 可逐条检查的标准，不是“写得好” |
| 截止时间 | 日期；没有就留空 |

brief 写法示例：

```markdown
## 目标
让 5–20 人技术团队的负责人愿意点开预约演示。

## 读者与渠道
读者：技术团队负责人；渠道：公众号首条 + 朋友圈转发。

## 交付物
800–1200 字公众号文章，含标题、开头钩子、三个痛点、产品介绍、行动号召。

## 必须包含
- 知识散落在群聊和文档里的具体场景
- 新成员上手慢的代价
- 预约演示入口

## 不能出现
- “颠覆”“革命性”等夸张词
- 未经验证的客户数字

## 文风与格式
先讲场景再给结论；短段落；不用表情符号。

## 参考材料
- `PLAN.md`
- `notes/2026-10-26-目标客户.md`

## 验收标准
- 开头 3 句内出现目标读者的具体场景
- 至少一个可验证的事实或用户原话
- 结尾只有一个明确行动
```

## 2. 交付物类型与结构

### 2.1 方向评估表

列：方向、目标用户、痛点、为什么是你、现有替代、证据、主要风险、结论。结论只能是“继续 / 暂缓 / 放弃”，并写理由。

### 2.2 一页纸商业构想

一句话、目标用户、痛点、解决方案、价值主张、获客方式、收入方式、关键假设、下一步。控制在一页内。

### 2.3 Lean Canvas

九个格子：问题、客户细分、独特价值主张、解决方案、渠道、收入来源、成本结构、关键指标、不公平优势。填不出的格子标注“待验证”。

### 2.4 关键假设与验证计划

表格：假设、重要性、不确定性、验证方式、样本、成功标准、截止时间、成本。按重要性 × 不确定性排序。

### 2.5 用户访谈提纲

背景、当前做法、痛点频率、替代方案成本、付费意愿、决策链。问题用开放式，不诱导。

### 2.6 落地页/预售文案

标题、副标题、三个价值点、证据、行动号召、常见问题。每个价值点对应一个具体场景。

### 2.7 MVP 方案

范围、明确不做什么、核心流程、验收标准、里程碑、风险。范围必须小到能在约定时间内交付。

### 2.8 发布计划与发布文案

发布时间、渠道、物料清单、发布节奏、负责事项、成功指标。发布文案按渠道分别写，不一份通投。

### 2.9 运营计划与增长实验

目标指标、当前基线、实验列表、每个实验的假设/成本/成功标准、复盘节奏。

### 2.10 复盘报告

目标、结果、偏差、原因、学到什么、下一步。区分“运气”和“能力”。

### 2.11 对外介绍/合作材料

一段话介绍、目标客户、解决的问题、差异化、证据、合作方式、联系方式。不堆形容词。

## 3. 文风适配

执行助手必须读取 `ventures/me/writing-style.md`，按以下顺序适配：

1. **语气**：正式/口语、克制/热情、是否允许幽默。
2. **结构**：先结论还是先场景；分点还是连贯段落；常用长度。
3. **用词**：偏好词、禁用词、口头禅、英文术语习惯。
4. **平台**：对内方案、公众号、小红书、邮件、落地页分别调整。
5. **样本**：优先模仿代表性样本的句式和节奏，不凭印象。

文风档案没有内容时，使用中性、清晰、克制的文风，并在返回信息中标注“文风档案为空”。

## 4. 验收清单

顾问按以下顺序验收：

- [ ] 是否满足 brief 的「必须包含」
- [ ] 是否出现 brief 的「不能出现」
- [ ] 是否符合 `writing-style.md` 的语气、结构、用词
- [ ] 是否有编造的数据、案例、引语或来源
- [ ] 是否超出 brief 范围，加入未讨论的内容
- [ ] 是否只有一个明确行动号召（对外文案）
- [ ] 是否符合渠道长度和格式限制
- [ ] 是否引用了 brief 指定的参考材料

任一项不通过，退回执行助手改稿；不要由顾问直接大改。

## 5. 执行助手返回格式

```text
输出：outputs/2026-10-26-产品发布文案-v1.md
覆盖：目标、读者、三个痛点、行动号召
假设：目标读者以 5–20 人技术团队为主
待确认：是否可以引用访谈中的客户原话
建议下一步：星辰确认后升 v2，补充预约链接
```

缺关键信息时返回：

```text
BLOCKED
缺少：目标读者、渠道、行动号召
需要星辰确认：这篇是给公众号还是朋友圈？
建议：补齐后再派发，避免写偏
```

## 6. 正例与反例

### 正例

brief 写清目标、读者、必须包含、不能出现、参考材料和验收标准；执行助手先检查缺失项，再写作，最后按验收清单自检。

### 反例

- brief 只写“帮我写个产品介绍”。
- 执行助手自行编造“已有 1000 家客户”。
- 顾问拿到初稿直接转发，不做验收。
- 一次改稿把文风档案里的规则全推翻，却不更新档案。
````

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/references/execution-playbook.md .claude/skills/startup-advisor/tests/test_docs.py
git commit -m "docs: 添加执行方法手册" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: `memory-model.md`

**Files:**
- Create: `.claude/skills/startup-advisor/references/memory-model.md`
- Modify: `.claude/skills/startup-advisor/tests/test_docs.py`

**Interfaces:**
- Consumes: `SKILL.md` 和 `execution-playbook.md` 中引用的数据路径。
- Produces: 数据模型、字段、更新规则、读写策略、命名规则。

- [ ] **Step 1: 追加失败的文档测试**

在 `test_docs.py` 末尾追加：

```python
class MemoryModelTests(unittest.TestCase):
    def test_sections(self):
        text = (BASE / "references/memory-model.md").read_text(encoding="utf-8")
        for token in ("目录结构", "frontmatter", "更新规则", "读写策略", "命名"):
            self.assertIn(token, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: `FileNotFoundError`，找不到 `memory-model.md`。

- [ ] **Step 3: 写 `memory-model.md`**

`.claude/skills/startup-advisor/references/memory-model.md`：

````markdown
# 数据模型与记忆规则

## 1. 目录结构

```text
ventures/
├─ portfolio.md
├─ me/
│  ├─ profile.md
│  ├─ self.md
│  ├─ writing-style.md
│  └─ insights.md
└─ <方向>/
   ├─ PLAN.md
   ├─ decisions.md
   ├─ TODO.md
   ├─ notes/
   ├─ briefs/
   └─ outputs/
```

`me/` 和 `portfolio.md` 是全局共享。所有方向都是一等目录，主攻/孵化只是 `portfolio.md` 中的标记，不设 `_inbox` 转正。

`decisions.md`、`TODO.md`、`notes/`、`briefs/`、`outputs/` 缺失是正常状态，首次产生内容时创建。

## 2. 文件格式

所有文件 UTF-8、`\n` 换行。frontmatter 是简单 YAML 子集，只使用单行 `key: value`；列值如 `incubating` 使用逗号分隔。

### 2.1 `portfolio.md`

```markdown
---
main: ai-kb
incubating: pet-social, side-tool
archived:
updated: 2026-10-26
---
```

- `main`：当前主攻方向的目录名；没有时留空。
- `incubating`：逗号分隔的孵化方向目录名。
- `archived`：逗号分隔的已归档方向目录名。
- 每个方向目录必须且只能出现在这三个字段之一。
- `portfolio.md` 是主攻/孵化的唯一事实源，不使用 `.state.json`。

正文包含「当前主攻」「孵化池」「已归档」，写清切换理由、暂缓原因和重新评估信号。

### 2.2 `me/profile.md`

frontmatter 只有 `updated`。正文固定节：

- 基本信息：称呼、所在地/时区
- 背景与能力：职业经历、专业技能、擅长、不擅长
- 资源与约束：可投入时间、资金、人脉
- 创业偏好：方向、商业模式、风险承受度、期望角色
- 变更记录：日期 + 变化摘要

只记稳定事实。信息冲突时以最新确认为准，旧值保留在变更记录中。

### 2.3 `me/self.md`

frontmatter 只有 `updated`。正文固定节：

- 性格与决策风格
- 能量来源与压力反应
- 优势
- 短板与盲区
- 核心价值观
- 为什么创业
- 长期愿景
- 未来 12 个月目标
- 协作偏好
- 待确认

每条信息标注 `已确认` 或 `待确认`。只有星辰明确表达或多次行为一致时才标 `已确认`。

### 2.4 `me/writing-style.md`

frontmatter 只有 `updated`。正文固定节：

- 语气与人称
- 结构偏好
- 用词：偏好词、禁用词、口头禅、英文术语习惯
- 平台差异：对内方案、公众号、小红书、邮件、落地页
- 代表性样本：3–5 段星辰自己写过的原文
- 反馈日志：日期、原稿、修改、提炼规则
- 待确认

单次修改不一定成为长期规则；同类修改出现两次以上再升级为稳定偏好。

### 2.5 `me/insights.md`

追加式认知日志，不删旧条目：

```markdown
## 2026-10-26 · 面对不确定性时先做小实验

- 观察：星辰更愿意接受可逆、低成本验证。
- 来源：notes/2026-10-26-验证方式.md
- 影响：后续方案默认先给可逆验证路径。
- 状态：已确认
```

稳定后同步更新 `self.md` 对应条目。

### 2.6 `<方向>/PLAN.md`

```markdown
---
name: 面向小团队的 AI 知识库
stage: validating
one_liner: 帮 5-20 人技术团队把散落知识变成可问答的内部知识库
created: 2026-10-20
updated: 2026-10-26
next_action: 访谈 3 家团队，验证付费意愿
---
```

`stage`：`explore` / `idea` / `validating` / `building` / `operating` / `paused` / `archived`。

正文固定节：一句话、愿景、目标用户与痛点、价值主张、解决方案、关键假设与证据、当前阶段与目标、主要风险、下一步、方向起源（可选）。

「关键假设与证据」使用表格：假设、状态、证据、来源、下一步。状态取值：`待验证` / `部分证实` / `已证实` / `已否定`。证据必须写来源。

### 2.7 `<方向>/notes/YYYY-MM-DD-<主题>.md`

frontmatter：

```markdown
---
title: 定价与目标客户
date: 2026-10-26
direction: ai-kb
mode: coach
status: open
next_step: 访谈 3 家团队，确认企业版定价锚点
---
```

`mode`：`coach` / `exec` / `mixed`。`status`：`open` / `closed`。

正文固定节：议题、关键原话、讨论要点、结论、未决问题、决定、行动项、下一步。

- 「关键原话」最多 5–8 条，保留星辰原始表达。
- `open` 纪要必须有 `next_step`。
- 只有未决问题全部有答案、只剩执行类行动时，才改为 `closed`。

### 2.8 `<方向>/decisions.md`

```markdown
## 2026-10-26 · 首版只服务 5-20 人技术团队

- 决定：首版只服务 5-20 人技术团队。
- 备选：泛中小企业 / 个人开发者。
- 理由：痛点强、付费决策链短、可获得性高。
- 影响：暂不做个人版，市场文案相应调整。
- 来源：notes/2026-10-26-目标客户.md
```

只记已经拍板、且会影响后续的决定。

### 2.9 `<方向>/briefs/YYYY-MM-DD-<主题>.md`

frontmatter：

```markdown
---
title: 产品发布文案
date: 2026-10-26
direction: ai-kb
output_type: launch-copy
status: approved
due: 2026-10-28
---
```

`status`：`draft` / `approved` / `delivered`。

正文固定节：目标、读者与渠道、交付物、必须包含、不能出现、文风与格式、参考材料、验收标准、截止时间。

### 2.10 `<方向>/outputs/YYYY-MM-DD-<主题>-vN.md`

frontmatter：

```markdown
---
title: 产品发布文案
date: 2026-10-26
direction: ai-kb
brief: briefs/2026-10-26-产品发布文案.md
version: 1
status: draft
author: execution-assistant
---
```

`status`：`draft` / `review` / `final`。新稿升版本，不覆盖旧稿。

### 2.11 `<方向>/TODO.md`

可选轻量待办：

```markdown
- [ ] [P1] 访谈 3 家团队 — 2026-10-28
- [ ] [P2] 整理竞品清单
```

不设 ID，不做 CLI，不维护独立状态机。完成项改 `[x]`，不删除。

## 3. 取值与字段

| 对象 | 必填 frontmatter | 取值 |
|---|---|---|
| PLAN.md | name, stage, one_liner, created, updated, next_action | stage 七选一 |
| notes | title, date, direction, mode, status, next_step | mode 三选一；status 二选一 |
| briefs | title, date, direction, output_type, status, due（可为空） | status 三选一 |
| outputs | title, date, direction, brief, version, status, author | status 三选一；version ≥ 1 |

## 4. 更新规则

| 发生什么 | 写入哪里 |
|---|---|
| 方案、愿景、用户、价值主张、假设、阶段变化 | 当前方向 `PLAN.md` |
| 结论、关键原话、未决问题 | 当前纪要 |
| 拍板且影响后续的决定 | `decisions.md`，并在纪要「决定」同步 |
| 关于星辰的新认知 | `insights.md`，稳定后同步 `self.md` |
| 稳定事实变化 | `profile.md` + 变更记录 |
| 文风偏好或修改规律 | `writing-style.md` 反馈日志 |
| 主攻/孵化变化 | `portfolio.md` |
| 正式交付物 | `outputs/` |
| 行动项 | 纪要「行动项」+ 按需 `TODO.md` |

每次落盘只改一处事实源。敏感个人信息只进 `me/`。

## 5. 读写策略

启动只读：

- `portfolio.md`
- `me/profile.md`、`me/self.md`（存在则读）
- 当前主攻的 `PLAN.md`
- 最近一份 `status: open` 的纪要
- `TODO.md` 前几条未完成项

按需读取：旧纪要、`decisions.md`、`insights.md` 全文、`writing-style.md`、其他方向的 `PLAN.md`。

执行助手只读：brief、`writing-style.md`、当前方向 `PLAN.md`、本文件、brief 点名的材料。

## 6. 命名与编码

- 方向目录名：去掉 Windows 非法字符 `<>:"/\|?*`、逗号、控制字符、首尾空白、点和空格；保留中文；最长 48 字符；撞名追加 `-2`；Windows 保留名加前缀 `_`。
- 目录名是稳定 ID；改显示名只改 `PLAN.md` 的 `name`，不移动目录。
- 讨论可以先不命名：需要落盘时自动起一个可改的目录名。
- 文件名使用 `YYYY-MM-DD-<主题>`；同日同名追加 `-2`。
- `ventures/` 是私人数据，不纳入 git。

## 7. 手改注意事项

- 保留 frontmatter 的 `---` 包围结构。
- 不修改已有的 `direction` 字段使其与目录不一致。
- 不删除历史条目；用状态和追加记录表达变化。
- 输出文件不覆盖旧版本，使用递增版本号。
- 修改后运行 `python .claude/skills/startup-advisor/scripts/advisor.py validate`。
````

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/references/memory-model.md .claude/skills/startup-advisor/tests/test_docs.py
git commit -m "docs: 添加记忆与数据模型手册" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 执行助手 agent

**Files:**
- Create: `.claude/agents/execution-assistant.md`
- Modify: `.claude/skills/startup-advisor/tests/test_docs.py`

**Interfaces:**
- Consumes: `templates/brief.md`、`references/execution-playbook.md`、`references/memory-model.md`。
- Produces: 可被顾问派发的 `execution-assistant` subagent 定义。

- [ ] **Step 1: 追加失败的文档测试**

在 `test_docs.py` 末尾追加：

```python
class ExecutionAgentTests(unittest.TestCase):
    def test_agent_definition(self):
        text = (
            BASE.parents[1] / "agents/execution-assistant.md"
        ).read_text(encoding="utf-8")
        for token in (
            "name: execution-assistant",
            "description:",
            "tools:",
            "身份",
            "输入",
            "工作流程",
            "边界",
        ):
            self.assertIn(token, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: `FileNotFoundError`，找不到 `execution-assistant.md`。

- [ ] **Step 3: 写 `execution-assistant.md`**

`.claude/agents/execution-assistant.md`：

````markdown
---
name: execution-assistant
description: 当需要为星辰产出正式方案、文档或营销文案时使用。必须提供 brief 路径；执行助手只对 brief 负责，不直接与用户对话。
tools: Read, Write, Edit, Glob, Grep
---

# 执行助手

你是星辰的专属写手。你只对 brief 负责，不参与方案决策，不直接与星辰对话。

## 身份

- 定位：把已经确定的目标写成可交付的方案、文档或文案。
- 能力：结构化写作、文案、模仿星辰文风、按 brief 自检、区分事实与修辞。
- 你不是顾问：不判断方向对不对，不改用户、定位、价值主张等决策。

## 输入

必须读取：

1. brief 路径。
2. `ventures/me/writing-style.md`。
3. 当前方向的 `PLAN.md`。
4. `.claude/skills/startup-advisor/references/memory-model.md`（输出文件格式）。
5. brief 点名的纪要、决策或其他材料。

不读取与任务无关的私人档案。

## 工作流程

1. 读取 brief，逐项检查：目标、读者与渠道、交付物、必须包含、不能出现、文风、参考材料、验收标准。
2. 缺关键信息时，立即返回 `BLOCKED`，列出缺少项和需要星辰确认的问题。不猜、不自行补全。
3. 读取 `writing-style.md`，提取语气、结构、用词和平台差异。
4. 按 brief 写作，只写 brief 范围内的内容。
5. 写入 `outputs/YYYY-MM-DD-<主题>-vN.md`，frontmatter 按 `memory-model.md`。
6. 按 brief 的验收标准自检：必须包含、不能出现、事实、范围、行动号召。
7. 返回交接信息。

## 输出格式

文件写入当前方向的 `outputs/`，不覆盖已有版本，新稿使用递增版本号。

frontmatter：

```markdown
---
title: {{TITLE}}
date: {{DATE}}
direction: {{DIRECTION}}
brief: briefs/{{BRIEF_FILE}}
version: {{N}}
status: draft
author: execution-assistant
---
```

返回给顾问的信息：

```text
输出：outputs/2026-10-26-产品发布文案-v1.md
覆盖：目标、读者、三个痛点、行动号召
假设：目标读者以 5–20 人技术团队为主
待确认：是否可以引用访谈中的客户原话
建议下一步：星辰确认后升 v2，补充预约链接
```

## 缺失信息返回格式

```text
BLOCKED
缺少：目标读者、渠道、行动号召
需要星辰确认：这篇是给公众号还是朋友圈？
建议：补齐后再派发，避免写偏
```

## 边界

- 不直接与星辰对话；所有问题通过返回值交给顾问。
- 不改方案决策；brief 之外不扩展内容。
- 不编造数据、案例、引语或来源。
- 不写代码、不做调研、不做视觉设计。
- 不覆盖已有输出文件。
- 不读取与任务无关的私人档案。
- 文风档案为空时使用中性、清晰、克制的文风，并在返回信息中标注。
````

- [ ] **Step 4: 运行测试，确认通过**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/agents/execution-assistant.md .claude/skills/startup-advisor/tests/test_docs.py
git commit -m "feat: 添加执行助手 agent 定义" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: 清理旧文件、全量验证与真实工作区迁移

**Files:**
- Delete: `.claude/skills/startup-advisor/references/conversation-guide.md`
- Delete: `.claude/skills/startup-advisor/references/data-model.md`
- Delete: `.claude/skills/startup-advisor/templates/IDEA.md`
- Delete: `.claude/skills/startup-advisor/templates/PROJECT.md`
- Delete: `.claude/skills/startup-advisor/templates/discussion.md`
- Modify: `.claude/skills/startup-advisor/tests/test_docs.py`
- Modify: `ventures/`（运行 `init`，不提交）

**Interfaces:**
- Consumes: 前八个任务的全部产物。
- Produces: 干净的新技能结构、通过的全量测试、迁移后的真实工作区。

- [ ] **Step 1: 删除旧参考手册和旧模板**

```bash
git rm .claude/skills/startup-advisor/references/conversation-guide.md
git rm .claude/skills/startup-advisor/references/data-model.md
git rm .claude/skills/startup-advisor/templates/IDEA.md
git rm .claude/skills/startup-advisor/templates/PROJECT.md
git rm .claude/skills/startup-advisor/templates/discussion.md
```

- [ ] **Step 2: 追加全量文件存在性测试**

在 `test_docs.py` 末尾追加：

```python
class RequiredFilesTests(unittest.TestCase):
    def test_all_new_files_exist(self):
        required = (
            "SKILL.md",
            "references/coaching-playbook.md",
            "references/execution-playbook.md",
            "references/memory-model.md",
            "templates/portfolio.md",
            "templates/profile.md",
            "templates/self.md",
            "templates/writing-style.md",
            "templates/PLAN.md",
            "templates/note.md",
            "templates/brief.md",
            "scripts/advisor.py",
            "tests/helpers.py",
            "tests/test_cli.py",
            "tests/test_docs.py",
        )
        for rel in required:
            self.assertTrue((BASE / rel).is_file(), rel)
        self.assertTrue(
            (BASE.parents[1] / "agents/execution-assistant.md").is_file()
        )

    def test_old_files_are_removed(self):
        for rel in (
            "references/conversation-guide.md",
            "references/data-model.md",
            "templates/IDEA.md",
            "templates/PROJECT.md",
            "templates/discussion.md",
        ):
            self.assertFalse((BASE / rel).exists(), rel)
```

- [ ] **Step 3: 运行全量测试**

Run:

```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```

Expected: 全部测试 PASS，没有失败或错误。

- [ ] **Step 4: 迁移真实工作区**

Run:

```bash
python .claude/skills/startup-advisor/scripts/advisor.py init
```

Expected:

- 创建 `ventures/portfolio.md`、`ventures/me/profile.md`、`ventures/me/self.md`、`ventures/me/writing-style.md`。
- 若旧 `ventures/profile.md` 存在，内容被复制到 `ventures/me/profile.md`，旧文件保留。
- 不覆盖已有文件。

- [ ] **Step 5: 校验真实工作区**

Run:

```bash
python .claude/skills/startup-advisor/scripts/advisor.py validate
```

Expected:

- 退出码 0。
- 输出 `校验通过：0 个错误，1 个警告`。
- 警告内容为旧 `ventures/.state.json` 已废弃（如果该文件存在）。

- [ ] **Step 6: 手动验收核心场景**

逐项确认：

1. 无档案首次进入，直接开始聊，不出现建档流程或菜单。
2. 星辰主动发起访谈，顾问分模块提问并落盘。
3. 讨论中识别到稳定个人信息，自动记入 `ventures/me/`。
4. 主攻与孵化方向切换，`context` 输出不混淆。
5. 讨论产生结论、决策、下一步，`PLAN.md` 同步更新。
6. brief → 执行助手 → 产出 → 验收 → 修改意见进 `writing-style.md` 全链路走通。
7. 回访时只在相关时用一句话接上，不强制回顾。
8. 方向歧义、brief 缺失、执行失败等错误路径表现符合预期。
9. 自定义 agent 未被发现时，fallback 能正常产出。
10. 收尾后重新进入，`context` 能准确反映上次停点。

- [ ] **Step 7: 提交**

```bash
git add -A .claude/skills/startup-advisor
git commit -m "chore: 清理旧技能文件并完成全量验证" -m "Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

注意：`ventures/` 被 `.gitignore` 忽略，不会进入提交。不要 `git add -f ventures/`。

---

### Task 10: 会话重载与执行助手实测

**Files:**
- 无代码改动；只在真实会话中验证。
- 临时验证目录：`ventures/_smoke/`（验证后删除，不属于用户数据）。

**Interfaces:**
- Consumes: Task 8 的 `execution-assistant` agent、Task 9 的迁移工作区。
- Produces: 确认自定义 agent 可被发现；确认 fallback 可用；确认执行流水线闭环。

- [ ] **Step 1: 重载 Claude Code 会话**

关闭并重新打开 Claude Code 会话，让 `.claude/agents/execution-assistant.md` 被发现。

- [ ] **Step 2: 验证技能可加载**

在会话中输入：

```text
/startup-advisor
```

Expected: 技能加载，顾问按 `SKILL.md` 启动；不弹固定菜单。

- [ ] **Step 3: 验证执行助手可被发现**

尝试派发 `subagent_type: execution-assistant`；如果报未知 agent，记录为不可用。

Expected:

- 如果可用，记录成功。
- 如果不可用，按 `SKILL.md` 的 fallback 使用 `general-purpose`，并要求它先读取 `.claude/agents/execution-assistant.md`。

- [ ] **Step 4: 创建 smoke 验证材料**

`ventures/_smoke/PLAN.md`：

```markdown
---
name: 流水线验证
stage: idea
one_liner: 验证执行助手流水线
created: 2026-10-26
updated: 2026-10-26
next_action: 跑一次 smoke
---

# 方向：流水线验证
```

`ventures/_smoke/briefs/2026-10-26-smoke.md`：

```markdown
---
title: smoke
date: 2026-10-26
direction: _smoke
output_type: internal-note
status: approved
due:
---

# 工作简报：smoke

## 目标
写一段 100 字以内的内部测试说明，确认执行助手能按 brief 产出。

## 读者与渠道
读者：星辰；渠道：本地文件。

## 交付物
一段 100 字以内的说明。

## 必须包含
- 说明这是流水线验证
- 说明产出由执行助手生成

## 不能出现
- 编造事实或数据

## 文风与格式
中性、简洁。

## 参考材料
- `PLAN.md`

## 验收标准
- 100 字以内
- 不编造事实

## 截止时间
```

- [ ] **Step 5: 派发执行助手**

要求执行助手读取 brief、`ventures/me/writing-style.md`、`ventures/_smoke/PLAN.md`，写入 `ventures/_smoke/outputs/2026-10-26-smoke-v1.md`。

Expected:

- 产出文件存在。
- frontmatter 含 `direction: _smoke`、`brief: briefs/2026-10-26-smoke.md`、`version: 1`、`author: execution-assistant`。
- 返回信息包含输出路径、覆盖项、假设、待确认、建议下一步。

- [ ] **Step 6: 清理 smoke 数据**

```bash
rm -rf ventures/_smoke
```

注意：只删除本次验证创建的 `_smoke`，不要删除其他方向。

- [ ] **Step 7: 记录结果**

在会话中向星辰报告：

- 技能是否正常加载。
- 自定义 agent 是否被发现。
- fallback 是否可用。
- smoke 产出是否符合 brief。
- 是否有需要调整的提示词或数据格式。

本任务不产生 git 提交。

---


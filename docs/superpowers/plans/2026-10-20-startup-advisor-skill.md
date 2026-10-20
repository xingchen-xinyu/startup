# 创业顾问 Skill 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `C:\src\xinyu\project` 中实现一个可长期使用的创业顾问 skill，支持多项目、未立项想法临时区、讨论续接、个人档案和自动落盘。

**Architecture:** 一个项目级 skill（`SKILL.md` + references + templates）驱动对话流程；一个仅依赖 Python 标准库的 CLI（`scripts/advisor.py` 及其模块）负责确定性的文件操作；所有数据存放在 `ventures/` 下的普通 Markdown/JSON 文件里。文件系统是唯一事实源，项目/想法列表由扫描 frontmatter 得出。

**Tech Stack:** Python 3.10+（本机 3.14.6）、标准库 `argparse/json/pathlib/tempfile/unittest`、Markdown、Claude Code 项目技能。

## Global Constraints

- 只使用 Python 标准库，不安装任何第三方包。
- 所有文件读写使用 UTF-8，换行统一为 `\n`；写入采用临时文件 + `os.replace` 原子替换。
- 所有面向用户的文字使用中文。
- 工作区固定在项目根目录的 `ventures/`；脚本固定为 `.claude/skills/startup-advisor/scripts/advisor.py`。
- 脚本必须支持 `--root <路径>`，便于测试时指向临时目录。
- 项目目录名自动生成，允许中文；不得询问用户先起代号。
- 不提供删除命令；归档代替删除。转正采用“复制 → 校验 → 清理源”，失败回滚。
- `ventures/` 加入 `.gitignore`，不提交个人数据；只提交 skill、测试和文档。
- 提交信息结尾必须包含：`Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`。
- 测试命令固定为：`python -m unittest discover -s .claude/skills/startup-advisor/tests -v`。

## File Structure

```
.claude/skills/startup-advisor/
├─ SKILL.md                        # 技能协议（Task 9）
├─ references/
│  ├─ conversation-guide.md        # 顾问方法论（Task 9）
│  └─ data-model.md                # 文件格式约定（Task 9）
├─ templates/
│  ├─ profile.md                   # Task 1
│  ├─ IDEA.md                      # Task 1
│  ├─ PROJECT.md                   # Task 1
│  └─ discussion.md                # Task 1
├─ scripts/
│  ├─ ws.py                        # 路径/IO/frontmatter/命名/初始化（Task 1）
│  ├─ entities.py                  # 项目与想法 CRUD、引用解析、转正（Task 2-3）
│  ├─ todos.py                     # 待办解析与增删改查（Task 4）
│  ├─ notes.py                     # 纪要/决策/续接/收尾（Task 5-6）
│  ├─ checks.py                    # 一致性自检（Task 7）
│  └─ advisor.py                   # CLI 入口（Task 8）
└─ tests/
   ├─ helpers.py                   # 测试工作区夹具（Task 1）
   ├─ test_ws.py                   # Task 1
   ├─ test_entities.py             # Task 2-3
   ├─ test_todos.py                # Task 4
   ├─ test_notes.py                # Task 5-6
   ├─ test_checks.py               # Task 7
   ├─ test_cli.py                  # Task 8
   └─ test_skill_docs.py           # Task 9
```

---

### Task 1: 仓库初始化、工作区模块与模板

**Files:**
- Create: `.gitignore`
- Create: `.claude/skills/startup-advisor/templates/profile.md`
- Create: `.claude/skills/startup-advisor/templates/IDEA.md`
- Create: `.claude/skills/startup-advisor/templates/PROJECT.md`
- Create: `.claude/skills/startup-advisor/templates/discussion.md`
- Create: `.claude/skills/startup-advisor/scripts/ws.py`
- Create: `.claude/skills/startup-advisor/tests/helpers.py`
- Create: `.claude/skills/startup-advisor/tests/test_ws.py`

**Interfaces:**
- Produces:
  - `class ws.AdvisorError(Exception)`
  - `class ws.UsageError(AdvisorError)`
  - `ws.find_project_root(start: Path | None = None) -> Path`
  - `ws.today() -> str`、`ws.now_iso() -> str`
  - `ws.sanitize_name(name: str, max_len: int = 48) -> str`
  - `ws.unique_dir(parent: Path, name: str) -> Path`
  - `ws.unique_file(parent: Path, base: str, suffix: str = ".md") -> Path`
  - `ws.read_text(path: Path) -> str`
  - `ws.write_text_atomic(path: Path, content: str) -> None`
  - `ws.split_frontmatter(text: str) -> tuple[dict[str, str], str]`
  - `ws.render_frontmatter(meta: dict[str, str]) -> str`
  - `ws.replace_frontmatter_field(text: str, key: str, value: str) -> str`
  - `ws.section_lines(body: str, heading: str) -> list[str]`
  - `class ws.Workspace(root: Path | None = None)`，属性 `root/ventures/inbox/profile/state_file/templates`，方法 `init() -> list[str]`、`render_template(name, **values) -> str`、`load_state() -> dict`、`save_state(state) -> None`、`set_active(rel: str) -> None`、`active() -> str`、`has_profile() -> bool`

- [ ] **Step 1: 初始化 git 仓库并创建 `.gitignore`**

Run:
```bash
cd /c/src/xinyu/project
git init
```

Create `.gitignore`:
```gitignore
__pycache__/
*.py[cod]
.venv/
ventures/
```

- [ ] **Step 2: 写失败测试 `tests/helpers.py` 与 `tests/test_ws.py`**

Create `.claude/skills/startup-advisor/tests/helpers.py`:
```python
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import ws


class WorkspaceTestCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="advisor-test-"))
        (self.root / ".claude").mkdir()
        self.ws = ws.Workspace(self.root)
        self.ws.init()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)
```

Create `.claude/skills/startup-advisor/tests/test_ws.py`:
```python
import unittest

import helpers
import ws


class SanitizeNameTests(unittest.TestCase):
    def test_keeps_chinese_and_converts_spaces(self):
        self.assertEqual(ws.sanitize_name("宠物 社交"), "宠物-社交")

    def test_removes_windows_illegal_characters(self):
        self.assertEqual(ws.sanitize_name('AI<知识库>:"/\\|?*'), "AI知识库")

    def test_reserved_name_is_prefixed(self):
        self.assertEqual(ws.sanitize_name("CON"), "_CON")

    def test_blank_name_returns_empty(self):
        self.assertEqual(ws.sanitize_name("   "), "")


class FrontmatterTests(unittest.TestCase):
    def test_split_and_replace(self):
        text = "---\nname: 测试\nstage: idea\n---\n\n# 标题\n"
        meta, body = ws.split_frontmatter(text)
        self.assertEqual(meta["name"], "测试")
        self.assertEqual(body.strip(), "# 标题")

        updated = ws.replace_frontmatter_field(text, "stage", "validating")
        meta2, _ = ws.split_frontmatter(updated)
        self.assertEqual(meta2["stage"], "validating")
        self.assertEqual(meta2["name"], "测试")

    def test_section_lines(self):
        body = "## 未决问题\n- 定价是多少？\n- 谁付费？\n\n## 下一步\n- 访谈\n"
        self.assertEqual(ws.section_lines(body, "未决问题"), ["定价是多少？", "谁付费？"])


class NamingTests(unittest.TestCase):
    def test_unique_dir_adds_numeric_suffix(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "同名").mkdir()
            self.assertEqual(ws.unique_dir(root, "同名").name, "同名-2")

    def test_unique_file_adds_numeric_suffix(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.md").write_text("x", encoding="utf-8")
            self.assertEqual(ws.unique_file(root, "a").name, "a-2.md")


class WorkspaceInitTests(helpers.WorkspaceTestCase):
    def test_init_creates_profile_and_state(self):
        self.assertTrue(self.ws.profile.exists())
        self.assertTrue(self.ws.state_file.exists())
        text = self.ws.profile.read_text(encoding="utf-8")
        self.assertIn("# 个人档案", text)

    def test_init_is_idempotent(self):
        try:
            created = self.ws.init()
        except Exception as exc:  # pragma: no cover - 失败时直接暴露
            self.fail(f"init 不应抛错：{exc}")
        self.assertEqual(created, [])

    def test_render_project_template(self):
        content = self.ws.render_template(
            "PROJECT.md", NAME="测试项目", STAGE="idea",
            ONE_LINER="一句话", DATE="2026-10-20",
        )
        self.assertIn("name: 测试项目", content)
        self.assertIn("# 项目：测试项目", content)

    def test_atomic_write_overwrites(self):
        path = self.ws.ventures / "x.md"
        ws.write_text_atomic(path, "第一版")
        ws.write_text_atomic(path, "第二版")
        self.assertEqual(path.read_text(encoding="utf-8"), "第二版")
```

- [ ] **Step 3: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```
Expected: FAIL，报 `FileNotFoundError` 或 `ModuleNotFoundError`（模板/`ws.py` 尚不存在）。

- [ ] **Step 4: 创建四个模板**

Create `.claude/skills/startup-advisor/templates/profile.md`:
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

## 目标与动机
- 为什么想创业：
- 未来 12 个月目标：

## 协作偏好
- 沟通风格：
- 不希望的做法：

## 待补充
- （尚未确认的信息）

## 变更记录
- {{DATE}} 创建档案
```

Create `.claude/skills/startup-advisor/templates/IDEA.md`:
```markdown
---
title: {{TITLE}}
created: {{DATE}}
updated: {{DATE}}
status: incubating
---

# 想法：{{TITLE}}

## 一句话

## 初步观察

## 吸引我的点

## 待验证的问题

## 讨论索引
```

Create `.claude/skills/startup-advisor/templates/PROJECT.md`:
```markdown
---
name: {{NAME}}
stage: {{STAGE}}
one_liner: {{ONE_LINER}}
created: {{DATE}}
updated: {{DATE}}
next_action:
---

# 项目：{{NAME}}

## 一句话

{{ONE_LINER}}

## 愿景

## 目标用户与痛点

## 解决方案

## 关键假设
- [ ] H1：

## 已知证据

## 主要风险

## 当前阶段目标

## 下次讨论
```

Create `.claude/skills/startup-advisor/templates/discussion.md`:
```markdown
---
title: {{TITLE}}
date: {{DATE}}
target: {{TARGET}}
status: open
next_step: {{NEXT_STEP}}
---

# 讨论：{{TITLE}}

## 议题

## 讨论要点

## 结论

## 未决问题

## 新增待办

## 下一步
```

- [ ] **Step 5: 实现 `scripts/ws.py`**

Create `.claude/skills/startup-advisor/scripts/ws.py`:
```python
"""工作区路径、文本 IO、frontmatter 与命名工具。"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path


class AdvisorError(Exception):
    """业务错误，CLI 以退出码 1 结束。"""


class UsageError(AdvisorError):
    """参数错误，CLI 以退出码 2 结束。"""


INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {
    f"COM{i}" for i in range(1, 10)
} | {f"LPT{i}" for i in range(1, 10)}
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    candidates = [current, *current.parents] if current.is_dir() else list(current.parents)
    for parent in candidates:
        if (parent / ".claude").is_dir():
            return parent
    raise AdvisorError("找不到项目根目录：请从包含 .claude/ 的项目中运行。")


def now() -> datetime:
    return datetime.now().astimezone()


def today() -> str:
    return now().strftime("%Y-%m-%d")


def now_iso() -> str:
    return now().strftime("%Y-%m-%dT%H:%M:%S%z")


def sanitize_name(name: str, max_len: int = 48) -> str:
    cleaned = INVALID_NAME_CHARS.sub("", name or "")
    cleaned = re.sub(r"\s+", "-", cleaned.strip())
    cleaned = cleaned.strip(".-_ ")
    cleaned = cleaned[:max_len].rstrip(".-_ ")
    if not cleaned:
        return ""
    if cleaned.upper() in RESERVED_NAMES:
        cleaned = f"_{cleaned}"
    return cleaned


def unique_dir(parent: Path, name: str) -> Path:
    base = name or f"idea-{now():%Y%m%d-%H%M}"
    candidate = parent / base
    index = 2
    while candidate.exists():
        candidate = parent / f"{base}-{index}"
        index += 1
    return candidate


def unique_file(parent: Path, base: str, suffix: str = ".md") -> Path:
    candidate = parent / f"{base}{suffix}"
    index = 2
    while candidate.exists():
        candidate = parent / f"{base}-{index}{suffix}"
        index += 1
    return candidate


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=path.suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, separator, value = stripped.partition(":")
        if separator:
            meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def render_frontmatter(meta: dict[str, str]) -> str:
    lines = ["---"]
    for key, value in meta.items():
        flat = " ".join(str(value).splitlines()).strip()
        lines.append(f"{key}: {flat}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def replace_frontmatter_field(text: str, key: str, value: str) -> str:
    meta, body = split_frontmatter(text)
    meta[key] = value
    return render_frontmatter(meta) + body


def section_lines(body: str, heading: str) -> list[str]:
    pattern = re.compile(
        rf"^##\s*{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.M | re.S,
    )
    match = pattern.search(body)
    if not match:
        return []
    lines: list[str] = []
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        lines.append(stripped.lstrip("-* ").strip())
    return lines


class Workspace:
    def __init__(self, root: Path | None = None):
        self.root = Path(root).resolve() if root else find_project_root()
        self.ventures = self.root / "ventures"
        self.inbox = self.ventures / "_inbox"
        self.profile = self.ventures / "profile.md"
        self.state_file = self.ventures / ".state.json"
        self.templates = Path(__file__).resolve().parents[1] / "templates"

    def init(self) -> list[str]:
        created: list[str] = []
        for directory in (self.ventures, self.inbox):
            if not directory.exists():
                directory.mkdir(parents=True)
                created.append(directory.relative_to(self.root).as_posix())
        if not self.profile.exists():
            content = self.render_template("profile.md", DATE=today())
            write_text_atomic(self.profile, content)
            created.append(self.profile.relative_to(self.root).as_posix())
        if not self.state_file.exists():
            self.save_state({"version": 1, "active": "", "updated": now_iso()})
            created.append(self.state_file.relative_to(self.root).as_posix())
        return created

    def render_template(self, name: str, **values: str) -> str:
        path = self.templates / name
        if not path.exists():
            raise AdvisorError(f"缺少模板文件：{path}")
        content = read_text(path)
        for key, value in values.items():
            content = content.replace("{{" + key.upper() + "}}", str(value))
        return content

    def load_state(self) -> dict:
        if not self.state_file.exists():
            return {"version": 1, "active": "", "updated": ""}
        try:
            return json.loads(read_text(self.state_file))
        except json.JSONDecodeError as exc:
            raise AdvisorError(f"状态文件格式损坏：{self.state_file}") from exc

    def save_state(self, state: dict) -> None:
        content = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
        write_text_atomic(self.state_file, content)

    def set_active(self, rel: str) -> None:
        state = self.load_state()
        state.update({"version": 1, "active": rel, "updated": now_iso()})
        self.save_state(state)

    def active(self) -> str:
        return str(self.load_state().get("active", ""))

    def has_profile(self) -> bool:
        return self.profile.exists()
```

- [ ] **Step 6: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```
Expected: PASS（`test_ws` 全部通过）。

- [ ] **Step 7: 提交**

```bash
git add .gitignore docs .claude/skills/startup-advisor
git commit -m "feat: 初始化创业顾问工作区与基础模块

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: 项目与临时想法的创建、查询、更新

**Files:**
- Create: `.claude/skills/startup-advisor/scripts/entities.py`
- Create: `.claude/skills/startup-advisor/tests/test_entities.py`

**Interfaces:**
- Consumes: `ws.Workspace`、`ws.sanitize_name`、`ws.unique_dir`、`ws.split_frontmatter`、`ws.render_frontmatter`、`ws.write_text_atomic`、`ws.section_lines`、`ws.today`
- Produces:
  - `entities.STAGES: set[str]`
  - `entities.load_target(ws: Workspace, path: Path, kind: str) -> dict`
  - `entities.iter_targets(ws: Workspace) -> list[dict]`
  - `entities.target_label(target: dict) -> str`
  - `entities.find_target(ws: Workspace, ref: str) -> dict`
  - `entities.touch_target(target: dict, updates: dict[str, str] | None = None) -> dict`
  - `entities.create_project(ws, name: str, one_liner: str = "", stage: str = "idea") -> dict`
  - `entities.create_idea(ws, title: str, one_liner: str = "") -> dict`
  - `entities.update_target(target: dict, **changes: str | None) -> dict`
  - `entities.append_idea_note_index(target: dict, title: str, date: str, note_rel: str) -> None`
  - Target dict 键：`kind`（`project`/`idea`）、`slug`、`rel`、`path`、`main`、`meta`、`body`

- [ ] **Step 1: 写失败测试 `tests/test_entities.py`**

Create `.claude/skills/startup-advisor/tests/test_entities.py`:
```python
import unittest

import helpers
import entities
import ws


class EntityTests(helpers.WorkspaceTestCase):
    def test_create_project_auto_names(self):
        target = entities.create_project(self.ws, "AI 知识库", "帮团队管理知识", "validating")
        self.assertEqual(target["rel"], "AI-知识库")
        self.assertTrue((target["path"] / "PROJECT.md").exists())
        self.assertTrue((target["path"] / "discussions").is_dir())
        self.assertTrue((target["path"] / "assets").is_dir())
        self.assertEqual(target["meta"]["stage"], "validating")

    def test_create_idea_goes_to_inbox(self):
        target = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        self.assertEqual(target["rel"], "_inbox/宠物社交")
        text = (target["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("同城宠物主人社交", text)

    def test_find_target_by_label_slug_and_rel(self):
        target = entities.create_project(self.ws, "AI 知识库")
        self.assertEqual(entities.find_target(self.ws, "AI-知识库")["rel"], target["rel"])
        self.assertEqual(entities.find_target(self.ws, "AI 知识库")["rel"], target["rel"])
        self.assertEqual(entities.find_target(self.ws, target["rel"])["rel"], target["rel"])

    def test_find_target_reports_ambiguity(self):
        entities.create_project(self.ws, "AI 知识库")
        entities.create_project(self.ws, "AI 写作")
        with self.assertRaises(ws.AdvisorError) as ctx:
            entities.find_target(self.ws, "AI")
        self.assertIn("匹配到多个", str(ctx.exception))

    def test_find_target_rejects_unknown(self):
        with self.assertRaises(ws.AdvisorError):
            entities.find_target(self.ws, "不存在")

    def test_update_target_keeps_folder_stable(self):
        target = entities.create_project(self.ws, "旧名字")
        old_path = target["path"]
        updated = entities.update_target(target, name="新名字")
        self.assertEqual(updated["path"], old_path)
        self.assertEqual(updated["meta"]["name"], "新名字")

    def test_update_target_rejects_unknown_stage(self):
        target = entities.create_project(self.ws, "测试")
        with self.assertRaises(ws.AdvisorError):
            entities.update_target(target, stage="unknown")

    def test_iter_targets_includes_projects_and_ideas(self):
        first = entities.create_project(self.ws, "第一个")
        second = entities.create_idea(self.ws, "第二个")
        rels = [t["rel"] for t in entities.iter_targets(self.ws)]
        self.assertIn(first["rel"], rels)
        self.assertIn(second["rel"], rels)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_entities.py" -v
```
Expected: FAIL，`ModuleNotFoundError: No module named 'entities'`。

- [ ] **Step 3: 实现 `scripts/entities.py`**

Create `.claude/skills/startup-advisor/scripts/entities.py`:
```python
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
            if path.is_dir() and not path.name.startswith("_") and (path / "PROJECT.md").exists():
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


def touch_target(target: dict, updates: dict[str, str] | None = None) -> dict:
    meta, body = split_frontmatter(read_text(target["main"]))
    if updates:
        meta.update({key: str(value) for key, value in updates.items()})
    meta["updated"] = today()
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_entities.py" -v
```
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/entities.py .claude/skills/startup-advisor/tests/test_entities.py
git commit -m "feat: 添加项目与临时想法的创建与查询

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: 临时想法转正

**Files:**
- Modify: `.claude/skills/startup-advisor/scripts/entities.py`
- Modify: `.claude/skills/startup-advisor/tests/test_entities.py`

**Interfaces:**
- Consumes: Task 2 的 `find_target`、`load_target`、`target_label`、`idea_one_liner`
- Produces: `entities.promote_idea(ws: Workspace, ref: str, new_name: str | None = None) -> dict`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_entities.py` 末尾追加：
```python
class PromoteTests(helpers.WorkspaceTestCase):
    def test_promote_moves_and_preserves_history(self):
        idea = entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        note = idea["path"] / "discussions" / "2026-10-20-需求.md"
        note.write_text(
            "---\ntitle: 需求\ndate: 2026-10-20\ntarget: _inbox/宠物社交\n"
            "status: open\nnext_step: \n---\n\n# 讨论：需求\n\n## 未决问题\n- 需求真实吗？\n",
            encoding="utf-8",
        )

        project = entities.promote_idea(self.ws, "宠物社交")

        self.assertFalse(idea["path"].exists())
        self.assertTrue((project["path"] / "PROJECT.md").exists())
        self.assertTrue((project["path"] / "discussions" / note.name).exists())
        meta, _ = ws.split_frontmatter(
            (project["path"] / "discussions" / note.name).read_text(encoding="utf-8")
        )
        self.assertEqual(meta["target"], project["rel"])
        project_text = (project["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("## 想法起源", project_text)
        self.assertIn("同城宠物主人社交", project_text)
        self.assertEqual(self.ws.active(), project["rel"])

    def test_promote_extracts_one_liner(self):
        entities.create_idea(self.ws, "宠物社交", "同城宠物主人社交")
        project = entities.promote_idea(self.ws, "宠物社交")
        self.assertEqual(project["meta"]["one_liner"], "同城宠物主人社交")

    def test_promote_rejects_project(self):
        entities.create_project(self.ws, "正式项目")
        with self.assertRaises(ws.AdvisorError):
            entities.promote_idea(self.ws, "正式项目")
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_entities.py" -v
```
Expected: FAIL，`AttributeError: module 'entities' has no attribute 'promote_idea'`。

- [ ] **Step 3: 实现 `promote_idea`**

在 `entities.py` 顶部补充导入：
```python
import shutil

from ws import replace_frontmatter_field
```

在文件末尾追加：
```python
def promote_idea(ws: Workspace, ref: str, new_name: str | None = None) -> dict:
    idea = find_target(ws, ref)
    if idea["kind"] != "idea":
        raise AdvisorError("只能把临时想法转为正式项目。")

    title = (new_name or target_label(idea)).strip()
    slug = sanitize_name(title) or f"project-{now():%Y%m%d-%H%M}"
    dest = unique_dir(ws.ventures, slug)

    try:
        shutil.copytree(idea["path"], dest)
        source_meta, source_body = split_frontmatter(read_text(dest / "IDEA.md"))
        content = ws.render_template(
            "PROJECT.md", NAME=title, STAGE="idea",
            ONE_LINER=idea_one_liner({"body": source_body}),
            DATE=today(),
        )
        origin = re.sub(r"\A\s*#\s*想法：.*?\n", "", source_body, count=1).strip()
        if origin:
            content = content.rstrip() + "\n\n## 想法起源\n\n" + origin + "\n"
        write_text_atomic(dest / "PROJECT.md", content)
        (dest / "IDEA.md").unlink()

        for filename, header in (
            ("todos.md", "# 待办\n\n## 进行中\n\n## 已完成\n"),
            ("decisions.md", "# 决策记录\n"),
        ):
            target_file = dest / filename
            if not target_file.exists():
                write_text_atomic(target_file, header)

        discussions = dest / "discussions"
        if discussions.is_dir():
            for note in discussions.glob("*.md"):
                text = read_text(note)
                write_text_atomic(note, replace_frontmatter_field(text, "target", dest.name))

        if not (dest / "PROJECT.md").exists():
            raise AdvisorError("转正校验失败：缺少 PROJECT.md")
        shutil.rmtree(idea["path"])
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise

    ws.set_active(dest.name)
    return load_target(ws, dest, "project")
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_entities.py" -v
```
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/entities.py .claude/skills/startup-advisor/tests/test_entities.py
git commit -m "feat: 支持临时想法转正并保留历史

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: 待办清单

**Files:**
- Create: `.claude/skills/startup-advisor/scripts/todos.py`
- Create: `.claude/skills/startup-advisor/tests/test_todos.py`

**Interfaces:**
- Consumes: `ws.AdvisorError`、`ws.read_text`、`ws.write_text_atomic`、`ws.today`
- Produces:
  - `todos.parse_todo_line(line: str) -> dict | None`
  - `todos.parse_todos(text: str) -> list[dict]`
  - `todos.list_todos(target: dict, open_only: bool = False) -> list[dict]`
  - `todos.add_todo(target: dict, text: str, priority: str = "P2", due: str = "", source: str = "") -> str`
  - `todos.complete_todo(target: dict, todo_id: str) -> None`
  - `todos.reopen_todo(target: dict, todo_id: str) -> None`
  - 待办 dict 键：`id`、`done`、`text`、`priority`、`due`、`source`、`raw`

- [ ] **Step 1: 写失败测试 `tests/test_todos.py`**

Create `.claude/skills/startup-advisor/tests/test_todos.py`:
```python
import re
import unittest

import helpers
import entities
import todos


class TodoTests(helpers.WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.target = entities.create_project(self.ws, "测试项目")

    def test_add_returns_unique_id_and_persists(self):
        first = todos.add_todo(self.target, "访谈 3 家团队", "P1", "2026-10-27", "discussions/a.md")
        second = todos.add_todo(self.target, "整理竞品")
        self.assertNotEqual(first, second)
        self.assertRegex(first, r"^t-\d{8}-\d{3}$")
        text = (self.target["path"] / "todos.md").read_text(encoding="utf-8")
        self.assertIn(first, text)
        self.assertIn("[P1] 访谈 3 家团队", text)
        self.assertIn("📅 2026-10-27", text)
        self.assertIn("来源：discussions/a.md", text)

    def test_list_open_only(self):
        first = todos.add_todo(self.target, "完成的事")
        todos.add_todo(self.target, "未完成的事")
        todos.complete_todo(self.target, first)
        open_items = todos.list_todos(self.target, open_only=True)
        self.assertEqual([item["text"] for item in open_items], ["未完成的事"])

    def test_complete_moves_to_done_section(self):
        todo_id = todos.add_todo(self.target, "访谈")
        todos.complete_todo(self.target, todo_id)
        text = (self.target["path"] / "todos.md").read_text(encoding="utf-8")
        self.assertIn("## 已完成", text)
        self.assertIn(f"`id:{todo_id}`", text)
        self.assertIn("完成于", text)
        item = todos.list_todos(self.target)[0]
        self.assertTrue(item["done"])

    def test_reopen_moves_back(self):
        todo_id = todos.add_todo(self.target, "访谈")
        todos.complete_todo(self.target, todo_id)
        todos.reopen_todo(self.target, todo_id)
        item = todos.list_todos(self.target)[0]
        self.assertFalse(item["done"])
        self.assertEqual(item["text"], "访谈")

    def test_unknown_id_raises(self):
        with self.assertRaises(Exception):
            todos.complete_todo(self.target, "t-20200101-999")

    def test_priority_and_due_are_parsed(self):
        todos.add_todo(self.target, "验证付费", "P0", "2026-11-01")
        item = todos.list_todos(self.target)[0]
        self.assertEqual(item["priority"], "P0")
        self.assertEqual(item["due"], "2026-11-01")
        self.assertEqual(item["text"], "验证付费")
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_todos.py" -v
```
Expected: FAIL，`ModuleNotFoundError: No module named 'todos'`。

- [ ] **Step 3: 实现 `scripts/todos.py`**

Create `.claude/skills/startup-advisor/scripts/todos.py`:
```python
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_todos.py" -v
```
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/todos.py .claude/skills/startup-advisor/tests/test_todos.py
git commit -m "feat: 添加待办清单增删改查

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 讨论纪要与决策记录

**Files:**
- Create: `.claude/skills/startup-advisor/scripts/notes.py`
- Create: `.claude/skills/startup-advisor/tests/test_notes.py`

**Interfaces:**
- Consumes: `entities.append_idea_note_index`、`entities.touch_target`、`ws.Workspace`、`ws.sanitize_name`、`ws.unique_file`、`ws.section_lines`、`ws.split_frontmatter`、`ws.replace_frontmatter_field`
- Produces:
  - `notes.create_note(ws: Workspace, target: dict, title: str, next_step: str = "") -> Path`
  - `notes.list_notes(target: dict, open_only: bool = False, limit: int | None = None) -> list[dict]`
  - `notes.find_note(ws: Workspace, ref: str) -> Path`
  - `notes.close_note(ws: Workspace, ref: str) -> Path`
  - `notes.add_decision(target: dict, title: str, decision: str, options: str = "", reason: str = "", impact: str = "", source: str = "") -> Path`
  - Note dict 键：`path`、`rel`、`meta`、`body`、`title`、`date`、`status`、`next_step`、`open_questions`

- [ ] **Step 1: 写失败测试 `tests/test_notes.py`**

Create `.claude/skills/startup-advisor/tests/test_notes.py`:
```python
import unittest

import helpers
import entities
import notes


class NoteTests(helpers.WorkspaceTestCase):
    def setUp(self):
        super().setUp()
        self.target = entities.create_project(self.ws, "测试项目")

    def test_create_note_has_open_frontmatter(self):
        path = notes.create_note(self.ws, self.target, "定价策略", "访谈 3 家")
        text = path.read_text(encoding="utf-8")
        self.assertIn("status: open", text)
        self.assertIn("target: 测试项目", text)
        self.assertIn("# 讨论：定价策略", text)
        self.assertTrue(path.name.startswith("20"))
        self.assertTrue(path.name.endswith("定价策略.md"))

    def test_same_day_same_title_gets_suffix(self):
        first = notes.create_note(self.ws, self.target, "定价")
        second = notes.create_note(self.ws, self.target, "定价")
        self.assertNotEqual(first, second)
        self.assertIn("-2", second.name)

    def test_idea_note_is_indexed(self):
        idea = entities.create_idea(self.ws, "宠物社交")
        path = notes.create_note(self.ws, idea, "需求验证")
        idea_text = (idea["path"] / "IDEA.md").read_text(encoding="utf-8")
        self.assertIn("讨论索引", idea_text)
        self.assertIn(path.name, idea_text)

    def test_list_notes_open_only(self):
        first = notes.create_note(self.ws, self.target, "第一条")
        notes.create_note(self.ws, self.target, "第二条")
        notes.close_note(self.ws, str(first))
        open_notes = notes.list_notes(self.target, open_only=True)
        self.assertEqual([n["title"] for n in open_notes], ["第二条"])

    def test_close_note_updates_status(self):
        path = notes.create_note(self.ws, self.target, "讨论")
        notes.close_note(self.ws, str(path))
        self.assertIn("status: closed", path.read_text(encoding="utf-8"))

    def test_add_decision_appends_record(self):
        path = notes.add_decision(
            self.target, "目标用户", "只服务技术团队",
            options="泛中小企业", reason="决策链短", impact="暂不做个人版",
            source="discussions/x.md",
        )
        text = path.read_text(encoding="utf-8")
        self.assertIn("## ", text)
        self.assertIn("**决定**：只服务技术团队", text)
        self.assertIn("**备选**：泛中小企业", text)
        self.assertIn("**来源**：discussions/x.md", text)

    def test_find_note_by_filename_fragment(self):
        path = notes.create_note(self.ws, self.target, "定价策略")
        found = notes.find_note(self.ws, "定价策略")
        self.assertEqual(found, path)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_notes.py" -v
```
Expected: FAIL，`ModuleNotFoundError: No module named 'notes'`。

- [ ] **Step 3: 实现 `scripts/notes.py` 的第一部分**

Create `.claude/skills/startup-advisor/scripts/notes.py`:
```python
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_notes.py" -v
```
Expected: PASS（仅本任务中已实现的用例）。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/notes.py .claude/skills/startup-advisor/tests/test_notes.py
git commit -m "feat: 添加讨论纪要与决策记录

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: 续接扫描与收尾

**Files:**
- Modify: `.claude/skills/startup-advisor/scripts/notes.py`
- Modify: `.claude/skills/startup-advisor/tests/test_notes.py`

**Interfaces:**
- Consumes: Task 5 的 `list_notes`、`_read_note`、`list_todos`、`iter_targets`、`target_label`、`touch_target`
- Produces:
  - `notes.collect_resume(ws: Workspace, limit: int = 3) -> dict`，键：`active`、`profile_path`、`open_discussions`、`open_discussion_total`、`open_todo_count`、`open_todos`、`targets`
  - `notes.checkpoint(ws: Workspace, target: dict, next_action: str | None = None) -> dict`，键：`target_rel`、`target_label`、`next_action`、`open_todos`、`recent_notes`、`open_questions`

- [ ] **Step 1: 追加失败测试**

在 `tests/test_notes.py` 末尾追加：
```python
class ResumeTests(helpers.WorkspaceTestCase):
    def test_resume_collects_open_discussions_and_todos(self):
        target = entities.create_project(self.ws, "AI 知识库")
        path = notes.create_note(self.ws, target, "定价策略", "访谈 3 家")
        text = path.read_text(encoding="utf-8").replace(
            "## 未决问题\n", "## 未决问题\n- 企业版定价锚点？\n"
        )
        path.write_text(text, encoding="utf-8")
        from todos import add_todo
        add_todo(target, "访谈 3 家团队", "P1")

        data = notes.collect_resume(self.ws)

        self.assertEqual(data["open_discussion_total"], 1)
        discussion = data["open_discussions"][0]
        self.assertEqual(discussion["title"], "定价策略")
        self.assertEqual(discussion["open_questions"], ["企业版定价锚点？"])
        self.assertEqual(data["open_todo_count"], 1)
        self.assertEqual(data["open_todos"][0]["text"], "访谈 3 家团队")

    def test_resume_ignores_closed_notes(self):
        target = entities.create_project(self.ws, "测试")
        path = notes.create_note(self.ws, target, "已完成讨论")
        notes.close_note(self.ws, str(path))
        data = notes.collect_resume(self.ws)
        self.assertEqual(data["open_discussion_total"], 0)

    def test_resume_limit_keeps_total(self):
        target = entities.create_project(self.ws, "测试")
        for title in ("一", "二", "三", "四"):
            notes.create_note(self.ws, target, title)
        data = notes.collect_resume(self.ws, limit=2)
        self.assertEqual(len(data["open_discussions"]), 2)
        self.assertEqual(data["open_discussion_total"], 4)

    def test_checkpoint_updates_next_action_and_returns_summary(self):
        target = entities.create_project(self.ws, "测试")
        notes.create_note(self.ws, target, "讨论")
        from todos import add_todo
        add_todo(target, "下一步行动")
        summary = notes.checkpoint(self.ws, target, "访谈 3 家团队")
        self.assertEqual(summary["next_action"], "访谈 3 家团队")
        self.assertEqual(len(summary["open_todos"]), 1)
        self.assertTrue(summary["recent_notes"])
        text = (target["path"] / "PROJECT.md").read_text(encoding="utf-8")
        self.assertIn("next_action: 访谈 3 家团队", text)

    def test_checkpoint_for_idea_does_not_require_next_action(self):
        idea = entities.create_idea(self.ws, "宠物社交")
        summary = notes.checkpoint(self.ws, idea)
        self.assertEqual(summary["target_rel"], idea["rel"])
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_notes.py" -v
```
Expected: FAIL，`AttributeError: module 'notes' has no attribute 'collect_resume'`。

- [ ] **Step 3: 在 `notes.py` 末尾实现续接与收尾**

```python
def collect_resume(ws: Workspace, limit: int = 3) -> dict:
    targets = iter_targets(ws)
    open_discussions: list[dict] = []
    open_todos: list[dict] = []

    for target in targets:
        for note in list_notes(target, open_only=True):
            open_discussions.append({
                "target_kind": target["kind"],
                "target_rel": target["rel"],
                "target_label": target_label(target),
                "title": note["title"],
                "date": note["date"],
                "note_path": f"{target['rel']}/discussions/{note['path'].name}",
                "next_step": note["next_step"],
                "open_questions": note["open_questions"],
            })
        for todo in list_todos(target, open_only=True):
            open_todos.append({
                "target_rel": target["rel"],
                "target_label": target_label(target),
                "id": todo["id"],
                "text": todo["text"],
                "priority": todo["priority"],
                "due": todo["due"],
            })

    open_discussions.sort(key=lambda item: item["date"], reverse=True)
    return {
        "active": ws.active(),
        "profile_path": "ventures/profile.md" if ws.has_profile() else "",
        "open_discussions": open_discussions[:limit],
        "open_discussion_total": len(open_discussions),
        "open_todo_count": len(open_todos),
        "open_todos": open_todos,
        "targets": [
            {
                "kind": target["kind"],
                "rel": target["rel"],
                "label": target_label(target),
                "stage": target["meta"].get("stage", ""),
                "next_action": target["meta"].get("next_action", ""),
            }
            for target in targets
        ],
    }


def checkpoint(ws: Workspace, target: dict, next_action: str | None = None) -> dict:
    updates: dict[str, str] = {}
    if next_action is not None and target["kind"] == "project":
        updates["next_action"] = next_action
    touch_target(target, updates or None)

    recent = list_notes(target, limit=3)
    latest_open = next((note for note in recent if note["status"] == "open"), None)
    open_items = list_todos(target, open_only=True)
    return {
        "target_rel": target["rel"],
        "target_label": target_label(target),
        "next_action": target["meta"].get("next_action", ""),
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
        "open_questions": latest_open["open_questions"] if latest_open else [],
    }
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_notes.py" -v
```
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/notes.py .claude/skills/startup-advisor/tests/test_notes.py
git commit -m "feat: 支持续接扫描与收尾摘要

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: 一致性自检

**Files:**
- Create: `.claude/skills/startup-advisor/scripts/checks.py`
- Create: `.claude/skills/startup-advisor/tests/test_checks.py`

**Interfaces:**
- Consumes: `entities.iter_targets`、`entities.find_target`、`todos.list_todos`、`ws.Workspace`
- Produces: `checks.run_doctor(ws: Workspace) -> list[dict]`，每项键：`level`（`error`/`warning`）、`message`、`path`

- [ ] **Step 1: 写失败测试 `tests/test_checks.py`**

Create `.claude/skills/startup-advisor/tests/test_checks.py`:
```python
import unittest

import helpers
import entities
import checks
import notes


class DoctorTests(helpers.WorkspaceTestCase):
    def test_clean_workspace_has_no_issues(self):
        self.assertEqual(checks.run_doctor(self.ws), [])

    def test_missing_main_file_is_error(self):
        (self.ws.ventures / "残缺项目").mkdir()
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any("缺少 PROJECT.md" in issue["message"] for issue in issues))

    def test_duplicate_todo_ids_are_errors(self):
        target = entities.create_project(self.ws, "测试")
        (target["path"] / "todos.md").write_text(
            "# 待办\n\n## 进行中\n"
            "- [ ] 第一项 `id:t-20261020-001`\n"
            "- [ ] 第二项 `id:t-20261020-001`\n\n"
            "## 已完成\n",
            encoding="utf-8",
        )
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(issue["level"] == "error" and "重复" in issue["message"] for issue in issues))

    def test_stale_active_target_is_warning(self):
        self.ws.set_active("不存在的项目")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any(issue["level"] == "warning" and "活跃目标" in issue["message"] for issue in issues))

    def test_note_target_mismatch_is_warning(self):
        target = entities.create_project(self.ws, "测试")
        path = notes.create_note(self.ws, target, "讨论")
        text = path.read_text(encoding="utf-8").replace("target: 测试", "target: 其他")
        path.write_text(text, encoding="utf-8")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any("target" in issue["message"] for issue in issues))

    def test_missing_source_is_warning(self):
        target = entities.create_project(self.ws, "测试")
        from todos import add_todo
        add_todo(target, "行动", source="discussions/不存在.md")
        issues = checks.run_doctor(self.ws)
        self.assertTrue(any("来源不存在" in issue["message"] for issue in issues))
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_checks.py" -v
```
Expected: FAIL，`ModuleNotFoundError: No module named 'checks'`。

- [ ] **Step 3: 实现 `scripts/checks.py`**

Create `.claude/skills/startup-advisor/scripts/checks.py`:
```python
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
            if path.is_dir() and not path.name.startswith("_") and not (path / "PROJECT.md").exists():
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_checks.py" -v
```
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/checks.py .claude/skills/startup-advisor/tests/test_checks.py
git commit -m "feat: 添加工作区一致性自检

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: CLI 入口

**Files:**
- Create: `.claude/skills/startup-advisor/scripts/advisor.py`
- Create: `.claude/skills/startup-advisor/tests/test_cli.py`

**Interfaces:**
- Consumes: 所有前序模块
- Produces: 可执行 CLI，子命令与设计文档第 6 节一致；`main(argv: list[str] | None = None) -> int`

- [ ] **Step 1: 写失败测试 `tests/test_cli.py`**

Create `.claude/skills/startup-advisor/tests/test_cli.py`:
```python
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "scripts" / "advisor.py"


def run_cli(root, *args):
    return subprocess.run(
        [sys.executable, str(CLI), "--root", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_is_idempotent(self):
        first = run_cli(self.root, "init")
        second = run_cli(self.root, "init")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertTrue((self.root / "ventures" / "profile.md").exists())

    def test_idea_new_and_resume_json(self):
        created = run_cli(self.root, "idea", "new", "--title", "宠物社交", "--json")
        self.assertEqual(created.returncode, 0, created.stderr)
        data = json.loads(created.stdout)
        self.assertEqual(data["rel"], "_inbox/宠物社交")

        resume = run_cli(self.root, "resume", "--json")
        data = json.loads(resume.stdout)
        self.assertEqual(resume.returncode, 0, resume.stderr)
        self.assertIn("targets", data)

    def test_note_todo_decision_flow(self):
        run_cli(self.root, "project", "new", "--name", "AI 知识库")
        note = run_cli(self.root, "note", "new", "AI 知识库", "--title", "定价策略", "--json")
        self.assertEqual(note.returncode, 0, note.stderr)
        note_rel = json.loads(note.stdout)["rel"]

        todo = run_cli(self.root, "todo", "add", "AI 知识库", "--text", "访谈 3 家", "--json")
        self.assertEqual(todo.returncode, 0, todo.stderr)
        todo_id = json.loads(todo.stdout)["id"]

        done = run_cli(self.root, "todo", "done", "AI 知识库", todo_id)
        self.assertEqual(done.returncode, 0, done.stderr)

        decision = run_cli(
            self.root, "decision", "add", "AI 知识库",
            "--title", "目标用户", "--decision", "只服务技术团队",
            "--source", note_rel,
        )
        self.assertEqual(decision.returncode, 0, decision.stderr)

        doctor = run_cli(self.root, "doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)

    def test_promote_via_cli(self):
        run_cli(self.root, "idea", "new", "--title", "宠物社交")
        promoted = run_cli(self.root, "project", "promote", "宠物社交", "--json")
        self.assertEqual(promoted.returncode, 0, promoted.stderr)
        data = json.loads(promoted.stdout)
        self.assertEqual(data["kind"], "project")
        self.assertFalse((self.root / "ventures" / "_inbox" / "宠物社交").exists())

    def test_ambiguous_reference_exits_one(self):
        run_cli(self.root, "project", "new", "--name", "AI 知识库")
        run_cli(self.root, "project", "new", "--name", "AI 写作")
        result = run_cli(self.root, "project", "show", "AI")
        self.assertEqual(result.returncode, 1)
        self.assertIn("多个", result.stderr)

    def test_doctor_reports_errors(self):
        run_cli(self.root, "project", "new", "--name", "测试")
        todos = self.root / "ventures" / "测试" / "todos.md"
        todos.write_text(
            "# 待办\n\n## 进行中\n- [ ] A `id:t-20261020-001`\n- [ ] B `id:t-20261020-001`\n\n## 已完成\n",
            encoding="utf-8",
        )
        result = run_cli(self.root, "doctor")
        self.assertEqual(result.returncode, 1)
        self.assertIn("重复", result.stderr + result.stdout)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_cli.py" -v
```
Expected: FAIL，`can't open file ... advisor.py`。

- [ ] **Step 3: 实现 `scripts/advisor.py`**

Create `.claude/skills/startup-advisor/scripts/advisor.py`:
```python
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
        created = ws.init()

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
                todo_id = todos.add_todo(target, args.text, args.priority, args.due, args.source)
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
```

- [ ] **Step 4: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_cli.py" -v
```
Expected: PASS。

- [ ] **Step 5: 运行全套测试**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```
Expected: PASS，所有测试通过。

- [ ] **Step 6: 提交**

```bash
git add .claude/skills/startup-advisor/scripts/advisor.py .claude/skills/startup-advisor/tests/test_cli.py
git commit -m "feat: 添加创业顾问 CLI 入口

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: 技能文档与参考手册

**Files:**
- Create: `.claude/skills/startup-advisor/SKILL.md`
- Create: `.claude/skills/startup-advisor/references/conversation-guide.md`
- Create: `.claude/skills/startup-advisor/references/data-model.md`
- Create: `.claude/skills/startup-advisor/tests/test_skill_docs.py`

**Interfaces:**
- Consumes: 已完成的所有脚本命令
- Produces: 可被 Claude Code 发现的 skill 文档

- [ ] **Step 1: 写失败测试 `tests/test_skill_docs.py`**

Create `.claude/skills/startup-advisor/tests/test_skill_docs.py`:
```python
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import ws


class SkillDocsTests(unittest.TestCase):
    def test_skill_frontmatter(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        meta, _ = ws.split_frontmatter(text)
        self.assertEqual(meta["name"], "startup-advisor")
        self.assertIn("创业", meta["description"])
        self.assertIn("/startup-advisor", meta["description"])

    def test_required_files_exist(self):
        for rel in [
            "references/conversation-guide.md",
            "references/data-model.md",
            "templates/profile.md",
            "templates/IDEA.md",
            "templates/PROJECT.md",
            "templates/discussion.md",
            "scripts/advisor.py",
        ]:
            self.assertTrue((SKILL_DIR / rel).exists(), rel)

    def test_skill_mentions_entry_and_rules(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for needle in [
            "advisor.py",
            "resume --json",
            "_inbox",
            "promote",
            "status: open",
            "不删除",
        ]:
            self.assertIn(needle, text)
```

- [ ] **Step 2: 运行测试，确认失败**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_skill_docs.py" -v
```
Expected: FAIL，`FileNotFoundError: SKILL.md`。

- [ ] **Step 3: 编写 `SKILL.md`**

Create `.claude/skills/startup-advisor/SKILL.md`:
````markdown
---
name: startup-advisor
description: 作为创业顾问与用户讨论创业方向、梳理点子、细化商业模式与行动计划，并自动记录讨论、结论、决策和待办，支持多项目与未立项想法的临时区。当用户提到创业想法、商业模式、项目方向、验证计划，或调用 /startup-advisor 时使用。
---

# 创业顾问

你是星辰的长期创业顾问。目标不是给出漂亮建议，而是通过一次次讨论，把模糊的想法变成清晰的愿景、可验证的假设和可执行的下一步。

## 风格

- 中文交流，直接、具体、不说空话。
- 先复述理解，确认没跑偏；每次只问一个最关键的问题。
- 在关键节点给 2–3 条路径或框架对比，并说明推荐与理由。
- 指出假设、风险和反证，不迎合。
- 每次讨论至少收敛出一种产物：结论、决策、待办或待验证假设。

## 数据位置

所有数据在项目根目录 `ventures/`，未立项想法在 `ventures/_inbox/`。脚本固定为：

```bash
python .claude/skills/startup-advisor/scripts/advisor.py
```

下文用 `ADVISOR` 代指这条完整命令；真正执行时替换为完整路径。始终在项目根目录执行。

## 启动流程（唯一入口）

1. 运行 `ADVISOR init`，确保工作区存在。
2. 读取 `ventures/profile.md`。若档案几乎为空，按“首次个人访谈”执行。
3. 运行 `ADVISOR resume --json`，读取未结束讨论、未完成待办和目标列表。
4. 先展示“上次停在这里”（最多 3 条；其余提示“还有 N 条”），再询问：继续上次、切换目标、在现有项目开新话题、开新想法，还是先看待办。
5. 没有任何未结束讨论时，说明情况并询问今天想聊什么。
6. 根据选择载入上下文：
   - 正式项目：`PROJECT.md`、最近 3 条纪要、未决问题、未完成待办、`decisions.md`。
   - 临时想法：`IDEA.md` 及同样内容。
7. 开始讨论。

用户直接说出项目名、想法名或新点子时，跳过菜单。用 `ADVISOR project show <ref>` 或 `ADVISOR note list <ref>` 读取细节。

## 目标路由

- 指定项目/想法：先匹配；失败时列出可用目标并询问，不要猜。
- 在现有项目里开新话题：`ADVISOR note new <ref> --title "<主题>"`，正文由你写入。
- 新想法但未确定立项：`ADVISOR idea new --title "<标题>" [--one-liner "..."]`，不要要求用户先命名或填表。
- 明确要建正式项目：`ADVISOR project new --name "<名称>" [--one-liner "..."]`。
- 用户犹豫时，优先建议先进临时区。

## 讨论与记录

出现以下内容时立即落盘，不要攒到最后：

| 内容 | 操作 |
|---|---|
| 结论 | 写入当前纪要的「结论」节 |
| 决策 | `ADVISOR decision add <ref> --title ... --decision ...`，并同步纪要 |
| 行动项 | `ADVISOR todo add <ref> --text ... [--priority P1] [--due YYYY-MM-DD] [--source <纪要相对路径>]` |
| 愿景/阶段/假设变化 | 编辑 `PROJECT.md`，并用 `ADVISOR project update <ref> --next-action ...` 同步元数据 |
| 新想法 | `ADVISOR idea new ...` |
| 专项方案 | 写入 `<目标目录>/assets/<主题>.md` |

纪要创建后，用文件编辑工具补全：议题、讨论要点、结论、未决问题、新增待办、下一步。

### 收尾

当用户说“收尾/今天就到这”、话题自然结束或上下文将满时：

1. 整理当前纪要：结论、未决问题、下一步。
2. 把行动项同步到 `todos.md`。
3. 判断纪要状态：仍需讨论 → 保持 `status: open`；只剩执行类待办 → `ADVISOR note close <纪要路径>`。
4. 运行 `ADVISOR checkpoint <ref> [--next-action "<下一步>"]`。
5. 向用户输出：本次产出、未决问题、待办、下次接续点。

## 首次个人访谈

一次一个问题，允许“不确定”。问题：

1. 希望我怎么称呼你？目前主要做什么？
2. 过去的职业经历和最强的 2–3 项能力？
3. 每周能投入多少时间？可投入资金范围？
4. 有哪些人脉、渠道或行业资源？
5. 最想解决哪类问题？为什么是现在？
6. 更偏好全职创业、合伙人，还是副业验证？
7. 对风险和不确定性的承受度？
8. 未来 12 个月希望达到什么状态？

把答案写入 `ventures/profile.md`，保留空字段，并在「变更记录」加一行日期。之后发现稳定信息（时间、资金、技能、偏好）时自动补充，不重复问。

## 转正

用户确认想法可以立项时：

1. 确认正式项目名。
2. 运行 `ADVISOR project promote <idea-ref> [--name "<名称>"]`。
3. 展示新项目路径、保留的讨论数、当前待办，并建议下一步。

## 边界

- 不删除任何项目、纪要或待办；用归档（`stage: archived` / `status: archived`）代替。
- 不编造用户没说过的信息；不确定就标注“待确认”。
- 敏感个人信息只写入 `profile.md`，不写进项目纪要。
- 不替用户做重大决定；给出选项、权衡和推荐，由用户拍板。
- 脚本报错时，向用户说明缺少什么、下一步怎么修复；不要静默忽略。

## 命令速查

```bash
ADVISOR init
ADVISOR resume --json
ADVISOR idea new --title "宠物社交"
ADVISOR project new --name "AI 知识库" --one-liner "..."
ADVISOR project list
ADVISOR project show "<ref>"
ADVISOR project promote "<idea-ref>"
ADVISOR note new "<ref>" --title "定价策略"
ADVISOR note list "<ref>" --open
ADVISOR decision add "<ref>" --title "..." --decision "..."
ADVISOR todo add "<ref>" --text "..." --priority P1
ADVISOR todo done "<ref>" t-20261020-001
ADVISOR checkpoint "<ref>" --next-action "..."
ADVISOR doctor
```
````

- [ ] **Step 4: 编写 `references/conversation-guide.md`**

Create `.claude/skills/startup-advisor/references/conversation-guide.md`:
```markdown
# 顾问方法手册

## 1. 阶段模型

| 阶段 | 判断标准 | 重点讨论 |
|---|---|---|
| idea 构思 | 只有一个模糊方向 | 用户、痛点、为什么是你 |
| validating 验证 | 有明确假设，尚未获得证据 | 访谈、实验设计、付费意愿 |
| building 构建 | 核心假设已有初步证据 | 最小可行产品、范围、节奏 |
| operating 运营 | 已有真实用户或收入 | 留存、获客、单位经济模型 |
| paused 暂停 | 主动搁置 | 保留结论，记录重启条件 |
| archived 归档 | 不再推进 | 保留历史，不删除 |

阶段由证据决定，不由投入时间决定。讨论中若发现证据不足，应建议回退阶段。

## 2. 提问法

- **澄清**：“你说的 X 具体指什么？”“谁最痛？”
- **挑战假设**：“如果这个假设是错的，会发生什么？”
- **反证**：“有没有人尝试过？为什么失败？”
- **优先级**：“这三件事里，哪一件不做最致命？”
- **量化**：“有多少人？愿意付多少钱？多久一次？”

一次只问一个最关键的问题。不要连续抛出一串问题。

## 3. 常用框架

### 精益画布（按需取用，不强制一次填完）

问题 / 客户细分 / 独特价值主张 / 解决方案 / 渠道 / 收入来源 / 成本结构 / 关键指标 / 不公平优势。

### 关键假设清单

按“重要性 × 不确定性”排序，优先验证右上角的假设。每个假设写成可证伪的句子，并配对：

- 验证方式（访谈、落地页、预售、手动服务）
- 成功标准（数量、比例、金额）
- 截止时间

### 决策对比表

列：选项、满足的目标、主要风险、成本、可逆性、推荐理由。

## 4. 收尾模板

```text
本次产出
- 结论：…
- 决策：…
- 新增待办：…
- 待验证假设：…

未决问题
- …

下次接续点
- 从哪个问题开始，需要带什么材料
```

## 5. 示例

用户：我想做面向小团队的 AI 知识库。

顾问：先确认一下，你说的“小团队”大概多少人？他们现在把知识放在哪里？

（用户回答后）

顾问：这个方向可以，但先别急着做产品。有三条路径：A 直接做通用工具；B 针对技术团队做深度集成；C 先做人工服务验证需求。我建议 C，因为两周内就能拿到付费信号。你更担心哪一条的风险？

## 6. 反例

- 一次问五个问题，用户无从回答。
- 只给鼓励，不指出风险。
- 把用户的猜测当成事实写进项目档案。
- 讨论结束没有结论、没有待办、没有下次接续点。
```

- [ ] **Step 5: 编写 `references/data-model.md`**

Create `.claude/skills/startup-advisor/references/data-model.md`:
```markdown
# 数据模型

所有文件使用 UTF-8 和 `\n`。frontmatter 是简单 YAML 子集，只使用单行 `key: value`。

## 目录

- `ventures/profile.md`：个人档案，全项目唯一。
- `ventures/.state.json`：`{"version": 1, "active": "<相对路径>", "updated": "<ISO 时间>"}`。
- `ventures/_inbox/<想法>/IDEA.md`：未立项想法。
- `ventures/<项目>/PROJECT.md`：正式项目主档。
- 每个目标的 `discussions/`、`todos.md`、`decisions.md`、`assets/`。

## PROJECT.md frontmatter

`name`、`stage`、`one_liner`、`created`、`updated`、`next_action`。

`stage`：`idea` / `validating` / `building` / `operating` / `paused` / `archived`。

## IDEA.md frontmatter

`title`、`created`、`updated`、`status`。

`status`：`incubating` / `promoted` / `archived`。

## 讨论纪要

路径：`<目标>/discussions/YYYY-MM-DD-<标题>.md`。

frontmatter：`title`、`date`、`target`、`status`、`next_step`。

- `target` 是相对 `ventures/` 的路径，例如 `AI-知识库` 或 `_inbox/宠物社交`。
- `status: open` 表示下次启动需要续接；`closed` 表示讨论结束。

## 待办

文件：`<目标>/todos.md`，分为 `## 进行中` 和 `## 已完成`。

行格式：

```text
- [ ] [P1] 动作描述 — 📅 2026-10-27 `id:t-20261020-001` — 来源：discussions/xxx.md
```

- ID 在目标内唯一。
- 完成项改 `[x]`，移动到已完成区，并追加 `— 完成于 YYYY-MM-DD`。
- 不删除待办；确实不做时改写文本或标记完成。

## 决策记录

文件：`<目标>/decisions.md`。每条包含决定、备选、理由、影响、来源。

## 手改注意事项

- 保留 frontmatter 的 `---` 包围结构。
- 不要修改待办 ID；需要新待办时用 `ADVISOR todo add`。
- 项目/想法目录名是稳定 ID，改名请改 frontmatter，不要手动移动目录。
```

- [ ] **Step 6: 运行测试，确认通过**

Run:
```bash
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_skill_docs.py" -v
```
Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add .claude/skills/startup-advisor/SKILL.md .claude/skills/startup-advisor/references .claude/skills/startup-advisor/tests/test_skill_docs.py
git commit -m "docs: 添加创业顾问技能协议与参考手册

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: 端到端验收与真实工作区初始化

**Files:**
- Modify: 无（只运行与验证）

**Interfaces:**
- Consumes: 全部前序任务
- Produces: 可交付的工作区与验收证据

- [ ] **Step 1: 运行全套自动化测试**

Run:
```bash
cd /c/src/xinyu/project
python -m unittest discover -s .claude/skills/startup-advisor/tests -v
```
Expected: PASS，0 failures，0 errors。

- [ ] **Step 2: 在临时目录跑完整用户流程**

Run:
```bash
TMP=$(mktemp -d)
ADV="python .claude/skills/startup-advisor/scripts/advisor.py --root $TMP"
$ADV init
$ADV idea new --title "宠物社交" --one-liner "同城宠物主人社交"
$ADV note new "宠物社交" --title "需求验证"
$ADV todo add "宠物社交" --text "访谈 5 位宠物主" --priority P1
$ADV resume --json
$ADV project promote "宠物社交" --json
$ADV project list
$ADV doctor
rm -rf "$TMP"
```
Expected:
- `init` 输出创建项；
- `idea new` 创建 `_inbox/宠物社交`；
- `resume --json` 中出现该想法/其待办；
- `promote` 后 `_inbox/宠物社交` 不存在，`ventures/宠物社交` 存在；
- `doctor` 输出“自检通过，未发现问题。”。

- [ ] **Step 3: 初始化真实工作区**

Run:
```bash
python .claude/skills/startup-advisor/scripts/advisor.py init
python .claude/skills/startup-advisor/scripts/advisor.py doctor
```
Expected: 创建 `ventures/profile.md` 与 `ventures/.state.json`；`doctor` 通过。不要在这一步创建示例项目或想法。

- [ ] **Step 4: 确认技能可被发现**

Run:
```bash
ls .claude/skills/startup-advisor/SKILL.md
```
Expected: 文件存在。Claude Code 通常需要重启会话才能发现新技能；完成后提示星辰重载，再输入 `/startup-advisor` 验证。

- [ ] **Step 5: 确认工作区干净**

```bash
git status --short
```
Expected: 无未提交的 skill/文档改动；`ventures/` 不出现在输出中（已被忽略）。

---

## 计划自查

- 规格覆盖：目录/数据模型（Task 1-7）、唯一入口与续接（Task 6、8、9）、临时区与转正（Task 2-3）、待办（Task 4）、决策（Task 5）、个人档案（模板 + SKILL.md）、自动命名（Task 1）、多项目（Task 2）、测试与验收（各任务 + Task 10）。
- 无占位符：每个代码步骤给出完整实现或完整测试。
- 类型/命名一致：`Workspace`、`target` dict 键、`collect_resume`、`checkpoint`、`promote_idea` 在各任务间保持一致。
- 已知取舍：不做 hook；记录可靠性依赖 SKILL.md 的增量写入规则和 `checkpoint`。

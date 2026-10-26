# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

这不是一个常规应用，而是一个 **Claude Code 项目技能**：`startup-advisor`（创业顾问）+ `execution-assistant`（执行助手 subagent）。仓库同时承载技能定义、数据模型说明、模板、确定性 CLI 和用户数据目录 `ventures/`（gitignored，私人内容）。

- 顾问留在主对话，负责访谈、判断、记忆维护和派发。
- 执行助手是独立 subagent，只对 brief 负责，产出正式方案与文案，不与用户直接对话。
- 所有用户内容为中文；修改技能行为、模板和文档时也应使用中文。

## 常用命令

```bash
# 运行全部测试（Python 3.10+，当前环境 3.14.6）
python -m unittest discover -s .claude/skills/startup-advisor/tests -v

# 只跑某个测试文件
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_cli.py" -v

# 只跑单个用例
python -m unittest discover -s .claude/skills/startup-advisor/tests -p "test_cli.py" -k test_init_migrates_legacy_profile -v

# 技能 CLI（必须在项目根目录执行）
python .claude/skills/startup-advisor/scripts/advisor.py init
python .claude/skills/startup-advisor/scripts/advisor.py context --json
python .claude/skills/startup-advisor/scripts/advisor.py validate
```

没有 pyproject、requirements 或第三方依赖，只用 Python 标准库。`advisor.py` 也支持 `--root <项目根>`，测试即通过它指向临时目录。

## 架构

四层，改动任何一层都要保持契约一致：

1. **协议层** — `.claude/skills/startup-advisor/SKILL.md`：顾问身份、顾问档/参谋档切换、启动、记录规则、收尾、执行流水线。这是技能运行时真正遵循的行为规范，不是普通 README。
2. **执行层** — `.claude/agents/execution-assistant.md`：执行助手的输入（必须读 brief、`writing-style.md`、当前方向 `PLAN.md`、memory-model、execution-playbook）、输出格式（`outputs/` 版本文件）、`BLOCKED` 返回格式和边界。
3. **数据层** — `ventures/` 下的 Markdown。三层结构：
   - 创始人层：`ventures/me/`（`profile.md`、`self.md`、`writing-style.md`、`insights.md`）
   - 组合层：`ventures/portfolio.md`（`main` / `incubating` / `archived` 的唯一事实源）
   - 方向层：`ventures/<方向>/`（`PLAN.md` 活方案、`notes/`、`briefs/`、`outputs/`，可选 `decisions.md`、`TODO.md`）
4. **工具层** — `scripts/advisor.py`：只有 `init` / `context` / `validate` 三个确定性命令，其余编辑由模型按模板完成。

支撑文件：`references/` 是顾问方法、执行方法和数据模型手册；`templates/` 是各类数据文件的骨架，`init` 直接复制它们。

### 顾问 → 执行助手流水线

1. 顾问判断需要正式产出，补齐 brief 字段（目标、读者与渠道、交付物、必须包含、不能出现、文风、参考材料、验收标准、截止时间）。
2. `briefs/YYYY-MM-DD-<主题>.md` 是唯一交接接口；执行助手看不到对话，brief 必须能独立说明任务。
3. 优先派发 `subagent_type: execution-assistant`；未发现时退回 `general-purpose` 并要求先完整读取 agent 定义。
4. 执行助手写 `outputs/YYYY-MM-DD-<主题>-vN.md` 并返回交接信息；`BLOCKED` 时由顾问补 brief，不由顾问代写交付物。
5. 顾问按 brief 和 `writing-style.md` 验收，不直接把初稿转交用户。

## 关键约束

- **portfolio 是唯一事实源**：每个方向目录必须且只能出现在 `main` / `incubating` / `archived` 之一；不使用 `.state.json`（遗留文件仅告警）。
- **frontmatter 是简单 YAML 子集**：只允许单行 `key: value`，逗号分隔列表；UTF-8（读入兼容 BOM）、`\n` 换行。
- **模板占位符**：`templates/` 里的 `{{NAME}}` 等必须在实例化时替换，`validate` 会拒绝残留的 `{{` / `}}`。
- **输出只增不改**：新稿用递增 `version`，不覆盖旧文件；`validate` 校验 `brief` 引用存在且 `version >= 1`。
- **归档不删数据**：方向归档通过 `stage: archived` + `portfolio.md` 登记完成，不移动或删除目录。
- **命名**：方向目录名去掉 Windows 非法字符、逗号、控制字符、首尾空白/点，最长 48 字符；目录名是稳定 ID，改显示名只改 `PLAN.md` 的 `name`。文件名统一 `YYYY-MM-DD-<主题>`。
- **顾问不越界**：不写正式交付物、不替用户拍板、不编造证据、不把猜测写成已确认；敏感信息只进 `ventures/me/`。
- **`ventures/` 是用户私人数据**：不要提交、不要在测试中改写它。所有测试用 `tempfile` 建临时工作区（见 `tests/helpers.py`）。
- **Windows 中文输出**：`advisor.py` 通过 `configure_stdio()` 把 stdout/stderr 切到 UTF-8，新增 CLI 输出时保持这一约定。

## 修改文档或模板时的陷阱

`tests/test_docs.py` 是对文档本身的结构测试，改 `SKILL.md`、`templates/`、`references/` 或 agent 定义时这些测试会失败，需同步更新：

- `SKILL.md` 必须包含 `顾问档`、`参谋档`、`brief`、`execution-assistant`、`init`/`context`/`validate`、`按需访谈`、`收尾`、`BLOCKED`、`项目根目录`，且不得出现已移除的 `resume`、`doctor`、`_inbox` 等字样。
- 模板的固定章节标题被逐个断言（例如 `PLAN.md` 的「关键假设与证据」、`note.md` 的「未决问题」）；调整章节结构要连带更新 `TEMPLATE_HEADINGS`。
- 旧设计文件不得复活：`conversation-guide.md`、`data-model.md`、`templates/IDEA.md`、`PROJECT.md`、`discussion.md`。

`docs/superpowers/specs/` 与 `plans/` 是历史设计与实施记录，不是当前行为的事实源；当前设计以 `2026-10-26-startup-advisor-redesign-design.md` 为准。`.superpowers/` 已被 gitignore，属于过程产物。

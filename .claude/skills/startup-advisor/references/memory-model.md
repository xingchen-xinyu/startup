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
顾问档写 mode: coach；参谋档写 mode: exec；同一次讨论两者都有时写 mode: mixed。

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

执行助手只读：brief、`writing-style.md`、当前方向 `PLAN.md`、本文件、`references/execution-playbook.md`、brief 点名的材料。

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

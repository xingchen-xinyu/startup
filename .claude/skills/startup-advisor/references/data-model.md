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

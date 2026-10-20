# 数据模型

所有文件使用 UTF-8 和 `\n`。frontmatter 是简单 YAML 子集，只使用单行 `key: value`。

## 目录

- `ventures/profile.md`：个人档案，全项目唯一。
- `ventures/.state.json`：`{"version": 1, "active": "<相对路径>", "updated": "<ISO 时间>"}`。
- `ventures/_inbox/<想法>/IDEA.md`：未立项想法。
- `ventures/<项目>/PROJECT.md`：正式项目主档。
- 每个目标创建时生成 `discussions/` 与 `assets/`；`todos.md`/`decisions.md` 在首次写入时创建。

`discussions/` 存放讨论纪要，`assets/` 用于存放专项方案。读取时 `todos.md`/`decisions.md` 不存在是正常状态，不要当成数据损坏。

## PROJECT.md frontmatter

`name`、`stage`、`one_liner`、`created`、`updated`、`next_action`。

`stage`：`idea` / `validating` / `building` / `operating` / `paused` / `archived`。

## IDEA.md frontmatter

`title`、`created`、`updated`、`status`。

`status`：`incubating` / `archived`。转正时会复制内容并删除源 `IDEA.md`，因此不保留 `promoted` 状态。

## 转正迁移

`ADVISOR project promote <idea-ref>` 将 `_inbox/<想法>/` 复制为新项目目录，并完成以下转换：

- `IDEA.md` → `PROJECT.md`；想法的标题与一句话介绍映射为项目的 `name` 和 `one_liner`。
- 原想法的正文保留在 `PROJECT.md` 的 `## 想法起源` 节。
- `discussions/`、`assets/` 等历史内容原样保留；讨论纪要 frontmatter 的 `target` 更新为新项目目录（如 `_inbox/宠物社交` → `宠物社交`）。
- 若缺少 `todos.md` / `decisions.md`，转正时初始化为空文件。
- `ventures/.state.json` 的 `active` 指向新项目。
- 源 `_inbox/<想法>/` 目录随后删除，历史内容已随复制保留。

## 讨论纪要

路径：`<目标>/discussions/YYYY-MM-DD-<标题>.md`。

frontmatter：`title`、`date`、`target`、`status`、`next_step`。

- `target` 是相对 `ventures/` 的路径，例如 `AI-知识库` 或 `_inbox/宠物社交`。
- `status: open` 表示下次启动需要续接；`closed` 表示讨论结束。
- `next_step` 为空时，`resume` 会回退读取正文 `## 下一步` 节的第一条。

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

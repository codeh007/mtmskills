---
name: gomtm-skills-improve
description: Use when editing, refactoring, reviewing, or standardizing gomtm skill documents, references, templates, scripts, examples, or trigger descriptions.
---

# gomtm Skills Improve

## 核心原则

技能文档是可复用入口，不是一次性任务报告。正文保持短、准、可触发；长说明放 `references/`，可复制配置放 `templates/`，可执行验证放 `scripts/`。

## 必做流程

1. 先读目标 `SKILL.md`、关联 `references/`、`templates/`、`scripts/`，再改。
2. 对照真实源码、官方文档、仓库 README、用户指出的问题，确认问题确实存在。
3. 优先最小修改；只有结构已承载不了时才重构。
4. 去重：同一事实只保留一个权威位置，`SKILL.md` 只摘要并链接。
5. 保持路径可移植：技能内引用用 `references/...`、`templates/...`、`scripts/...`；跨仓库路径用仓库相对路径或 `<repo>/...`，避免机器绝对路径。
6. 修改后运行仓库提供的技能校验和发现命令；若失败来自无关旧问题，精确报告 blocker。

## 写作规则

- frontmatter `description` 只写触发条件，不写流程总结。
- 技能正文面向专家：给判断规则、关键命令、坑点；不要解释显而易见的背景。
- 一个完整正确例子优于多个碎片例子。
- 模板必须能作为完整起点；用注释表达可选分支，避免多个互相矛盾模板。
- 示例使用 `<service>`、`<host>`、`<repo>`、`SERVICE="..."` 等占位符；只有稳定 canonical 事实才写真实项目名。
- 不把一次性域名、端口、账号、绝对路径、临时输出固化为技能规则。

## 取舍规则

| 内容 | 放置位置 |
| --- | --- |
| 触发条件、边界、最短流程、常见坑 | `SKILL.md` |
| 长排障说明、架构背景、深入解释 | `references/*.md` |
| 可复制配置、env、提示词、清单 | `templates/*` |
| 可重复执行的检查或迁移 | `scripts/*` |

若 `SKILL.md` 与模板/引用重复，保留更权威的一处：配置细节进模板，排障细节进 reference，正文只写“使用哪个文件”和关键注意事项。

## 验证

优先使用仓库脚本；在 mtmskills 仓库通常运行：

```bash
bash scripts/validate-skills
npx skills add . --list
```

同时检查目标技能是否能被发现、frontmatter 名称与目录一致、引用文件存在、模板语法可解析、脚本可执行且不泄露 secret。

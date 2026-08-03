---
name: gomtm-skills-improve
description: Use when maintaining gomtm skills, including creating, revising, reviewing, or validating SKILL.md files, trigger descriptions, references, templates, assets, scripts, examples, or agent metadata.
---

# gomtm Skills Improve

## 要求

1. 使用`writing-great-skills`技能.

## 内容的权威位置

| 内容 | 权威位置 | 质量契约 |
| --- | --- | --- |
| 调用条件与分支 | frontmatter `description` | 只写触发；一个真实分支一个条件 |
| 所有分支都需要的步骤、边界和选择规则 | `SKILL.md` | 保持入口化；步骤以完成条件收束 |
| 仅特定分支需要的背景、排障和深入解释 | `references/*.md` | 从 `SKILL.md` 直接指向，并写明读取条件 |
| 可复制配置和交付物起点 | `templates/*` 或 `assets/*` | 提供完整起点；用注释表达可选分支 |
| 重复、脆弱或需要确定性的操作 | `scripts/*` | 明确“执行”或“阅读”；实际运行验证 |
| 技能列表和入口的 UI 元数据 | `agents/openai.yaml` | 与 `SKILL.md` 保持一致；按仓库生成器校验 |

正文面向专家，提供判断规则、关键命令和真实坑点。路径使用 `references/...`、`templates/...`、`scripts/...` 等技能相对形式；跨仓库路径使用仓库相对路径或 `<repo>/...`。示例使用 `<service>`、`<host>`、`<repo>`、`SERVICE="..."` 等稳定占位符，并保留一个完整、正确、可迁移的例子。

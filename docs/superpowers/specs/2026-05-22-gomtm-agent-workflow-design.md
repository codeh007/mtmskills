# gomtm-agent-workflow 技能完善设计

日期：2026-05-22

## 背景

用户希望把“GitHub Issue + Hermes Kanban + 多 Agent + Telegram 审批”的全自动化开发和运行工作流沉淀为 `/workspace/mtmskills/skills/mtmskills/` 下的专用技能，并安装到全局。

已阅读：

- `/workspace/mtmwiki/wiki/reports/2026-05-22_issue-kanban-agent-workflow-memo.md`
- `/workspace/mtmwiki/wiki/raw/todo.md`
- `/workspace/mtmskills/skills/mtmskills/gomtm-agent-workflow/SKILL.md` 草稿
- `/workspace/mtmskills/README.md`

## 目标

完善现有 `gomtm-agent-workflow`，不要新增重复技能。

该技能负责指导 agent 如何组织 gomtm/mtm 系列项目的任务生命周期：

- 从 `todo.md` 文本队列迁移到 GitHub Issues；
- 对提案型 Issue 做执行前规格化评论；
- 通过人类 approval gate 控制是否进入实现；
- 使用 Hermes Kanban 表达执行状态和多 Agent 协作；
- 通过 PR、CI、release、命令输出、线上域名或截图提供验收证据；
- 通过 Telegram / GitHub comment 作为人类控制面。

## 非目标

- 不重复 `gomtm-hermes` 已有的 Hermes Agent 安装、配置、Kanban runtime、dashboard、gateway、Telegram、provider 细节。
- 不实现 webhook、cron、profile 创建脚本。
- 不写过长工作流百科。
- 不把一次性 issue、真实 token、临时域名、临时路径固化为技能规范。

## 方案

采用“短入口 + 单 reference”的结构。

### 主文档

`skills/mtmskills/gomtm-agent-workflow/SKILL.md` 保持简短，覆盖：

- 触发条件；
- Issue / Kanban / PR-CI-Release / Telegram-GitHub comment / mtmwiki reports 的职责边界；
- 默认生命周期；
- approval gate 基本规则；
- webhook / cron / gateway / manual bridge 的现实边界；
- repository routing；
- 验收证据；
- 常见陷阱；
- verification checklist；
- 引用 `references/github-issue-kanban-approval.md`。

### Reference

新增或完善：

`skills/mtmskills/gomtm-agent-workflow/references/github-issue-kanban-approval.md`

内容只承载主文档不适合展开的内容：

- 执行前规格化评论模板；
- approval sync 最小步骤；
- Kanban graph 最小模式；
- bridge 类型对比；
- 幂等与失败处理；
- 最终 Issue 汇总模板。

## 验证

完成后运行：

1. 手工 frontmatter 检查：`name`、`description`、目录匹配、body 非空、description ≤1024。
2. `npx -y skills add . --list` 确认新技能可发现。
3. `gomtm skills link . --dry-run` 预览全局链接。
4. `gomtm skills link .` 安装到全局。
5. 若仓库提供额外验证命令，按仓库真实约定运行；如失败来自无关既有问题，精确报告。

## 自检

- 无 TBD/TODO。
- 范围聚焦单个技能完善，不拆多技能。
- 不重复 Hermes Agent 技能已有内容，只引用。
- 与用户偏好一致：中文、精简、入口导向、实用。

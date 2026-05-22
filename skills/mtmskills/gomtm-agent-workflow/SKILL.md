---
name: gomtm-agent-workflow
description: Use when replacing todo.md with GitHub Issues, coordinating Hermes Kanban, Telegram or GitHub approvals, multi-agent execution, PR/CI evidence, webhook or cron bridges, or diagnosing why an automated gomtm/mtm workflow did not advance.
version: 1.0.0
author: gomtm
license: MIT
metadata:
  hermes:
    tags: [gomtm, github-issues, hermes, kanban, workflow, automation, telegram, multi-agent]
    related_skills: [gomtm-global, gomtm-hermes, github-actions-local, gomtm-skills-improve]
---

# gomtm Agent Workflow

## Overview

本技能是 gomtm/mtm 项目的 Agent-first 任务生命周期入口。核心原则：**Issue 是需求真相，Kanban 是执行状态机，PR/CI/发布物是验收证据，Telegram/GitHub comment 是人类控制面。**

本技能只定义任务如何流转；Hermes Agent 安装、配置、dashboard、gateway、Kanban runtime、Telegram 和 provider 细节使用 `gomtm-hermes`。

## When to Use

- 用户要求从 `todo.md` 迁移到 GitHub Issues、Kanban 或多 Agent 工作流。
- 用户要求执行、规格化、拆解、审批、同步或收尾某个 GitHub Issue。
- 用户通过 Telegram/GitHub comment 表达 `批准执行`、`调整方案`、`暂缓`。
- 用户问为什么评论、label、webhook、cron 或 Kanban task 没有推进。
- 任务需要用 PR、CI、release、命令输出、线上域名或截图作为完成证据。

## Source of Truth Split

- **GitHub Issue**：目标、范围、不做项、验收标准、讨论、批准、PR 链接、关闭状态。
- **Hermes Kanban**：依赖、assignee、running/blocked/done、worker runs、heartbeat、retry、日志。
- **PR / CI / Release**：代码变更、review、自动检查、可安装或可访问产物。
- **Telegram / GitHub comment**：人类最终管理者的确认、调整、暂停。
- **mtmwiki reports**：长期中文报告和决策备忘。

## Default Flow

```text
Issue -> specify/comment -> approval gate -> Kanban execution -> review -> evidence summary
```

1. 读取或创建 GitHub Issue。
2. 提案型 Issue 先写执行前规格化评论：目标、范围、不做项、风险、方案、验收。
3. 创建 blocked approval gate；人类明确回复前不启动 implementer。
4. 批准后记录 approval URL/text，推进 Kanban graph。
5. Worker 产出 PR-ready diff、验证命令和用户可见证据。
6. Reviewer 独立复核；最终把 PR、CI、命令、域名、截图或 release 结果评论回 Issue。

## Required Sub-skills

- Hermes/Kanban 配置、dashboard、gateway、Telegram、provider：使用 `gomtm-hermes`。
- GitHub Actions 本地复现：使用 `github-actions-local`。
- 技能文档维护：使用 `gomtm-skills-improve`、`writing-skills`。
- 代码开发、调试、review：按任务类型加载对应 gomtm / GitHub / Superpowers 技能。

## Approval Gate Rules

- `批准执行`：同步 Issue label、记录 approval URL/text、complete gate、dispatch 后续任务。
- `调整方案`：更新规格化评论或补充 comment，不进入实现。
- `暂缓`：保持 gate blocked，并说明等待条件。
- 没有明确批准时，不能把“基本同意”“看起来可以”当作授权实现。
- GitHub comment 不会自动触发 Kanban；必须存在 webhook、cron/poller、gateway dispatcher 或人工同步 bridge。

## Repository Routing

- Go runtime、CLI、数据库、device/runtime：`codeh007/gomtm`。
- Next.js dashboard、Web UI、用户可访问页面：`codeh007/gomtmui`。
- Python CLI、FastAPI、Hermes embedded gateway、设备编排：`codeh007/mtmai`。
- 私有知识库、长期报告、raw 迁移：`codeh007/mtmwiki`。
- 私有技能源码：`codeh007/mtmskills`。
- 跨仓任务：创建 umbrella issue，再为实际改动仓库创建 child issues。

## Acceptance Evidence

“代码已改”不是完成证据。按任务类型回写至少一种用户可验证证据：

- PR URL 与 review 结论；
- CI run URL 或本地验证命令输出；
- release artifact、安装命令或可执行命令输出；
- 可访问域名、Playwright/截图/健康检查；
- Issue 最终评论中的验证摘要和遗留风险。

## Common Pitfalls

1. **跳过 specify。** 提案型 Issue 必须先规格化并等待批准。
2. **把 GitHub label 当执行状态机。** Label 便于扫描，执行细节仍在 Kanban。
3. **以为评论会魔法触发。** 没有 bridge 时，评论只是审批事实。
4. **重复 dispatch。** approval sync 必须幂等，记录 approval URL 和 gate 状态。
5. **无验收产物。** 最终结果必须能被人类从 Issue/PR/CI/域名/命令输出看到。

## Verification Checklist

- [ ] Issue 有目标、范围、不做项、验收标准。
- [ ] 提案型任务已有 specify comment。
- [ ] approval gate 状态与人类评论一致。
- [ ] Issue label 与 Kanban 状态不冲突。
- [ ] Dispatcher 已 spawn 预期 profile，或明确说明未启动原因。
- [ ] 最终评论包含 PR/CI/命令/域名/截图/release 等证据。

详细模板和命令片段见 `references/github-issue-kanban-approval.md`。

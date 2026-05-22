# GitHub Issue + Kanban Approval

本参考只补充 `gomtm-agent-workflow` 的操作模板。Hermes Kanban、gateway、Telegram、provider 配置细节使用 `gomtm-hermes`。

## Pre-execution Issue Comment

提案型 Issue 先评论，不直接实现：

```markdown
## 执行前规格化

目标：<用 1-3 句复述 issue 要解决什么>

范围：
- <会做的事>

不做：
- <本轮明确不做的事>

风险 / 歧义：
- <需要人类确认或注意的点>

方案：
1. <方案 A>：<取舍>
2. <方案 B>：<取舍>

推荐：<推荐方案和原因>

验收：
- <PR/CI/命令/域名/截图/release 等证据>

请回复：`批准执行` / `调整方案：...` / `暂缓：...`
```

## Approval Sync

发现人类批准后：

1. 确认评论来源可信，且内容包含明确命令。
2. 找到对应 Issue 与 Kanban gate；没有 gate 时先补 specify/gate，不直接实现。
3. 记录 approval URL/text 到 gate comment。
4. 同步 label，例如 `status:needs-spec` -> `status:ready`。
5. complete gate，再 dispatch 或确认 gateway dispatcher 会接手。
6. 回报 spawned task id、Issue URL 和查看命令。

## Minimal Kanban Graph

```bash
hermes kanban boards create <board> --name '<name>' --switch --default-workdir <repo-path>
hermes kanban create '<repo>#<issue-number> specify: 执行前规格化评论' --assignee orchestrator --workspace dir:<repo-path>
hermes kanban create '<repo>#<issue-number> gate: 等待人工批准执行' --assignee orchestrator --parent <spec-task-id> --initial-status blocked
hermes kanban create '<repo>#<issue-number> implement: <summary>' --assignee implementer --parent <gate-task-id> --workspace worktree:<worktree-path>
hermes kanban create '<repo>#<issue-number> review: 独立复核与验收' --assignee reviewer --parent <implement-task-id> --workspace dir:<repo-path>
```

先创建 parent，再创建 child，避免 child 被提前 claim。profile 名称以实际 `hermes profile list` / Kanban assignees 为准。

## Bridge Choices

- **manual**：人类在 Telegram/CLI 指示 Hermes 检查 Issue 并推进。最稳，适合当前阶段。
- **gateway dispatcher**：已有 gateway/dispatcher 持续运行，由 Kanban 状态推动 worker。
- **GitHub webhook**：issue/comment/label event 触发 Hermes。需要外网入口、secret、权限边界。
- **cron/poller**：定期扫描 approvals、blocked tasks、超时 runs。适合 watchdog，不替代事件触发。

没有 bridge 时，GitHub comment 只是事实记录，不会自动推进执行。

## Idempotency

- 同一个 approval URL 只能推进一次。
- gate 已 complete 时，不重复 dispatch；只回报当前状态。
- label 与 Kanban 冲突时，以 Kanban gate/run 为执行真相，修正 label。
- 人类回复 `调整方案` 后，更新规格评论并保持 gate blocked。
- 人类回复 `暂缓` 后，保持 blocked 并写明恢复条件。

## Final Issue Summary

任务完成后评论：

```markdown
## 执行结果

状态：<完成 / 部分完成 / 阻塞>

变更：
- <人类能理解的结果>

证据：
- PR: <url>
- CI: <url 或命令输出摘要>
- 验证: `<command>` -> <result>
- 产物: <release/domain/screenshot/command output>

遗留风险：
- <没有则写“无已知遗留风险”>

下一步：
- <需要人类审批、merge、release 或后续 issue>
```

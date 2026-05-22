# Hermes Persistent Goals (`/goal`)

## 结论

`/goal` 是 Hermes 的持久目标循环：设置目标后，Hermes 会在同一 session 中持续推进，直到目标完成、暂停、清除或达到预算。它适合长任务，不适合一次性问答。

## 使用

```text
/goal <目标>
/goal status
/goal pause
/goal resume
/goal clear
```

追加验收条件：

```text
/subgoal <条件>
/subgoal remove <N>
/subgoal clear
```

`/goal <目标>` 会立即把目标文本作为普通 user turn 排队执行；不需要再发送“开始”。

## 实现要点

- 命令定义在 `hermes_cli/commands.py`；CLI 处理在 `cli.py`，gateway/Telegram 处理在 `gateway/run.py`。
- 核心状态机在 `hermes_cli/goals.py::GoalManager`。
- 状态持久化在 `SessionDB.state_meta`，key 为 `goal:<session_id>`；`/resume` 可恢复。
- 每轮结束后 `GoalManager.evaluate_after_turn()` 使用 `auxiliary.goal_judge` 判断 `done` / `continue`。
- 未完成时生成普通 user-role continuation prompt；不修改 system prompt，不切换 toolset。
- CLI continuation 进入 `_pending_input`；gateway/Telegram continuation 进入 adapter FIFO；真实用户消息优先。
- `/subgoal` 会把额外条件加入 judge prompt 和 continuation prompt，直到所有条件满足才算完成。

## 配置

```yaml
goals:
  max_turns: 20

auxiliary:
  goal_judge:
    provider: <provider>
    model: <fast-json-reliable-model>
```

`goals.max_turns` 是自动继续预算。judge 失败默认按 `continue` 处理；连续返回不可解析 JSON 或预算耗尽时会自动 pause。排障时优先检查 `auxiliary.goal_judge`，不要直接改主模型。

## 判断规则

- 需要 Hermes 自动多轮推进时用 `/goal`。
- 需要中途补充验收标准时用 `/subgoal`。
- 需要停止自动推进但保留目标时用 `/goal pause`。
- 目标已失效或 judge 误判时用 `/goal clear` 后重设更明确目标。

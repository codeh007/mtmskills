# Kanban worker 与 TUI 环境变量

## 结论

在会运行 `hermes gateway run`、Kanban dispatcher、cron、webhook 或任何后台 worker 的主机上，不要在 `$HERMES_HOME/.env`、profile `.env`、systemd environment 或容器通用 env 中默认设置：

```env
HERMES_TUI=1
```

`HERMES_TUI=1` 会让普通 `hermes` 调用偏向交互式 TUI。它适合纯人工交互 shell，不适合非 TTY 后台环境。

## 为什么会破坏 Kanban

官方 Kanban dispatcher 发现 ready + assignee 的任务后，会后台启动 worker，等价于：

```bash
hermes -p <profile> --accept-hooks --skills kanban-worker chat -q "work kanban task <task_id>"
```

worker 依赖 dispatcher 注入的环境变量启用 `kanban_*` 工具：

```env
HERMES_KANBAN_TASK=<task-id>
HERMES_KANBAN_WORKSPACE=<workspace-path>
HERMES_KANBAN_BOARD=<board-name>
```

如果全局 env 里有 `HERMES_TUI=1`，即使命令写的是 `hermes chat -q ...`，也可能被强制进入 TUI 分支。后台 worker 没有 TTY，典型表现是：

```text
hermes-tui: no TTY
```

Kanban 任务会反复出现 `spawned -> crashed`、`protocol_violation` 或被 dispatcher 判定为失败。

## 正确配置

服务/共享主机：

```bash
# 交互式使用时显式进入 TUI
hermes --tui

# 可选：只放在个人 shell profile 中，不写入 Hermes .env
alias h='hermes --tui'
```

如果需要检查并清理 Hermes env：

```bash
env_path="$(hermes config env-path)"
grep -n '^HERMES_TUI=1$' "$env_path" || true
# 如存在，改成注释或删除：
# HERMES_TUI=1  # disabled: breaks non-TTY Kanban/cron/background workers
```

Kanban / cron / worker smoke test：

```bash
HERMES_TUI=0 hermes chat -q '只输出 OK'

HERMES_TUI=0 \
HERMES_KANBAN_TASK=t_debug \
HERMES_KANBAN_WORKSPACE=/tmp/hermes-kanban-debug \
HERMES_KANBAN_BOARD=kanban-debug \
hermes -p default chat -q '只输出 OK'
```

如果以上命令在无 TTY 环境输出 OK，说明非交互路径可用。

## 何时可以使用 HERMES_TUI=1

只在纯个人交互机器或只在交互 shell profile 中使用。不要把它写进会被 gateway、cron、Kanban dispatcher、CI、systemd service、容器 entrypoint 或脚本继承的 Hermes `.env`。

# Hermes Kanban 运行入口与 Dashboard 关系

## 结论

使用 Kanban 不必须启动：

```bash
hermes dashboard --no-open
```

`hermes dashboard` 是本地 Web UI / 可视化操作入口。它方便人类查看和操作 Kanban，但不是 Kanban 数据层、CLI、slash command 或 worker tool 的前置服务。

## 必须区分的进程

- `hermes kanban ...`：人类和脚本的 CLI 入口，直接读写官方 Kanban DB。
- `/kanban ...`：gateway 平台中的 slash command 入口，仍读写同一 Kanban DB。
- `kanban_*` tools：dispatcher-spawned worker / orchestrator profile 使用的模型工具。
- `hermes gateway run|start`：启动 messaging gateway；默认同时承载 Kanban dispatcher。
- `hermes dashboard`：启动 Web UI；只提供浏览器界面和 dashboard plugin host。

## 什么时候需要 gateway

如果只创建、查看、评论、block/unblock、complete Kanban task，可以不运行 dashboard；CLI 仍可工作。

如果希望 `ready` task 自动被分配给 assignee profile 执行，需要 dispatcher 在线。默认配置下 dispatcher 嵌在 gateway 中：

```yaml
kanban:
  dispatch_in_gateway: true
```

因此常规启动方式是：

```bash
hermes gateway start
```

没有 gateway / dispatcher 时，task 可以存在于 board 中，但 `ready` task 会停留等待，不会自动 spawn worker。

## 不推荐的旧路径

`hermes kanban daemon --force` 是旧 standalone dispatcher 逃生口。只有无法运行 gateway 时才考虑。不要让 gateway 内嵌 dispatcher 和 standalone daemon 同时操作同一个 `kanban.db`。

## gomtm / mtmai / gomtmui 判断规则

- 不要把 Kanban 是否可用绑定到 `hermes dashboard` 是否运行。
- gomtmui 的 Kanban 页面只是 host adaptation；核心状态以官方 Kanban DB/API 为准。
- Telegram bot 使用 Kanban 依赖 gateway 在线；这与 dashboard 无关。
- 排查“任务不执行”优先查 gateway/dispatcher、assignee profile、worker env 和 logs，而不是要求用户启动 dashboard。

# Hermes Kanban + gomtmui Web UI 对齐参考

## 触发场景

用户要求 gomtmui 的 `/dash/hermes` 与最新版官方 Hermes Web UI 对齐，尤其涉及 Kanban、dashboard plugin、gateway dispatcher、mtmai embedded gateway 或 selected gomtm server 边界时，使用本参考。

## 关键结论

1. `hermes gateway run` 启动 messaging gateway、cron scheduler 与默认内嵌 Kanban dispatcher。
2. 官方 Web UI 入口是 `hermes dashboard`。
3. Kanban 是官方 Hermes bundled dashboard plugin，manifest 形态包括：
   - name: `kanban`
   - label: `Kanban`
   - tab path: `/kanban`
   - position: `after:skills`
   - entry/css: `dist/index.js` / `dist/style.css`
   - API: `plugin_api.py`
4. gomtm / mtmai / gomtmui 的职责是 host adaptation。业务真相继续属于官方 `hermes-agent`：`kanban_db`、`plugin_api.py`、gateway dispatcher、worker `kanban_*` tools、`~/.hermes/kanban*.db`。

## 推荐对齐路径

### 1. mtmai API surface

官方 Kanban API mount：

```text
/api/plugins/kanban/*
```

gomtmui selected server 下推荐 mtmai 暴露受保护代理：

```text
/api/hermes/plugins/kanban/* -> official /api/plugins/kanban/*
```

WebSocket：

```text
/api/hermes/plugins/kanban/events?token=...&board=...
  -> /api/plugins/kanban/events?token=...&board=...
```

### 2. gomtmui plugin/nav

- `/dash/hermes/kanban` 来自 plugin tab `/kanban`，按 `position: after:skills` 插在 Skills 后。
- `/dash/hermes` root 对齐官方 root 行为。
- route、nav、selected server token、plugin runtime 由 gomtmui host 负责。

### 3. 官方 bundle 优先

先验证官方 Kanban dashboard bundle 是否可通过 gomtmui dashboard plugin SDK 运行：

- bundle 可注册时复用官方 bundle。
- SDK 能力缺失时补最小通用 SDK。
- 需要本地页面时，API 和行为按官方 `plugin_api.py`。

### 4. 本地页面功能基线

- board list/create/switch/archive
- columns: `triage`, `todo`, `scheduled`, `ready`, `running`, `blocked`, `review`, `done`; `archived` toggle
- create/edit task, comment, block/unblock, complete, archive/delete, reclaim/reassign
- links/dependency editor
- run history, events timeline, worker log
- orchestration settings: `auto_decompose`, `orchestrator_profile`, `default_assignee`
- specify/decompose
- `/events` WebSocket live refresh with board + token
- gateway stopped / dispatcher disabled / missing profile / missing token clear empty states

## 安全要求

1. 所有 Kanban writes 带 selected gomtm server 对应的 `X-Hermes-Session-Token`。
2. Kanban events WebSocket 带 `?token=`，token 与 selected server origin 匹配。
3. 远程 gomtmui 将 task body、comments、run metadata、logs 作为敏感数据处理。
4. 删除 board、archive、bulk complete/block 等危险动作需要二次确认。

## 文档产物

针对这类需求，优先写 superpowers 文档：

- 规格：`docs/superpowers/specs/YYYY-MM-DD-hermes-latest-web-ui-kanban-parity-design.md`
- 计划：`docs/superpowers/plans/YYYY-MM-DD-hermes-latest-web-ui-kanban-parity-plan.md`

计划包含 mtmai proxy tests、gomtmui API/types/nav/page tests、官方 bundle 可加载性决策点、fallback 页面任务拆分、`bun run check` 与 mtmai focused pytest。

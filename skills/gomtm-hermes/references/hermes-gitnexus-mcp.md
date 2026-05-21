# Hermes + GitNexus MCP 速查

## 结论

Hermes 稳定使用 GitNexus，需要同时满足：

1. 目标 repo 已执行 `npx -y gitnexus@latest analyze`。
2. Hermes 已通过 `mcp_servers.gitnexus` 连接 `npx -y gitnexus@latest mcp`。
3. 目标 repo 的 `AGENTS.md` / `CLAUDE.md` 写明 GitNexus 规则。

MCP 只提供工具；规则仍写在 context file 中。

## 最短流程

```bash
cd <repo-root>
npx -y gitnexus@latest analyze
hermes mcp add gitnexus --command npx --args -y gitnexus@latest mcp
hermes mcp test gitnexus
hermes  # with HERMES_TUI=1 in ~/.hermes/.env, this opens the TUI
```

GitNexus 常用工具：`query`、`context`、`impact`、`detect_changes`、`rename`、`cypher`。

## Hermes 配置

```yaml
mcp_servers:
  gitnexus:
    command: npx
    args: [-y, gitnexus@latest, mcp]
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: true
```

## 规则注入

Hermes 会加载 `AGENTS.md` / `CLAUDE.md`，但要满足：

- 不使用 `--ignore-rules`
- CLI 从 repo 根目录启动
- gateway / service / TUI 场景设置 `TERMINAL_CWD=<repo-root>`
- 改配置后开新 session；gateway 场景 restart

目标 repo 的 `AGENTS.md` / `CLAUDE.md` 可写成：

```markdown
<!-- gitnexus:start -->
# GitNexus — Code Intelligence

Use GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` first.

## Always Do
- Run impact analysis before changing a function, class, method, or exported symbol.
- Run detect-changes before committing.
- Use query for unfamiliar code.
- Use context for full symbol context.

## Never Do
- Edit symbols before impact analysis.
- Rename with plain find-and-replace when GitNexus rename is available.
- Ignore HIGH or CRITICAL warnings.
<!-- gitnexus:end -->
```

`hermes gateway run` 场景同样设置：

```bash
TERMINAL_CWD=<repo-root> hermes gateway run
```

## 验证

```bash
cd <repo-root>
npx -y gitnexus@latest status
hermes mcp list
hermes mcp test gitnexus
```

进入 Hermes 后，用 `query` 或 `context` 确认能看到目标 repo。

## 常见问题

- **规则不生效**：检查 repo 根目录和 `TERMINAL_CWD`。
- **找不到 repo**：重新 `npx -y gitnexus@latest analyze`。
- **启动慢**：把 MCP `command` 改成全局 `gitnexus` 或绝对路径。
- **索引过时**：重新 analyze。

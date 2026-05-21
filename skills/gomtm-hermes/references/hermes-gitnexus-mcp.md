# Hermes + GitNexus MCP 开发者配置

## 目标

让 Hermes Agent 在开发代码仓库时稳定使用 GitNexus 的知识图谱能力，避免只靠 grep 或模型猜测调用链、影响范围和执行流程。

正确配置需要三层同时成立：

1. **索引层**：目标代码仓库已由 GitNexus 分析并注册。
2. **工具层**：Hermes 已通过 MCP 连接 GitNexus server。
3. **规则层**：Hermes system prompt 已注入目标仓库的 `AGENTS.md` / `CLAUDE.md`，其中写明 GitNexus 的使用规则。

MCP 只提供工具；项目规则仍应写在 context file 中。

## GitNexus 官方主线

GitNexus npm 包是 `gitnexus`，官方推荐 CLI + MCP 方式：

```bash
# 在目标 repo 根目录执行
npx -y gitnexus@latest analyze

# 查看当前 repo 索引状态
npx -y gitnexus@latest status

# 查看全局 registry 中的 repo
npx -y gitnexus@latest list

# 启动 stdio MCP server
npx -y gitnexus@latest mcp
```

`gitnexus analyze` 会在 repo 内生成 `.gitnexus/` 索引，并在 `~/.gitnexus/registry.json` 注册。一个 GitNexus MCP server 可以服务多个已注册 repo；当只索引了一个 repo 时，很多工具的 `repo` 参数可以省略。多个 repo 时应显式传 repo 名。

GitNexus MCP 主要提供：

- `list_repos`：列出已索引仓库。
- `query`：按概念搜索执行流程和相关代码。
- `context`：查看符号的 callers、callees、参与流程等上下文。
- `impact`：分析修改某符号的上游/下游影响范围。
- `detect_changes`：把当前 git diff 映射到符号和受影响流程。
- `rename`：基于图谱辅助多文件重命名。
- `cypher`：执行底层图查询。

## Hermes MCP 配置

Hermes 读取 `~/.hermes/config.yaml` 的 `mcp_servers`：

```yaml
mcp_servers:
  gitnexus:
    command: npx
    args:
      - -y
      - gitnexus@latest
      - mcp
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: true
```

也可使用 CLI 写入：

```bash
hermes mcp add gitnexus --command npx --args -y gitnexus@latest mcp
hermes mcp test gitnexus
hermes mcp list
```

如果目标机器已全局安装 GitNexus，可把 command 改成绝对路径或 `gitnexus`，减少 `npx` 冷启动成本：

```yaml
mcp_servers:
  gitnexus:
    command: gitnexus
    args: [mcp]
    timeout: 180
    connect_timeout: 30
```

## Hermes context files 加载条件

Hermes Agent 会把 context files 注入 system prompt，包括 `AGENTS.md`、`CLAUDE.md`、`.cursorrules` 等。该行为有条件：

1. 不能使用 `--ignore-rules`，因为它会跳过 context files。
2. CLI 场景从目标仓库根目录启动 Hermes，或确保当前 cwd 能向上找到目标 context files。
3. gateway / service / TUI 嵌入场景设置 `TERMINAL_CWD=<repo-root>`，让 Hermes 从目标项目根目录发现 context files。
4. 修改 `AGENTS.md` / `CLAUDE.md` 或 MCP 配置后，开启新 session；gateway 场景执行 restart。

开发者配置只添加 MCP 工具还不够。需要目标 repo 的 `AGENTS.md` / `CLAUDE.md` 明确 GitNexus 规则，例如：

```markdown
<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **<repo-name>**. Use GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- Before modifying a function, class, method, or exported symbol, run impact analysis and report direct callers, affected processes, and risk level.
- Before committing, run detect-changes to verify the changed symbols and affected execution flows match the intended scope.
- When exploring unfamiliar code, use query to find process-grouped execution flows.
- When full symbol context is needed, use context to inspect callers, callees, and process participation.

## Never Do

- Edit a function, class, method, or exported symbol before impact analysis.
- Rename symbols with plain find-and-replace when GitNexus rename is available.
- Ignore HIGH or CRITICAL impact warnings.
<!-- gitnexus:end -->
```

## 推荐开发者初始化流程

```bash
cd <repo-root>

# 1. 建立或刷新索引
npx -y gitnexus@latest analyze
npx -y gitnexus@latest status

# 2. 配置 Hermes MCP
hermes mcp add gitnexus --command npx --args -y gitnexus@latest mcp
hermes mcp test gitnexus

# 3. 从 repo 根目录启动 Hermes，确保 AGENTS.md / CLAUDE.md 注入
hermes
```

gateway / systemd / Docker 场景：

```bash
TERMINAL_CWD=<repo-root> hermes gateway run
```

systemd unit 可使用：

```ini
Environment=TERMINAL_CWD=<repo-root>
WorkingDirectory=<repo-root>
```

Docker / Compose 可使用：

```yaml
environment:
  TERMINAL_CWD: /workspace/<repo-name>
working_dir: /workspace/<repo-name>
volumes:
  - <repo-root>:/workspace/<repo-name>
```

## 验证清单

```bash
cd <repo-root>
npx -y gitnexus@latest status
npx -y gitnexus@latest list
hermes mcp list
hermes mcp test gitnexus
hermes chat --quiet --toolsets terminal,file -q '只回复 OK'
```

进入 Hermes 会话后，让 agent 使用 GitNexus 查询一个明确概念或符号，确认工具可见且返回目标 repo 信息。

## 常见问题

1. **MCP 已配置但 agent 不遵守 GitNexus 规则。** 检查 Hermes 是否从 repo 根目录启动，或 gateway 是否设置 `TERMINAL_CWD`；MCP 不会替代 `AGENTS.md` / `CLAUDE.md` 中的行为规则。
2. **工具返回找不到 repo。** 在目标 repo 根目录重新执行 `npx -y gitnexus@latest analyze`，再运行 `npx -y gitnexus@latest list`。
3. **启动很慢。** 全局安装 `gitnexus`，并把 MCP `command` 改为 `gitnexus` 或绝对路径，避免每次 `npx` 冷启动。
4. **索引过时。** 重新执行 `npx -y gitnexus@latest analyze`；大仓库可按 GitNexus 官方说明调整 worker / timeout 环境变量。
5. **使用了 `--ignore-rules`。** 该模式会跳过 context files，开发者场景通常不适合用来验证 GitNexus 规则注入。

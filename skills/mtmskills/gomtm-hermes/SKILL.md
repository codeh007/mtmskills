---
name: gomtm-hermes
description: Use when developing, configuring, deploying, debugging, or aligning gomtm, mtmai, gomtmui, mtmhermes, or customer servers with official NousResearch Hermes Agent, including dashboard, gateway, providers, Telegram, Docker, Kanban, and VPS or Termux handoff.
version: 1.1.0
author: gomtm
license: MIT
metadata:
  hermes:
    tags: [gomtm, hermes, mtmai, gomtmui, mtmhermes, deployment, configuration, gateway, kanban]
    related_skills: [gomtm-global, gomtm-skills-improve, hermes-agent]
---

# gomtm Hermes

## 核心原则

官方 Hermes Agent 拥有 provider、model metadata、session store、tools、skills、gateway、Kanban、cron、dashboard plugin 与配置语义。gomtm / mtmai / gomtmui / mtmhermes 只做宿主边界、路径适配、安全代理、页面承载和交付自动化；不要复制或改写官方运行逻辑。

## 何时使用

- 配置、部署、升级、验证或排障 Hermes Agent。
- 将 gomtm、mtmai、gomtmui、mtmhermes 与 Hermes dashboard、gateway、profiles、providers、Telegram、Kanban 对齐。
- 在 Linux VPS、Android/Termux、容器或受控客户环境中交付 Hermes。
- 诊断 Hermes 长任务停止、空回复、provider 鉴权、上下文压缩、gateway、Telegram、dashboard plugin。
- 处理 Hermes `/goal`、`/subgoal`、goal judge 或自动 continuation。

## 官方资料优先

执行前优先核对当前官方文档和本机源码：

- Docs: `https://hermes-agent.nousresearch.com/docs/`
- Configuration: `https://hermes-agent.nousresearch.com/docs/user-guide/configuration`
- Providers: `https://hermes-agent.nousresearch.com/docs/integrations/providers`
- Messaging / Telegram: `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/`
- Kanban: `https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/features/kanban`
- Goals: `https://hermes-agent.nousresearch.com/docs/user-guide/features/goals`
- Releases: `https://github.com/NousResearch/hermes-agent/releases`
- 本机源码：`$HERMES_AGENT_SOURCE`，或 `python -c "import hermes_cli, pathlib; print(pathlib.Path(hermes_cli.__file__).parents[1])"`

## 当前基线

- 官方 `v2026.5.16 / v0.14.0` 支持 PyPI / `uv tool` / `uvx` / installer。
- `custom_providers:` 是自定义 provider 选择器入口；模板使用 `custom_providers` 以便 `custom:<slug>` 选择。
- `config.yaml` 保存结构和 `${VAR}` 引用；`.env` / service env / secret store 保存 secret。
- 新会话或 gateway restart 才会稳定读取配置变化。
- 需要 TUI 时显式运行 `hermes --tui`；不要在共享 `$HERMES_HOME/.env` 默认写 `HERMES_TUI=1`，否则非 TTY worker/cron/gateway 任务会失败。

## gomtm 边界

1. `mtmai`：Python runtime、CLI 转发、`HERMES_HOME` 策略、FastAPI mount、embedded gateway、dashboard token、WebSocket/URL 适配。
2. `gomtm`：宿主入口、容器、反向代理、生命周期、安全边界、声明式部署。
3. `gomtmui`：Next.js host、selected server、session token、页面壳、导航、dashboard plugin runtime、监督界面。
4. `mtmhermes`：专用 Hermes 容器、运行态数据、私有配置、交付脚本。
5. 官方 Hermes：provider、模型路由、credential pool、memory、skills、tools、session DB、Kanban、cron、proxy、gateway。

## 配置模板

只维护一套配置入口：

- `templates/config.yaml`：完整可复制的 `~/.hermes/config.yaml` 起点，包含 custom provider、model alias、compression、secret redaction、skills、auxiliary、可选 GitNexus MCP 注释块。
- `templates/env.example`：完整 `.env` 起点，包含 OpenAI-compatible secret、可选 Telegram、可选 GitNexus 调参注释。

使用规则：

1. 复制模板前先备份真实 `config.yaml` 和 `.env`。
2. 用注释启用可选分支，不新增 default/developer/custom/telegram 分散模板。
3. `context_length` 用 plain integer（如 `1050000`），并在 `model`、`custom_providers[].models`、`model_aliases`、`auxiliary.compression` 中一致。
4. `model.max_tokens` 是单次输出预算，默认模板用 `32768` 降低长工具调用参数被过早截断的概率；它不能解决长上下文下 endpoint 空回复 / 截断问题，必须配合更早的 compression threshold、fallback 或新 session。
5. `security.redact_secrets: true` 保持开启；不要用 `HERMES_REDACT_SECRETS=false` 覆盖。
6. 自定义 OpenAI-compatible endpoint 使用 `OPENAI_BASE_URL` / `OPENAI_API_KEY`。
7. 修改后开新 session；gateway 场景重启 gateway。

## 自定义 provider / 长上下文排障

详见 `references/hermes-long-context-empty-response.md`。快速判断：

```bash
grep -Ei "pending tool result|Empty response|No fallback available|AuthenticationError|context|Provider:|Response truncated" ~/.hermes/logs/errors.log | tail -80
HERMES_TUI=0 hermes chat --quiet -q '只输出 OK'
```

关键事实：

- Hermes 的 `model.context_length` 是总上下文窗口（输入 + 输出），影响上下文压缩和窗口估算；`model.max_tokens` 是单次 assistant 输出预算，长 `tool_calls[].function.arguments` 也算输出。二者不能互相替代。
- `hermes config set model.max_tokens 32768` 是官方 `hermes config set` 写入 `config.yaml` 的标准配置方式，不是 monkey patch；当前源码会在 agent 初始化时读取 `model.max_tokens` 并传给 Chat Completions / Anthropic / Responses transport。
- `Response truncated due to output length limit` 出现在复杂任务中，尤其是一次性生成很长的 `write_file` / `patch` 参数时，先确认 `model.max_tokens` 已设置，再改用分块写入；如果同类错误稳定出现在约 250K-300K 上下文，根因更可能是 custom endpoint 的实际稳定窗口低于配置窗口，需把 `compression.threshold` 调低到触发点之前。
- `compression.threshold` 乘以 `model.context_length` 才是自动压缩触发线。`context_length: 1050000` 且 `threshold: 0.5` 会等到约 525K prompt tokens 才自动压缩；若现场在约 270K 已空回复或截断，应先试 `threshold: 0.25`，或把 `context_length` 临时保守下调到实测稳定窗口。
- Hermes 未知模型或探测失败 fallback 可能显示 `256K` / `256,000`；这不是 gpt-5.5 的推荐窗口。
- 官方/公开元数据确认 gpt-5.5 窗口为 `1050000` 时，模板应填写 `1050000`，不要只改一处。
- `/model` 切到 custom provider 时，官方源码已有回归用例要求读取 `custom_providers[].models.<model>.context_length`，否则会显示 128K/256K fallback。
- `Empty response` + `No fallback available` 通常是模型/中转在长工具链后返回空内容；无 fallback 时 turn 会停在 pending tool result。
- `Provider: openrouter` + 自定义模型名通常是 provider override、默认 provider、alias 或 fallback 配置错误。

必要验证：

```bash
hermes --version
hermes config path
hermes config env-path
hermes config check
hermes doctor
hermes -z "Reply exactly: OK" --provider custom:<provider-slug> --model <model-id> --ignore-rules
hermes -z "Reply exactly: OK" --provider custom --model <model-id> --ignore-rules
```

Provider 原始 HTTP 调试优先用短内联命令，避免维护额外脚本：

```bash
curl -sS -H "Authorization: Bearer <redacted>" "${OPENAI_BASE_URL%/}/models" | python3 -m json.tool | head -80
```

## 用户级 / 外部技能目录

- Hermes 原生技能目录：`${HERMES_HOME:-~/.hermes}/skills`。
- `npx -y skills@latest add <repo> -g -a hermes-agent ...` 安装到 Hermes 原生目录。
- universal 全局目录通常是 `~/.config/agents/skills`；`~/.agents/skills` 不是 Hermes 官方默认扫描目录。
- 需要读取外部目录时配置 `skills.external_dirs` 为 YAML list；不要写成字符串，不要用大量 symlink 代替配置。

推荐：

```bash
hermes config set skills.external_dirs '["~/.agents/skills", "~/.config/agents/skills"]'
hermes skills list
hermes chat --quiet --skills <skill-name> -q '只回复 OK'
```

## Linux VPS 交付

Preflight：

```bash
TARGET_USER=<target-user>
id "$TARGET_USER"
sudo -iu "$TARGET_USER" hermes --version || true
sudo -iu "$TARGET_USER" hermes config path || true
sudo -iu "$TARGET_USER" hermes config env-path || true
sudo -iu "$TARGET_USER" hermes doctor || true
sudo -iu "$TARGET_USER" hermes config check || true
sudo -iu "$TARGET_USER" sh -c 'env_path="$(hermes config env-path)"; grep -q "^HERMES_TUI=1$" "$env_path" 2>/dev/null && echo "WARN: HERMES_TUI=1 breaks workers" || true'
sudo -iu "$TARGET_USER" systemctl --user status hermes-gateway --no-pager || true
```

安装/升级以官方文档为准，常用路径：

```bash
sudo -iu "$TARGET_USER" uv tool install --upgrade hermes-agent
# 或
sudo -iu "$TARGET_USER" curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
sudo -iu "$TARGET_USER" hermes doctor
sudo -iu "$TARGET_USER" hermes config check
```

Gateway：

```bash
sudo loginctl enable-linger "$TARGET_USER"
sudo -iu "$TARGET_USER" hermes gateway install
sudo -iu "$TARGET_USER" hermes gateway start
sudo -iu "$TARGET_USER" hermes gateway status
sudo -iu "$TARGET_USER" tail -n 120 ~/.hermes/logs/gateway.log
```

Telegram `.env` 使用数字 user/chat ID；群组 chat ID 通常为负数。交付说明只记录配置类型和轮换方式，不记录真实 token/key。

## Android / Termux

Termux 使用官方 installer。失败时补齐 `python`、`git`、`clang`、`rust`、`make`、`pkg-config`、`libffi`、`openssl`、`ca-certificates`、`curl`。云手机操作结合 `using-vmoscloud` / `gomtm-adb-operate`。

## GitNexus MCP

开发者场景启用 `templates/config.yaml` 中的 `mcp_servers.gitnexus` 注释块，细节见 `references/hermes-gitnexus-mcp.md`。

```bash
cd <repo-root>
npx -y gitnexus@latest analyze
hermes mcp add gitnexus --command npx --args -y gitnexus@latest mcp
hermes mcp test gitnexus
hermes --tui
```

从 repo 根目录启动 Hermes，或设置 `TERMINAL_CWD=<repo-root>`；不要用 `--ignore-rules` 验证规则注入。

## Kanban / gomtmui Web UI

- Web UI parity：`references/hermes-kanban-gomtmui-parity.md`
- runtime 边界：`references/hermes-kanban-runtime-boundary.md`
- TUI env 坑：`references/kanban-worker-tui-env.md`

关键规则：`hermes gateway run` 启动 messaging gateway、cron scheduler、Kanban dispatcher；`hermes dashboard` 提供 Web UI；gomtmui 优先承载官方 Kanban plugin bundle，不复制 Kanban 业务逻辑。

## Persistent Goals

涉及 `/goal`、`/subgoal`、goal judge、自动 continuation 时读 `references/hermes-persistent-goals.md`。要点：goal 状态在 `SessionDB.state_meta`，每轮后由 auxiliary goal judge 决定 done/continue；gateway/Telegram continuation 走 adapter FIFO，真实用户消息优先。

## 常见坑

1. provider / endpoint / alias 不一致。
2. secret 写进 docs、issue、commit。
3. 服务环境默认 `HERMES_TUI=1`。
4. 修改配置后继续用旧 session。
5. Telegram allowlist 写 username/手机号而不是数字 ID。
6. gateway service 和 foreground gateway 冲突。
7. gomtmui 复制官方 Kanban 逻辑。
8. 跳过 `hermes -z` smoke test。
9. 把 checkout 绝对路径当可移植文档。
10. `~/.agents/skills` 被误认为 Hermes 默认目录。
11. `skills.external_dirs` 写成字符串。
12. 只在一个配置路径设置 `context_length`。
13. `context_length` 与 `max_tokens` 混用：前者是总窗口，后者是单次输出预算。

## 验收清单

- [ ] 官方文档/源码或真实命令已核对。
- [ ] `config.yaml` 与 provider schema 对齐；`context_length` 跨路径一致，`model.max_tokens` 为 endpoint 实测可承受的单次输出预算。
- [ ] 服务/worker env 不含意外 `HERMES_TUI=1`。
- [ ] secret 未进入文档和 commit。
- [ ] `hermes config check`、`hermes doctor`、custom provider smoke test 已按场景运行。
- [ ] gateway status/logs 已按场景检查。
- [ ] 相关 repo 测试已运行。
- [ ] 技能目录/外部技能配置已按场景验证。

## 支持文件

- `templates/config.yaml`
- `templates/env.example`
- `references/hermes-long-context-empty-response.md`
- `references/hermes-kanban-runtime-boundary.md`
- `references/hermes-kanban-gomtmui-parity.md`
- `references/kanban-worker-tui-env.md`
- `references/hermes-gitnexus-mcp.md`
- `references/hermes-persistent-goals.md`

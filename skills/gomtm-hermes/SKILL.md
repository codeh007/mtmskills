---
name: gomtm-hermes
description: Use when developing, configuring, deploying, debugging, or aligning gomtm, mtmai, gomtmui, or customer servers with official NousResearch Hermes Agent, including dashboard, gateway, providers, Telegram, Docker, Kanban, and VPS or Termux handoff.
version: 1.0.0
author: gomtm
license: MIT
metadata:
  hermes:
    tags: [gomtm, hermes, mtmai, gomtmui, deployment, configuration, gateway, kanban]
    related_skills: [gomtm-global, gomtm-skills-improve, hermes-agent]
---

# gomtm Hermes

## Overview

本技能用于处理 gomtm 体系中与官方 NousResearch Hermes Agent 相关的开发、配置、部署、调试和交付任务。适用范围包括 mtmai embedded gateway、gomtm 反向代理、gomtmui `/dash/hermes`、官方 Hermes dashboard、gateway、provider、Telegram、Docker、Kanban，以及客户 Linux VPS 或 Android/Termux 部署。

Hermes 行为归官方 `hermes-agent` 包、`HERMES_HOME`、`~/.hermes/config.yaml`、`~/.hermes/.env`、官方 session store、官方 tools、官方 skills 与官方 Kanban 组件拥有。gomtm、mtmai、gomtmui 只承担宿主边界、路径适配、安全代理、页面承载和交付自动化。

## When to Use

- 用户要求配置、部署、升级、验证或排障 Hermes Agent。
- 用户要求将 gomtm、mtmai、gomtmui 与 Hermes dashboard、gateway、profiles、providers、Telegram 或 Kanban 对齐。
- 用户要求在客户 Linux VPS、Android/Termux 或受控运行环境中交付 Hermes Agent。
- 用户要求诊断 Hermes 长任务停止、空回复、provider 鉴权、上下文压缩、gateway、Telegram 或 dashboard plugin 问题。
- 用户要求实现 gomtmui Hermes 最新 Web UI 对齐，尤其涉及 Kanban 和 dashboard plugin。

## Official Sources First

执行前优先读取当前官方资料和本机源码，确认命令与配置仍然有效：

- Hermes Agent docs: `https://hermes-agent.nousresearch.com/docs/`
- Providers: `https://hermes-agent.nousresearch.com/docs/integrations/providers`
- Configuration: `https://hermes-agent.nousresearch.com/docs/user-guide/configuration`
- Telegram: `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram`
- Gateway: `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/`
- Installation: `https://hermes-agent.nousresearch.com/docs/getting-started/installation`
- Termux: `https://hermes-agent.nousresearch.com/docs/getting-started/termux`
- 本机官方源码：`$HERMES_AGENT_SOURCE`，未设置时按需定位 `~/.hermes/hermes-agent` 或当前官方 checkout。

## gomtm Integration Boundaries

1. `mtmai` 负责 Python runtime、CLI 转发、`HERMES_HOME` 默认值、FastAPI mount path 改写、embedded gateway 生命周期、dashboard token bootstrap、WebSocket 与 URL 路径适配。
2. `gomtm` 负责宿主入口、容器、反向代理、生命周期、安全边界和声明式部署集成。
3. `gomtmui` 负责 Next.js host、selected gomtm server、session token、页面壳、导航、dashboard plugin runtime 和用户监督界面。
4. 官方 Hermes 负责 provider、model metadata、credential pool、memory、skills、tools、session store、Kanban DB、dispatcher 和 worker tools。
5. 需要判断上游能力时，以官方文档、release notes、`hermes --version`、`hermes doctor`、官方源码和真实命令输出为准。

## Development Workflow

1. 读取官方文档、release notes 和本机 Hermes 源码，确认目标行为。
2. 检查 `/workspace/mtmai/pyproject.toml` 与 lock，确认 `hermes-agent` 依赖范围。
3. 检查 mtmai embedded gateway surface：`/api/hermes/*`、`/dashboard-plugins/*`、dashboard session token、WebSocket 与敏感接口鉴权。
4. 检查 gomtmui Hermes route tree、API client、dashboard plugin SDK 与导航。
5. 后端 surface 先补 mtmai focused tests，再实现路径改写和鉴权。
6. 前端 surface 先补 API/types/nav/page tests，再实现 UI。
7. gomtmui 运行 focused vitest 与 `bun run check`；mtmai 运行相关 pytest；gomtm 运行相关 Go tests。
8. 涉及 gomtm 源码符号修改时，按项目 GitNexus 规则先做 impact analysis，再编辑。

## Configuration

### Current custom endpoint shape

自定义 OpenAI-compatible endpoint 使用 `provider: custom`。模型、endpoint 和 key 的主配置在 `config.yaml`，secret 值放入 `.env` 并通过 `${VAR}` 引用。

模板文件：`templates/config.custom-provider.yaml`、`templates/env.custom-provider.example`。

最小配置：

```yaml
model:
  provider: custom
  default: <model-id>
  base_url: ${HERMES_MODEL_BASE_URL}
  api_key: ${HERMES_MODEL_API_KEY}
  api_mode: chat_completions
  context_length: 1050000
  models:
    <model-id>:
      context_length: 1050000
```

`.env`：

```env
HERMES_MODEL_BASE_URL=https://<provider-host>/v1
HERMES_MODEL_API_KEY=<redacted>
```

配置原则：

1. `config.yaml` 保存结构和 `${VAR}` 引用。
2. `.env` 保存 secret 和环境差异值。
3. `provider` 对自定义 endpoint 使用 `custom`。
4. `default` 保存模型名；保持一个当前默认模型。
5. `api_mode` 对 OpenAI-compatible chat completions endpoint 使用 `chat_completions`。
6. `context_length` 根据 provider 真实支持窗口设置。
7. 配置生效需要新会话；gateway 需要 restart 或新会话。

### Required checks

```bash
hermes config check
hermes doctor
hermes chat -q "Reply with OK" --quiet
```

调试 provider 时可使用：

```bash
bash scripts/verify-custom-provider.sh
```

该脚本只打印 endpoint、model、HTTP 状态和模型列表摘要，不打印 API key。

## Linux VPS Deployment

### Preflight

默认运行用户是 `code`，安装产物位于该用户的 `$HOME/.hermes/` 与 `$HOME/.local/bin/hermes`。客户服务器、Telegram bot、模型 key 属于客户；交付材料只记录配置类型和轮换方式。

```bash
id code
sudo -iu code bash -lc 'git --version'
sudo -iu code bash -lc 'test -x ~/.local/bin/hermes && ~/.local/bin/hermes --version || true'
sudo -iu code bash -lc 'test -d ~/.hermes && find ~/.hermes -maxdepth 1 -type f -printf "%f\n" || true'
systemctl --user -M code@ status hermes-gateway --no-pager || true
```

发现已有安装、已有 gateway service 或已有客户配置时，先备份 `config.yaml` 和 `.env`，再确认交付动作。

### Install

以目标运行用户执行官方 installer：

```bash
sudo -iu code bash -lc 'curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash'
sudo -iu code bash -lc 'hermes --version && hermes doctor && hermes config check'
```

### Configure model

使用 `hermes model` 交互配置，或写入 `templates/config.custom-provider.yaml` 对应形态。配置后运行：

```bash
sudo -iu code bash -lc 'hermes chat -q "Reply with OK" --quiet'
```

### Configure Telegram Gateway

`.env`：

```env
TELEGRAM_BOT_TOKEN=<redacted>
TELEGRAM_ALLOWED_USERS=<numeric-user-id>
```

群组场景按需增加：

```env
TELEGRAM_GROUP_ALLOWED_USERS=<numeric-user-id>
TELEGRAM_GROUP_ALLOWED_CHATS=<negative-chat-id>
```

`TELEGRAM_ALLOWED_USERS` 使用数字 user ID。私聊验收只需要 bot token 和允许用户 ID。

### Install gateway service

```bash
sudo loginctl enable-linger code
sudo -iu code bash -lc 'hermes gateway install'
sudo -iu code bash -lc 'hermes gateway start'
sudo -iu code bash -lc 'hermes gateway status'
sudo -iu code bash -lc 'tail -n 120 ~/.hermes/logs/gateway.log'
```

### Delivery checklist

- `hermes --version` 成功。
- `hermes doctor` 无阻塞错误。
- `hermes config check` 无必须迁移项。
- `hermes chat -q "Reply with OK" --quiet` 能调用模型。
- `hermes gateway status` 显示运行中。
- Telegram 允许用户私聊 bot 能得到回复。
- `~/.hermes/logs/gateway.log` 无 token invalid、unauthorized、model auth failed、event loop crash。
- 交付说明包含运行用户、安装路径、常用 gateway 命令、日志路径、bot username、授权 user ID、模型 endpoint 名称、key/token 轮换方式。

## Android / Termux Deployment

Termux 使用官方 installer：

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Termux 依赖通过 `pkg` 安装。失败时补齐 `python`、`git`、`clang`、`rust`、`make`、`pkg-config`、`libffi`、`openssl`、`ca-certificates`、`curl` 后重试。

云端 Android 设备操作时结合 `using-vmoscloud` 和 `gomtm-adb-operate`。Termux 场景使用 Termux 自身进程管理、shell profile 和官方 Hermes 命令。

## Kanban and gomtmui Web UI Alignment

当需求涉及 gomtmui Hermes 最新 Web UI、Kanban、dashboard plugin、gateway dispatcher 或 selected server 安全代理时，阅读 `references/hermes-kanban-gomtmui-parity.md`。

关键规则：

1. `hermes gateway run` 启动 messaging gateway、cron scheduler 和 Kanban dispatcher。
2. Web UI 入口是 `hermes dashboard`。
3. Kanban 是官方 bundled dashboard plugin，tab path 是 `/kanban`。
4. mtmai 暴露受保护代理：`/api/hermes/plugins/kanban/*` 到官方 `/api/plugins/kanban/*`。
5. gomtmui 优先加载官方 Kanban plugin bundle；本地页面只承担 host adaptation。
6. Kanban writes 使用 selected server 对应 `X-Hermes-Session-Token`。
7. Kanban events WebSocket 使用 selected server token 和 origin 边界。

## Empty Response and Stuck Session Debugging

当长任务停止、后续“继续”得到空回复时，先看日志和 session：

```bash
grep -Ei "pending tool result|Empty response|No fallback available|AuthenticationError|context" ~/.hermes/logs/errors.log | tail -80
hermes sessions list
```

判断点：

1. `pending tool result` 表示上一轮工具结果未被模型消化。
2. `Empty response (no content or reasoning)` 表示模型返回空内容。
3. `No fallback available` 表示没有可用回退 provider。
4. `AuthenticationError`、endpoint 指向错误或 provider 与 endpoint 不一致会让新回合持续失败。
5. 旧 session 已出现空回复链时，修复配置后开新 session 验证。

修复顺序：

1. 检查 `~/.hermes/config.yaml` 的 `model.provider`、`model.default`、`model.base_url`、`model.api_key`、`model.api_mode`。
2. 检查 `~/.hermes/.env` 中引用变量是否存在。
3. 运行 `hermes config check`、`hermes doctor`。
4. 运行 `hermes chat -q "Reply with OK" --quiet`。
5. gateway 场景执行 `hermes gateway restart` 并开新会话。

## Support Files

- `templates/config.custom-provider.yaml` — 自定义 OpenAI-compatible endpoint 配置模板。
- `templates/env.custom-provider.example` — secret 和 endpoint 环境变量模板。
- `templates/env.telegram.example` — Telegram gateway 环境变量模板。
- `scripts/verify-custom-provider.sh` — 自定义 endpoint 模型与 chat completions 烟雾验证。
- `references/hermes-kanban-gomtmui-parity.md` — Kanban 与 gomtmui 对齐细节。

## Common Pitfalls

1. provider 与 endpoint 不一致，导致 Hermes 访问错误平台。
2. 将 secret 写入报告、wiki、commit、截图或技能文档。
3. 修改运行中 session 的配置后继续在旧 session 验证。
4. Telegram allowlist 写用户名、bot name 或手机号。
5. 忽略 gateway service 与前台 gateway 进程冲突。
6. 在 gomtmui 中复制 Kanban 业务逻辑。
7. 长任务空回复后继续堆叠新任务。
8. 跳过 `hermes chat -q` 模型烟雾测试。

## Verification Checklist

- [ ] 已读取官方文档或本机官方源码确认当前命令。
- [ ] `config.yaml` 使用当前 provider schema。
- [ ] secret 只存放于 `.env`、客户 secret store 或运行环境。
- [ ] `hermes config check` 成功。
- [ ] `hermes doctor` 无阻塞错误。
- [ ] `hermes chat -q "Reply with OK" --quiet` 成功。
- [ ] gateway 场景完成 `hermes gateway status` 与日志检查。
- [ ] gomtmui / mtmai / gomtm 改动完成对应 focused tests。
- [ ] 新增或更新的技能通过发现检查并可全局安装。

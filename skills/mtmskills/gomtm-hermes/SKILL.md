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

## Overview

本技能用于处理 gomtm 体系中与官方 NousResearch Hermes Agent 相关的开发、配置、部署、调试和交付任务。适用范围包括 mtmai embedded gateway、gomtm 反向代理、gomtmui `/dash/hermes`、mtmhermes 或同类专用容器实例、官方 Hermes dashboard、gateway、provider、Telegram、Docker、Kanban，以及客户 Linux VPS 或 Android/Termux 部署。

Hermes 行为归官方 `hermes-agent` 包、`HERMES_HOME`、`config.yaml`、`.env`、官方 session store、官方 tools、官方 skills 与官方 Kanban 组件拥有。gomtm、mtmai、gomtmui、mtmhermes 只承担宿主边界、路径适配、安全代理、页面承载和交付自动化。

## When to Use

- 用户要求配置、部署、升级、验证或排障 Hermes Agent。
- 用户要求将 gomtm、mtmai、gomtmui、mtmhermes 与 Hermes dashboard、gateway、profiles、providers、Telegram 或 Kanban 对齐。
- 用户要求在客户 Linux VPS、Android/Termux、容器或受控运行环境中交付 Hermes Agent。
- 用户要求诊断 Hermes 长任务停止、空回复、provider 鉴权、上下文压缩、gateway、Telegram 或 dashboard plugin 问题。
- 用户要求实现 gomtmui Hermes 最新 Web UI 对齐，尤其涉及 Kanban 和 dashboard plugin。
- 用户要求了解、配置或排障 Hermes `/goal`、`/subgoal`、goal judge 或自动 continuation 行为。

## Official Sources First

执行前优先读取当前官方资料和本机源码，确认命令与配置仍然有效：

- Hermes Agent docs: `https://hermes-agent.nousresearch.com/docs/`
- Installation: `https://hermes-agent.nousresearch.com/docs/getting-started/installation`
- Configuration: `https://hermes-agent.nousresearch.com/docs/user-guide/configuration`
- Providers: `https://hermes-agent.nousresearch.com/docs/integrations/providers`
- Messaging gateway: `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/`
- Telegram: `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram`
- Kanban: `https://hermes-agent.nousresearch.com/docs/zh-Hans/user-guide/features/kanban`
- Persistent Goals: `https://hermes-agent.nousresearch.com/docs/user-guide/features/goals`
- Termux: `https://hermes-agent.nousresearch.com/docs/getting-started/termux`
- Release notes: `https://github.com/NousResearch/hermes-agent/releases`
- 本机官方源码：优先使用 `$HERMES_AGENT_SOURCE`；未设置时按需定位当前官方 checkout、包安装目录，或用 `python -c "import hermes_cli, pathlib; print(pathlib.Path(hermes_cli.__file__).parents[1])"` 查找。

## Latest Baseline

以官方 `v2026.5.16 / v0.14.0` 及当前安装包为基线：

1. Hermes Agent 已正式支持 PyPI / `uv tool` / `uvx` 安装。
2. 官方 installer 仍可用于普通 Linux、macOS、WSL 与 Termux。
3. `hermes proxy` 是官方 OpenAI-compatible proxy 能力。
4. `custom_providers:` 是当前自定义 provider 选择器入口；`providers:` dict 也被 runtime 支持，但技能模板优先使用 `custom_providers:`，便于 `custom:<slug>` 选择。
5. `model:` 可以保存当前默认 endpoint/model；默认模型的 `provider` 不应误写成 `openrouter`，否则会回到 OpenRouter 并触发 401。
6. `config.yaml` 保存结构和 `${VAR}` 引用；`.env` 或运行环境保存 secret。
7. 官方 TUI 是交互式入口；需要 TUI 时显式运行 `hermes --tui`。不要在共享/服务主机的 `$HERMES_HOME/.env` 默认写 `HERMES_TUI=1`，否则 `hermes chat -q`、Kanban worker、cron 等非 TTY 后台任务会被强制进 TUI 并失败；细节见 `references/kanban-worker-tui-env.md`。
8. `hermes gateway run` 启动 messaging gateway、cron scheduler 与 Kanban dispatcher；Web UI 入口是 `hermes dashboard`。Kanban 不依赖 dashboard 运行，运行边界见 `references/hermes-kanban-runtime-boundary.md`。
9. 新会话或 gateway restart 才会稳定读取配置变化。

## gomtm Integration Boundaries

1. `mtmai` 负责 Python runtime、CLI 转发、`HERMES_HOME` 默认值策略、FastAPI mount path 改写、embedded gateway 生命周期、dashboard token bootstrap、WebSocket 与 URL 路径适配。
2. `gomtm` 负责宿主入口、容器、反向代理、生命周期、安全边界和声明式部署集成。
3. `gomtmui` 负责 Next.js host、selected gomtm server、session token、页面壳、导航、dashboard plugin runtime 和用户监督界面。
4. `mtmhermes` 或同类私有实例仓库负责专用 Hermes 容器、运行态数据、私有配置和交付脚本。
5. 官方 Hermes 负责 provider、model metadata、credential pool、memory、skills、tools、session store、Kanban DB、dispatcher、worker tools、proxy 和 gateway。
6. 需要判断上游能力时，以官方文档、release notes、`hermes --version`、`hermes doctor`、官方源码和真实命令输出为准。

## Development Workflow

1. 读取官方文档、release notes 和可用的本机 Hermes 源码，确认目标行为。
2. 若任务涉及 mtmai Hermes 依赖，定位目标 mtmai 仓库后检查 `pyproject.toml` 与 lock，确认 `hermes-agent` 依赖范围；路径用 `<mtmai-repo>` 表示，不假定固定在 `/workspace/mtmai`。
3. 检查 mtmai embedded gateway surface：`/api/hermes/*`、`/dashboard-plugins/*`、dashboard session token、WebSocket 与敏感接口鉴权。
4. 检查 gomtmui Hermes route tree、API client、dashboard plugin SDK 与导航。
5. 后端 surface 先补 mtmai focused tests，再实现路径改写和鉴权。
6. 前端 surface 先补 API/types/nav/page tests，再实现 UI。
7. gomtmui 运行 focused vitest 与 `bun run check`；mtmai 运行相关 pytest；gomtm 运行相关 Go tests。
8. 涉及 gomtm 源码符号修改时，按项目 GitNexus 规则先做 impact analysis，再编辑。

## Configuration Templates

`templates/` 维护两套主模板：

- `templates/config.default.yaml` + `templates/env.default.example`：普通用户。包含单一模型 endpoint、`skills.external_dirs: ["~/.agents/skills"]`、可选 Telegram 和基础 auxiliary 配置；不默认启用 TUI。
- `templates/config.developer.yaml` + `templates/env.developer.example`：开发者。包含 default 模板内容、GitNexus MCP；不默认启用 TUI。
- 旧的 `templates/config.custom-provider.yaml`、`templates/env.custom-provider.example`、`templates/env.telegram.example` 作为兼容片段保留。

选择规则：

- 只做聊天、Telegram、基础自动化：用 default 模板。
- 要在代码仓库里开发、审查影响范围、遵守 GitNexus 规则：用 developer 模板。
- 所有 secret 只放 `.env`、profile secret store、容器 secret 或运行环境；`config.yaml` 只保留 `${VAR}` 引用。不要把交互式偏好 `HERMES_TUI=1` 写入共享 `$HERMES_HOME/.env`，以免破坏后台 worker；需要 TUI 时显式用 `hermes --tui`。
- 修改 `config.yaml`、`.env`、MCP 或 context files 后，开启新 session；gateway 场景执行 restart。

## User-level / External Skills

`npx -y skills@latest` 属于 Vercel Labs 的 `skills` CLI（npm 包 `skills`）。执行 Hermes 技能目录相关任务时，先区分三类路径：

1. Hermes 原生技能目录：`$HERMES_HOME/skills`，默认通常是 `~/.hermes/skills`。
2. `skills` CLI 的 agent-specific 全局目录：由 `--agent` 决定，例如 `--agent hermes-agent` 写入 `~/.hermes/skills`，`--agent codex` 写入 `${CODEX_HOME:-~/.codex}/skills`。
3. `skills` CLI 的 universal/user-level 目录：项目级 canonical path 是 `.agents/skills/`；全局 universal 路径是 `~/.config/agents/skills`。部分 agent 在 `skills` CLI 的表中也把自己的全局路径映射到 `~/.agents/skills`，但 **Hermes Agent 官方不会自动扫描 `~/.agents/skills`**。

当前 `skills` CLI 文档/源码要点：

- `npx -y skills@latest add <repo> -g -a hermes-agent ...` 安装到 `~/.hermes/skills`，Hermes 可直接加载。
- `npx -y skills@latest add <repo> -g -a codex ...` 安装到 `${CODEX_HOME:-~/.codex}/skills`，不是 `~/.agents/skills`。
- `npx -y skills@latest add <repo> -g -a universal ...` 安装到 `~/.config/agents/skills`。
- `~/.agents/skills` 不是所有 AI agent 共享的唯一默认全局路径；它只是部分 agent 的 global path，同时 `.agents/skills/` 是很多 agent 的 project path。
- Codex 在 `skills` CLI 映射中使用 project path `.agents/skills/`，global path 是 `${CODEX_HOME:-~/.codex}/skills`；不要假设 Codex CLI 默认加载 `~/.agents/skills`。
- `skills` CLI 通过 `-a/--agent` 决定链接/安装到哪些 agent 目录；如果没有明确包含 `hermes-agent`，安装结果可能不在 Hermes 原生目录。

Hermes 支持通过 `config.yaml` 的 `skills.external_dirs` 读取额外技能目录。官方源码约定：

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - ~/.config/agents/skills
  template_vars: true
  inline_shell: false
```

行为规则：

1. `external_dirs` 会展开 `~` 和 `${VAR}`，相对路径按 `$HERMES_HOME` 解析。
2. 只加载实际存在的目录；不存在的目录会被跳过。
3. Hermes 本地目录 `$HERMES_HOME/skills` 优先，外部目录随后扫描；同名技能由本地目录优先，重复名在显式 `skill_view` 时可能触发歧义提示。
4. 外部目录按只读共享技能目录使用；通过 `skill_manage(action='create')` 创建的新技能仍写入 `$HERMES_HOME/skills`。
5. 修改后启动新会话；gateway 场景执行 `hermes gateway restart` 或新 session。
6. 对不完全信任的外部技能源不要开启 `skills.inline_shell`；保持默认 `false`。

推荐配置命令：

```bash
hermes config set skills.external_dirs '["~/.agents/skills"]'
# 如需同时读取 universal 全局目录：
# hermes config set skills.external_dirs '["~/.agents/skills", "~/.config/agents/skills"]'
```

如果 `hermes config set` 把列表写成了字符串，直接修正 `~/.hermes/config.yaml` 为 YAML list：

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
```

验证：

```bash
python - <<'PY'
from agent.skill_utils import _external_dirs_cache_clear, get_external_skills_dirs, get_all_skills_dirs
_external_dirs_cache_clear()
print('external=', [str(p) for p in get_external_skills_dirs()])
print('all=', [str(p) for p in get_all_skills_dirs()])
PY
hermes skills list
hermes chat --quiet --skills <skill-name> -q '只回复 OK'
```

优先级建议：

1. 若希望 `npx skills` 安装结果专供 Hermes 使用，优先安装时显式指定 `-a hermes-agent`。
2. 若希望 Hermes 同时读取其它 agent 或 universal 用户级技能目录，再配置 `skills.external_dirs`。
3. 不要用大量手工 symlink 代替 `skills.external_dirs`；symlink 适合临时兼容，但配置额外目录更清晰、可维护。

## Model Configuration

### Current OpenAI-compatible shape

完整模板优先使用：

- 普通用户：`templates/config.default.yaml`、`templates/env.default.example`
- 开发者：`templates/config.developer.yaml`、`templates/env.developer.example`

兼容片段：`templates/config.custom-provider.yaml`、`templates/env.custom-provider.example`、`templates/env.telegram.example`。

`config.yaml` 推荐形态。`context_length` 用 endpoint/模型真实稳定窗口，并在所有解析路径保持一致；不要把 Hermes 未知模型 fallback（256K）当成所有模型的最佳值。OpenRouter 当前公开元数据中 `openai/gpt-5.5` / `openai/gpt-5.5-pro` 为 `1050000`，若实际 endpoint 支持该窗口，应配置为 `1050000`：

```yaml
model:
  default: <model-id>
  model: <model-id>
  base_url: ${OPENAI_BASE_URL}
  api_key: ${OPENAI_API_KEY}
  api_mode: chat_completions
  context_length: <context-length>
  models:
    <model-id>:
      context_length: <context-length>

custom_providers:
  - name: <Provider Display Name>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    api_mode: chat_completions
    model: <model-id>
    context_length: <context-length>
    models:
      <model-id>:
        context_length: <context-length>

model_aliases:
  <model-id>:
    provider: custom
    model: <model-id>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    api_mode: chat_completions
    context_length: <context-length>

compression:
  enabled: true
  threshold: 0.5

auxiliary:
  compression:
    provider: custom
    model: <model-id>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    timeout: 180
    extra_body: {}
```

`model_aliases` 用于让 `hermes -z ... --model <model-id>` 这类未显式传 `--provider` 的一次性命令仍保持在自定义 endpoint，避免模型名被静态目录误判到 OpenAI Codex 或 OpenRouter。

`.env`：

```env
OPENAI_BASE_URL=https://<provider-host>/v1
OPENAI_API_KEY=<redacted>
```

交互式 TUI：

```bash
hermes --tui
# 可选：只在个人交互 shell 中设置 alias，不要写入 Hermes 服务用 .env
alias h='hermes --tui'
```

配置原则：

1. `config.yaml` 保存结构和 `${VAR}` 引用。
2. `.env`、profile secret store、容器 secret 或运行环境保存 secret。共享/服务主机不要默认写 `HERMES_TUI=1`；交互式 TUI 使用 `hermes --tui`。
3. 自定义 OpenAI-compatible endpoint 使用 `api_mode: chat_completions`。
4. `custom_providers[].name` 生成 provider slug，例如 `Example Relay` 对应 `custom:example-relay`；实际 slug 以 `hermes model` / 真实命令为准。
5. `model.default` / `model.model` 保存当前默认模型；保持一个当前默认模型。
6. `context_length` 必须按真实 provider/model 窗口填写，并在 `model`、`model.models`、`custom_providers[].context_length`、`custom_providers[].models`、`model_aliases` 中一致；不要只改一处。
7. `compression.threshold` 按 `context_length × threshold` 触发；`context_length` 写小会过早压缩，写大于实际窗口会过晚压缩并增加空回复/上下文错误风险。
8. 第三方中转 endpoint 先查供应商 `/models`/公开元数据/实测稳定窗口；能确认百万级窗口（如 OpenRouter `openai/gpt-5.5` 为 `1050000`）就配置真实值，未知时才临时保守下调。
9. 显式配置 `auxiliary.compression`，避免 auto 路径选择到 context 元数据不一致的模型。
10. 避免把 `model.provider` 写成 `openrouter`；自定义 endpoint 验证时显式使用 `--provider custom:<slug>` 或 bare custom endpoint 配置。
11. 对第三方中转模型补 `model_aliases`，确保 `--model <model-id>` 不带 `--provider` 时仍命中自定义 endpoint。
12. 修改配置后启动新会话；gateway 场景执行 restart。

### Required checks

```bash
hermes --version
hermes config path
hermes config env-path
hermes config check
hermes doctor
hermes -z "Reply exactly: OK" --provider custom:<provider-slug> --model <model-id> --ignore-rules
hermes -z "Reply exactly: OK" --provider custom --model <model-id> --ignore-rules
```

调试 provider 时可使用：

```bash
bash scripts/verify-custom-provider.sh <model-id>
```

该脚本只打印 endpoint、model、HTTP 状态和模型列表摘要，不打印 API key。

### Empty-response configuration trap

出现 `Provider: openrouter Model: gpt-5.5 Endpoint: https://openrouter.ai/api/v1 Missing Authentication header` 时，优先检查：

1. 当前 session 是否仍在使用旧配置；开新 session 或 gateway restart。
2. `model.provider` 是否被写成 `openrouter` 或被 CLI/provider override 强制到 OpenRouter。
3. `model.base_url`、`model.api_key`、`model.api_mode` 是否实际存在且引用的 `${VAR}` 可在 `.env` 解析。
5. `custom_providers` 是否使用 list 形态，并设置 `api_mode: chat_completions`。
6. `model_aliases` 是否覆盖当前第三方中转模型，避免 `--model` 自动检测到 OpenAI Codex / OpenRouter。
7. `fallback_providers` / fallback 配置是否把失败路由到未配置的 OpenRouter。
8. 用 `hermes -z ... --provider custom:<slug>`、`hermes -z ... --provider custom`、`hermes -z ... --model <model-id>` 分别验证 named custom、bare custom 与默认模型路径。

## Linux VPS Deployment

### Preflight

目标运行用户由客户或管理员决定。安装产物通常位于该用户的 `$HOME/.hermes/` 与 `$HOME/.local/bin/hermes`。客户服务器、Telegram bot、模型 key 属于客户；交付材料只记录配置类型和轮换方式。

```bash
TARGET_USER=<target-user>
id "$TARGET_USER"
sudo -iu "$TARGET_USER" git --version
sudo -iu "$TARGET_USER" hermes --version || true
sudo -iu "$TARGET_USER" hermes config path || true
sudo -iu "$TARGET_USER" hermes config env-path || true
sudo -iu "$TARGET_USER" sh -c 'env_path="$(hermes config env-path)"; if grep -q "^HERMES_TUI=1$" "$env_path" 2>/dev/null; then echo "WARN: HERMES_TUI=1 in $env_path can break Kanban/cron/background workers"; fi'
sudo -iu "$TARGET_USER" hermes doctor || true
sudo -iu "$TARGET_USER" hermes config check || true
sudo -iu "$TARGET_USER" sh -c 'test -d "${HERMES_HOME:-$HOME/.hermes}" && find "${HERMES_HOME:-$HOME/.hermes}" -maxdepth 1 -type f -printf "%f\n" || true'
sudo -iu "$TARGET_USER" systemctl --user status hermes-gateway --no-pager || true
```

发现已有安装、已有 gateway service 或已有客户配置时，先备份 `config.yaml` 和 `.env`，再确认交付动作。

### Install

按当前官方文档选择一种安装路径。

PyPI / uv tool：

```bash
sudo -iu "$TARGET_USER" uv tool install --upgrade hermes-agent
sudo -iu "$TARGET_USER" hermes --version
```

官方 installer：

```bash
sudo -iu "$TARGET_USER" curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
sudo -iu "$TARGET_USER" hermes --version
```

安装后运行：

```bash
sudo -iu "$TARGET_USER" hermes doctor
sudo -iu "$TARGET_USER" hermes config check
```

如需交互式 TUI，使用 `hermes --tui`；不要在 gateway/Kanban/cron 主机的 Hermes `.env` 中默认写入 `HERMES_TUI=1`。

### Configure model

使用 `hermes model` 交互配置，或写入 `templates/config.custom-provider.yaml` 对应形态。配置后运行：

```bash
sudo -iu "$TARGET_USER" hermes -z "Reply exactly: OK" --provider custom:<provider-slug> --model <model-id> --ignore-rules
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

`TELEGRAM_ALLOWED_USERS` 使用数字 user ID。私聊验收只需要 bot token 和允许用户 ID。群组场景先确认 BotFather privacy mode、bot admin、mention 策略和 group allowlist。

### Install gateway service

```bash
sudo loginctl enable-linger "$TARGET_USER"
sudo -iu "$TARGET_USER" hermes gateway install
sudo -iu "$TARGET_USER" hermes gateway start
sudo -iu "$TARGET_USER" hermes gateway status
sudo -iu "$TARGET_USER" tail -n 120 ~/.hermes/logs/gateway.log
```

### Delivery checklist

- `hermes --version` 成功。
- 需要交互 UI 时 `hermes --tui` 可启动；服务/worker 环境不含全局 `HERMES_TUI=1`。
- `hermes doctor` 无阻塞错误。
- `hermes config check` 无必须迁移项。
- `hermes -z "Reply exactly: OK" --provider custom:<provider-slug> --model <model-id> --ignore-rules` 能调用模型。
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

## Developer Code Intelligence / GitNexus MCP

开发者场景用 `templates/config.developer.yaml`，细节见 `references/hermes-gitnexus-mcp.md`。

要点：

- 先在目标 repo 跑 `npx -y gitnexus@latest analyze`。
- Hermes 通过 `mcp_servers.gitnexus` 连接 `npx -y gitnexus@latest mcp`。
- 目标 repo 的 `AGENTS.md` / `CLAUDE.md` 负责写 GitNexus 规则。
- Hermes 从 repo 根目录启动，或设置 `TERMINAL_CWD=<repo-root>`；不要用 `--ignore-rules` 验证规则注入。
- 改 gomtm 源码符号前跑 impact，提交前跑 detect-changes。

快速启动：

```bash
cd <repo-root>
npx -y gitnexus@latest analyze
hermes mcp add gitnexus --command npx --args -y gitnexus@latest mcp
hermes mcp test gitnexus
hermes --tui
```

`hermes gateway run` 场景同样设置 `TERMINAL_CWD=<repo-root>`，且不要在 gateway 使用的 `$HERMES_HOME/.env` 默认启用 `HERMES_TUI=1`。

## Kanban and gomtmui Web UI Alignment

当需求涉及 gomtmui Hermes 最新 Web UI、Kanban、dashboard plugin、gateway dispatcher 或 selected server 安全代理时，阅读 `references/hermes-kanban-gomtmui-parity.md`；当判断 Kanban 是否必须启动 dashboard/gateway 时，阅读 `references/hermes-kanban-runtime-boundary.md`。

关键规则：

1. `hermes gateway run` 启动 messaging gateway、cron scheduler 和 Kanban dispatcher。
2. Web UI 入口是 `hermes dashboard`；Kanban CLI、slash command 和 worker tools 不以 dashboard 为前置条件。
3. Kanban 是官方 bundled dashboard plugin，tab path 是 `/kanban`。
4. mtmai 暴露受保护代理：`/api/hermes/plugins/kanban/*` 到官方 `/api/plugins/kanban/*`。
5. gomtmui 优先加载官方 Kanban plugin bundle；本地页面只承担 host adaptation。
6. Kanban writes 使用 selected server 对应 `X-Hermes-Session-Token`。
7. Kanban events WebSocket 使用 selected server token 和 origin 边界。

## Persistent Goals (`/goal`)

当需求涉及 Hermes `/goal`、`/subgoal`、persistent goals、Ralph loop、goal judge 或 Telegram/gateway 自动 continuation 时，阅读 `references/hermes-persistent-goals.md`。

关键规则：

1. `/goal <text>` 在当前 session 保存 standing goal，并立即把目标文本作为普通 user turn 排队。
2. 每轮结束后 `GoalManager` 调用 `auxiliary.goal_judge` 判断 done/continue；未完成时继续排入普通 user-role continuation prompt。
3. goal 状态保存在 `SessionDB.state_meta` 的 `goal:<session_id>`，可随 `/resume` 恢复。
4. continuation 不修改 system prompt、不切换 toolset；CLI 走 `_pending_input`，gateway/Telegram 走 adapter FIFO，真实用户消息优先。
5. `/subgoal` 用于追加验收标准；judge 失败默认 continue，连续坏 JSON 或超过 `goals.max_turns` 会自动 pause。

## Empty Response and Stuck Session Debugging

长任务停止或“继续”空回复时，按 `references/hermes-long-context-empty-response.md` 排查。最短命令：

```bash
grep -Ei "pending tool result|Empty response|No fallback available|AuthenticationError|context|Provider:" ~/.hermes/logs/errors.log | tail -80
HERMES_TUI=0 hermes chat --quiet -q '只输出 OK'
```

关键判断：

1. `Empty response (no content or reasoning)` + `No fallback available`：模型在 tool result 后返回空内容，且无回退 provider。
2. 高 `input_tokens` / 大量 tool calls：优先收紧 `context_length`，让压缩提前触发。
3. 自定义 OpenAI-compatible endpoint：`context_length` 要在 `model`、`custom_providers`、`model_aliases` 中全部一致。
4. `Provider: openrouter` + 自定义模型名：provider override 或 alias 缺失。
5. 修复配置后开新 session；gateway 场景必须 restart 或重新运行 gateway。

## Support Files

- `templates/config.default.yaml`
- `templates/env.default.example`
- `templates/config.developer.yaml`
- `templates/env.developer.example`
- `templates/config.custom-provider.yaml`
- `templates/env.custom-provider.example`
- `templates/env.telegram.example`
- `scripts/verify-custom-provider.sh`
- `references/hermes-kanban-runtime-boundary.md`
- `references/hermes-kanban-gomtmui-parity.md`
- `references/kanban-worker-tui-env.md`
- `references/hermes-gitnexus-mcp.md`
- `references/hermes-long-context-empty-response.md`
- `references/hermes-persistent-goals.md`

## Common Pitfalls

1. provider / endpoint mismatch.
2. secret in docs or commits.
3. 在共享/服务主机的 `$HERMES_HOME/.env` 默认写 `HERMES_TUI=1`；这会让 `hermes chat -q`、Kanban worker、cron 等非 TTY 后台任务进入 TUI 并失败。
4. old session after config change.
5. Telegram allowlist uses usernames or phone numbers.
6. gateway service / foreground conflict.
7. kanban logic copied into gomtmui.
8. `hermes -z` smoke test skipped.
9. checkout absolute path treated as portable.
10. fixed `/home/<user>` assumed universal.
11. `~/.agents/skills` misunderstood as Hermes default.
12. `skills.external_dirs` written as a string.
13. GitNexus MCP without repo `AGENTS.md` / `CLAUDE.md`.
14. `--ignore-rules` used to test GitNexus injection.
15. custom endpoint uses optimistic `context_length` in only one config path; compression triggers too late and long tool-heavy sessions return empty content.

## Verification Checklist

- [ ] current command source checked.
- [ ] `config.yaml` matches provider schema and context_length is consistent across model/custom provider/alias paths.
- [ ] service/worker env checked for accidental `HERMES_TUI=1` when using Kanban/cron/background workers.
- [ ] secrets stay out of docs and commits.
- [ ] `hermes config check` passes.
- [ ] `hermes doctor` passes.
- [ ] custom provider smoke test passes.
- [ ] gateway status and logs checked.
- [ ] related repo tests run.
- [ ] `skills.external_dirs` / `hermes chat --skills` checked when applicable.
- [ ] GitNexus status + `hermes mcp test gitnexus` pass in repo-root or `TERMINAL_CWD` setup.

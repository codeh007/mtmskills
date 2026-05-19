---
name: gomtm-codex-dev
description: Use when 需要安装、配置、诊断或维护 Codex CLI、~/.codex/config.toml、~/.codex/auth.json、第三方 OpenAI-compatible provider、sub2api 中转模型或 Codex 模型切换。
---

# gomtm-codex-dev

本技能用于维护 Codex CLI 的本机配置。默认面向 `~/.codex/`，也适用于通过 `CODEX_HOME=/path` 指向的独立 Codex home。

## 使用时机

- 需要安装、升级、诊断 Codex CLI。
- 需要修改 `~/.codex/config.toml`、`~/.codex/auth.json` 或项目级 `.codex/config.toml`。
- 需要接入第三方 OpenAI-compatible API，例如 `https://sub2api.yuepa8.com`。
- 需要确认当前可用模型、切换默认模型、增加 Codex profiles。
- 需要排查 Codex 模型不可用、认证失败、provider 不生效、project-local config 被忽略等问题。

## 官方资料

- Codex README: <https://github.com/openai/codex/blob/main/README.md>
- Codex docs: <https://developers.openai.com/codex>
- 配置基础: <https://developers.openai.com/codex/config-basic>
- 高级配置: <https://developers.openai.com/codex/config-advanced>
- 配置参考: <https://developers.openai.com/codex/config-reference>

遇到版本相关问题时，先运行：

```bash
codex --version
codex doctor --summary
```

## 关键文件

- 主配置：`~/.codex/config.toml`
- 登录凭据：`~/.codex/auth.json`
- 项目级配置：`<project>/.codex/config.toml`

重要约束：`model_provider`、`model_providers`、`profiles`、`openai_base_url` 等 provider/auth 级配置必须放在用户级 `~/.codex/config.toml`。如果写进项目级 `.codex/config.toml`，新版本 Codex 会加载但提示 unsupported project-local config keys，并忽略这些 key。

修改 `config.toml` 或 `auth.json` 前必须备份：

```bash
cd ~/.codex
cp config.toml "config.$(date +%Y%m%d-%H%M%S).toml"
cp auth.json "auth.$(date +%Y%m%d-%H%M%S).json"
```

## OpenAI-compatible provider

Codex 支持在 `config.toml` 中定义第三方 OpenAI-compatible provider。认证有三种常见方式：

| 方式 | 配置 | 适用场景 |
|---|---|---|
| `requires_openai_auth = true` | API key 保存在 `auth.json` 的 `OPENAI_API_KEY` | 当前本机已登录或希望复用 Codex 官方登录流程 |
| `env_key = "ENV_NAME"` | API key 来自环境变量 | 推荐方式，密钥不落入 `config.toml` |
| `experimental_bearer_token = "sk-..."` | API key 直接写在 provider 下 | 可用但不推荐，只适合受控私有机器或临时验证 |

不要把 `[model_providers.<id>.auth]` 与 `env_key`、`experimental_bearer_token`、`requires_openai_auth` 同时使用。

## sub2api 当前模型

截至 2026-05-19，通过当前可用 key 查询 `https://sub2api.yuepa8.com/v1/models`，接口可见模型为：

```text
gpt-4o-audio-preview
gpt-4o-realtime-preview
gpt-5.2
gpt-5.2-2025-12-11
gpt-5.2-chat-latest
gpt-5.2-pro
gpt-5.2-pro-2025-12-11
gpt-5.3-codex
gpt-5.3-codex-spark
gpt-5.4
gpt-5.4-2026-03-05
gpt-5.4-mini
gpt-5.5
gpt-image-1
gpt-image-1.5
gpt-image-2
```

Codex agent 主模型应使用文本/编码模型。当前可写入 `config.toml` profile 的 OpenAI 文本/编码模型为：

```text
gpt-5.5
gpt-5.4
gpt-5.4-2026-03-05
gpt-5.4-mini
gpt-5.3-codex
gpt-5.2
gpt-5.2-2025-12-11
gpt-5.2-chat-latest
gpt-5.2-pro
gpt-5.2-pro-2025-12-11
```

其中 `codex debug models` 当前明确列出的 Codex 内置模型目录为 `gpt-5.5`、`gpt-5.4`、`gpt-5.4-mini`、`gpt-5.3-codex`、`gpt-5.2`。日期版本、pro、chat-latest 等模型来自 `sub2api` 的 `/v1/models`，可以作为 profile 预置，实际使用时仍应以 `codex exec -p <profile>` 最小任务验证。`gpt-5.3-codex-spark` 当前虽然在列表可见，但 2026-05-19 直接调用 `/v1/responses` 返回 502，不放入开箱即用 profile。

`gpt-image-*`、`gpt-4o-audio-preview`、`gpt-4o-realtime-preview` 虽然在 API 列表可见，但不适合作为 Codex CLI 的主模型。图片模型应通过 OpenAI-compatible 图片接口单独调用，不要写成 `model = "gpt-image-2"`。

查询模型：

```bash
key="$(jq -r .OPENAI_API_KEY ~/.codex/auth.json)"
curl -fsSL -H "Authorization: Bearer $key" \
  https://sub2api.yuepa8.com/v1/models | jq -r '.data[].id' | sort -u
```

查看 Codex 实际可切换模型目录：

```bash
codex debug models | jq -r '.models[] | select(.visibility == "list") | .slug'
```

## 标准 config.toml

推荐使用一个 provider 加多个 profile。这样用户可以通过 `codex -p gpt-5.4`、`codex -p gpt-5.3-codex` 切换模型，无需再次编辑配置文件。

```toml
model_provider = "sub2api"
model = "gpt-5.5"
review_model = "gpt-5.5"
model_reasoning_effort = "medium"
disable_response_storage = true
network_access = "enabled"
windows_wsl_setup_acknowledged = true
model_context_window = 1000000
model_auto_compact_token_limit = 900000

[model_providers.sub2api]
name = "sub2api.yuepa8.com"
base_url = "https://sub2api.yuepa8.com"
wire_api = "responses"
env_key = "SUB2API_API_KEY"
request_max_retries = 4
stream_max_retries = 10
stream_idle_timeout_ms = 300000

[profiles."gpt-5.5"]
model_provider = "sub2api"
model = "gpt-5.5"
model_reasoning_effort = "medium"

[profiles."gpt-5.4"]
model_provider = "sub2api"
model = "gpt-5.4"
model_reasoning_effort = "medium"

[profiles."gpt-5.4-2026-03-05"]
model_provider = "sub2api"
model = "gpt-5.4-2026-03-05"
model_reasoning_effort = "medium"

[profiles."gpt-5.4-mini"]
model_provider = "sub2api"
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"

[profiles."gpt-5.3-codex"]
model_provider = "sub2api"
model = "gpt-5.3-codex"
model_reasoning_effort = "medium"

[profiles."gpt-5.2"]
model_provider = "sub2api"
model = "gpt-5.2"
model_reasoning_effort = "medium"

[profiles."gpt-5.2-2025-12-11"]
model_provider = "sub2api"
model = "gpt-5.2-2025-12-11"
model_reasoning_effort = "medium"

[profiles."gpt-5.2-chat-latest"]
model_provider = "sub2api"
model = "gpt-5.2-chat-latest"
model_reasoning_effort = "medium"

[profiles."gpt-5.2-pro"]
model_provider = "sub2api"
model = "gpt-5.2-pro"
model_reasoning_effort = "medium"

[profiles."gpt-5.2-pro-2025-12-11"]
model_provider = "sub2api"
model = "gpt-5.2-pro-2025-12-11"
model_reasoning_effort = "medium"

[profiles.no_approval]
approval_policy = "never"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true

[tui.model_availability_nux]
"gpt-5.5" = 4
"gpt-5.4" = 4
"gpt-5.4-2026-03-05" = 4
"gpt-5.4-mini" = 4
"gpt-5.3-codex" = 4
"gpt-5.2" = 4
"gpt-5.2-2025-12-11" = 4
"gpt-5.2-chat-latest" = 4
"gpt-5.2-pro" = 4
"gpt-5.2-pro-2025-12-11" = 4
```

环境变量方式：

```bash
export SUB2API_API_KEY="sk-..."
codex -p gpt-5.4
```

如果明确需要把 key 直接写进 `config.toml`，把 `env_key` 替换为：

```toml
experimental_bearer_token = "sk-..."
```

如果希望沿用 `auth.json` 的 `OPENAI_API_KEY`，可以改成：

```toml
[model_providers.OpenAI]
name = "OpenAI via sub2api"
base_url = "https://sub2api.yuepa8.com"
wire_api = "responses"
requires_openai_auth = true
```

对应 `auth.json`：

```json
{
  "auth_mode": "apikey",
  "OPENAI_API_KEY": "sk-..."
}
```

## 切换与验证

常用命令：

```bash
codex -m gpt-5.4
codex -p gpt-5.3-codex
codex exec -p gpt-5.2 "用一句话回复当前模型是否可用"
```

配置验证：

```bash
codex doctor --summary
codex doctor --json | jq '.checks["config.load"], .checks["network.provider_reachability"]'
```

模型目录验证：

```bash
codex debug models | jq -r '.models[] | [.slug, .visibility, .supported_in_api] | @tsv'
```

若 `codex doctor` 输出 `Ignored unsupported project-local config keys`，说明 provider 或 profiles 被写到了项目级 `.codex/config.toml`。把这些 key 移到 `~/.codex/config.toml`。

若 `codex exec` 在受限环境中报 `failed to initialize in-process app-server client: Read-only file system`，这是当前 Codex 运行时初始化问题，不等同于 provider 或模型不可用。此时用 `codex doctor --summary`、`codex debug models`、直接 `/v1/models` 和 `/v1/responses` 调用分别验证配置加载、模型目录和上游模型可调用性。

## 排查规则

- 先运行 `codex doctor --json`，不要凭记忆判断配置是否生效。
- `base_url` 按实际可用服务填写。当前 `sub2api.yuepa8.com` 的 Codex 配置使用 `https://sub2api.yuepa8.com`，不要盲目追加 `/v1`。
- 认证失败时先确认 provider 使用的是 `env_key`、`experimental_bearer_token` 还是 `requires_openai_auth`，再查对应凭据位置。
- 模型不可用时同时查两处：`/v1/models` 的接口列表，以及 `codex debug models` 的 Codex 模型目录。接口可见不等于适合作为 Codex 主模型。
- 第三方 OpenAI-compatible 服务可能只兼容部分 Responses API 行为。出现流式、工具调用、图片/音频相关问题时，用最小 `codex exec` 任务和直接 `curl` 分别验证。

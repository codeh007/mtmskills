---
name: gomtm-codex-dev
description: Use when 需要安装、配置、诊断或维护 Codex CLI、~/.codex/config.toml、~/.codex/auth.json、第三方 OpenAI-compatible provider、sub2api 中转模型或 Codex 模型切换。
---

# gomtm-codex-dev

用于维护 Codex CLI 本机配置。默认配置目录是 `~/.codex/`；设置 `CODEX_HOME=/path` 时，以该目录作为 Codex home。

## 先确认

```bash
codex --version
codex doctor --summary
```

版本、配置键、模型可用性相关判断以当前输出和官方文档为准：

- Codex docs: <https://developers.openai.com/codex>
- Config reference: <https://developers.openai.com/codex/config-reference>
- Codex README: <https://github.com/openai/codex/blob/main/README.md>

## 配置文件

- 用户级配置：`~/.codex/config.toml`
- 登录凭据：`~/.codex/auth.json`
- 项目级配置：`<project>/.codex/config.toml`
- 本技能模板：`templates/config.toml`、`templates/auth.json`
- 用户常见问题：`references/致用户-常见问题.md`

`model_provider`、`model_providers`、`profiles`、`profile`、`openai_base_url`、`chatgpt_base_url`、`notify`、`otel` 等机器级配置放在用户级 `~/.codex/config.toml`。项目级 `.codex/config.toml` 适合保存该项目自己的 sandbox、approval、workspace 等覆盖项。

修改前先备份：

```bash
cd ~/.codex
cp config.toml "config.$(date +%Y%m%d-%H%M%S).toml"
cp auth.json "auth.$(date +%Y%m%d-%H%M%S).json"
```

## sub2api 配置

当前私有中转服务使用：

```toml
[model_providers.sub2api]
name = "sub2api.yuepa8.com"
base_url = "https://sub2api.yuepa8.com"
wire_api = "responses"
```

`templates/config.toml` 已包含常用 sub2api provider、profiles、sandbox 和网络配置。需要 API key 文件时，按 `templates/auth.json` 写入本机 `~/.codex/auth.json`。

查询中转接口可见模型：

```bash
key="$(jq -r .OPENAI_API_KEY ~/.codex/auth.json)"
curl -fsSL -H "Authorization: Bearer $key" \
  https://sub2api.yuepa8.com/v1/models | jq -r '.data[].id' | sort -u
```

查询 Codex 可切换模型目录：

```bash
codex debug models | jq -r '.models[] | [.slug, .visibility, .supported_in_api] | @tsv'
```

## 切换与验证

常用命令：

```bash
codex -m gpt-5.4
codex -p gpt-5.5
codex exec -p gpt-5.5 "用一句话回复当前模型是否可用"
```

配置验证：

```bash
codex doctor --summary
codex doctor --json | jq '.checks["config.load"], .checks["network.provider_reachability"]'
```

判断模型可用性时同时看三处：

1. `codex doctor` 的配置加载和 provider 连通性结果。
2. `/v1/models` 返回的上游模型列表。
3. `codex debug models` 返回的 Codex 模型目录。

若 `codex exec` 输出 `failed to initialize in-process app-server client: Read-only file system`，按当前运行时初始化问题处理；继续用 `codex doctor`、`codex debug models`、`/v1/models` 和 `/v1/responses` 分别验证配置加载、模型目录和上游调用。

## Windows

Windows 下 `~/.codex/` 通常对应 `%USERPROFILE%\.codex\`。备份可用 PowerShell `Copy-Item`。在 WSL 里使用 Codex 时，保留 `windows_wsl_setup_acknowledged = true`。

## Codex App

Codex App 是桌面端，适合普通用户管理多个 agent、查看 diff、切换项目并接续本地和云端任务。编程开发场景使用 Codex CLI。下载入口：<https://openai.com/codex/>。

---
name: gomtm-codex-dev
description: use when 需要理解codex, codex cli, 的安装,配置和使用
---

## when to use 

- 需要理解codex, codex cli, 的安装,配置和使用
- 需要对本机或者远程 codex 命令进行安装,诊断,维护,更改配置

## 官方文档

- [codex README](https://github.com/openai/codex/blob/main/README.md)
- [codex 详细文档](https://github.com/openai/codex/tree/main/docs)

## 关键文件

- [主配置文件](~/.codex/config.toml)

典型配置

```toml
model_provider = "OpenAI"
model = "gpt-5.5"
review_model = "gpt-5.5"
model_reasoning_effort = "medium"
disable_response_storage = true
network_access = "enabled"
windows_wsl_setup_acknowledged = true
model_context_window = 1000000
model_auto_compact_token_limit = 900000

[model_providers.OpenAI]
name = "OpenAI"
base_url = "https://sub2api.yuepa8.com"
wire_api = "responses"
requires_openai_auth = true

[tui.model_availability_nux]
"gpt-5.5" = 4

[profiles.no_approval]
approval_policy = "never"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = true

[plugins."superpowers@openai-curated"]
enabled = true

[mcp_servers.gitnexus]
command = "npx"
args = ["-y", "gitnexus@latest", "mcp"]

```

- [oauth凭据文件](~/.codex/auth.json)
    典型配置:
```json
{
  "auth_mode": "apikey",
  "OPENAI_API_KEY": "sk-bc4ad0c......"
}
```

## 提示

1. 用户通常使用自定义的第三方模型服务, 而不是官方默认的模型服务. 第三方模型服务通常是完全兼容openai官方接口的.
2. 当用户对codex cli的使用存在疑问,需要咨询 codex 配置和使用相关问题时,优先基于`https://github.com/openai/codex/tree/main/docs/`文档的说明进行回答, 其次基于基于`https://developers.openai.com/codex`在线文档进行回答.
3. 注意codex cli 版本的更新带来的影响. 并且总是建议和对标最新版.

## 约束

1. 当需要对`~/.codex/config.toml` 或者 `~/.codex/auth.json`编辑前, 必须先在进行备份. 备份文件写到同级目录下的带当前时间标记的文件中,例如:`config.{YYYYMMdd-hhmmss}.toml`

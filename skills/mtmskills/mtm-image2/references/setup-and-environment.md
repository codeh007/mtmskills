# 安装与环境

用于确认机器是否能真正调用 GPT Image。配置应遵循 OpenAI 官方环境变量或用户已有的 OpenAI-compatible 配置，不在本技能里固化具体中转域名。

## 环境类型

| Environment | What to do |
| --- | --- |
| Codex CLI / developer shell | 运行 `scripts/mtm_image2.py`。 |
| Codex app 有 shell | 让 agent 运行 Python 脚本，并保存 prompt/image/report。 |
| Codex app 无 shell | 交付完整 brief 与最终 prompt，说明仍需图片 API 执行环境。 |
| 原生图片工具可用 | 把最终 prompt 与参考图交给宿主工具，仍保留 prompt。 |

## 运行时要求

- Python 3 标准环境。
- 可访问 OpenAI Images API 或兼容的图片端点。
- `OPENAI_API_KEY`，或用户的 Codex/OpenAI-compatible 配置中可读取的 key。
- `OPENAI_BASE_URL` 可选；未设置时优先读取 Codex provider `base_url`，再默认 `https://api.openai.com/v1`。

## Codex 配置

常见位置：

- Windows: `%USERPROFILE%\.codex\config.toml`、`%USERPROFILE%\.codex\auth.json`
- macOS/Linux: `~/.codex/config.toml`、`~/.codex/auth.json`
- Shell 环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`

若用户已经配置 OpenAI-compatible provider，复用其 base URL 与 key；不要在技能文档或脚本中写死某个私有网关。

只确认 key 是否存在，不打印 key 值。

## Codex App 提示模板

```text
Use mtm-image2 to create a professional image.
Subject: ...
Purpose: ...
Style: ...
Required text in the image: ...
Size/aspect ratio: ...
References attached: ...
Use gpt-image-2, not local drawing code. Save the final prompt and generated file path.
```

如果 Codex app 不能访问 shell 或图片 API，agent 应返回 prompt brief，而不是声称已生成图片。

## API 基址

脚本接受 root 或 `/v1` 形式，会规范化为一个 `/v1`：

- `https://api.openai.com`
- `https://api.openai.com/v1`

OpenAI-compatible provider 也应遵循同样规则。

## 环境变量

优先级：

1. Explicit command flags.
2. `OPENAI_API_KEY`.
3. `~/.codex/auth.json` 中的 OpenAI-compatible key 字段。

Optional:

```text
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_MODEL=gpt-image-2
MTM_IMAGE2_OUTPUT_DIR=mtm-image2-output
```

不要把密钥写入仓库、技能目录、issue 评论或截图。

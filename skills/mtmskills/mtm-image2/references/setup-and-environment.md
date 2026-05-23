# 安装与环境

用于确认机器是否能真正调用 GPT Image。配置应遵循 OpenAI 官方环境变量或用户已有的 OpenAI-compatible 配置，不在本技能里固化具体中转域名。

## 环境类型

| Environment | What to do |
| --- | --- |
| Codex CLI / developer shell | 运行 `scripts/mtm_image2.py`。 |
| Codex app 有 shell | 优先运行本技能的 Python 脚本，并保存 prompt/image/report。 |
| Codex app 无 shell | 交付完整 brief 与最终 prompt，说明仍需图片 API 执行环境。 |
| 原生图片工具可用 | 只有确认宿主工具会调用 GPT Image 或兼容图片模型时，才把最终 prompt 与参考图交给宿主工具，仍保留 prompt。 |

## Codex App 优先级

- 用户要求图片成品时，`mtm-image2` 是主流程；内置 `imagegen` 只可作为能真实调用 GPT Image 的宿主工具。
- 不要把缺少参考图、Pillow 安装失败、PowerShell 受限、浏览器可截图等情况解释为可以改用 HTML/SVG/Canvas/本地绘图交付。
- 如果当前 Codex app 无法访问 shell、OpenAI Images API、Responses image tool 或兼容图片端点，输出 prompt-only，并明确“未生成图片”。
- 用户明确要求可编辑版式稿、SVG 或网页海报时，才把本地排版文件作为目标产物；这不属于 GPT Image 生成结果。

## 运行时要求

- Python 3 标准环境。
- 可访问 OpenAI Images API 或兼容的图片端点。
- `OPENAI_API_KEY`，或 Codex provider `env_key` 指向且已注入当前进程的 key。
- `OPENAI_BASE_URL` 或 `OPENAI_API_BASE` 可选；未设置时读取 Codex provider `base_url` 或 `openai_base_url`，再默认 `https://api.openai.com/v1`。

## Codex 配置

常见位置：

- Windows: `%USERPROFILE%\.codex\config.toml`
- macOS/Linux: `~/.codex/config.toml`
- Shell/agent 环境变量：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_API_BASE`
- Codex 用户级环境文件可作为启动时注入来源；脚本只读取当前进程环境，不手动解析 `.env`。

若用户已经配置 OpenAI-compatible provider，复用其 base URL、静态 headers、环境变量 headers 和 query params；`env_key` 只用于读取已经存在于当前进程环境中的变量。不要在技能文档或脚本中写死某个私有网关。设置了 `CODEX_HOME` 时，脚本从该目录读取 `config.toml`。

Codex provider/profile 相关配置应放在用户级 config；项目级 `.codex/config.toml` 不适合保存 provider、auth、profile 或 telemetry 路由键。需要显式选择 profile 时：

```text
python scripts/mtm_image2.py --codex-profile <profile-name> --prompt "A product photo, no text."
```

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

## Python 演示

跨平台演示优先直接运行 Python，避免依赖 Bash：

```text
python scripts/mtm_image2.py --prompt "A clean product hero image on white background, no text." --size 1024x1024 --quality medium
```

高清或公网网关可能超时时，优先 streaming：

```text
python scripts/mtm_image2.py --prompt "A photorealistic product hero image, no text." --size 2048x2048 --quality high --format jpeg --stream --partial-images 2
```

## 环境变量

优先级：

1. Explicit command flags.
2. `OPENAI_API_KEY`.
3. Codex provider `env_key` 指向的环境变量。

Optional:

```text
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_IMAGE_MODEL=gpt-image-2
MTM_IMAGE2_OUTPUT_DIR=mtm-image2-output
```

不要把密钥写入仓库、技能目录、issue 评论或截图。

# API 边界

## 核心边界

对话模型可以理解文字和图片输入。真实图片生成/编辑必须路由到 GPT Image 能力，例如 `gpt-image-2`：

- `/v1/images/generations`
- `/v1/images/edits`
- 宿主支持时，也可用 Responses API image generation tool
- 长耗时生成优先使用 `stream=true` 和 `partial_images=1..3`

不要调用本地绘图库、HTML canvas、SVG 渲染器、matplotlib、PIL 绘图或截图技巧，并把它们当作 GPT Image 2 输出。

Codex app 的默认 `imagegen` 技能不自动等于真实 GPT Image 输出。只有确认它背后调用了 OpenAI Images API、Responses image generation tool 或兼容 GPT Image 模型时，才可把它作为本技能的执行工具。

## 端点选择

| 用户请求 | 端点 |
| --- | --- |
| 从文字生成图片 | `/v1/images/generations` |
| 使用参考图生成新图 | `/v1/images/edits` |
| 修改背景、对象或风格 | `/v1/images/edits` |
| 用 mask 局部修改 | `/v1/images/edits` + mask |

## OpenAI-Compatible 要求

OpenAI-compatible 网关必须支持图片端点，而不只是 chat completions。需确认：

- `POST /v1/images/generations`
- `POST /v1/images/edits`
- edits 支持 multipart form 上传
- `model=gpt-image-2`
- 返回 `data[0].b64_json`，或返回脚本可下载的图片 URL
- streaming 请求返回 SSE，并包含可解码的 partial 或 final image base64 事件
- 如果 Codex provider 配置了静态 headers、环境变量 headers 或 query params，图片端点也能接受这些附加参数。

如果网关只支持 `/v1/chat/completions` 或 `/v1/responses`，本技能仍可写 prompt，但不能保证真实 `gpt-image-2` 出图。

## 常见错误

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 401/403 | key 缺失或错误 | 检查环境变量或 auth 文件，不打印 key。 |
| `/images/...` 404 | 网关不支持图片端点或 base URL 错误 | 避免重复 `/v1`，检查 provider 文档。 |
| `model not found` | 上游未启用 `gpt-image-2` | 查询 `/v1/models` 或选择已启用的 GPT Image 模型。 |
| multipart 失败 | edits 用了 JSON | 使用 multipart form，字段为 `image[]`/`image` 和可选 `mask`。 |
| 没有 `b64_json` | 网关只返回 URL | 使用脚本 URL 下载能力或检查响应 JSON。 |
| 文字渲染差 | 模型限制或文字太多 | 缩短文字、提高质量，或在设计工具中补最终文字。 |
| 公网长请求 524/超时 | `stream=false` 长时间无响应字节，代理空闲超时 | 优先改用 streaming；产品接口改成异步 job；必须同步时才验证网关非流式 keepalive。 |

## 验收

图片任务完成条件：

1. 已保存或展示最终 prompt。
2. 命令/API 调用成功。
3. 已报告图片文件路径或宿主图片产物。
4. 已确认输出来自 `gpt-image-2` 或用户明确指定的兼容 GPT Image 模型。
5. 高清或长耗时任务已优先验证 streaming 路径，或说明为什么只能使用同步/异步 job 路径。

prompt-only 模式只能说“prompt 已准备”，不能说“图片已生成”。

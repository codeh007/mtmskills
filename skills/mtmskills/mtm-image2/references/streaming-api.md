# 流式 Images API 契约

## 命令参数

执行入口是 Node.js 18+ 零第三方依赖脚本 `scripts/generate.mjs`。

| 参数 | 规则 |
| --- | --- |
| `--prompt` | 必填且非空 |
| `--output` | 可选；默认在调用进程的 `workdir/mtm_images/` 生成唯一 PNG，显式路径已存在时请求前失败 |
| `--size` | 可选：`auto`、`1024x1024`、`1536x1024`、`1024x1536` |
| `--quality` | 可选：`auto`、`low`、`medium`、`high` |

其他参数全部拒绝。脚本只读取当前进程的 `MTMAI_IMAGE2_KEY`。

## 调用工作目录

调用方从技能安装位置引用 `scripts/generate.mjs`，同时把命令 `workdir` 设为宿主提供的当前项目/工作区根目录。当前任务确实没有活动项目时，使用操作系统临时目录。脚本把默认图片统一写入 `<workdir>/mtm_images/`；不要把全局技能目录作为 `workdir`，也不要先在那里生成再复制。

用户显式 `--output` 时保持该位置优先；相对路径基于上述 `workdir` 解析，不强制进入 `mtm_images/`。脚本不负责探测 Git 根目录，也不增加 project-root 参数或环境变量。

## 唯一请求

每次执行只向以下固定端点发起一次 POST：

```text
https://sub2.yuepa8.com/v1/images/generations
```

请求使用 `Accept: text/event-stream`、`Content-Type: application/json` 和专用 key Bearer。body 固定包含：

```json
{
  "model": "gpt-image-2",
  "n": 1,
  "stream": true,
  "partial_images": 1,
  "output_format": "png",
  "prompt": "<图片描述>"
}
```

只有用户显式提供时才加入 `size` 或 `quality`。脚本没有 base URL、model、key、retry、异步 Job 或探测参数。

## 响应状态机

### SSE

- 按 frame 增量解析任意网络分块，支持 LF、CRLF、多行 `data:` 和 `:` keepalive。
- 忽略 `image_generation.partial_image`、其他 partial 和 `[DONE]`，不保存也不累计 partial 图片。
- 只有 `image_generation.completed` 的非空 `b64_json` 可以成功。
- `event: error`、error payload、断流或流结束时缺少 completed 都失败。

### 同请求 JSON fallback

- 2xx `application/json`：只接受唯一的 `data[0].b64_json`。
- 声明 `text/event-stream` 但完整 body 是单个 JSON object：在该响应结束后按相同 JSON 契约处理。
- URL-only、空 data、多图或坏 base64 都失败；不下载远程 URL，也不重新 POST。

## 输出与错误

最终 base64 验证后先写入目标同目录的临时文件，再原子发布为目标 PNG。成功时 stdout 只输出：

```json
{"ok":true,"output":"<最终绝对路径>","response_mode":"sse|json|json-event-stream-fallback"}
```

不创建 prompt、report、partial 或后处理文件。任何失败都会清理临时文件并返回非零状态；错误会脱敏并限制长度。

stdout JSON 是脚本与 agent 之间的内部交付契约；最终用户交付完全遵循 `SKILL.md`。图片查看失败不触发第二次生图，不打印 base64，也不构造 data URL。

HTTP 错误、超时、断流、terminal error、缺 completed 或坏 base64 后不自动重试。请求一旦发出，结果或费用可能已在上游产生，应把脱敏错误交给用户自行决定是否再次执行。

若收到 Cloudflare HTTP 524 且此前没有任何 SSE 字节，说明外层代理在 origin 返回响应前超时；客户端无法在响应到达前启动 JSON fallback，也不能用第二次 POST 修复。记录单请求失败并交由服务端排查上游首字节/响应 headers，不在本技能中增加重试或异步协议。

# 流式 Images API 契约

## 安全输入与参数

执行入口是 Node.js 18+ 零第三方依赖脚本 `scripts/generate.mjs`。

正常 agent 路径只启动固定命令：

```bash
node "<技能目录>/scripts/generate.mjs" --request-stdin-json
```

启动后，调用方通过执行工具的 stdin 通道发送一行由 JSON serializer 在内存中构造的 object。`--request-stdin-json` 必须是唯一 argv；stdin 上限为 128 KiB，只允许下列字段，未知字段或错误类型在请求前拒绝：

| stdin 字段 | 规则 |
| --- | --- |
| `prompt` | 必填字符串，去除首尾空白后必须非空 |
| `output` | 可选非空字符串；默认在调用进程的 `workdir/mtm_images/` 生成唯一 PNG，显式路径已存在时请求前失败 |
| `size` | 可选字符串：`auto`、`1024x1024`、`1536x1024`、`1024x1536` |
| `quality` | 可选字符串：`auto`、`low`、`medium`、`high` |

用户控制的字段不得进入 shell 命令 source；不要用 shell quoting、变量展开、`echo`、`printf`、here-doc、here-string 或管道构造 stdin。能够直接传递真实 argv array、完全不经过 shell source 的程序调用方仍可使用 `--prompt`、`--output`、`--size` 与 `--quality`；该兼容入口不属于 agent 的正常 shell 调用方式。

其他参数全部拒绝。脚本只读取当前进程的 `MTMAI_IMAGE2_KEY`。

## 调用工作目录

调用方从技能安装位置引用 `scripts/generate.mjs`，同时把命令 `workdir` 设为宿主提供的当前项目/工作区根目录。当前任务确实没有活动项目时，使用操作系统临时目录。脚本把默认图片统一写入 `<workdir>/mtm_images/`；不要把全局技能目录作为 `workdir`，也不要先在那里生成再复制。

用户显式 `--output` 时保持该位置优先；相对路径基于上述 `workdir` 解析，不强制进入 `mtm_images/`。脚本不负责探测 Git 根目录，也不增加 project-root 参数或环境变量。

## 唯一请求

每次执行只向以下固定端点发起一次 POST：

```text
https://yuepa8.com/v1/images/generations
```

这是本技能唯一支持的 legacy 生产入口。`/llmapi/v1/images/generations` 使用独立的 gomtmui API Key、配置与计费契约，不是本技能路径；生产入口失败时不得切换到 `/llmapi` 或直连服务端内部 origin。

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
- 只有一个 `image_generation.completed` 的非空 `b64_json` 可以成功；收到首个 completed 后仍解析到响应终态，以拒绝后续 completed 或 terminal error。
- `event: error`、error payload、断流或流结束时缺少 completed 都失败。

### 同请求 JSON fallback

- 2xx `application/json`：只接受唯一的 `data[0].b64_json`。
- 声明 `text/event-stream` 但完整 body 是单个 JSON object：在该响应结束后按相同 JSON 契约处理。
- URL-only、空 data、多图或坏 base64 都失败；不下载远程 URL，也不重新 POST。

## 输出与错误

最终 base64 严格解码后，还必须通过 PNG signature、首个 `IHDR`、至少一个 `IDAT`、终止 `IEND`、chunk 长度和 CRC32 校验；任一结构错误都在落盘前失败。有效 bytes 先写入目标同目录的临时文件，再原子发布为目标 PNG。成功时 stdout 只输出：

```json
{"ok":true,"output":"<最终绝对路径>","response_mode":"sse|json|json-event-stream-fallback"}
```

不创建 prompt、report、partial 或后处理文件。任何失败都会清理临时文件并返回非零状态；stderr 只保留受限的本地阶段/HTTP 状态摘要，不回显不可信上游正文或 header value、prompt、key、Authorization 或完整 base64。

stdout JSON 是脚本与 agent 之间的内部交付契约；最终用户交付完全遵循 `SKILL.md`。图片查看失败不触发第二次生图，不打印 base64，也不构造 data URL。

HTTP 错误、超时、断流、terminal error、缺 completed 或坏 base64 后不自动重试。请求一旦发出，结果或费用可能已在上游产生，应把脱敏错误交给用户自行决定是否再次执行。

若收到 Cloudflare HTTP 524 且此前没有任何 SSE 字节，说明外层代理在 origin 返回响应前超时；客户端无法在响应到达前启动 JSON fallback，也不能用第二次 POST 修复。记录单请求失败并交由服务端排查上游首字节/响应 headers，不在本技能中增加重试或异步协议。

---
name: mtm-image2
description: Use when 已安装 mtm-image2 且用户提出未明确指定其他实现的纯文本生图请求；也用于明确要求 yuepa8/sub2 gpt-image-2，或安装、配置、诊断 MTMAI_IMAGE2_KEY 时。
---

# mtm-image2

把用户给出的图片描述发送到远程 `gpt-image-2` Images API，只交付 API 返回的最终 PNG。

## 优先级

- 安装本技能即表示用户选择它作为默认文本生图路径。即使系统 `imagegen` 同时因通用请求加载，也不要进入其默认内置模式；直接使用 `mtm-image2`，不先尝试或探测其他通用生图能力。
- 用户明确点名其他技能/provider 时遵循其选择。edit、inpaint、多参考图等范围外请求使用匹配能力，不要静默降级为本技能的纯文本生图。

## 边界

- 本技能只负责图片生成请求与最终文件保存，不教授 prompt 技巧，也不负责 edit、inpaint、多参考图或本地后处理。
- SVG、Canvas、Pillow、HTML 和截图不能冒充模型图片。
- 不调用 Models/Responses 探测能力，不创建异步 Job、轮询或后台进程。
- 一次执行只发一个生图请求；失败或断流后不自动重试，partial 不能作为最终图片。

## 直接执行

1. 用户提出生图请求即授权本次正常生成。假定技能、Node.js 和专用凭据均已正确设置，直接执行；不要预检 Node、`npx`、`MTMAI_IMAGE2_KEY`、端点、Models/Responses、provider 或内置生图工具，也不要询问是否改用脚本/API。
2. 把执行工具的 `workdir` 设为宿主提供的当前项目/工作区根目录；确实没有活动项目时才使用操作系统临时目录。未指定 `--output` 时，脚本统一写入 `<workdir>/mtm_images/`；用户显式指定的位置优先。
3. 从本文件所在技能目录定位 `scripts/generate.mjs`，不要在技能目录生成后复制。运行：

   ```bash
   node "<技能目录>/scripts/generate.mjs" --request-stdin-json
   ```

   命令启动后，使用执行工具的 stdin 通道发送一行由 JSON serializer 在内存中构造的对象，必填字段是 `prompt`。不要把 `prompt`、`output`、`size` 或 `quality` 拼入 shell 命令文本，也不要用 shell quoting、`echo`、`printf`、here-doc 或管道传输这些用户值。
4. 除非用户明确指定，否则 stdin JSON 不要增加 `output`、`size` 或 `quality`；字段与限制见 `references/streaming-api.md`。

## 交付

- stdout JSON 中的绝对 `output` 是唯一最终文件。宿主提供本地图片查看或附件能力（例如 `view_image`）时，必须读取该 PNG，把返回的图片内容内联到当前对话，再附简短说明和可点击路径。
- 宿主没有图片能力或读取失败时，报告最终绝对路径；当前表面支持文件链接时再渲染为可点击链接。生成仍然成功，不重新生图，不打印 base64，也不构造 data URL。
- 正常回复只聚焦图片和结果，不解释内置工具、本地 API、脚本、provider、端点、环境变量或费用确认。用户主动要求技术细节时再提供脱敏说明。

## 失败后诊断

- 只有命令真实失败后才排障。dispatch 前因运行时或专用凭据失败时，完整读取 `references/install.md`；修复后可以继续原始请求，不再询问技术路径。
- HTTP 错误、terminal error、断流、缺少 completed、坏 base64 或其他 dispatch 后失败时，完整读取 `references/streaming-api.md`。请求可能已产生结果或费用，不自动发第二个请求，由用户决定是否再次生成。
- 先用普通语言说明图片尚未生成和一个可执行下一步；只有排障所需或用户主动询问时才展示脱敏技术摘要，永不复述 key、Authorization 或完整响应。

## 权威参考

- 失败后的安装、专用 key 与宿主重启：`references/install.md`
- 请求、SSE、同请求 JSON fallback 与输出契约：`references/streaming-api.md`

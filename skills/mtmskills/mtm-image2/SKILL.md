---
name: mtm-image2
description: Use when 用户要求通过 yuepa8/sub2 的 gpt-image-2 Images API 生成图片，或需要安装、配置、诊断 MTMAI_IMAGE2_KEY 生图流程时。
---

# mtm-image2

把用户给出的图片描述发送到远程 `gpt-image-2` Images API，只交付 API 返回的最终 PNG。

## 边界

- 本技能只负责图片生成请求与最终文件保存，不教授 prompt 技巧，也不负责 edit、inpaint、多参考图或本地后处理。
- SVG、Canvas、Pillow、HTML 和截图不能冒充模型图片。
- 不调用 Models/Responses 探测能力，不创建异步 Job、轮询或后台进程。
- 一次执行只发一个生图请求；失败或断流后不自动重试，partial 不能作为最终图片。

## 执行

1. 当前进程缺少 `MTMAI_IMAGE2_KEY` 时，不发请求；完整读取 `references/install.md` 并完成专用凭据配置。
2. 有专用 key 时，完整读取 `references/streaming-api.md`，在本技能目录运行：

   ```bash
   node scripts/generate.mjs --prompt "<图片描述>"
   ```

3. 成功后只向用户报告 stdout JSON 中的 `output` 路径。除非用户明确指定，否则不要增加 `--output`、`--size` 或 `--quality`。

## 失败语义

- 缺 key、参数错误或已有输出文件会在网络请求前失败。
- HTTP 错误、terminal error、断流、缺少 completed 或坏 base64 会返回非零状态，且不会发第二个请求。
- 请求发出后的错误表示结果或费用可能已经产生；把脱敏错误交给用户决定是否重新执行。

## 权威参考

- 安装、专用 key、宿主重启与首次演示：`references/install.md`
- 请求、SSE、同请求 JSON fallback 与输出契约：`references/streaming-api.md`

# 稳定高清生图演示

## 结论

长耗时或高清图片优先使用 Image API 的 streaming 路径：

```bash
scripts/demo_stream_highres.sh
```

该脚本调用 `scripts/mtm_image2.py --stream --partial-images 2`，会保存 partial 图片和最终图片。公网代理、隧道、负载均衡器或平台网关存在空闲超时时，streaming 能持续返回 SSE 字节，比 `stream=false` 的长时间同步等待更稳定。

## 必要环境

至少提供一种认证来源：

```bash
export OPENAI_API_KEY="..."
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

兼容网关可把 `OPENAI_BASE_URL` 指向自己的 `/v1` 地址。脚本也会尝试读取 Codex 的 `~/.codex/config.toml` 和 `~/.codex/auth.json`。

不要把 key 写入技能目录、仓库、issue 或报告。

## 演示脚本

| 场景 | 脚本 | 默认设置 |
| --- | --- | --- |
| 高清稳定路径 | `scripts/demo_stream_highres.sh` | `2048x2048`、`quality=high`、`format=jpeg`、`stream=true`、`partial_images=2` |
| 同步基线对照 | `scripts/demo_sync_baseline.sh` | `1024x1024`、`quality=medium`、`format=png`、`stream=false` |

可用环境变量覆盖演示参数：

```bash
MTM_IMAGE2_SIZE=1536x1024 \
MTM_IMAGE2_QUALITY=high \
MTM_IMAGE2_FORMAT=jpeg \
MTM_IMAGE2_PARTIAL_IMAGES=2 \
scripts/demo_stream_highres.sh "A photorealistic product hero image, no text."
```

## 验证标准

一次真实可用演示必须同时满足：

1. 命令返回 JSON report。
2. `images` 中至少有一个最终图片路径。
3. stream 演示通常还会出现 `*-partial-<n>.*` 文件；模型生成很快时，partial 数量可能少于请求值。
4. report 中记录 `model`、`size`、`quality`、`stream`、`prompt`、`images`。
5. 图片文件是 API 返回的 base64 或 URL 下载结果；不得用本地绘图替代。

## 高清参数

优先从稳定尺寸开始：

| 目标 | 建议尺寸 |
| --- | --- |
| 方形成品 | `2048x2048` |
| 横版成品 | `2048x1152` 或 `1536x1024` |
| 竖版成品 | `1024x1536` |
| 4K 横版实验 | `3840x2160` |

`gpt-image-2` 尺寸需满足：两边都是 16 的倍数、长短边比例不超过 3:1、最长边不超过 3840px，并满足像素总量限制。超过 `2560x1440` 总像素的输出属于实验路径，失败时先降到 2K 级别验证。

## stream=false 失败排查

如果 `stream=false` 请求在公网入口返回超时，而本机 origin 或 streaming 请求成功，优先判断为链路空闲超时，不是模型不可用。处理顺序：

1. 改用 `stream=true` + `partial_images=1..3`。
2. 对产品接口改成异步任务：快速返回 job id，后台生成，客户端轮询或下载结果。
3. 只有必须保留同步接口时，才检查网关是否会在 images 非流式路径 flush keepalive。仅设置网关 keepalive 间隔不等于已经修复 `stream=false` 的长等待。

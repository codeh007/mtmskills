# 工作流

## 类型

| 类型 | 触发 | 端点 |
| --- | --- | --- |
| `generate` | 只有文字 prompt | `/v1/images/generations` |
| `edit` | 一张或多张参考图 | `/v1/images/edits` |
| `inpaint` | 参考图加 mask | `/v1/images/edits` |
| `prompt-only` | 没有可用 API/tool | 不调用 API |

## 生成检查

调用 API 前确认：

- 主体和场景。
- 用途：海报、头像、产品图、UI mockup、图解、缩略图等。
- 比例或精确尺寸。
- 质量：`low`、`medium`、`high`、`auto`。
- 必须出现的文字、拼写和语言。
- 约束：无水印、无多余 logo、不改变人脸/产品形状等。
- 图片输出路径和 prompt 归档路径。
- 高清、复杂 prompt 或公网入口调用时，优先使用 streaming 演示路径。

## 编辑检查

编辑时先定义不变量：

- 哪些图片是参考图。
- 必须保持：身份、姿势、产品形状、构图、文字、颜色、背景、光线。
- 需要改变：对象、背景、风格、镜头、文字、材质、局部区域。
- 使用 mask 时，确认有 alpha 通道且尺寸匹配源图。

## 尺寸

`gpt-image-2` 支持更多尺寸；优先使用官方常见尺寸，复杂尺寸需满足边长、比例、像素总量限制。

| 用途 | 尺寸 |
| --- | --- |
| 方形社媒/产品/头像 | `1024x1024` |
| 竖版海报/手机封面 | `1024x1536` |
| 横版 hero/产品 banner | `1536x1024` |
| 2K 方形成品 | `2048x2048` |
| 4K 横版 | `3840x2160` |
| 4K 竖版 | `2160x3840` |

文字多、产品成品、UI mockup、图解、品牌资产用 `high`；草稿探索用 `low`。

## Codex App

1. 把用户自然语言需求转成结构化 brief。
2. 需要参考图时，让用户在 Codex app 附图或提供文件路径。
3. 有 shell 和 Python 时运行 `scripts/mtm_image2.py`。
4. 命令返回后报告保存路径。
5. 修订时基于上一次 prompt 和图片路径继续，不从模糊需求重来。

## 高清稳定路径

需要 2K/4K、`quality=high`、复杂写实图、产品成品或公网网关容易超时的任务，先读 `references/stable-highres-demo.md`，优先运行：

```text
python scripts/mtm_image2.py --prompt "<final prompt>" --size 2048x2048 --quality high --format jpeg --stream --partial-images 2
```

只有在确认链路可稳定承受同步长等待时，才用 `stream=false` 做最终同步生成。产品化接口更适合异步 job：快速返回 job id，后台生成，客户端轮询或下载结果。

## 失败处理

- 缺少 API key：先检查当前进程是否已有 `OPENAI_API_KEY`，再检查 Codex provider `env_key` 指向的环境变量；不要让用户把密钥贴到公开 issue。
- 端点不支持：确认 provider 是否支持 `/v1/images/generations` 和 `/v1/images/edits`。
- 模型不可用：说明请求的模型，建议检查 `/v1/models`。
- 公网超时：对比 `scripts/demo_sync_baseline.sh` 和 `scripts/demo_stream_highres.sh`；stream 成功而 sync 超时通常是链路空闲超时。
- 拒绝或审核失败：概括原因，给出合规改写。
- 出图质量差：保留 prompt/report，只调整具体字段。

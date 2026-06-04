# 流式生图

## 核心流程

1. 把用户需求整理成结构化 prompt。
2. 先运行 `scripts/mtm_image_gen.py --probe`，确认当前 provider 的图片能力。
3. 选择尺寸、质量、格式和输出路径。
4. 调用 `scripts/mtm_image_gen.py`；正常生图只走 `/v1/images/generations`，并强制 `stream=true`。
5. 保存最终 prompt、图片和 JSON report。

## 命令

能力探测：

```text
python scripts/mtm_image_gen.py \
  --probe \
  --report-output /tmp/mtm-image2-probe.json
```

真实生图：

```text
python scripts/mtm_image_gen.py \
  --prompt "<final prompt>" \
  --output "./out/product-hero.png" \
  --size 2048x2048 \
  --quality high \
  --format jpeg \
  --partial-images 2
```

`--output` 必须显式传入。未指定 `--prompt-output` 和 `--report-output` 时，脚本会在图片同目录生成 `<name>.prompt.md` 和 `<name>.report.json`。

## 环境

- `OPENAI_API_KEY`：首选认证来源。
- `OPENAI_BASE_URL` 或 `OPENAI_API_BASE`：可选，支持 root 或 `/v1` 形式。
- `OPENAI_IMAGE_MODEL`：可选，默认 `gpt-image-2`。
- Codex provider：脚本可读取 `~/.codex/config.toml` 的 `base_url`、`env_key`、headers 和 query params，但只读取当前进程已有环境变量，不手动解析 `.env`。

不要把 key 写入技能目录、仓库、issue、prompt 或 report。

## Prompt 结构

```text
为[受众/用途]创建[资产类型]。

主体：
- ...

构图：
- ...

风格与渲染：
- ...

光线与镜头：
- ...

图片文字：
- 精确文字："..."
- 语言：...
- 位置：...

约束：
- 无水印、无多余 logo、无拼错文字、保持主体形状。

输出：
- 尺寸：...
- 质量目标：...
```

只有缺失信息会显著改变结果时才问一个短问题；用户说“你决定”时，选择合理默认值并简短说明。

## 参数

- `--size`：常用 `1024x1024`、`1536x1024`、`1024x1536`、`2048x2048`、`2048x1152`、`3840x2160`、`2160x3840`。
- `--quality`：草稿用 `low`，常规成品用 `medium`，产品图/海报/UI mockup/图解用 `high`。
- `--format`：默认 `png`；关注速度或体积时用 `jpeg` 或 `webp`。
- `--partial-images`：`0..3`；公网入口或高清图建议 `1..2`。
- `--codex-profile`：需要显式选择 Codex provider profile 时使用。

`gpt-image-2` 尺寸需满足两边为 16 的倍数、长短边比例不超过 3:1、最长边不超过 3840px，并满足像素总量限制。超过 `2560x1440` 总像素的输出属于实验路径，失败时先降到 2K 级别验证。

## 验收

一次真实可用结果必须满足：

1. `--probe` 返回 `can_generate_image: true`，或者同一次生图命令返回 JSON report。
2. `images` 中至少有一个最终图片路径。
3. report 中记录 `model`、`size`、`quality`、`stream=true`、`prompt`、`images`。
4. 图片文件来自 API 返回的 base64 事件；不得用本地绘图替代。

`prompt-only` 模式只能说“prompt 已准备”，不能说“图片已生成”。

## 失败处理

- `/v1/models` 列出 `gpt-image-2` 但 `--probe` 的 `can_generate_image=false`：按不可出图处理；模型列表只是路由目录，不证明图片端点或账号组权限可用。
- 缺少 API key：检查当前进程是否已有 `OPENAI_API_KEY`，再检查 Codex provider `env_key` 指向的环境变量；不要让用户把密钥贴到公开 issue。
- `/images/generations` 404：网关不支持图片端点或 base URL 错误；确认 provider 是否支持 Image API。
- `/images/generations` 403 且 message 类似 `Image generation is not enabled for this group`：上游账号组没有图片能力，需要启用图片权限或更换上游。
- `/images/generations` 502：公网服务在线不等于 Images API 可用；优先排查上游 origin/网关对图片端点的转发。
- `/responses` 返回 200 但 `output_types` 只有 `message`，或文本里是 SVG/Data URL：这是文本模型绕开图片工具的结果，不是 GPT Image 出图。
- `model not found`：上游未启用 `gpt-image-2`；查询 `/v1/models` 或选择已启用的 GPT Image 模型。
- 公网长请求 524/超时：保持 streaming；产品接口改成异步 job；必须同步时才验证网关非流式 keepalive。
- 拒绝或审核失败：概括原因，给出合规改写。
- 出图质量差：保留 prompt/report，只调整具体字段。

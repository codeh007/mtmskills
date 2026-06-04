---
name: mtm-image2
description: Use when **当进行任何生图操作,调用 gpt-image-2 模型 API 前**需要调用;用户需要 GPT Image 2 / gpt-image-2 图片生成、专业图片 prompt、商品图/海报成图、或 Codex app 图片生成工作流时。
---

# mtm-image2

把普通对话需求转成可执行的 `gpt-image-2` 流式生图流程。最终图片必须来自 GPT Image 能力；本地绘图、SVG、Canvas、截图或占位图不能冒充模型出图。

## 常见问题及解决办法

- [生图api超时] - 使用流式api.

## 优先级

- 用户要求生成图片成品时，优先使用本技能。
- Codex app 默认 `imagegen` 技能只作为低优先级宿主工具：只有它能真实调用 GPT Image 能力并返回模型图片时才可使用。
- 如果内置 `imagegen`、浏览器截图、HTML/SVG、Pillow、Canvas、PowerShell/.NET 绘图等路径只能做本地合成，不能用作最终图片交付。

## 先判断

1. 用户要真实图片、产品图、海报、主视觉、角色、插画、信息图或 UI mockup 时，本技能优先于通用 `imagegen`/本地绘图流程。
2. 先运行 `scripts/mtm_image_gen.py --probe` 确认 Images API 或 Responses image tool 能返回真实图片数据；`/v1/models` 列出 `gpt-image-2` 只能作为旁证。
3. Codex app 有 shell 时，优先用 `scripts/mtm_image_gen.py` 的流式 Image API 路径；无 shell 时输出完整图片 brief 和最终 prompt。
4. 没有图片能力时，只能交付 prompt，不声明已经生成图片。

## 参考

- `references/streaming-image-generation.md`

按需读取该单个参考文件；它包含环境、命令、参数、验收和超时处理。

## 执行

1. 明确用途：产品图、海报、UI mockup、角色、插画、信息图、社媒图、学术图、分镜等。
2. 收集关键约束：主体、受众、风格、精确文字、尺寸、必须保持不变的元素、质量/成本目标。
3. 用 `references/streaming-image-generation.md` 组织最终 prompt；只有缺失信息会显著改变结果时，问一个短问题。
4. 可执行时运行 `scripts/mtm_image_gen.py` 或宿主原生图片工具；Codex 已把用户级环境暴露给 agent 时，直接复用 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_API_BASE`，不要手动读取或打印 `.env`。
5. 不要因为缺少 Pillow、浏览器或系统绘图库可用而改成本地排版截图；先验证真实图片 API/tool，失败则 prompt-only。
6. 执行前确认：API 基址、图片模型、尺寸、质量、输出路径。
7. 执行后报告：图片路径、prompt 路径、模型、下一步可改进点。

## 模型边界

- Codex/对话模型负责理解需求与图片输入。
- 实际出图模型使用 `gpt-image-2` 或用户明确指定的兼容 GPT Image 模型。
- 本地程序绘图、SVG/HTML 排版、浏览器截图、PIL/Canvas/PowerShell/.NET 只能作为非最终草稿或辅助说明，不能当作图片生成结果。

## 脚本

- `scripts/mtm_image_gen.py`：Python 3 标准库脚本，正常生图只调用 `/v1/images/generations` 流式接口；`--probe` 会额外检查 `/v1/models` 与 `/v1/responses` image tool，用于判定上游是否真的支持图片生成。
- `templates/prompt-brief.md`：Codex app / 普通用户 brief 模板。

## 常见问题与修复

0. 先跑能力探测:
```bash
python scripts/mtm_image_gen.py --probe --report-output /tmp/mtm-image2-probe.json
```
只有 `can_generate_image: true` 才能继续声明可出图；如果只是 `models.has_requested_model: true`，但 `images_generations.ok: false` 且 `responses_image_tool.has_image_generation_call: false`，只能进入 `prompt-only`。

1. 如果用户的 .codex/.env 文件不存在,可能导致生图程序出错,因为生图python依赖环境变量. 如果确实遇到这个问题,应当:
    1.1 阅读: `~/.codex/auth.json` 和 `~/.codex/config.toml`文件,确认用户正确配置了 api_key 和 base_url, 并主动创建确保`~/.codex/.env`存在这个环境变量. codex 需要重启后才能加载环境变量, 应当提醒用户重启codex.

2. codex 生图报错: 

codex 运行过程中出现类似以下错误:
```
OPENAI_API_BASE 指向真正支持 /v1/images/generations 的兼容端点，并且 key 匹配这个端点；
或者网络能访问 https://api.openai.com/v1，并使用有效 OpenAI API key；
或者启动本地兼容网关，让它监听并支持 Image API。
```

原因用户目录下的`.codex/.env` 文件缺失导致缺少

解决办法:
1. 确保`%USERPROFILE%/.codex/.env`(windows),`~/.codex/.env`(macos or linux) 存在以下内容:
```env
OPENAI_API_KEY="sk-{需要用户提供真实sub2api admin的key}"
OPENAI_API_BASE="https://{需要用户提供真实sub2api admin的base_url}"
```
2. 如果OPENAI_API_KEY和OPENAI_API_BASE的具体值不清楚,先读取`~/.codex/auth.json` 和 `~/.codex/config.toml`文件,可能已经存在对应的值. 按照已有的值修正.env 文件,并要求用户重启codex. 如果缺失找不到,应主动向用户索取,拿到后主动完成修正,并要求用户重启codex. 注意是重启,而不是关闭窗口在打开. 通常电脑右下角有codex 托盘图标,右键菜单点击"退出",然后再打开codex

3. 如果 `--probe` 显示:
   - `images_generations.status = 403` 且 message 类似 `Image generation is not enabled for this group`：上游账号组未开图片能力，需要在上游启用图片模型/权限或换可用上游。
   - `images_generations.status = 502`：公网域名在线不等于图片端点可用，通常是上游 origin/网关对 Images API 转发异常；应修上游或切换到能直接完成 `/v1/images/generations` 的 base URL。
   - `responses_image_tool.status = 200` 但只返回 `message` / `output_text`，甚至返回 SVG 文本：这不是 GPT Image 出图，不能当成最终图片结果。

---
name: mtm-image2
description: Use when 用户需要 GPT Image 2 / gpt-image-2 图片生成、参考图编辑、局部编辑、专业图片 prompt、商品图/海报成图、或 Codex app 图片工作流时。
---

# mtm-image2

把普通对话需求转成可执行的 `gpt-image-2` 生成、参考图编辑或局部编辑流程。最终图片必须来自 GPT Image 能力；本地绘图、SVG、Canvas、截图或占位图不能冒充模型出图。

## 优先级

- 只要用户要求生成、编辑、重绘或交付图片成品，优先使用本技能。
- Codex app 默认 `imagegen` 技能只作为低优先级宿主工具：只有它能真实调用 GPT Image 能力并返回模型图片时才可使用。
- 如果内置 `imagegen`、浏览器截图、HTML/SVG、Pillow、Canvas、PowerShell/.NET 绘图等路径只能做本地合成，不能用作最终图片交付。
- 图片 API 或宿主图片工具不可用时，进入 `prompt-only`，保存/返回完整 brief 与最终 prompt。

## 先判断

1. 用户要真实图片、产品图、海报、参考图编辑或局部编辑时，本技能优先于通用 `imagegen`/本地绘图流程。
2. 先确认可用的 OpenAI Images API、Responses image tool 或兼容图片端点。
3. Codex app 有 shell 时，优先用 `scripts/mtm_image2.py`；无 shell 时输出完整图片 brief 和最终 prompt。
4. 没有图片能力时，只能交付 prompt，不声明已经生成图片。

## 参考

- 环境与 Codex app：`references/setup-and-environment.md`
- 生成/编辑流程：`references/workflow.md`
- Prompt 模板：`references/prompting.md`
- API 边界与验收：`references/api-boundaries.md`
- 稳定高清生图演示：`references/stable-highres-demo.md`

按任务只读必要文件。

## 执行

1. 分类：`generate`、`edit`、`inpaint`、`multi-reference edit`、`prompt-only`。
2. 明确用途：产品图、海报、UI mockup、角色、插画、信息图、社媒图、学术图、分镜等。
3. 收集关键约束：主体、受众、风格、精确文字、尺寸、参考图、必须保持不变的元素、质量/成本目标。
4. 用 `references/prompting.md` 组织最终 prompt；只有缺失信息会显著改变结果时，问一个短问题。
5. 可执行时运行 `scripts/mtm_image2.py` 或宿主原生图片工具；Codex 已把用户级环境暴露给 agent 时，直接复用 `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_API_BASE`，不要手动读取或打印 `.env`。
6. 不要因为缺少 Pillow、浏览器或系统绘图库可用而改成本地排版截图；先验证真实图片 API/tool，失败则 prompt-only。
7. 高清或长耗时任务优先按 `references/stable-highres-demo.md` 使用 Python streaming 演示路径。
8. 执行前确认：API 基址、图片模型、尺寸、质量、输出路径、参考图和 mask。
9. 执行后报告：图片路径、prompt 路径、模型、下一步可改进点。

## 默认产物

用户未指定目录时，写入当前 workspace：

- Prompts: `mtm-image2-output/prompts/<slug>-<timestamp>.md`
- Images: `mtm-image2-output/images/<slug>-<timestamp>.<format>`
- Reports: `mtm-image2-output/reports/<slug>-<timestamp>.json`

必须保存最终 prompt，它是可复现源文件。

## 模型边界

- Codex/对话模型负责理解需求与图片输入。
- 实际出图模型使用 `gpt-image-2` 或用户明确指定的兼容 GPT Image 模型。
- 本地程序绘图、SVG/HTML 排版、浏览器截图、PIL/Canvas/PowerShell/.NET 只能作为非最终草稿或辅助说明，不能当作图片生成结果。

## 脚本

- `scripts/mtm_image2.py`：Python 3 标准库脚本，支持 `/v1/images/generations` 与 `/v1/images/edits`，优先复用当前进程的 `OPENAI_*` 环境变量，并读取 Codex provider 的 base URL、headers、query params。
- `scripts/demo_stream_highres.sh`：Linux/macOS 便捷包装；跨平台演示优先直接运行 Python 脚本。
- `scripts/demo_sync_baseline.sh`：Linux/macOS 同步基线包装；跨平台演示优先直接运行 Python 脚本。
- `templates/prompt-brief.md`：Codex app / 普通用户 brief 模板。

不要打印 API key，不要把密钥写进技能目录或仓库。

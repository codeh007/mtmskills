# mtmskills

## 安装

面向日常使用时，直接从 GitHub 安装：

```bash
npx skills add --all --global --yes codeh007/mtmskills
```

## 安装

```bash
npx skills add /workspace/mtmskills --list --full-depth
npx skills add /workspace/mtmskills --all --global --yes --full-depth
npx skills add . --all --global --yes --full-depth
```

# 收集的技能仓库

- https://github.com/anthropics/skills
- https://github.com/mattpocock/skills
- golang 开发 - https://github.com/cxuu/golang-skills
- https://github.com/samber/cc-skills-golang/tree/main/skills
- https://github.com/vercel-labs/skills
- https://github.com/lennney/stop-that-shit
- https://github.com/humanlayer/skills/tree/main/plugins/show-me/skills/show-me - 画图告诉我

# harness 框架收集

- https://github.com/garrytan/gstack

# 编程规范及优化

- https://github.com/DietrichGebert/ponytail 强迫AI少些代码


# 优化-压缩-节省token

- [rtk](https://www.rtk-ai.app)
- [headroom](https://github.com/headroomlabs-ai/headroom) - 视频: https://www.youtube.com/watch?v=UXfkQokND4g Headroom compresses everything your AI agent reads — tool outputs, logs, RAG chunks, files, and conversation history — before it reaches the LLM. Same answers, fraction of the tokens.


# 设计类skill

- [Impeccable](https://github.com/pbakaus/impeccable)
- [baoyu skills](https://github.com/jimliu/baoyu-skills) 22k starts

# 其他

- [shadcn 作者 improve skills] (https://github.com/shadcn/improve)

# 前端开发类

- https://pols.dev/slop.md - 避免AI味.
- https://github.com/Nutlope/hallmark - A design skill for Claude Code, Cursor, and Codex that refuses to look AI-generated.


https://github.com/yikart/AiToEarn


## 热门库

- https://github.com/img2threejs/img2threejs 给定一个图片, 基于llm的方式生成3d视图.
1️⃣ diagram-design — 给 Claude Code 和 Codex 用的画图技能包，38 种图表，纯 HTML+SVG 浏览器直接开，不用构建。装完还能读你自己网站，把配色和字体抄过来。本周涨 14397⭐，全榜最猛
2️⃣ MoneyPrinterTurbo — 给个主题就出成片，脚本、素材、字幕、配乐、合成一条龙，还能一键传 TikTok 和 YouTube Shorts。2024 年的老项目，11.2w⭐
3️⃣ needle — 45M 参数，整个模型就是一个 14MB 的文件，跑一轮会话约 28MB 内存。专做工具调用和结构化抽取，手机、手表这类小设备是它瞄的场景
4️⃣ unsloth — 以前是个微调库，现在出了桌面应用，本地跑模型和训模型在一个界面里。刚加 Qwen3.8-27B。「快 2 倍省 70% 显存」是官方自述数据
5️⃣ macro — 邮件、聊天、文档、任务、CRM、agent 装进一个工作区，全部 @ 互链、共享团队级记忆。AGPL-3.0，可以自建
6️⃣ modly — 一张图或者一句话出一个 3D 模型，全程跑自己的显卡。许可证是 MIT 加一条署名条款，fork 出去要标出处
7️⃣ ai-memory — Claude Code 干到一半退出，同目录换 Codex 接着干，不用重讲架构和试过的死路。记忆是 git 里的普通 markdown，能 grep，不用管向量库
8️⃣ OpenViking — 火山引擎出的 agent 上下文数据库，记忆、资源、技能存成一个虚拟文件系统，agent 用 ls、tree、find 自己翻，检索还留轨迹
9️⃣ llmfit — 一条命令扫一遍你的内存、CPU、显卡，告诉你哪些模型在这台机器上真跑得动。跑完基准还能提 PR 把实测速度交回项目
🔟 Switchyard — NVIDIA 出的 LLM 流量代理，OpenAI 和 Anthropic 两套 API 互相翻译，后端随便换。README 明写 pre-alpha，别上生产
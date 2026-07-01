# mtmskills

```bash
# 首次获取源码；也可以替换为你自己的 checkout 路径
git clone https://github.com/codeh007/mtmskills.git 
# 预览
gomtm skills link . --dry-run
gomtm skills link .
```

## 安装

```bash
npx skills add --all --global --yes codeh007/mtmskills
```

## 目录结构

```text
skills/
  mtmskills/
    <skill-name>/SKILL.md
    <group>/<skill-name>/SKILL.md
```

`SKILL.md` frontmatter `name` 仍是技能名；`gomtm skills link .` 默认保留目录级 namespace，并分别链接到 Codex、Hermes Agent、Claude Code 的用户级技能目录。

# 收集的技能仓库

- https://github.com/anthropics/skills
- https://github.com/mattpocock/skills
- golang 开发 - https://github.com/cxuu/golang-skills
- https://github.com/samber/cc-skills-golang/tree/main/skills
- https://github.com/vercel-labs/skills

# harness 框架收集

- https://github.com/garrytan/gstack

# 编程规范及优化

- https://github.com/DietrichGebert/ponytail


# 优化-压缩-节省token

- [rtk](https://www.rtk-ai.app)
- [headroom](https://github.com/headroomlabs-ai/headroom) - 视频: https://www.youtube.com/watch?v=UXfkQokND4g Headroom compresses everything your AI agent reads — tool outputs, logs, RAG chunks, files, and conversation history — before it reaches the LLM. Same answers, fraction of the tokens.


# 设计类skill

- [Impeccable](https://github.com/pbakaus/impeccable)
- [baoyu skills](https://github.com/jimliu/baoyu-skills) 22k starts

# 其他

- [shadcn 作者 improve skills] (https://github.com/shadcn/improve)


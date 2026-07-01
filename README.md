# mtmskills

`mtmskills` 是私有 agent skills 源码仓库。源码目录是本地开发时的唯一真相源；不要把正在维护的 skills 复制安装成长期使用副本。

## 本地开发安装（推荐）

不要在本地开发场景使用 `npx skills add . --all --global --yes` 复制安装；复制会让 `~/.hermes/skills`、`~/.agents/skills` 与源码分叉。

先获取或更新源码，然后直接使用已发布的 `gomtm` 命令创建目录级 symlink：

```bash
# 首次获取源码；也可以替换为你自己的 checkout 路径
git clone https://github.com/codeh007/mtmskills.git 

# 预览
gomtm skills link . --dry-run

# 应用到 Hermes/Codex/Claude 三端
gomtm skills link .
```

已有 checkout 时只需要在仓库根目录执行 `gomtm skills link .`；命令会按约定查找 `skills/` 目录并发现其中符合规范的 skill。不要使用 `go run ./cmd`，也不要假定机器上存在 `/workspace/gomtm` 或 `/workspace/mtmskills`。

## 远程/一次性安装

远程机器或只读环境可以继续使用 `npx skills` 做复制式安装，但这不应作为本机源码开发工作流：

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


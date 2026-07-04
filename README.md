# mtmskills

mtmskills 是公开的 agent skills 仓库，源码权威位置是本仓库的 `skills/mtmskills/**/SKILL.md`。

```bash
# 首次获取源码；也可以替换为你自己的 checkout 路径
git clone https://github.com/codeh007/mtmskills.git 
# 预览
gomtm skills link . --dry-run
gomtm skills link .
```

## 安装

面向日常使用时，直接从 GitHub 安装：

```bash
npx skills add --all --global --yes codeh007/mtmskills
```

## 基于 npx skills 的开发安装

`npx skills` 支持把本地目录作为 package 来源：

```bash
npx skills add /workspace/mtmskills --list --full-depth
npx skills add /workspace/mtmskills --all --global --yes --full-depth
```

如果只想安装到指定 agent，可以显式指定：

```bash
npx skills add /workspace/mtmskills --skill gomtm-skills-improve --agent codex --global --yes --full-depth
npx skills add /workspace/mtmskills --skill gomtm-skills-improve --agent hermes-agent --global --yes --full-depth
```

需要注意：`npx skills` 的默认 symlink 模式是让不同 agent 目录指向一个 canonical 安装副本，而不是让 canonical 安装副本指向本仓库源码。以 `skills@1.5.14` 为例，本地路径安装会先把技能复制到 `~/.agents/skills/<skill-name>` 或对应 canonical 目录；只有 agent 目标目录可能再通过 symlink 指向这个 canonical 目录。

因此，如果 Codex、Hermes Agent 或其他 agent 修改的是安装后的 `~/.agents/skills/...`、`~/.codex/skills/...`、`~/.hermes/skills/...`，这些修改不会自动回写到 `/workspace/mtmskills/skills/...`。开发技能时应明确要求 agent 修改本仓库源码路径，修改后再运行 `npx skills add /workspace/mtmskills ...` 重新安装同步。

`--copy` 会强制复制到各 agent 目录，进一步增加多份副本；开发环境通常不要使用它，除非当前系统不支持 symlink。

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

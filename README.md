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
npx skills add https://github.com/codeh007/mtmskills --all --global --yes
```

## 目录结构

```text
skills/
  mtmskills/
    <skill-name>/SKILL.md
    <group>/<skill-name>/SKILL.md
```

`SKILL.md` frontmatter `name` 仍是技能名；`gomtm skills link .` 默认保留目录级 namespace。Hermes Agent 也读取 `~/.agents/skills`，因此不需要额外改写 Hermes 配置。

## 贡献

- 技能名使用小写 `hyphen-case`。
- `SKILL.md` frontmatter 保持 `name` 和 `description` 两个必要字段。
- `description` 只写触发条件，不写流程摘要。
- 技能应自包含；不要依赖私有路径、密钥或本机环境。
- 只有确实需要时才添加 `scripts/`、`references/`、`assets/`。

# 收集的技能仓库

- https://github.com/anthropics/skills
- https://github.com/mattpocock/skills
- golang 开发 - https://github.com/cxuu/golang-skills
- https://github.com/samber/cc-skills-golang/tree/main/skills
- https://github.com/vercel-labs/skills

# harness 框架收集

- https://github.com/garrytan/gstack

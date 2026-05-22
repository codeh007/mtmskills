# mtmskills

## 安装

```bash
# 全局安装(覆盖已有更新)
npx skills add https://github.com/codeh007/mtmskills --all --global --yes
# 从本地安装
npx skills add . --all --global --yes
```

安装指定技能到 Codex：

```bash
npx skills add https://github.com/codeh007/mtmskills --skill demo-smoke-test -a codex
```

## 目录结构

```text
skills/
  <skill-name>/
    SKILL.md
    agents/openai.yaml  # 可选
```

`skills/<skill-name>` 必须与 `SKILL.md` frontmatter 中的 `name` 一致。

## 贡献

- 技能名使用小写 `hyphen-case`。
- `SKILL.md` frontmatter 保持 `name` 和 `description` 两个必要字段。
- `description` 只写触发条件，不写流程摘要。
- 技能应自包含；不要依赖私有路径、密钥或本机环境。
- 只有确实需要时才添加 `scripts/`、`references/`、`assets/`。


# 收集的 技能仓库

- https://github.com/anthropics/skills
- https://github.com/mattpocock/skills
- golang 开发 - https://github.com/cxuu/golang-skills
- https://github.com/samber/cc-skills-golang/tree/main/skills
- https://github.com/vercel-labs/skills

# harness 框架收集

- https://github.com/garrytan/gstack
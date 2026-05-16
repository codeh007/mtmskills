# mtmskills

面向 Agent 的可安装 Skills 集合。

## 安装

列出可安装技能：

```bash
npx skills add codeh007/mtmskills --list
```

安装指定技能到 Codex：

```bash
npx skills add codeh007/mtmskills --skill demo-smoke-test -a codex
```

全局安装：

```bash
npx skills add codeh007/mtmskills --skill demo-smoke-test -a codex -g -y
```

从本地仓库安装：

```bash
npx skills add /workspace/mtmskills --list
npx skills add /workspace/mtmskills --skill demo-smoke-test -a codex -g -y
```

## 更新

重新执行安装命令即可覆盖已安装技能：

```bash
npx skills add codeh007/mtmskills --skill demo-smoke-test -a codex -g -y
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

提交前运行：

```bash
scripts/validate-skills
```

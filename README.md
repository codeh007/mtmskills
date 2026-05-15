# mtmskills

`mtmskills` 是 MTM 相关 Agent Skills 的独立仓库，用来把可复用技能从 `gomtm` 主项目中拆出来，方便 Codex、hermes-agent 以及其他支持标准 Agent Skills 布局的工具安装和使用。

## 仓库结构

```text
skills/
  gomtm-demo1/
    SKILL.md
    agents/openai.yaml
  gomtm-demo2/
    SKILL.md
    agents/openai.yaml
```

每个技能都是一个独立目录，目录名必须和 `SKILL.md` frontmatter 里的 `name` 保持一致。

## 技能规范

- 技能名使用小写 `hyphen-case`。
- `SKILL.md` frontmatter 默认只写 `name` 和 `description`。
- `description` 聚焦“什么时候应该使用这个技能”，不要写成流程摘要。
- `SKILL.md` 保持精简；较长参考资料放到一级 `references/` 文件中。
- 只有确实需要时才增加 `scripts/`、`references/`、`assets/`。
- 需要 Codex 展示元数据时，使用 `agents/openai.yaml`。

## 安装技能

推荐使用标准 Agent Skills CLI：

```bash
npx skills add codeh007/mtmskills --list
npx skills add codeh007/mtmskills --skill gomtm-demo1 -a codex
npx skills add codeh007/mtmskills --skill gomtm-demo2 -a codex
npx skills add codeh007/mtmskills --skill gomtm-demo1 -a hermes-agent
```

全局安装到 Codex：

```bash
npx skills add codeh007/mtmskills --skill gomtm-demo2 -a codex -g -y
```

开发本仓库时，可以从本地 checkout 安装：

```bash
npx skills add /workspace/mtmskills --list
npx skills add /workspace/mtmskills --skill gomtm-demo2 -a codex -g -y
```

也可以手动复制或软链接到目标 Agent 的技能目录：

```bash
git clone https://github.com/codeh007/mtmskills.git
mkdir -p ~/.codex/skills
cp -R mtmskills/skills/gomtm-demo2 ~/.codex/skills/
```

通过 GitHub 安装时，仓库必须是公开仓库，或者当前环境必须拥有读取该私有仓库的 GitHub 凭据。

## 更新技能

技能仓库会频繁更新。已经安装过技能后，推荐直接重新运行相同的 `npx skills add ... --skill ...` 命令覆盖安装目标技能。这条路径已经用 `gomtm-demo2` 验证过：推送主分支后，重新执行 `skills add` 能把本机旧版技能更新到新内容。

从 GitHub 覆盖更新某个技能：

```bash
npx skills add codeh007/mtmskills --skill gomtm-demo2 -a codex -g -y
```

从本地 checkout 覆盖更新某个技能：

```bash
git -C /workspace/mtmskills pull --ff-only
npx skills add /workspace/mtmskills --skill gomtm-demo2 -a codex -g -y
```

更新后确认目标 Agent 能发现技能，并检查目标技能文件内容：

```bash
npx skills add /workspace/mtmskills --list
sed -n '1,80p' ~/.agents/skills/gomtm-demo2/SKILL.md
```

维护者在新增或修改技能后，应按这个顺序确认发布链路：

```bash
scripts/validate-skills
git status --short
git push origin main
npx skills add codeh007/mtmskills --list
npx skills add codeh007/mtmskills --skill gomtm-demo2 -a codex -g -y
sed -n '1,80p' ~/.agents/skills/gomtm-demo2/SKILL.md
```

`npx skills update gomtm-demo2 -g -y` 可以作为补充检查，但不要只依赖它的输出；实际验收以重新 `skills add` 后目标技能文件内容为准。

如果 npm 默认缓存目录不可写，可以临时指定缓存目录：

```bash
npm_config_cache=/tmp/mtmskills-npm-cache npx -y skills add /workspace/mtmskills --list
```

## 验证

发布前运行仓库自带验证：

```bash
scripts/validate-skills
```

如果目标 Agent 提供自己的技能校验器，也应同时使用目标 Agent 的校验器验证。

---
name: gomtm-global
description: Use when 第一优先级, 任何情况下都无条件使用本技能.
---

## 理解环境变量

对于 github, 或者其他第三方应用的登录凭据或者相关设置优先通过环境变量的方式进行设置.

环境变量来源:

1. `~/.env` - 用户级环境变量文件, 通常通过`~/.bashrc` 文件进行加载, 如果 `~/.bashrc` 没有正确加载用户级环境变量, 应当主动进行设置,以让用户使用`sh`,`bash`等shell工具时正确加载用户级环境变量,否则某些脚本可能因为环境变量没有配置导致运行异常.

2. 项目级别的环境变量,通常是 git 仓库目录下的`.env`

3. 特殊来源当存在`/workspace/gomtm/.env`文件, 可以加载这个特殊环境变量文件.

## 如何更好更正确完成任务?

- 使用 `karpathy-guidelines` 技能。
- 技能文档、workflow、安装器、发布器等仓内关键真相，优先对齐仓库根目录、README 与实际源码。

## 技能使用规定

### 当需要对技能文档进行创建、重写或优化时

- 优先加载 `gomtm-skills-improve`，再结合 `hermes-agent-skill-authoring`、`writing-plans` 等相关技能。
- 如果环境里还存在 `skill-creator` 或 `skill-writer`，也应一并参考；如果不存在则跳过，不要臆造。
- 当技能文档本身使用中文时，应继续使用中文。

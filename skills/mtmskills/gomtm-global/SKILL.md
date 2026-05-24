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

## gomtm 本地数据目录

- `gomtm` 本地运行数据目录由 `GOMTM_HOME` 指定，未设置时默认 `~/.gomtm`。
- 不再使用项目目录下的 `.gomtm.vol`，也不再通过 runtime `server.storage.root_dir` 配置本机数据目录；配置文档只保存运行时业务配置。
- 源码路径应通过 `mtutils.GOMTMHome()` / `mtutils.StorageDirJoins(...)` 派生；日志默认在 `$GOMTM_HOME/logs/`。

## 如何更好更正确完成任务?

- 使用 `karpathy-guidelines` 技能。
- 技能文档、workflow、安装器、发布器等仓内关键真相，优先对齐仓库根目录、README 与实际源码。

## 技能使用规定

### 当需要对技能文档进行创建、重写或优化时

- 优先加载 `gomtm-skills-improve`，再结合 `hermes-agent-skill-authoring`、`writing-plans` 等相关技能。
- 如果环境里还存在 `skill-creator` 或 `skill-writer`，也应一并参考；如果不存在则跳过，不要臆造。
- 当技能文档本身使用中文时，应继续使用中文。


## 全局源码编程规范

本规范跟编程语言无关, 跟项目类型无关, 是全局适用于所有需要编写代码的场景, 适用于所有需要对代码进行反思重构的场景.
如果目标项目没有具体的特殊规定, 应当以本文档为准.


### 源码文件规定

- 任何程序源码函数必须少于在**350行**

## 相关项目

以下项目通常已经在本机的对应的目录中,应当根据实际情况镜像同步开发, 每个项目(repo)通常是独立的,可能存在依赖关系.
当增加或者删除了相关子项目后,应当**主动维护**以下的项目列表.

- gomtmui - 全站前端
- mtmsub2api - 单镜像启动完整 sub2api服务.

## 路径约定

除非有额外规定,否则按照以下阅读组织相关文件路径

- [临时文件夹] - `~/.tmp`
  - [截屏] - `~/.tmp/screenshots/`
  - [录屏] - `~/.tmp/recordings/`
  - [日志] - `~/.tmp/logs/`


## github 仓库分支规定

- main 分支是最终发布版, 是功能完善完整通过测试和验收后的版本.

## 基于 github issues 进行开发任务编排

- 特殊仓库: `https://github.com/codeh007/mtmwiki` 是知识库以及全局跨多个repo的全局仓库. 如果一个任务不是针对特定仓库的,则通常在这里进行处理.
- 人类仅在: `https://github.com/` 进行项目管理和安排任务, 当写了规格文件或者开发计划文件,应当及时提交, 并在 对应的 issue 回复中带上清晰连接,让人类可以通过点击连接快捷查看对应的文档.

- 当任务来自 github issues 例如:`https://github.com/codeh007/mtmwiki/issues/{id}`, 那么应当在任务结束后提交相关更改并推送到github, 在对应的issue中回复处理结果.

### superpowers 技能规定

1. 当任务来自 github issues, 在 使用 `brainstorming` 或者其他相关技能,需要人类管理员澄清,做选择,拍板的情况时, 应当直接在原issue基础上回复. 而不是在任务对话中登录人类用户选择.

---
name: openclaw-dev
description: Use when 开发、排查或集成仓库中的 OpenClaw 能力，尤其是本地实例启动、配置文件管理、slash/plugin 扩展、宿主机侧诊断，以及确认当前仓库已经移除 `/dash/openclaws` 与旧数据库驱动控制面时。
---


## openclaw 源码

- 源码路径:`/workspace/openclaw` 可以通过命令`git clone https://github.com/openclaw/openclaw /workspace/openclaw`克隆(或者拉取最新版).
- 注意及时拉取最新源码.
- 关键文档[openclaw README](https://github.com/openclaw/openclaw/blob/main/README.md)
- 官方文档[openclaw docs](https://github.com/openclaw/openclaw/blob/main/docs) - 可直接在本地仓库源码中找到.

## 当前入口

1. 本地或宿主机直接启动 OpenClaw：`gomtm openclaw gateway --force`
2. 使用 `gomtm oc` 从仓库化状态启动实例：`gomtm oc --repo=<path_or_repo_uri> gateway --force`
3. 直接调用 OpenClaw CLI：

```bash
OPENCLAW_CONFIG_PATH="/home/code/.openclaw/openclaw.json" openclaw agent --local --agent main -m "ping" --json
```

4. 查看会话：

```bash
openclaw sandbox explain --session "agent:main:telegram:group:-1003702801226" --json
```

## 编程开发约定

1. 不要再把 `/dash/openclaws`、`public.openclaws`、`/api/system/openclaw/runtime` 当成现有能力；这些都已经退役。
2. 如果任务要求“恢复 OpenClaw 控制面”，先停下来确认是不是确实要重新设计，而不是误把历史方案当成现有实现。
3. 在开发环境中，OpenClaw 的实际物理路径仍可使用`/workspace/gomtm/.openclaw/`，必要时链接到`~/.openclaw/`，以兼容官方默认目录。
4. OpenClaw 当前更适合由宿主机或独立仓库状态直接驱动；配置真相优先落在 `openclaw.json` 与其状态目录中，而不是重新引入一套数据库生命周期编排。


## 参考文档

1. `references/openclaw-agent-driven-architecture-analysis.md`
   - 用于判断 Agent-Driven / Database-Driven / 混合模式边界。

## 当前集成边界

1. `gomtm` 目前提供的是 OpenClaw 的安装、启动辅助和通用宿主机环境，而不是内建的 OpenClaw 生命周期控制平面。
2. `gomtm server` 仍然可以作为通用执行环境或网络入口能力的宿主，但当前仓库已经不再维护面向 OpenClaw 的专用数据库编排链路。
3. 如果需要“统一控制多台宿主机上的 OpenClaw”，应优先把它当成新协议设计问题，而不是回退到旧数据库状态机方案。
4. 未来若重建控制面，默认方向是：
   - libp2p 负责控制协议和节点发现
   - OpenClaw 保持自身配置与状态目录为本地真相
   - 对外兼容层按需提供 HTTP / WebSocket / Webhook，而不是把 HTTP 端点当内部真相

## 架构不变量（PDDL）

| 约束 | 内容 |
|------|------|
| 前置条件 | 宿主机已安装 OpenClaw，且存在可用的 `openclaw.json` / 状态目录 |
| 效果 | OpenClaw 可以以独立实例方式启动、诊断、暴露到公网或接入外部自动化链路 |
| 不变量 | 当前仓库不再以内建数据库控制面驱动 OpenClaw 生命周期 |

## 服务隧道与端点暴露（设计基线）

openclaw 实例启动后，必须具备公网可访问能力，否则 Web UI 与外部回调能力不可用。

可选方案：

1. Cloudflare Tunnel
   - 可作为当前阶段的公网暴露方案之一，但它只是部署选择，不代表仓库里仍存在一套 OpenClaw 专用的 gomtm 控制面。
   - 适合当前阶段快速落地。
2. Tailscale（Serve/Funnel）
   - 适合内网或受限公网场景；若要面向公共域名，需额外网关层。
3. 单网关聚合模式
   - 使用独立在线网关，按域名或路径将请求路由到不同实例。
   - 适合大规模实例与统一流量治理。

## 开发流程

1. 先确认任务是在处理独立 OpenClaw 实例的配置/启动/诊断，还是在设计新的 gomtm 集成控制协议。
2. 如果只是启动、排障或状态管理，优先围绕 OpenClaw 本地状态目录、配置文件和宿主机进程诊断展开。
3. 命令扩展优先复用 slash/plugin 机制，避免新增脆弱的中间层。
4. 涉及公网暴露时，先验证域名解析、隧道连通性、路由命中，再验证 UI/Agent 行为。
5. 如果任务试图恢复旧的数据库驱动控制面，应先明确这已经不是修复，而是重建设计。

## 版本对齐规则

1. 仅保留当前有效方案，不做历史兼容叙事。
2. 当 openclaw 或隧道能力升级时，先更新参考文档，再更新本技能。
3. 保持文档聚焦“原则 + 决策 + 流程”，避免写死文件名、函数名、临时实现。


## 开发阶段的问题诊断指引

1. 开发阶段,远程服务器(vps ssh) 就是本机, 所以可以对本地的openclaw进程,文件,日志等进行访问,对于功能验证特别有用. 也可以使用脚本模拟远程启动的方式确认脚本是否可以正常启动; 特别是同时结合了 gomtm server 的源码,在本机进行模拟可以深入地诊断和确认问题.

2. `./scripts/`目录下可能已经有之前任务遗留的诊断脚本,如果没有,可以创建, 运行对诊断脚本进行改写以适配是新情况.

3. 对于openclaw 进程的探测, 不应当仅仅使用 openclaw 进程名,因为 openclaw 是基于nodejs的,进程名可能是node,建议使用端口,或者其他可能的方式深度检测.


## 命令

1. 快速调用 agent 

```
OPENCLAW_CONFIG_PATH="/home/code/.openclaw/openclaw.json" openclaw agent --local --agent main -m "ping" --json
```

2. 查看某个 session 的信息
```
openclaw sandbox explain --session "agent:main:telegram:group:-1003702801226" --json
```


## 避坑指南

1. 防止上游 LLM api 封锁 openclaw 请求

- 如上游 provider 会因为默认请求头封锁 openclaw，请优先在 provider 配置里覆写 `headers.User-Agent` 等必要请求头。
- 技能文档里不要写真实 `apiKey`、私有 base URL 或其他敏感配置；只保留字段名和排障原则。

2. 通常一个主机(容器)只建议运行一个openclaw实例. 虽然运行多个实例原则上是运行的,但是 telegram 机器人(同一个 bot token)会因为多个实例导致冲突
  ```
    03:22:12 [telegram] getUpdates conflict: Call to 'getUpdates' failed! (409: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running); retrying in 30s.
  03:22:23 [telegram] getUpdates conflict: Call to 'getUpdates' failed! (409: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running); retrying in 30s.
  03:22:25 [telegram] getUpdates conflict: Call to 'getUpdates' failed! (409: Conflict: terminated by other getUpdates request; make sure that only one bot instance is running); retrying in 30s.
  ```

## openclaw 行为特性备忘

1. openclaw 能检测对应的openclaw.json配置文件当被修改后会自动重载配置文件, 这个特性对于通过命令(或者脚本)编辑配置文件很有用. 可以确保编辑后自动生效.

2. 命令行权限审批关键文件: `.openclaw/exec-approvals.json`


## 本地练习调试实例

- 通常本机有一个实例正在运行, 是用于手工调试, 和练习用途的.当gomtm 集成的 openclaw 遇到疑难杂症,可以对比本地的实例,辅助问题诊断.

- 本地练习实例,重启命令:`openclaw gateway --force`


## gomtm 封装的 openclaw 命令

- 目的: 设置环境变量, 简单处理相关参数, 目的是为了可以基于gomtm 主程序一键完成 openclaw 的安装和初始化.
- 关键源码: `cmd/openclaw.go` 
- **关键技巧**:
   - openclaw.json 配置文件接受环境变量, 特别是 ${PWD} 环境变量对于动态启动路径相关设置至关重要, 防止使用据对路径写死进而导致多实例配置和工作区的冲突问题.

## 如何设置的 openclaw 实例

关键步骤: 安装 gomtm 命令, 使用`gomtm openclaw gateway --force` 启动 openclaw gateway实例.

如果需要仓库化状态目录,优先使用 `gomtm oc --repo=<path_or_repo_uri> gateway --force`。

gomtm 安装方式:
1. 如果目标主机存在 npm 命令, 可以使用`npm install -g gomtm` 安装.
2. 如果目标主机不存在 npm 命令, 可以使用`curl -fsSL "https://cdn.jsdelivr.net/npm/gomtm/bin/gomtm" -o /usr/local/bin/gomtm && chmod +x /usr/local/bin/gomtm` 安装.

## 如何初始化linux系统环境

对于全新的 linux 系统(debian, ubuntu), 基础环境初始化执行 `gomtm install`。

当需要补齐开发环境时, 执行 `gomtm install --dev`。安装器内部可能使用 `GOMTM_INSTALL_STAGE` 做重入状态，但不要把 `gomtm install --stage=...` 当作用户可见命令。
最终允许 `code` 用户通过 ssh remote 的方式在 vscode 开发环境中进行远程开发.


## 新版设计(v2) - gomtm oc 子命令

命令`gomtm oc` 是第二版用来一键启动 openclaw 的命令

**关键点**

1. 需要明白 openclaw 的启动不需要复杂配置, 在最极端的情况下,只需要`openclaw.json`配置文件即可. 甚至没有任何配置文件, openclaw 也能启动.

2. 本地是否存在 openclaw 状态目录仅决定了 openclaw 的状态,记意,提示词等.

3. 状态文件可以选择仅存放到本地或者使用 githhub 仓库进行辞旧化存储.
   - 如果没有使用独立的github 仓库, 则可能服务器磁盘被清理后无法恢复,除非有其他方式备份了状态文件.
   - 如果配置了github 仓库,则可以使用github仓库进行持久化和版本化存储(管理).
4. 通常建议基于github仓库来管理 openclaw 的状态文件.

5. 通常每个 github openclaw 都有明确的特定用途, 不建议以下情况:
   - 相同的配置运行在多个服务器上, 因为配置本身有很多资源冲突点, 例如, channels 配置, telegram bot配置等,本身就是冲突的的, 因此完全相同的 openclaw配置运行在不同的服务器上几乎肯定会冲突.
   同理: 如果使用 openclaw profile 的方式在同一个linux 服务器上运行多个openclaw 也不建议,至少官方文档虽然提供了这个功能,但是也同时说明大部分情况下建议一台主机部署一个实例.



### gomtm oc 参数选项设计

- [repo]: 以uri方式表示git仓库地址, 例如: `https://{auth_token}@github.com/codeh007/my-openclaw.git`
   - 如果repo以 file:// 开头, 则表示本地路径.


### 典型应用场景

作为人类用户(管理员)

1. 开通了 linux 服务器后, 第一步是设置环境并且第一时间启动 `gomtm oc --repo=<path_to_gomtm_repo> gateway --force`. 此时就可以确保服务器启动了openclaw服务实例. 由于 github 仓库本身已经正确配置了 openclaw 的配置而且可能已经有现成的状态,因此通常都可以正确启动,如果确实启动失败,通常应当由管理员确认仓库中的相关配置正确,修正后重新配置重新在linux运行 gomtm oc命令即可.

当已有现成的 AI Agent (openclaw、codex 等)时

1. 人类用户可以通过自然语言,向 AI Agent, 将目标服务器的 ssh 连接信息告知 ai agent,协助完成 openclaw 的安装和初始化.

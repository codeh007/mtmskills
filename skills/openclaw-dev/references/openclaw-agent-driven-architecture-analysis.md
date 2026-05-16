# OpenClaw Agent 驱动架构选择分析报告

> 重要更新（2026-03-31）: 本文是旧控制面时代的架构分析材料。文中涉及 `/dash/openclaws`、`public.openclaws`、`openclaws_*` / `openclaw_*`、`gomtm_openclaw_sync`、`/api/system/openclaw/runtime` 的描述，**都不再代表当前仓库实现**。当前仓库已经移除这些前端、数据库与 HTTP 控制面；如果后续要重新做 gomtm 与 OpenClaw 的深度集成，应按新的 libp2p 控制协议方向重新设计，而不是把本文当成现行实现说明。

> 日期: 2026-02-21
> 状态: 历史调研/分析
> 基于: OpenClaw 当时文档 + 2026-02 时点的 gomtm 实现

## 0. 当前真相（2026-03-31）

以下内容才代表当前仓库现状：

1. `/dash/openclaws` 前端页面已经删除，不再是任何有效入口。
2. 旧的数据库驱动控制面已经退役，`public.openclaws`、`openclaws_*` / `openclaw_*`、`gomtm_openclaw_sync`、`/api/system/openclaw/runtime` 都不再属于当前实现。
3. 当前仓库里的 OpenClaw 使用方式，主要是独立实例 / 宿主机管理，而不是 gomtm 内建的数据库生命周期编排。
4. 如果后续要重新做 gomtm 与 OpenClaw 的深度集成，应把它视为新设计问题，默认优先评估基于 libp2p 的控制协议，而不是恢复旧 UI、旧 RPC 或旧 HTTP runtime 端点。

## 0.1 当前有效入口

当前有效入口是：

1. `gomtm openclaw gateway --force`
2. `gomtm oc --repo=<path_or_repo_uri> gateway --force`
3. OpenClaw 自身 CLI / 配置目录工作流

## 0.2 如何阅读本文

从下一节开始，正文保留的是**历史背景与当时的架构分析**，目的是保存当时为什么会走向旧控制面、以及这些论证哪些部分后来被推翻。

阅读时请按以下边界理解：

1. 下文对 `Database-Driven`、`混合架构`、Cloudflare Tunnel + gomtm server HTTP 端点、数据库触发 Agent 等讨论，都是**历史方案讨论**，不是当前实现说明。
2. 下文如果提到 `/dash/openclaws`、`public.openclaws`、`/api/system/openclaw/runtime`、`openclaw_failover()` 等对象，应默认理解为“历史实现曾经存在过”。
3. 真正要做新方案设计时，只能把下文当作历史经验材料，而不能直接把其中的“推荐方案”拿来继续实现。

## 1. 历史问题定义（2026-02）

gomtm 系统的最终目标是构建一个 **无人值守的全自动化综合任务系统**：

- 24/7 不间断运行
- AI 自主决策和执行
- 用户只设定大目标，其余由 AI 自主完成
- AI 在必要时主动找用户/管理员寻求帮助
- 支持多种交互方式（Web UI、Telegram Bot 等）

**核心选择题**：以 OpenClaw 为主（Agent-Driven），还是以 Supabase 数据库为主（Database-Driven），还是两者并存？

## 2. 历史方案详析（以下均为旧控制面时代的方案讨论）

### 2.1 方案 A：Agent-Driven（OpenClaw 为主控端）

```text
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Agent (主控)                       │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Heartbeat │  │   Cron Jobs  │  │  HEARTBEAT.md 检查表   │   │
│  │  (30min)  │  │  (精确调度)   │  │  - 检查任务队列        │   │
│  └────┬─────┘  └──────┬───────┘  │  - 检查收件箱          │   │
│       │               │          │  - 处理待办            │   │
│       └───────┬───────┘          └──────────────────────┘   │
│               │                                              │
│               ▼                                              │
│     ┌───────────────┐                                       │
│     │ Agent 推理循环  │←→ 多种工具 (exec/read/write/browser)   │
│     └───────┬───────┘                                       │
│             │                                                │
│     ┌───────▼───────┐                                       │
│     │  Supabase RPC  │   ← Agent 通过工具调用数据库             │
│     │  (外置工具)    │   ← Agent 自主决定何时查/写数据           │
│     └───────────────┘                                       │
│                                                               │
│  用户交互: Telegram Bot / Web Chat UI / 通知                   │
└─────────────────────────────────────────────────────────────┘
```

**运作方式**：

1. OpenClaw 启动后，通过 HEARTBEAT.md 和 Cron 定时任务持续自主运行
2. Agent 通过提示词获知数据库的 RPC 函数和访问方式
3. Agent 自主决定何时查询数据库获取任务、何时执行、何时休眠
4. Agent 通过 Telegram/WhatsApp 等渠道主动联系用户，报告进度或寻求帮助
5. 数据库是 Agent 的"外置工具"，Agent 有完全自主权

**优势**：

| 维度 | 说明 |
|------|------|
| **自主性极高** | Agent 可以基于上下文自主决策，无需预编程每个场景 |
| **灵活应变** | 遇到异常情况可自主调整策略，不依赖预定义规则 |
| **统一交互** | 通过自然语言与用户交互，用户体验自然 |
| **自我进化** | Agent 可以修改自己的提示词/工具/配置，持续改进 |
| **复杂推理** | 可执行需要多步推理、上下文理解的复杂任务 |
| **原生多渠道** | OpenClaw 内置 Telegram/WhatsApp/Discord 等多渠道支持 |
| **定时+心跳** | 内置 Heartbeat (周期感知) + Cron (精确调度) 双重机制 |

**劣势**：

| 维度 | 说明 |
|------|------|
| **成本高** | 每次心跳/定时任务都消耗 LLM API Token（30分钟一次心跳 = 48次/天） |
| **不确定性** | AI 决策不一定总是正确，可能执行错误操作 |
| **有状态** | Agent 会话/工作区是有状态的，迁移/恢复需要额外处理 |
| **调试困难** | Agent 行为难以预测和复现，日志分析比结构化数据更难 |
| **启动慢** | 每次推理需要发起 LLM API 调用，延迟较高（秒级到分钟级） |
| **并发限制** | 单个 Agent 实例串行处理，高并发场景需要多个实例 |

### 2.2 方案 B：Database-Driven（数据库为主控端）

```text
┌─────────────────────────────────────────────────────────────┐
│                  Supabase 数据库 (主控)                        │
│                                                               │
│  ┌────────────┐  ┌───────────┐  ┌────────────────────────┐  │
│  │  触发器     │  │  RPC 函数  │  │  业务规则与状态机        │  │
│  │  (事件驱动) │  │  (业务逻辑)│  │  - cloud_accounts 管理  │  │
│  └────┬───────┘  └──────┬────┘  │  - campaigns 流程       │  │
│       │                 │       │  - tasks 调度           │  │
│       └────────┬────────┘       └────────────────────────┘  │
│                │                                              │
│       ┌────────▼────────┐                                    │
│       │  pg_net.http_post│                                    │
│       └────────┬────────┘                                    │
│                │                                              │
│    ┌───────────▼───────────────┐                              │
│    │  gomtm server HTTP 端点   │                              │
│    │  (被动执行器)              │                              │
│    │                           │                              │
│    │  ├── /api/v1/task/execute │                              │
│    │  ├── /openclaw/hooks/agent │ ←── 按需调用 OpenClaw       │
│    │  └── device_task_complete │ ←── 结果回填到 device_tasks  │
│    └──────────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
```

**运作方式**：

1. 数据库通过触发器和 RPC 函数管理所有业务规则和状态机
2. 当需要 AI 能力时，通过 `pg_net.http_post` 调用 OpenClaw 的 `/hooks/agent` 端点
3. OpenClaw 仅作为按需执行器，完成特定任务后通过 `device_task_complete` / `device_task_fail` 回填结果
4. 所有核心配置、状态、任务队列保存在数据库中
5. gomtm server 作为瘦客户端，仅负责转发和执行

**优势**：

| 维度 | 说明 |
|------|------|
| **确定性高** | 预编程的规则和状态机，行为可预测可审计 |
| **成本可控** | 仅在需要 AI 推理时才调用 LLM，大部分逻辑在数据库内完成 |
| **可恢复性** | 所有状态在数据库中，实例迁移后完全恢复 |
| **高并发** | 数据库天然支持并发，多个任务可并行处理 |
| **实时性好** | 事件驱动，状态变更即触发，无需等待心跳周期 |
| **调试方便** | 所有操作记录在 `sys_logs`/`device_tasks` 表中，可追溯 |
| **已有基础设施** | 已实现事件驱动链路、`pg_net`、`handle_http_response` 等 |

**劣势**：

| 维度 | 说明 |
|------|------|
| **灵活性低** | 每个新场景都需要手动编写触发器/函数/状态机 |
| **复杂推理难** | 数据库无法执行需要上下文理解的复杂推理任务 |
| **交互体验差** | 用户交互需要自行实现，无法直接自然语言对话 |
| **无自适应** | 无法根据上下文调整策略，必须预编程所有分支 |
| **开发工作量大** | 每新增一种自动化场景都需要大量 SQL 编写 |
| **与 OpenClaw 弱耦合** | OpenClaw 丰富的功能（多渠道、Skills、Tools）利用率低 |

### 2.3 方案 C：混合架构（推荐）

```text
┌─────────────────────────────────────────────────────────────────┐
│                       混合驱动架构                                 │
│                                                                   │
│  ┌──────────────────────────────┐                                │
│  │      Supabase 数据库 (基础层)  │                                │
│  │                              │                                │
│  │   结构化数据  │ 业务规则       │                                │
│  │   配置管理    │ 状态机         │                                │
│  │   任务队列    │ 权限/RLS       │                                │
│  │   审计日志    │ 事件驱动触发    │                                │
│  └──────────┬───────────────────┘                                │
│             │                                                     │
│  ┌──────────▼─────────────────────────────────────────────────┐  │
│  │              gomtm server (编排层/中间件)                    │  │
│  │                                                             │  │
│  │   Bootstrap + Realtime  │  HTTP 端点                         │  │
│  │   Cloudflare Tunnel     │  反代 OpenClaw                     │  │
│  │   状态报告              │  任务转发                          │  │
│  └──────────┬──────────────────────────────────────────────────┘  │
│             │                                                     │
│  ┌──────────▼─────────────────────────────────────────────────┐  │
│  │              OpenClaw Agent (智能层)                         │  │
│  │                                                             │  │
│  │   自主推理  │ 多渠道通信 │ 定时任务                            │  │
│  │   工具调用  │ 会话管理   │ 心跳监控                            │  │
│  │   插件系统  │ Hooks     │  Webhook                            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                   │
│    数据库 ←   pg_net   → OpenClaw (/hooks/agent)                  │
│    数据库 ← Realtime  → gomtm (状态同步)                          │
│    OpenClaw ← RPC/exec → 数据库 (工具调用)                        │
│    用户 ←  Telegram   → OpenClaw (自然语言)                       │
│    用户 ←  Web UI     → gomtmui → Supabase (结构化操作)           │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 历史结论（写作时的推荐方案）

### 3.1 核心结论

**推荐优先实现方案 A（Agent-Driven），同时保留方案 B 的基础设施作为补充。**

理由如下：

### 3.2 七大关键论据

#### 论据一：OpenClaw 天然适配「无人值守」目标

OpenClaw 的官方定位就是 **"personal assistant that actually does things"**。它内置了实现无人值守所需的所有核心机制：

| OpenClaw 内置能力 | 对应 gomtm 需求 |
|-------------------|----------------|
| **Heartbeat** (30分钟心跳) | 定期检查任务队列、处理待办 |
| **Cron Jobs** (精确调度) | 定时推广任务、定时报告 |
| **Multi-Agent** (多智能体) | 不同用途的独立 Agent (推广、监控、客服) |
| **Channels** (Telegram/WhatsApp) | 与用户的自然语言交互、通知 |
| **Hooks** (内部事件钩子) | 审计、拦截、状态同步 |
| **Webhooks** (/hooks/agent) | 数据库按需触发 Agent |
| **Skills** (可扩展技能) | 自定义推广技能、数据库查询技能 |
| **BOOT.md** (启动时自动运行) | 启动后自动恢复之前的工作 |
| **Session 管理** | 多轮对话、上下文保持 |
| **沙箱隔离** | 安全的命令执行环境 |

如果不利用这些能力，而是在数据库端重新实现自主调度、多步推理、渠道通信，等于是重新发明轮子。

#### 论据二：数据库驱动方式在「自主」场景下开发代价极高

用户的最终目标是 **"AI 自主决策"**：

- "用户设定大目标后，剩下都是 AI 自主"
- "AI 主动找用户进行确认和寻求帮助"
- "全方位综合性无预定规则全 AI 自主的综合任务系统"

要用数据库实现这种自主性，需要：

1. 为每种可能的场景编写决策树（SQL/触发器）
2. 预定义所有可能的状态转换
3. 实现自然语言交互层
4. 实现上下文理解和多步推理

这实质上是在数据库中重建一个 AI Agent 框架，工程量巨大且效果远不如使用现成的 LLM + Agent 框架。

#### 论据三：成本问题可通过策略优化

对于"Agent-Driven 成本高"的顾虑，可通过以下策略控制：

| 策略 | 实现方式 | 效果 |
|------|---------|------|
| **分级模型** | 心跳使用便宜模型(sonnet)，复杂任务使用高级模型(opus) | 降低 70%+ 日常成本 |
| **智能休眠** | `HEARTBEAT_OK` 静默处理，无事时不消耗 Token | 减少无效调用 |
| **隔离会话** | Cron 隔离任务，每次全新会话，不累积上下文 | 控制单次成本 |
| **活跃时段** | `activeHours` 限制心跳运行时间 | 夜间零成本 |
| **简单事务数据库处理** | 确定性的简单状态流转仍由数据库执行 | 避免用 AI 做简单工作 |

#### 论据四：实例迁移/恢复问题已有解决方案

任务要求："核心配置和数据在数据库中，gomtm server 服务实例可以随时停止、迁移"。

这在 Agent-Driven 模式下完全可实现：

1. **核心配置存数据库**: `servers.config` → OpenClaw 配置模板
2. **Agent 工作区同步**: OpenClaw 的 `AGENTS.md`、`HEARTBEAT.md`、skills 等文件可从数据库/Git 同步
3. **会话可重建**: Agent 的 BOOT.md 启动时读取数据库状态，自动恢复工作上下文
4. **临时状态可丢失**: Agent 的会话记录是临时的，任务状态（进度、结果）实时回填到数据库的 `tasks` 表

```text
实例迁移流程:
1. 旧实例停止 → OpenClaw 停止 → 正在执行的任务超时后自动标记失败
2. 新实例启动 → bootstrap() → OpenClaw 启动
3. BOOT.md 执行 → Agent 查询数据库 → 发现未完成任务 → 继续执行
4. Agent 检查 cloud_accounts → 恢复 Telegram 登录状态 → 继续推广
```

#### 论据五：数据库的核心价值在于「数据持久化」和「事件分发」

数据库不应该做复杂决策，而应该专注于：

| 数据库职责 | 说明 |
|-----------|------|
| **数据持久化** | 用户配置、账号凭证、任务队列、执行结果 |
| **事件分发** | 触发器检测状态变更 → 通过 `pg_net` 或 Realtime 通知 Agent |
| **权限管理** | RLS 确保 Agent 只能访问属于当前用户的数据 |
| **简单状态机** | 确定性的状态流转（如 task: pending → running → completed） |
| **审计日志** | 记录所有操作到 `sys_logs` |

#### 论据六：混合模式与 gomtm 已有架构完美契合

当前 gomtm 的架构已经为这种混合模式做好了准备：

| 现有能力 | 在 Agent-Driven 中的角色 |
|---------|------------------------|
| `pg_net.http_post` | 数据库 → OpenClaw `/hooks/agent` 按需触发 |
| `handle_http_response` | 处理 Agent 异步执行结果 |
| `task_complete` RPC | Agent 回填任务结果 |
| `servers.config` | 存储 OpenClaw 配置参数 |
| Realtime 订阅 | gomtm 实时接收数据库变更 |
| Cloudflare Tunnel | Agent 公网可访问（对外暴露 Webhook） |
| `cloud_accounts` | 管理社交媒体账号凭证（Agent 工具调用访问） |
| `campaigns` | 推广活动配置（Agent 读取并执行） |

#### 论据七：OpenClaw 的交互模式完美匹配用户需求

用户明确了两种交互方式：

1. **Web UI Chat**: OpenClaw 已内置 Web UI → gomtm 反代暴露（已实现）
2. **Telegram Bot**: OpenClaw 已内置 Telegram 渠道 → 直接配置即可

无需任何额外开发，这两种交互模式 OpenClaw 已经原生支持。用户可以：
- 通过 Telegram 发送自然语言指令："开始推广活动 XXX"
- Agent 查询数据库获取活动配置 → 执行 → 通过 Telegram 报告进度
- Agent 遇到需要验证码时，通过 Telegram 主动问用户要

## 4. 历史实施路线图

### 阶段零：基础设施就位（已完成 ✅）

| 项目 | 状态 |
|------|------|
| gomtm 服务实例管理 | ✅ |
| Bootstrap + Cloudflare Tunnel | ✅ |
| OpenClaw 自动启动 | ✅ |
| WebSocket 反代 + 鉴权 | ✅ |
| Realtime 双向通信 | ✅ |
| 事件驱动 (pg_net + 触发器) | ✅ |
| 任务系统 (tasks 表 + RPC) | ✅ |

### 阶段一：Agent 自主运行框架（优先实现）

```text
目标: Agent 启动后能自主持续运行，定期检查和处理数据库中的任务

核心开发项:
1. [OpenClaw 配置] 编写 HEARTBEAT.md 检查清单
   - 检查 tasks 表中的 pending 任务
   - 检查 cloud_accounts 的登录状态
   - 检查 campaigns 的活跃活动

2. [OpenClaw 配置] 编写 AGENTS.md 知识库
   - 数据库 RPC 函数清单和用法
   - 推广活动执行流程
   - Telegram 账号操作指南
   - 异常处理策略

3. [自定义 Skill] 创建 supabase-tools skill
   - 封装常用数据库 RPC 调用为工具
    - 例如: device_task_list_cursor, device_task_complete, campaign_get 等

4. [Webhook 集成] 配置 hooks
   - 启用 /hooks/agent 端点
   - 配置 hooks.token (从数据库配置读取)
   - 配置 agentId 路由规则

5. [数据库] 事件触发 Agent
   - campaign_start 触发器 → pg_net.http_post → /hooks/agent
   - task 状态变更 → 通知 Agent
```

### 阶段二：推广任务自动化

```text
目标: Agent 能自主执行完整的社交媒体推广流程

核心开发项:
1. [Agent Skill] Telegram 自动化技能
   - 登录/维持会话
   - 发送消息给目标联系人
   - 处理验证码（通过 Telegram Bot 问用户）

2. [HEARTBEAT.md] 定期检查活动状态
   - 未完成的推广任务
   - 需要重试的失败任务
   - 登录状态维持

3. [Cron Job] 定时推广任务
   - 每日定时执行推广批次
   - 避免高频操作触发风控
```

### 阶段三：多实例 + 多 Agent

```text
目标: 支持多 gomtm 实例，每个实例运行多个专用 Agent

核心开发项:
1. [Multi-Agent] 按职能拆分 Agent
   - main: 日常交互和协调
   - outreach: 专职推广
   - monitor: 系统监控和告警

2. [负载分配] 数据库根据实例状态分配任务
   - 健康实例优先
   - 按 Agent 能力匹配任务
```

## 5. 历史场景推演

### 场景 A：执行推广活动

```text
1. 用户在 Web UI 创建推广活动 (campaign) → INSERT campaigns 表
2. 用户点击"开始" → campaign_start RPC → status = 'active'
3. 触发器检测状态变更 → pg_net.http_post(/hooks/agent)
   消息: "新的推广活动已启动: {campaign_name}, ID: {id}, 
          目标: {target_filter}, 模板: {message_template}"
4. OpenClaw Agent 收到任务
   → 读取 campaigns 表获取详细配置
   → 读取 cloud_accounts 获取 Telegram 账号状态
   → 确认账号已登录 → 开始执行
5. Agent 逐个向目标联系人发送消息
    → 每发送一条 → device_task_complete 回填进度
   → 遇到频率限制 → 自主决定等待再试
   → 遇到验证码 → 通过 Telegram Bot 通知用户
6. 活动完成 → Agent 更新 campaign 状态
   → 通过 Telegram 通知用户"活动完成，发送了 X 条消息"
```

### 场景 B：无人值守日常运行

```text
每 30 分钟心跳:
1. Agent 读取 HEARTBEAT.md 检查清单
2. 检查 tasks 表 → 发现 2 个 pending 任务
    → 执行任务 A (查询统计) → 完成 → device_task_complete
    → 执行任务 B (发送报告) → 完成 → device_task_complete
3. 检查 cloud_accounts → 一个 Telegram 账号即将过期
   → 自动刷新 session
   → 如果失败 → 通过 Telegram 通知管理员
4. 检查 campaigns → 一个活动有失败任务
   → 重试失败任务
5. 无更多事项 → 返回 HEARTBEAT_OK → 静默处理
```

### 场景 C：实例迁移恢复

```text
1. 旧 VPS 故障 → Cloudflare Tunnel 断开
2. Cloudflare Webhook 通知 → 旧版 webhook 回调链路 → 标记 status = 'offline'
3. openclaw_failover() → 迁移实例到其他在线 server
4. 正在执行的任务 → timeout_check → 标记失败可重试
5. 管理员在新 VPS 执行 gomtm server --token=xxx 启动新实例
6. Cloudflare Tunnel 连接 → Webhook → 旧版 webhook 回调链路 → status = 'online'
7. server_bootstrap_push() → 推送初始化数据到 gomtm server
8. OpenClaw 启动 → BOOT.md 执行
   → 读取 "检查并恢复上一次中断的工作"
   → 查询 tasks 表 → 发现 2 个 failed/可重试任务
   → 自动重试
```

## 6. 历史边界定义

为了明确职责边界，避免混乱：

| 职责 | 负责方 | 原则 |
|------|--------|------|
| **复杂推理/决策** | OpenClaw Agent | 需要 LLM 理解上下文的场景 |
| **确定性状态流转** | 数据库触发器/函数 | 不需要 AI 的简单 if-else |
| **任务持久化/队列** | 数据库 tasks 表 | 数据源在数据库 |
| **配置管理** | 数据库 servers.config | 配置源在数据库 |
| **多渠道通信** | OpenClaw | 利用内置渠道能力 |
| **定时调度** | OpenClaw Cron + 心跳 | 在 Agent 内部管理 |
| **按需触发 Agent** | 数据库 → pg_net → /hooks/agent | 事件驱动触发 |
| **任务结果回填** | Agent → device_task_complete RPC | Agent 完成后主动写回 |
| **权限控制** | 数据库 RLS | 不可绕过 |
| **审计日志** | 两者都写 sys_logs | 双重记录 |

### 简单判断规则

```text
需要决策的场景 → 给 Agent
不需要决策的机械操作 → 给数据库
需要持久化的数据 → 放数据库
需要理解上下文的 → 给 Agent
需要毫秒级响应的 → 给数据库
需要自然语言的 → 给 Agent
```

## 7. 历史方案对当时约束的自检

任务中提出了三个刚性规定，验证如下：

### 规定一：核心数据来源于主数据库 ✅

- OpenClaw 通过 RPC 工具调用访问数据库，所有核心数据（配置、账号、任务）在 Supabase
- Agent 的 `AGENTS.md` 和 Skills 文件可以从数据库/Git 同步到本地工作区
- Agent 做出的所有决策的结果都回填到数据库

### 规定二：OpenClaw 拥有主机最高权限，但数据库访问基于用户权限 ✅

- OpenClaw 在 gomtm server 进程内运行，继承了 gomtm 的用户 Refresh Token
- 通过环境变量传入 `SUPABASE_URL` 和用户凭证
- Agent 通过 `exec` 工具调用 `psql` 或通过 HTTP 调用 Supabase RPC 时，权限受 RLS 约束
- 同时 Agent 对主机有完全的命令执行权限（安装软件、执行脚本等）

### 规定三：gomtm 托管 OpenClaw 实例，可迁移恢复 ✅

- gomtm 以子进程方式管理 OpenClaw（已实现）
- 核心配置在 `servers.config`（已实现）
- 迁移后 bootstrap 自动获取配置并启动 OpenClaw（已实现）
- BOOT.md 机制支持启动时自动恢复工作状态（待实现）

## 8. 历史最终建议

### 优先实现方案 A（Agent-Driven），原因总结：

1. **匹配终极目标**: "全 AI 自主"本质上就是 Agent-Driven
2. **避免重复造轮**: OpenClaw 已有完整的自主运行框架
3. **开发效率高**: 编写 HEARTBEAT.md + Skills 比编写触发器/状态机快 10 倍
4. **成本可控**: 通过分级模型和智能休眠策略控制
5. **基础已就绪**: gomtm 的 Bootstrap、反代、事件驱动基础设施已完备

### 保留方案 B 的场景：

- 确定性的简单状态流转（如 task status 变更）
- 低延迟的事件分发（触发器 → pg_net）
- 数据持久化和权限管理
- 作为 Agent 的"触发源"（数据库事件 → Agent 执行）

### 不推荐的做法：

- ❌ 在数据库中实现复杂的自主决策逻辑
- ❌ 用触发器模拟 Agent 的多步推理
- ❌ 在数据库端实现消息渠道通信
- ❌ 完全放弃数据库只用 Agent（数据持久化和权限仍需要数据库）

## 9. 历史后续开发任务建议

基于以上分析，建议按以下优先级安排后续任务：

1. **[P0/OpenClaw] 编写 Agent 工作区知识库**: 创建 `AGENTS.md`，包含数据库 RPC 清单、推广流程指引
2. **[P0/OpenClaw] 编写 HEARTBEAT.md**: 定义 Agent 每 30 分钟的检查清单
3. **[P1/OpenClaw] 创建 supabase-tools Skill**: 封装数据库 RPC 为 Agent 可调用的工具
4. **[P1/DB] 配置 Webhook 触发链路**: campaign_start 触发器 → pg_net → /hooks/agent
5. **[P1/OpenClaw] 编写 BOOT.md**: 实例启动/迁移时的自动恢复逻辑
6. **[P2/OpenClaw] 配置 Telegram Bot 渠道**: 让 Agent 直接通过 Telegram 与用户交互
7. **[P2/DB] Hook Token 管理**: 数据库存储 hook token，gomtm 启动时注入到 OpenClaw

## 10. 参考资料

- [OpenClaw 官方愿景](../../openclaw/VISION.md)
- [OpenClaw Hooks 文档](../../openclaw/docs/zh-CN/automation/hooks.md)
- [OpenClaw Webhooks 文档](../../openclaw/docs/zh-CN/automation/webhook.md)
- [OpenClaw Cron Jobs 文档](../../openclaw/docs/zh-CN/automation/cron-jobs.md)
- [OpenClaw 心跳文档](../../openclaw/docs/zh-CN/gateway/heartbeat.md)
- [OpenClaw 多智能体文档](../../openclaw/docs/zh-CN/concepts/multi-agent.md)
- [OpenClaw 智能体运行时文档](../../openclaw/docs/zh-CN/concepts/agent.md)

---
name: gomtm-cloudflare-tunnel
description: Use when an agent must expose a local or SSH-reachable Linux HTTP service through Cloudflare Tunnel, configure cloudflared, map a custom domain or subdomain, maintain per-service tunnel config, diagnose 502/1033/down/degraded tunnels, audit DNS/tunnel drift, or preserve public-domain-to-origin-service records.
---

# gomtm-cloudflare-tunnel

## 核心原则

把 Cloudflare Tunnel 当成长期运行的服务入口生命周期管理，而不是一次性命令。每个明确公网服务使用独立 tunnel root、独立 `cloudflared` 进程、独立 systemd unit、独立 README/registry，并同时验证本机 origin、Cloudflare tunnel 状态、DNS 路由和公网 URL。

## 官方资料

执行前优先查最新官方文档，因为 Zero Trust Tunnel 的 API、CLI 与 dashboard 文案会变化。

| 资料 | 用途 |
| --- | --- |
| `https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/` | dashboard / remotely-managed tunnel 主流程 |
| `https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/configure-tunnels/local-management/` | locally-managed tunnel、`config.yml`、service 运行 |
| `https://developers.cloudflare.com/api/resources/zero_trust/subresources/tunnels/` | `cfd_tunnel` / `tunnels` API、状态、metadata、config_src |
| `https://developers.cloudflare.com/api/resources/dns/subresources/records/` | DNS record 查询、CNAME、冲突记录审计 |

当前已验证的关键事实：

| 领域 | 事实 |
| --- | --- |
| 推荐默认 | Cloudflare 文档推荐大多数场景使用 remotely-managed tunnel；本技能在需要目标主机可审计、可恢复、可排错时仍要求本机保留 README/registry |
| local vs remote | Tunnel API 返回 `config_src: local/cloudflare` 与 `remote_config`；不要混淆 dashboard 管理的 ingress 与本机 YAML 管理的 ingress |
| API 状态 | Tunnel 状态常见 `inactive`、`degraded`、`healthy`、`down` |
| connectivity | 目标主机必须能主动连到 Cloudflare；受限防火墙场景先检查 outbound，尤其 Cloudflare 文档提到的 tunnel connectivity pre-checks |
| metadata | Tunnel API 暴露 `metadata` 字段，但 CLI/dashboard 是否稳定展示不应假设；本机 README/registry 仍是运维真相源 |

## 目标模型

默认目标是本机 Linux。远程目标通过 SSH 操作时，所有命令必须明确作用在目标主机，禁止把本机路径、凭据和目标主机路径混用。

每个公网服务使用一个独立目录，默认：

```text
~/.cloudflared-tunnels/<service-name>/
  config.yml
  credentials/
  .env
  README.MD
  reports/
  incidents/
  scripts/
```

推荐命名：

| 对象 | 格式 | 示例 |
| --- | --- | --- |
| Tunnel 名 | `{service}-{domain-with-dashes}` | `SERVICE="<service>"; DOMAIN="<domain>"` 后派生 |
| 公网域名 | `{service}.{domain}` | `PUBLIC_HOSTNAME="${SERVICE}.${DOMAIN}"` |
| systemd unit | `cloudflared-{service}.service` | `UNIT="cloudflared-${SERVICE}.service"` |
| tunnel root | `~/.cloudflared-tunnels/{service}` | `TUNNEL_HOME="$HOME/.cloudflared-tunnels/${SERVICE}"` |

如目标主机已有不同布局，先 inventory 并保留真实布局。不要为了套用默认目录而移动线上 tunnel，除非用户明确要求迁移。

## 凭据边界

| 凭据 | 存放位置 | 规则 |
| --- | --- | --- |
| 本机 `env/dev.env` 中的 Cloudflare API token/account/zone | 当前本机 | 可用于本机查询或创建 Cloudflare 资源；不要整文件复制到远程主机 |
| 目标主机 tunnel credential JSON 或 connector token | 目标服务目录或 `/etc/cloudflared` | 只保留 tunnel 运行所需的最小凭据，权限 `0600` |
| Cloudflare global key、zone edit token、account token | 不落到目标 README | 不在最终回复、README、incident note 中打印值 |
| 用户临时提供的 token | 当前操作会话 | 用完说明保存位置或销毁方式，禁止写 shell history |

如果目标主机缺少 Cloudflare 凭据，优先在本机完成 Cloudflare 侧创建/路由，再把 tunnel-scoped credential/token 带到目标主机。只有用户明确要求且理解风险时，才在目标主机放置 account/zone 级 token。

## 安全规则

- 不要为了公网访问把 origin 改成 `0.0.0.0` 或开放源服务端口；优先保持 `127.0.0.1:<port>` 只让 cloudflared 访问。
- 不要多个无关服务共用一个 `cloudflared` 进程，除非用户明确接受共享 tunnel 的重启和误配 blast radius。
- 不要 `pkill cloudflared`、重启所有 `cloudflared*` unit、删除 tunnel、轮换 credential、改 DNS、改 Access/WAF 策略，除非已定位目标并得到用户确认。
- 不要把 dashboard 中的临时改动当作完成；必须回写目标主机 README/registry。
- 不要只验证 `systemctl status`；必须验证本机 origin、ingress rule、Cloudflare tunnel 状态、DNS 和公网 URL。
- 不要把 `localhost` 与 `127.0.0.1` 混用。IPv6 `::1`、Docker 端口发布、Host header、HTTP/HTTPS 协议错配都可能导致 502。

## 快速参考

把 bundled scripts 复制到目标服务目录的 `scripts/`，或在本机对目标路径执行。远程主机使用 `scp` 后再通过明确 SSH 命令执行。

| 任务 | 脚本 | 默认行为 |
| --- | --- | --- |
| 准备本机管理的独立 tunnel root | `scripts/install.sh` | 生成 `config.yml`、README、可选创建 locally-managed tunnel、可选 systemd unit |
| 盘点本机/目标主机 tunnel | `scripts/inventory.sh` | 只读生成 reports，记录 config、unit、进程、hostname、origin、secret 状态 |
| 健康检查 | `scripts/healthcheck.sh` | 验证 `cloudflared` config、origin、公网 URL、unit 状态 |
| 查 Cloudflare 侧状态 | `scripts/cf-state.sh` | 只读 API 查询 tunnels 与 DNS CNAME，支持从 `env/dev.env` 加载凭据 |
| 事故记录 | `scripts/incident-note.sh` | 生成不含 secret 的 tunnel incident 模板 |

脚本使用顺序：新建前先 `cf-state.sh` 查冲突；目标主机上先 `inventory.sh` 盘点；创建/更新用 `install.sh`；每次修改后跑 `healthcheck.sh`；出现 502/1033/down/degraded 时先 `incident-note.sh` 建记录再按诊断流程收集证据。

脚本环境变量：

| 变量 | 默认 | 含义 |
| --- | --- | --- |
| `CF_TUNNELS_HOME` | `$HOME/.cloudflared-tunnels` | 所有服务 tunnel root 的父目录 |
| `CF_TUNNEL_HOME` | `$CF_TUNNELS_HOME/<name>` | 单个服务 tunnel root |
| `CF_TUNNEL_NAME` | 无 | tunnel / 服务短名 |
| `CF_TUNNEL_HOSTNAME` | 无 | 公网 FQDN |
| `CF_TUNNEL_ORIGIN` | 无 | origin，例如 `http://127.0.0.1:${PORT}` |
| `CLOUDFLARE_API_TOKEN` / `CF_API_TOKEN` | 无 | Cloudflare API bearer token |
| `CLOUDFLARE_ACCOUNT_ID` / `CF_ACCOUNT_ID` | 无 | Cloudflare account ID |
| `CLOUDFLARE_ZONE_ID` / `CF_ZONE_ID` | 无 | Cloudflare zone ID |

## 工作流

### 1. 发现现状

1. 确认目标：本机还是 SSH 主机；记录 host、用户、OS、systemd、cloudflared 版本、网络出口、Docker/本机服务、服务端口。
2. 验证 origin：在目标主机运行 `curl -fsS http://127.0.0.1:<port>/health` 或用户指定路径。
3. 盘点已有 cloudflared：`pgrep -a cloudflared`、`systemctl list-units '*cloudflared*'`、`~/.cloudflared-tunnels/*`、`/etc/cloudflared/*`。
4. 查询 Cloudflare 侧：tunnel name/id/status/config_src/connections、DNS 记录、Access/WAF/Zero Trust 应用（如相关）。
5. 查冲突：目标 hostname 是否已有 A/AAAA/CNAME、是否已有 tunnel route、同主机是否已有同名 unit 或同端口 origin。

### 2. 选择管理方式

| 场景 | 选择 |
| --- | --- |
| 新服务、需要快速发布、团队主要用 dashboard/API 管配置 | remotely-managed tunnel；目标主机仍保留 `README.MD` 记录 hostname、origin、token/unit |
| 需要目标主机本地可审计、AI agent 后续可直接修端口/ingress | locally-managed tunnel；使用 `config.yml` + 独立 systemd unit |
| 已存在 dashboard-managed tunnel | 不要强行迁移；先 inventory，明确 Cloudflare 侧 config 是真相源，本机 README 记录 Cloudflare 侧入口 |
| 已存在 locally-managed tunnel | 保持本机 `config.yml` 为真相源；修改前备份 config，修改后验证 rule |

如果不确定，先问用户一个问题：要优先 dashboard 集中管理，还是目标主机本地可审计。默认偏向本地可审计和每服务独立进程。

### 3. 新建独立 tunnel

1. 在本机加载 Cloudflare 凭据，例如 `source <local-env-file>`，确认 account、zone、token 权限。
2. 在目标主机准备服务目录：`~/.cloudflared-tunnels/${SERVICE}`。
3. 安装 `cloudflared`，优先使用官方包/发行方式；脚本不自动安装未知来源二进制。
4. 选择凭据来源：
   - locally-managed：目标主机已有 `cloudflared tunnel login` 产生的 cert，或本机创建 tunnel 后只复制 tunnel credential JSON 到目标主机。
   - remotely-managed：从 dashboard/API 得到 connector token，只保存到目标服务 `.env` 或 systemd credential，不复制 account token。
5. 写 `config.yml`，至少包含 hostname rule 和 `http_status:404` fallback。
6. 创建 `cloudflared-${SERVICE}.service`，`ExecStart` 指向该服务目录的 `config.yml`。
7. 写 `README.MD`，记录公网域名、origin、tunnel id/name、unit、config、credential 路径、验证命令、变更流程。
8. 启动并验证：origin、本机 ingress rule、公网 HTTPS、Cloudflare tunnel status、重启后 unit enabled。

### 4. 维护和变更

变更端口、域名、origin 协议、Host header、Access 策略时：

1. 先运行 `inventory.sh` 保存当前证据。
2. 定位唯一目标 tunnel root / Cloudflare tunnel id / systemd unit。
3. 修改最小范围：只改对应 hostname 的 `service` 或 Cloudflare 远程配置。
4. 验证 config：`cloudflared tunnel ingress validate --config config.yml`。
5. 只重启匹配 unit。
6. 验证受影响 hostname 和同 config 中其他 hostname。
7. 更新 `README.MD` 与 registry，记录 last verified 时间。

### 5. 诊断

| 症状 | 优先检查 |
| --- | --- |
| Cloudflare 502 | origin 是否监听、HTTP/HTTPS 是否错配、`localhost` IPv6、Docker 端口、Host header、cloudflared 日志 |
| 1033 | DNS/hostname 没有关联到有效 tunnel，或 tunnel route/config 缺失 |
| Tunnel `inactive/down` | `cloudflared` 进程、systemd unit、网络出口、connector token/credential、Cloudflare 侧连接 |
| Tunnel `degraded` | 多 connector 状态、版本、网络抖动、部分主机未修复 |
| 公网返回错误服务 | hostname rule 顺序、catch-all rule、旧端口被其他服务复用、共享 tunnel 误配 |
| 重启后失效 | unit 未 enable、token/env 未持久化、config/credential 权限错误、用户级 systemd linger 未开启 |

### 6. 多进程 502 最小修复流程

当同一主机有多个 `cloudflared` 进程且某个域名 502：

1. 固定输入：`HOSTNAME="<fqdn>"`、`NEW_ORIGIN="http://127.0.0.1:${PORT}"`、`HEALTH_PATH="<path>"`。
2. 收集只读证据：`pgrep -a cloudflared`、`systemctl list-units --type=service --all 'cloudflared*'`、`ls -la ~/.cloudflared-tunnels /etc/cloudflared`、`scripts/cf-state.sh --hostname "$HOSTNAME"`。
3. 在目标主机用 `scripts/inventory.sh --name "$SERVICE"` 或逐个服务目录 inventory，找出哪个 `config.yml` 包含该 hostname。
4. 对匹配 config 运行 `cloudflared tunnel ingress rule --config "$CONFIG" "https://${HOSTNAME}${HEALTH_PATH}"`，确认当前 origin。
5. 在目标主机验证新 origin：`curl -fsS "${NEW_ORIGIN}${HEALTH_PATH}"`；如失败，先修应用服务，不改 tunnel。
6. 只修改匹配 hostname 的 `service:` 行或对应 Cloudflare 远程配置；不要改其他 hostname、catch-all、DNS 或 credential。
7. 运行 `cloudflared tunnel ingress validate --config <config>`。
8. 只重启匹配 unit：`systemctl --user restart "$UNIT"` 或 `systemctl restart "$UNIT"`。
9. 验证公网 URL、该 config 中其他 hostname、Cloudflare tunnel status 和日志。
10. 更新 `README.MD`、`REGISTRY.md`、incident note。

禁止在该流程中使用 `pkill cloudflared`、重启所有 tunnel、删除 tunnel、轮换凭据、重新 route DNS、把 app 改到 `0.0.0.0`、或在未定位 config/unit 前做任何写操作。

### 7. 重启后恢复清单

当服务器重启后公网域名不可用或映射关系丢失：

1. 读取 `~/.cloudflared-tunnels/REGISTRY.md`；若不存在，立即创建恢复任务，把发现结果补进去。
2. 对 registry 中每个服务运行：origin health、`systemctl status`、`cloudflared tunnel ingress validate`、公网 URL、`cf-state.sh`。
3. 若 user systemd unit 没随开机启动，检查 `systemctl --user is-enabled <unit>` 与 `loginctl show-user <user> -p Linger`；生产主机优先考虑 system unit 或明确启用 linger。
4. 若 `config_src=cloudflare`，不要在本机猜 ingress；通过 Cloudflare dashboard/API 查远程配置并在 README 记录查询入口。
5. 恢复后更新 registry 的 `Last verified UTC` 和每个服务 README。

## REGISTRY.md 契约

多服务主机必须维护 `~/.cloudflared-tunnels/REGISTRY.md`，作为“域名 -> 本地服务”的第一入口。推荐表格：

```markdown
| Service | Public hostname | Origin URL | Health path | Tunnel name | Tunnel ID | Config source | Tunnel root | Unit | Owner | Last verified UTC | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `${SERVICE}` | `${PUBLIC_HOSTNAME}` | `${ORIGIN_URL}` | `${HEALTH_PATH}` | `${TUNNEL_NAME}` | `${TUNNEL_ID}` | local | `${TUNNEL_HOME}` | `${UNIT}` | `${OWNER}` | `${LAST_VERIFIED_UTC}` | maintained by this skill |
```

更新规则：

- 新增、删除、迁移、端口变化、hostname 变化、systemd unit 变化、`config_src` 变化时同步更新。
- 不写 secret 值，只写 secret 文件路径或 Cloudflare dashboard/API 入口。
- 应用技能文档或应用 README 中也要留下反向线索；例如对应应用的运维 README 必须记录公网 URL 与 tunnel root。
- 生产主机要把 `REGISTRY.md` 和每个服务 `README.MD` 纳入主机备份或应用运维文档派生副本；主机丢失时不能只依赖本机磁盘找回域名映射。

## README.MD 契约

任何 tunnel 创建、域名映射、origin 端口、systemd unit、Cloudflare 远程配置、Access 策略或 DNS 发生变化时，更新目标服务 `README.MD`：

- 公网 URL、zone、DNS record 类型、Cloudflare tunnel name/id/config_src/status。
- Origin URL、health path、是否要求 Host header、HTTP/HTTPS 协议。
- 目标主机、服务目录、config path、credential path（只写路径不写值）。
- systemd unit 名、start/stop/restart/status/log 命令、开机启动状态。
- Cloudflare API 查询命令、DNS/tunnel drift 检查方式。
- 最近一次验证时间、验证命令和结果。
- 事故记录位置、恢复步骤、凭据轮换步骤。

如果该公网域名属于某个应用技能，同时在该应用的 README/ops 文档中写入公网 URL 和“使用本技能维护入口”的线索。

## 远程 SSH 模式

优先把脚本复制到目标主机后执行：

```bash
SERVICE="<service>"
ssh user@host "mkdir -p ~/.cloudflared-tunnels/${SERVICE}/scripts"
scp .claude/skills/gomtm/gomtm-cloudflare-tunnel/scripts/*.sh "user@host:~/.cloudflared-tunnels/${SERVICE}/scripts/"
ssh user@host "chmod +x ~/.cloudflared-tunnels/${SERVICE}/scripts/*.sh && ~/.cloudflared-tunnels/${SERVICE}/scripts/inventory.sh --name ${SERVICE}"
```

不要通过 SSH 管道执行破坏性命令。不要把本机 `env/dev.env` 复制到目标主机；如需 Cloudflare API，优先在本机运行只读/创建命令，然后把 tunnel-scoped 结果交给目标主机。

## 示例：发布一个 HTTP 服务

目标：目标主机上的某个 HTTP 服务已在 loopback 端口提供健康检查，需要通过自有域名的子域名访问。

```bash
SERVICE="<service>"
PUBLIC_HOSTNAME="<service>.<domain>"
ORIGIN_URL="http://127.0.0.1:<port>"
HEALTH_PATH="<health-path>"

scripts/install.sh \
  --name "$SERVICE" \
  --hostname "$PUBLIC_HOSTNAME" \
  --origin "$ORIGIN_URL" \
  --create-tunnel \
  --route-dns \
  --systemd user

scripts/healthcheck.sh --name "$SERVICE" --path "$HEALTH_PATH"
scripts/inventory.sh --name "$SERVICE"
```

如果目标主机没有可用的 `cloudflared tunnel login` 凭据，则不要猜。改为在 Cloudflare dashboard/API 创建 tunnel 和 connector token，或让用户提供 tunnel credential/token；目标主机只保存 tunnel 级凭据。

## 常见错误

| 错误 | 正确行为 |
| --- | --- |
| 创建完 tunnel 就结束 | 必须写 README/registry、systemd、验证公网 URL 和重启策略 |
| 多个服务共用 `/etc/cloudflared/config.yml` | 每个明确服务用独立 config/unit，除非用户接受共享 blast radius |
| 复制 `env/dev.env` 到远程 | 只复制 tunnel-scoped credential/token |
| 只看 Cloudflare dashboard Healthy | 同时验证 origin、ingress rule、DNS、公网 URL、日志 |
| 502 时重启所有 cloudflared | 先定位 hostname 对应 config/unit，只重启目标 unit |
| 忘记记录域名和本地服务关系 | `README.MD` 和应用 ops 文档都记录公网 URL、origin、unit、config |
| 认为 metadata/tag 足够 | 可用则补充 metadata，但 README/registry 仍是 AI agent 后续维护入口 |
| 修改 dashboard 后不回写主机 | 本机 README 标记 `config_src=cloudflare`，并记录远程配置入口与查询命令 |
| 把一次性任务的真实服务名、真实域名、真实端口写进技能 | 技能正文用变量或占位符表达结构；真实值只应出现在用户任务、目标主机 README 或运行产物中 |

## 技能质量备注

RED 场景显示，无完整技能时 agent 容易漏掉目标主机凭据边界、重启后可维护记录、共享 tunnel blast radius、Cloudflare 侧 drift 查询和 502 的最小范围修复。本技能用每服务独立目录、README 契约、只读 inventory、Cloudflare API 状态查询和健康检查脚本关闭这些缺口。

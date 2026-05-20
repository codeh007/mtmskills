---
name: github-actions-local
description: Use when 需要在本机运行、调试、列出或校验 GitHub Actions workflow，复现 push、pull_request、workflow_dispatch、schedule 等事件，或需要用 nektos/act 在本地 Docker/self-hosted 环境执行 CI。
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [github-actions, act, local-ci, workflow]
    related_skills: [github-pr-workflow]
---

# GitHub Actions 本机运行

## Overview

使用 upstream [`nektos/act`](https://github.com/nektos/act) 在本机运行 GitHub Actions workflow。优先使用本技能自带脚本 `scripts/run-act.py`，它负责安装或查找 `act`、拼接透明命令，并在目标仓库目录执行。

## When to Use

- 需要在本机运行 `.github/workflows/*.yml`。
- GitHub Actions 远程额度不足、排队太慢，或需要快速反馈。
- 需要本地复现 `push`、`pull_request`、`workflow_dispatch`、`schedule` 等事件。
- 需要列出 workflow/job、只跑某个 job、传入 inputs/secrets/vars/env。
- 需要排查 runner 镜像、Docker、事件 payload、secret、cache 或 artifact 问题。

## Quick Start

```bash
python3 skills/github-actions-local/scripts/run-act.py doctor --repo . --install
python3 skills/github-actions-local/scripts/run-act.py list --repo .
python3 skills/github-actions-local/scripts/run-act.py run push --repo . -W .github/workflows/ci.yml -j test --install
```

直接使用 upstream `act`：

```bash
act -l
act push -W .github/workflows/ci.yml -j test
act workflow_dispatch -W .github/workflows/release.yml --input VERSION=1.2.3
```

## Script Contract

`scripts/run-act.py` 是精简包装器：

- 优先使用 PATH 中的 `act`。
- `--install` 时从 GitHub release 下载 upstream 二进制到 `$HOME/.cache/github-actions-local/<version>/`。
- 打印实际执行的 act 命令，便于复制、复查和排错。
- 默认使用 medium runner 映射：`ghcr.io/catthehacker/ubuntu:act-*`。
- 仅在 `.env`、`.secrets`、`.vars` 文件存在时传给 act。

常用命令：

```bash
# 安装/检查
python3 skills/github-actions-local/scripts/run-act.py doctor --repo . --install

# 列出 workflow/job
python3 skills/github-actions-local/scripts/run-act.py list --repo .
python3 skills/github-actions-local/scripts/run-act.py list pull_request --repo .

# 运行指定 workflow 和 job
python3 skills/github-actions-local/scripts/run-act.py run push --repo . \
  -W .github/workflows/ci.yml \
  -j test \
  --container-architecture linux/amd64

# workflow_dispatch inputs
python3 skills/github-actions-local/scripts/run-act.py run workflow_dispatch --repo . \
  -W .github/workflows/release.yml \
  --input VERSION=1.2.3 \
  --secret GITHUB_TOKEN

# pull_request payload
python3 skills/github-actions-local/scripts/run-act.py run pull_request --repo . \
  -e .tmp/act/pull_request.json

# 校验 workflow
python3 skills/github-actions-local/scripts/run-act.py validate push --repo . \
  -W .github/workflows/ci.yml
```

## Event and Input Rules

- 事件名默认是 `push`。
- `pull_request` 等依赖事件字段的 workflow 通常需要 `-e event.json`。

```json
{
  "pull_request": {
    "head": {"ref": "feature-branch"},
    "base": {"ref": "main"}
  }
}
```

- `workflow_dispatch` 可用 `--input KEY=VALUE`、`--input-file .input`，或 JSON payload。

```json
{"inputs": {"VERSION": "1.2.3"}}
```

- 本地运行时 act 会设置 `ACT=true`，可用于跳过外部通知、发布等步骤。

```yaml
- name: Notify external service
  if: ${{ !env.ACT }}
  run: ./notify.sh
```

- job 级条件可通过 event payload 控制，例如 payload 包含 `{"act": true}` 后使用 `${{ !github.event.act }}`。

## Secrets, Vars, Env

- secret：`--secret NAME` 读取同名环境变量；未设置时由 act 安全提示输入。
- secret 文件：`.secrets`，格式同 `.env`。
- repository variables：`--var NAME=value` 或 `.vars`，在 workflow 中通过 `${{ vars.NAME }}` 访问。
- env：`--env NAME=value` 或 `.env`，作为容器环境变量。
- `GITHUB_TOKEN` 需要显式传入：

```bash
GITHUB_TOKEN="$(gh auth token)" \
python3 skills/github-actions-local/scripts/run-act.py run push --repo . --secret GITHUB_TOKEN
```

## Runner and Docker Rules

- act 依赖 Docker Engine API 运行 Linux runner 容器。
- 默认 runner micro 镜像很小；脚本默认映射到 `ghcr.io/catthehacker/ubuntu:act-*` medium 镜像。
- 自定义 runner 映射：

```bash
python3 skills/github-actions-local/scripts/run-act.py run push --runner-size micro
python3 skills/github-actions-local/scripts/run-act.py run push --runner-size none -P ubuntu-latest=my/image:tag
```

- Apple Silicon 或跨架构复现时常用：`--container-architecture linux/amd64`。
- Windows/macOS job 可在对应宿主上使用 self-hosted 方式近似运行，例如 `-P windows-latest=-self-hosted`。
- cache/artifact 需要本地服务时传 `--cache-path`、`--artifact-path`。

## `.actrc` Guidance

act 会按顺序读取 XDG config、HOME 下 `.actrc`、调用目录 `.actrc`，然后叠加 CLI 参数。`.actrc` 一行一个参数。

仓库级 `.actrc` 示例：

```text
--container-architecture=linux/amd64
--action-offline-mode
```

共享 `.actrc` 只放稳定、无密钥的参数。

## Upstream Re-check

当 act 行为变化或脚本需要更新时，重新确认 upstream 状态：

```bash
git clone https://github.com/nektos/act.git /tmp/act-check
git -C /tmp/act-check describe --tags --abbrev=0
sed -n '56,132p' /tmp/act-check/cmd/root.go
sed -n '1,80p' /tmp/act-check/cmd/platforms.go
python3 - <<'PY'
import json, urllib.request
req = urllib.request.Request('https://api.github.com/repos/nektos/act/releases/latest', headers={'Accept':'application/vnd.github+json','User-Agent':'skill-check'})
data = json.load(urllib.request.urlopen(req, timeout=20))
print(data['tag_name'])
print('\n'.join(a['name'] for a in data['assets']))
PY
```

确认点：CLI flag、runner 映射、release asset 命名、Docker 后端支持、`.actrc` 加载顺序。

## Troubleshooting

1. **本地缺命令或工具。** 换 medium/full runner 镜像后再判断 workflow 问题。
2. **`GITHUB_TOKEN` 报错。** 传 `--secret GITHUB_TOKEN`；需要 gh 时先确认 `gh auth status`。
3. **事件字段为空。** 为 `pull_request`、tag push、release 等事件准备 `-e event.json`。
4. **Docker socket/权限失败。** 先 `docker version`，再看 `act --bug-report`。
5. **cache/artifact 步骤失败。** 显式传 `--cache-path` 或 `--artifact-path`。

## Verification Checklist

- [ ] `doctor` 确认 repo、act、Docker 状态。
- [ ] `list` 确认目标 workflow 和 job id。
- [ ] 对目标 workflow 执行 `validate` 或 `--dryrun`。
- [ ] 真实运行时使用了正确事件名、`-W`、`-j`、payload、inputs、secrets、vars。
- [ ] token 未写入命令历史、`.actrc` 或仓库文件。

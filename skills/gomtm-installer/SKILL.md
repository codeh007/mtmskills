---
name: gomtm-installer
description: Use when 需要配置、维护、迁移或审查 gomtm 安装器体系，尤其是要把安装逻辑收敛为可发布的 Go 单体 CLI、定义技能与源码边界、或设计构建发布和兼容迁移流程时。
version: 2.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [gomtm, installer, bootstrap, go, github-actions, release, migration]
    related_skills: [hermes-agent-skill-authoring, coding-standards-global, github-pr-workflow, writing-plans]
---

# gomtm 安装器

## Overview

这个技能定义的是 gomtm 安装器的长期形态：

- 核心实现以 **Go 单体 CLI `mtminstaller`** 为准
- 源码与技能就近管理，放在 `skills/gomtm-installer/src/`
- 构建、测试、打包、发布由仓库根目录 `.github/workflows/` 负责
- 用户侧安装目标是 **预构建二进制**，不是一组互相依赖的 shell 脚本

当前阶段可以保留兼容层，但兼容层只能承担过渡职责，不能成为新能力的归宿。

## When to Use

- 需要设计或修改 gomtm 的安装、初始化、bootstrap、doctor、dev 环境准备流程
- 需要决定安装职责应该放在 `gomtm` 主仓、`gomtm-install` 仓库，还是 `mtmskills` 里的 `src/`
- 需要把旧的 bash 安装逻辑迁移成可发布、可校验的 Go CLI
- 需要设计 GitHub Actions 构建、发布、校验和分发流程
- 需要判断旧入口 `gomtm/cmd/install.go` 该继续保留、收缩，还是转为兼容层
- 需要评估是否可以归档或删除 `/workspace/gomtm-install`

## Canonical Architecture

### 1) 源码归属

推荐把安装器源码放在：

```text
/workspace/mtmskills/skills/gomtm-installer/src/
```

这个目录维护 `mtminstaller` 的 Go 源码、测试、构建入口和发布辅助文件。

建议结构示例：

```text
skills/gomtm-installer/
  SKILL.md
  src/
    go.mod
    cmd/mtminstaller/
      main.go
    internal/
      app/
      bootstrap/
      doctor/
      install/
      platform/
      remote/
      release/
    tests/
    testdata/
  .github/
    workflows/
      mtminstaller-ci.yml
      mtminstaller-release.yml
```

原则：

- `SKILL.md` 定义意图、边界、操作方式
- `src/` 负责实现
- 仓库根目录 `.github/workflows/` 负责构建与发布
- 不要把核心安装逻辑继续散落在多个 bash 脚本中

### 2) 旧仓库 `gomtm-install`

`/workspace/gomtm-install` 不应再作为新的核心源码中心。它最多承担以下角色之一：

- **bootstrap 仓库**：只保留极薄的下载器 / 转发器
- **兼容仓库**：保留旧安装入口并输出迁移提示
- **临时迁移仓库**：在切换期短暂存在，之后归档

不建议继续把完整安装职责放回这个仓库里。

### 3) `gomtm/cmd/install.go` 的定位

旧版入口：

```text
/workspace/gomtm/cmd/install.go
```

应当只保留为：

- 过渡期兼容入口，或
- 很薄的转发层

不应继续承载安装器核心实现。

## User-Facing Goal

安装器应支持：

- 一条命令在线安装
- 无需先手动 clone 仓库
- 可明确选择版本
- 可验证下载结果
- 可重复安装与排障

理想形态是：

```bash
curl -fsSL https://.../install.sh | bash
```

但这个脚本只应做极少事情：

1. 识别平台
2. 下载预构建的 `mtminstaller`
3. 校验 checksum / signature
4. 执行 installer

脚本本身不应包含完整安装逻辑。

## `mtminstaller` Responsibilities

`mtminstaller` 至少应覆盖这些职责：

- `doctor`：检查主机前置条件
- `bootstrap`：准备最小运行环境
- `install`：执行可组合的安装项
- `dev`：准备开发环境
- `agent-tools`：安装 Agent 工具链
- `vnc` / `browser`：安装远程桌面或浏览器相关组件
- `remote bootstrap`：远程主机初始化
- `release`：生成、下载并校验 release artifact

命令设计应保持可组合、可 dry-run、可复查。

## Build and Release Workflow

See also: `references/root-workflow-notes.md` for the workflow boundary, `references/mtminstaller-release-chain.md` for the release/download/checksum chain, and `references/online-install-bootstrap.md` for the final public bootstrap shape.

`skills/gomtm-installer/src/` 下的源码应通过仓库根目录 `.github/workflows/` 中的 GitHub Actions 完成：

- `go test`
- `go build` / 多平台交叉编译
- 产物打包
- checksum 生成
- release 发布
- 版本号与 tag 绑定

### 推荐发布链路

1. 提交 `src/` 的变更
2. 运行单元测试和构建验证
3. 打 tag 触发 release workflow
4. Actions 编译多平台二进制
5. 生成 checksum / 校验信息
6. 上传 release artifact
7. 安装脚本只下载并校验该 artifact

### 发布原则

- 发布物应是可下载的预构建二进制
- 用户侧优先消费 release artifact，而不是源码仓
- 版本升级应该可回滚
- 构建产物要能被机器校验

### 推荐约束

- Linux 优先
- 明确支持架构，例如 `amd64` / `arm64`
- 产物名稳定、可预测
- 每次发布记录版本、commit、checksum

## Migration Rules

### 1) 不要把新能力继续加回 bash 方案

如果某个能力需要长期维护，应该进入 `mtminstaller` 源码，而不是继续往 shell 脚本里堆。

### 2) 兼容层只负责过渡

兼容层可以：

- 提示用户新入口
- 下载新二进制
- 转发到新命令

兼容层不应该：

- 继续扩展业务逻辑
- 成为事实上的主实现

### 3) 删除旧仓必须晚于稳定迁移

如果你最终想删除 `/workspace/gomtm-install`，前提是：

- 新的 `mtminstaller` 发布链路稳定
- 旧安装入口已能可靠转发或提示迁移
- 旧文档和旧链接已清理或重定向
- 回退路径明确可用

不要在迁移期直接删除整个仓库。

## Work Plan

落地时按这个顺序处理：

1. 确认 `skills/gomtm-installer/src/` 的目录结构
2. 把旧 bash 安装职责拆成可测试的 Go 包
3. 给 `mtminstaller` 补测试
4. 加 GitHub Actions 构建与 release 工作流
5. 让 `gomtm-install` 退化成 bootstrap / 兼容层
6. 收缩 `gomtm/cmd/install.go`
7. 更新所有文档与安装入口
8. 最后再评估是否需要归档或删除 `gomtm-install`

## Common Pitfalls

1. **把“就近管理源码”误解成“源码和技能没有边界”**

   更好的做法是：技能定义契约，`src/` 存实现，二者同仓但职责分离。

2. **继续用多个 shell 脚本拼装安装逻辑**

   这会让在线安装、版本管理和回滚都变差。脚本只能做 bootstrap，不该做主实现。

3. **过早删除 `gomtm-install` 仓库**

   迁移期需要兼容层。直接删除会让旧链接、旧文档和旧安装入口断掉。

4. **让 `gomtm/cmd/install.go` 继续膨胀**

   它应该收缩，而不是继续承担新职责。

5. **没有把发布产物当成一等公民**

   安装器如果不能稳定构建、校验和发布，就还不算成熟。

## Verification Checklist

- [ ] `mtminstaller` 源码放在 `skills/gomtm-installer/src/`
- [ ] 核心安装逻辑不再依赖一组互相耦合的 shell 脚本
- [ ] GitHub Actions 可以构建、测试并发布二进制
- [ ] 用户侧可以通过预构建产物完成安装
- [ ] `gomtm-install` 只保留 bootstrap 或兼容职责
- [ ] `gomtm/cmd/install.go` 不再是核心实现中心
- [ ] 技能文档与实际架构保持一致
- [ ] 迁移与删除旧仓库的时机明确，且有回退路径

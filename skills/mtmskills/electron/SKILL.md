---
name: electron
description: 使用 agent-browser 通过 Chrome DevTools Protocol 自动化 Electron 桌面应用（VS Code、Slack、Discord、Figma、Notion、Spotify 等）。当用户需要与 Electron 应用交互、自动化桌面应用、连接到正在运行的应用、控制原生应用，或测试 Electron 应用程序时使用。触发词包括 "automate Slack app"、"control VS Code"、"interact with Discord app"、"test this Electron app"、"connect to desktop app"，以及任何需要自动化原生 Electron 应用的任务。
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)
---

# Electron 应用自动化

使用 agent-browser 自动化任意 Electron 桌面应用。Electron 应用构建在 Chromium 之上，并暴露一个 Chrome DevTools Protocol (CDP) 端口，agent-browser 可以连接到它，从而使用与网页相同的 snapshot-交互工作流。

## 核心工作流

1. **启动** Electron 应用并启用远程调试
2. **连接** agent-browser 到 CDP 端口
3. **Snapshot** 以发现可交互元素
4. **交互** 时使用元素 ref
5. 在导航或状态变化后**重新 snapshot**

```bash
# 启动 Electron 应用并启用远程调试
open -a "Slack" --args --remote-debugging-port=9222

# 将 agent-browser 连接到应用
agent-browser connect 9222

# 从这里开始走标准工作流
agent-browser snapshot -i
agent-browser click @e5
agent-browser screenshot slack-desktop.png
```

## 使用 CDP 启动 Electron 应用

每个 Electron 应用都支持 `--remote-debugging-port` 标志，因为它内建于 Chromium。

### macOS

```bash
# Slack
open -a "Slack" --args --remote-debugging-port=9222

# VS Code
open -a "Visual Studio Code" --args --remote-debugging-port=9223

# Discord
open -a "Discord" --args --remote-debugging-port=9224

# Figma
open -a "Figma" --args --remote-debugging-port=9225

# Notion
open -a "Notion" --args --remote-debugging-port=9226

# Spotify
open -a "Spotify" --args --remote-debugging-port=9227
```

### Linux

```bash
slack --remote-debugging-port=9222
code --remote-debugging-port=9223
discord --remote-debugging-port=9224
```

### Windows

```bash
"C:\Users\%USERNAME%\AppData\Local\slack\slack.exe" --remote-debugging-port=9222
"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe" --remote-debugging-port=9223
```

**重要：** 如果应用已经在运行，先退出它，然后带上这个标志重新启动。`--remote-debugging-port` 标志必须在启动时就存在。

## 连接

```bash
# 连接到指定端口
agent-browser connect 9222

# 或者在每条命令上使用 --cdp
agent-browser --cdp 9222 snapshot -i

# 自动发现一个正在运行的基于 Chromium 的应用
agent-browser --auto-connect snapshot -i
```

执行 `connect` 后，后续所有命令都会指向已连接的应用，不再需要 `--cdp`。

## Tab 管理

Electron 应用通常有多个窗口或 webview。使用 tab 命令来列出并切换它们：

```bash
# 列出所有可用目标（窗口、webview 等）
agent-browser tab

# 按索引切换到指定 tab
agent-browser tab 2

# 按 URL 模式切换
agent-browser tab --url "*settings*"
```

## Webview 支持

Electron `<webview>` 元素会被自动发现，并且可以像普通页面一样控制。webview 会以单独目标的形式出现在 tab 列表中，`type: "webview"`：

```bash
# 连接到正在运行的 Electron 应用
agent-browser connect 9222

# 列出目标 -- webview 会和页面一起出现
agent-browser tab
# 输出示例：
#   0: [page]    Slack - Main Window     https://app.slack.com/
#   1: [webview] Embedded Content        https://example.com/widget

# 切换到某个 webview
agent-browser tab 1

# 像平常一样与 webview 交互
agent-browser snapshot -i
agent-browser click @e3
agent-browser screenshot webview.png
```

**注意：** Webview 支持通过原始 CDP 连接工作。

## 常见模式

### 检查并导航应用

```bash
open -a "Slack" --args --remote-debugging-port=9222
sleep 3  # 等待应用启动
agent-browser connect 9222
agent-browser snapshot -i
# 阅读 snapshot 输出以识别 UI 元素
agent-browser click @e10  # 导航到某个区域
agent-browser snapshot -i  # 导航后重新 snapshot
```

### 截取桌面应用截图

```bash
agent-browser connect 9222
agent-browser screenshot app-state.png
agent-browser screenshot --full full-app.png
agent-browser screenshot --annotate annotated-app.png
```

### 从桌面应用提取数据

```bash
agent-browser connect 9222
agent-browser snapshot -i
agent-browser get text @e5
agent-browser snapshot --json > app-state.json
```

### 在桌面应用中填写表单

```bash
agent-browser connect 9222
agent-browser snapshot -i
agent-browser fill @e3 "search query"
agent-browser press Enter
agent-browser wait 1000
agent-browser snapshot -i
```

### 同时运行多个应用

使用命名 session 同时控制多个 Electron 应用：

```bash
# 连接到 Slack
agent-browser --session slack connect 9222

# 连接到 VS Code
agent-browser --session vscode connect 9223

# 分别独立交互
agent-browser --session slack snapshot -i
agent-browser --session vscode snapshot -i
```

## 配色方案

通过 CDP 连接时，默认配色方案可能是 `light`。要保留 dark mode：

```bash
agent-browser connect 9222
agent-browser --color-scheme dark snapshot -i
```

或者全局设置：

```bash
AGENT_BROWSER_COLOR_SCHEME=dark agent-browser connect 9222
```

## 故障排查

### "Connection refused" or "Cannot connect"

- 确保应用启动时带上了 `--remote-debugging-port=NNNN`
- 如果应用已经在运行，先退出并带上该标志重新启动
- 检查端口是否被其他进程占用：`lsof -i :9222`

### 应用已启动但连接失败

- 启动后先等待几秒再连接（`sleep 3`）
- 某些应用需要时间来初始化它们的 webview

### 元素没有出现在 snapshot 中

- 应用可能使用了多个 webview。使用 `agent-browser tab` 列出目标并切换到正确的那个
- 使用 `agent-browser snapshot -i -C` 以包含鼠标可交互元素（带有 `onclick` handler 的 div）

### 无法在输入框中输入文字

- 试试 `agent-browser keyboard type "text"`，无需 selector，直接在当前焦点处输入
- 某些 Electron 应用使用自定义输入组件；使用 `agent-browser keyboard inserttext "text"` 可以绕过按键事件

## 支持的应用

任何基于 Electron 构建的应用都可以，包括：

- **沟通：** Slack、Discord、Microsoft Teams、Signal、Telegram Desktop
- **开发：** VS Code、GitHub Desktop、Postman、Insomnia
- **设计：** Figma、Notion、Obsidian
- **媒体：** Spotify、Tidal
- **生产力：** Todoist、Linear、1Password

如果一个应用是用 Electron 构建的，它就支持 `--remote-debugging-port`，并且可以通过 agent-browser 自动化。

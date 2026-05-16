---
name: slack
description: 使用浏览器自动化与 Slack 工作区交互。适用于用户需要检查未读频道、导航 Slack、发送消息、提取数据、查找信息、搜索会话，或自动化任何 Slack 任务时。触发语包括“check my Slack”“what channels have unreads”“send a message to”“search Slack for”“extract from Slack”“find who said”，以及任何需要以编程方式与 Slack 交互的任务。
allowed-tools: Bash(agent-browser:*), Bash(npx agent-browser:*)
---

# Slack 自动化

与 Slack 工作区交互，以检查消息、提取数据并自动化常见任务。

## Quick Start

连接到现有的 Slack 浏览器会话，或打开 Slack：

```bash
# 连接到 9222 端口上的现有会话（通常用于已经打开的 Slack）
agent-browser connect 9222

# 或者如果尚未运行，则打开 Slack
agent-browser open https://app.slack.com
```

然后拍摄一个快照，查看当前有哪些可操作元素：

```bash
agent-browser snapshot -i
```

## Core Workflow

1. **连接/导航**：打开或连接到 Slack
2. **快照**：获取带 refs 的交互元素（`@e1`、`@e2` 等）
3. **导航**：点击标签、展开分区，或导航到指定频道
4. **提取/交互**：读取数据或执行操作
5. **截图**：捕获发现结果作为证据

```bash
# 示例：检查未读频道
agent-browser connect 9222
agent-browser snapshot -i
# 查找 "More unreads" 按钮
agent-browser click @e21  # "More unreads" 按钮对应的 ref
agent-browser screenshot slack-unreads.png
```

## Common Tasks

### Checking Unread Messages

```bash
# 连接到 Slack
agent-browser connect 9222

# 拍摄快照以定位未读按钮
agent-browser snapshot -i

# 查找：
# - "More unreads" 按钮（通常在侧边栏顶部附近）
# - Activity 标签中的 "Unreads" 切换项（显示未读数量）
# - 带有 badge / 粗体文本、表示未读的频道名称

# 导航到 Activity 标签，在一个视图中查看全部未读
agent-browser click @e14  # Activity 标签（ref 可能不同）
agent-browser wait 1000
agent-browser screenshot activity-unreads.png

# 或检查 DMs 标签
agent-browser click @e13  # DMs 标签
agent-browser screenshot dms.png

# 或展开侧边栏中的 "More unreads"
agent-browser click @e21  # More unreads 按钮
agent-browser wait 500
agent-browser screenshot expanded-unreads.png
```

### Navigating to a Channel

```bash
# 在侧边栏中搜索频道，或按名称查找
agent-browser snapshot -i

# 在列表中查找频道名（例如 "engineering"、"product-design"）
# 点击该频道 treeitem 的 ref
agent-browser click @e94  # 示例：engineering 频道的 ref
agent-browser wait --load networkidle
agent-browser screenshot channel.png
```

### Finding Messages/Threads

```bash
# 使用 Slack 搜索
agent-browser snapshot -i
agent-browser click @e5  # Search 按钮（常见 ref）
agent-browser fill @e_search "keyword"
agent-browser press Enter
agent-browser wait --load networkidle
agent-browser screenshot search-results.png
```

### Extracting Channel Information

```bash
# 获取当前所有可见频道的列表
agent-browser snapshot --json > slack-snapshot.json

# 解析频道名称和元数据
# 查找 level=2 的 treeitem 元素（分区下的子频道）
```

### Checking Channel Details

```bash
# 打开一个频道
agent-browser click @e_channel_ref
agent-browser wait 1000

# 获取频道信息（成员、描述等）
agent-browser snapshot -i
agent-browser screenshot channel-details.png

# 滚动浏览消息
agent-browser scroll down 500
agent-browser screenshot channel-messages.png
```

### Taking Notes/Capturing State

当你需要记录来自 Slack 的发现结果时：

```bash
# 拍摄带注释的截图（显示元素编号）
agent-browser screenshot --annotate slack-state.png

# 拍摄整页截图
agent-browser screenshot --full slack-full.png

# 获取当前 URL 以供引用
agent-browser get url

# 获取页面标题
agent-browser get title
```

## Sidebar Structure

理解 Slack 的侧边栏结构有助于你更高效地导航：

```
- Threads
- Huddles
- Drafts & sent
- Directories
- [分区标题 - External connections、Starred、Channels 等]
  - [以 treeitem 形式列出的频道]
- Direct Messages
  - [列出的私信]
- Apps
  - [应用快捷方式]
- [More unreads] 按钮（切换未读频道列表）
```

需要重点留意的 refs：
- `@e12` - 通常是 Home 标签
- `@e13` - DMs 标签
- `@e14` - Activity 标签
- `@e5` - Search 按钮
- `@e21` - More unreads 按钮（会因会话而异）

## Tabs in Slack

点击某个频道后，你会看到这些标签：
- **Messages** - 频道会话
- **Files** - 已共享文件
- **Pins** - 已置顶消息
- **Add canvas** - 协作画布
- 以及取决于工作区配置的其他标签

点击这些标签的 ref，即可切换视图并获取不同信息。

## Extracting Data from Slack

### Get Text Content

```bash
# 获取某条消息或某个元素的文本
agent-browser get text @e_message_ref
```

### Parse Accessibility Tree

```bash
# 以 JSON 格式输出完整快照，便于程序化解析
agent-browser snapshot --json > output.json

# 查找：
# - 频道名称（treeitem 中的 name 字段）
# - 消息内容（listitem/document 元素中）
# - 用户名（带用户信息的 button 元素）
# - 时间戳（带时间信息的 link 元素）
```

### Count Unreads

```bash
# 在展开未读分区后：
agent-browser snapshot -i | grep -c "treeitem"
# 未读分区中每个带频道名称的 treeitem 都表示一个未读项
```

## Best Practices

- **连接到现有会话**：如果 Slack 已经打开，使用 `agent-browser connect 9222`。这比新开浏览器更快。
- **点击前先拍快照**：始终先执行 `snapshot -i`，再识别 refs 并点击按钮。
- **导航后重新拍快照**：导航到新频道或新分区后，再拍一个新的快照以查找新的 refs。
- **使用 JSON 快照做解析**：需要提取结构化数据时，使用 `snapshot --json` 获取机器可读输出。
- **控制交互节奏**：快速连续交互之间加入 `sleep 1`，给 UI 留出刷新时间。
- **检查 accessibility tree**：accessibility tree 展示了屏幕阅读器（以及你的自动化）能看到的内容。如果某个元素不在快照里，它可能是隐藏的，或者需要先滚动才能看到。
- **在侧边栏内滚动**：如果频道列表很长，使用 `agent-browser scroll down 300 --selector ".p-sidebar"` 在 Slack 侧边栏内部滚动。

## Limitations

- **无法访问 Slack API**：这里使用的是浏览器自动化，而不是 Slack API。不需要 OAuth、webhook 或 bot token。
- **依赖当前会话**：截图和快照都绑定在当前浏览器会话上。
- **可能遇到速率限制**：Slack 可能会限制过快的交互；必要时在命令之间加入延迟。
- **工作区特定**：你只与自己的工作区交互，不能跨工作区自动化。

## Debugging

### Check console for errors

```bash
agent-browser console
agent-browser errors
```

### View raw HTML of an element

```bash
# snapshot 显示的是 accessibility tree。如果某个元素不在里面，
# 它可能不是可交互元素（例如 div 而不是 button）
# 使用 snapshot -i -C 以包含光标可交互的 div
agent-browser snapshot -i -C
```

### Get current page state

```bash
agent-browser get url
agent-browser get title
agent-browser screenshot page-state.png
```

## Example: Full Unread Check

```bash
#!/bin/bash

# 连接到 Slack
agent-browser connect 9222

# 拍摄初始快照
echo "=== 检查 Slack 未读 ==="
agent-browser snapshot -i > snapshot.txt

# 检查 Activity 标签中的未读
agent-browser click @e14  # Activity 标签
agent-browser wait 1000
agent-browser screenshot activity.png
ACTIVITY_RESULT=$(agent-browser get text @e_main_area)
echo "Activity: $ACTIVITY_RESULT"

# 检查 DMs
agent-browser click @e13  # DMs 标签
agent-browser wait 1000
agent-browser screenshot dms.png

# 检查侧边栏中的未读频道
agent-browser click @e21  # More unreads 按钮
agent-browser wait 500
agent-browser snapshot -i > unreads-expanded.txt
agent-browser screenshot unreads.png

# 汇总
echo "=== 汇总 ==="
echo "完整细节请查看 activity.png、dms.png 和 unreads.png"
```

## References

- **Slack 文档**: https://slack.com/help
- **Web 体验**: https://app.slack.com
- **键盘快捷键**: 在 Slack 中输入 `?` 查看快捷键列表

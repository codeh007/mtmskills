---
name: gomtm-design
description: Use when designing, implementing, or refactoring gomtm/gomtmui UI screens, components, list views, datatables, mobile-first layouts, shadcn/ui composition, route query state, filters, pagination, sorting, status fields, or operational dashboards.
---

# Gomtm Design

## 使用入口

这是 gomtm/gomtmui UI 设计与实现的总入口。主文档只保留判断规则；具体页面模式按需读取 `references/`。

1. 先按移动端设计，再自适应桌面端；桌面端只是扩展信息密度，不应改变主流程。
2. 优先用 shadcn/ui 组件或组件组合解决问题；没有必要时不要新增自定义组件或自定义样式。
3. 图标优先表达工具动作；不熟悉的图标必须配 `Tooltip`、`aria-label` 或 `sr-only` 文本。
4. 简洁优先：不要用说明文案堆叠来弥补信息架构不清。
5. 不滥用 `<Card />`：卡片只用于重复记录项、弹窗内容或真正需要框定的工具，不把页面 section 套成 card，更不要 card-in-card。
6. datatable 采用 column-first 约定：桌面表格和移动摘要共用同一份 `ColumnDef<TData>[]`，`columnDef.meta.mobile` 决定是否进入移动摘要；`flexRender` 只负责渲染列定义，不承载查询、分页、筛选、排序或选择状态。
7. 表格 cell 先选公共 cell 原语，再写业务专用 cell；复制、长文本、指标、状态、动作都必须有明确宽度、截断、反馈和浅色/暗色主题状态。

## 组件选择

常见字段优先使用专用组件表达：

- 状态、类型、权限、平台：`Badge` / `Bubble`。
- 开关、启停、二元设置：`Switch`。
- 模式、筛选开关、视图切换：`Toggle` / `Toggle Group`。
- 图标按钮说明：`Tooltip`。
- 空数据：`Empty` 或仓库现有空态组件。
- 次级详情、低频信息：`Collapsible`。
- 一组互斥或并列命令：`Button Group`。
- 表格复制、长文本、指标、状态、动作：优先使用 `components/common/table/cells` 下的公共 cell；只服务单个业务表格的特殊 cell 留在当前子包。

如果当前仓库尚未安装某个 shadcn/ui 组件，先检查 `components.json`、`src/components/ui/` 和 shadcn CLI；不要为了名字手搓一套不一致的组件。

## 专题引用

| 场景 | 先读 |
| --- | --- |
| 列表页、运营对象列表、筛选表单、URL query、cursor、详情入口 | [列表视图](references/list-view.md) |
| table / datatable / grid、`@tanstack/react-table`、列显隐、排序、分页、行选择 | [数据表格](references/datatable.md) |

## 默认取舍

1. 对象列表默认是“摘要入口”，不是宽表；只有需要逐列比较大量同构字段时才做 datatable。
2. datatable 是列表视图的一种特殊形式，仍必须有移动端摘要表达。
3. gomtmui 列表页的 route query、服务端查询参数、RPC/API 参数应保持一致，不要另造前端私有筛选状态。
4. Next.js page 语法跟随当前仓库约定，例如 `searchParams: Promise<...>` 后 `await searchParams`。
5. 表格实现优先 `@tanstack/react-table` + shadcn/ui `Table` 外壳，而不是依赖一份通用 shadcn data-table 组件模板。

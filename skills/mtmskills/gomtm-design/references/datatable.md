# 数据表格

## 核心判断

datatable 只在用户确实需要逐列比较、排序、过滤、分页、列显隐、行选择或复制表格数据时使用。它是列表视图的一种特殊形式，不是默认的对象列表形态。

在 gomtmui 中，桌面表格使用 `@tanstack/react-table` + shadcn/ui `Table` 壳层。列定义是唯一来源：桌面表格、移动端摘要、复制动作、状态标签、指标字段都从同一份 `ColumnDef<TData>[]` 推导，不再维护第二份“移动版字段清单”。

## 必读来源

实现前重新核对官方文档和本地组件：

- `https://tanstack.com/table/latest/docs/guide/data`
- `https://tanstack.com/table/latest/docs/guide/cells`
- `https://tanstack.com/table/latest/docs/guide/column-defs`
- `https://ui.shadcn.com/docs/components/data-table`
- `https://ui.shadcn.com/docs/components/table`

同时检查本仓库的表格外壳与现有实现约定，避免照搬外部示例时引入不兼容写法。

## 实施流程

1. 先读 [列表视图](list-view.md)，确认这个页面真的需要 datatable。
2. 定义行类型 `TData`。真实后端数据用 schema、生成类型或适配层收窄，不要为了表格方便写 `as any`。
3. 先定义列，再定义表格壳层。列定义必须是稳定引用：模块级常量、`useMemo`，或函数返回后由调用方 `useMemo` 包住。
4. 用 `useReactTable` 组织状态机；查询、分页、筛选、排序、列显隐、行选择都属于 table state，不属于 `flexRender`。
5. 桌面表格只负责渲染 `<Table>`；移动端摘要只负责渲染同一份列契约对应的记录卡。
6. 宽表必须有移动端替代表达，不能只靠横向滚动解决手机主流程。

## 列契约

1. `ColumnDef<TData>` 是唯一数据契约来源。
2. `accessorKey` 或 `accessorFn` 负责提供稳定数据，`cell` 负责 UI 表达，不能把业务状态塞进 JSX 里再反向解析。
3. `columnDef.meta.mobile` 是移动摘要契约。未声明 `meta.mobile` 的列默认不进入移动摘要。
4. `columnDef.meta.mobile` 只描述移动端如何展示，不负责查询、分页、排序、过滤或权限判断。
5. 桌面列与移动摘要共享同一份列定义；任何新增字段都先改列定义，再决定是否落入移动摘要。
6. `flexRender` 只负责把 `header`、`cell`、`footer` 等列定义渲染出来，不负责保存或派生页面状态。

推荐的 `meta.mobile` 形态：

```tsx
type MobileMeta = {
  mobile?: {
    slot: "title" | "summary" | "status" | "metric" | "action" | "copy";
    priority?: number;
    hidden?: boolean;
  };
};
```

可执行规则：

- `title` 只放主身份信息，例如名称、标题、设备名。
- `summary` 放 1 到 2 个辅助事实，例如平台、来源、最近时间。
- `status` 放状态、类型、权限类标签，通常渲染 `BadgeCell`。
- `metric` 放数值、计数、额度、速率类字段，通常渲染 `MetricCell`。
- `action` 放单个高频动作或动作组，通常渲染 `ActionCell`。
- `copy` 放短 ID、URL、密钥片段、可复制文本，通常渲染 `CopyCell`。
- `hidden: true` 表示移动端完全不展示该列，但桌面仍可保留。

## 自适应列宽与溢出控制

列宽是表格契约，不是 cell 内部样式猜测。每个桌面列必须通过 `ColumnDef` 的 `size/minSize/maxSize` 或 `columnDef.meta.table` 声明尺寸和溢出类型，再由表格壳层统一渲染到 `colgroup`、`TableHead` 和 `TableCell`。

推荐的 `meta.table` 形态：

```tsx
type TableColumnOverflow = "truncate" | "wrap" | "nowrap" | "visible";

type TableColumnMeta = {
  size?: number;
  minSize?: number;
  maxSize?: number;
  align?: "left" | "center" | "right";
  priority?: "identity" | "content" | "metric" | "action" | "low";
  overflow?: TableColumnOverflow;
  className?: string;
  headerClassName?: string;
  cellClassName?: string;
};
```

执行规则：

1. 优先使用 TanStack Column Sizing 的 `size/minSize/maxSize` 和 `column.getSize()`；`meta.table` 只补充 gomtmui 的对齐、优先级和溢出语义。
2. `DataTableShell` 必须生成 `colgroup` 并计算表格最小宽度；当总列宽超过容器时，只允许表格整体横向滚动。
3. `TableCell` 默认必须允许内容收缩：`min-w-0 overflow-hidden align-top`。
4. 不把 `whitespace-nowrap` 作为所有 cell 的全局默认；nowrap 只用于状态、金额、动作等短内容列。
5. 长文本列使用 `truncate` 或 `wrap-anywhere`，完整值通过 `title`、tooltip、popover、详情入口或复制动作查看。
6. 指标列使用 `tabular-nums` 和稳定单行/两行结构，不把长 label 挤进主列。
7. 复制和动作按钮必须 `shrink-0` 且宽高稳定，hover/focus/copied 不改变列宽。
8. 禁止用 cell 内部固定 `w-*` 对抗表格列尺寸；如果必须控制宽度，先调整列契约。

## 桌面与移动边界

- `DataTableShell` 只管桌面表格壳层：toolbar、列显隐、分页、空态、错误态、`Table` 结构。
- `MobileRecordCard` 只管 `md` 以下的摘要结构：标题、状态、关键摘要、底部动作。
- `TextCell`、`BadgeCell`、`MetricCell`、`ActionCell`、`CopyCell` 是可组合原语，不是页面级容器。
- 通用 cell 放在 `components/common/table/cells`；仅服务当前业务表格、无法稳定复用的 cell 放在当前页面或子包内。
- 没有 `meta.mobile` 的列默认不进入移动摘要；需要移动展示时必须显式声明。
- 桌面和移动端的字段顺序应由列定义统一决定，不允许桌面一套顺序、移动端另一套顺序。

## 组件拆分

### `DataTableShell`

适合承载这些内容：

- 桌面端表头与表体。
- 列显隐菜单。
- 排序、分页、行选择等 table state。
- 空数据、加载中、错误态。

不适合承载这些内容：

- 页面查询参数解析。
- 后端查询拼接逻辑。
- 移动摘要卡的字段重组。
- 业务详情页的长文本拼装。

### `MobileRecordCard`

适合承载这些内容：

- 主标题与次标题。
- 1 到 3 个最重要的状态或摘要块。
- 1 到 2 个高频动作。
- 长 ID、可复制内容、短指标。

不适合承载这些内容：

- 全量列展示。
- 横向滚动表格。
- 复杂筛选表单。
- 完整详情、错误全文、命令全文。

### `TextCell` / `BadgeCell` / `MetricCell` / `ActionCell` / `CopyCell`

- `TextCell`：普通文本、长文本、次级说明。
- `BadgeCell`：状态、标签、权限、类型。
- `MetricCell`：数值、计数、速率、额度。
- `ActionCell`：按钮、链接、菜单入口。
- `CopyCell`：复制文本、短 ID、URL、外部引用。

这些原语只负责自己的视觉语义，不负责数据拉取，也不负责决定列是否出现在移动摘要。

## Cell 视觉规则

1. 每个 cell 必须声明适合表格密度的宽度、`min-w-0`、截断或换行策略，不能让长值撑开整列。
2. `TextCell` 展示长文本时只显示摘要；完整值通过 `Tooltip`、弹层、详情入口或可复制值查看。不要把完整 User-Agent、命令、错误全文直接铺在单元格里。
3. `MetricCell` 展示输入/输出、上传/下载、增减、请求/响应等成对指标时，优先用方向图标和 `aria-label`，不要用“入/出”这类窄列里容易挤压的文字前缀。
4. 金额、token、耗时、百分比等指标应使用紧凑的单行或清晰两行结构；辅助说明用 `text-muted-foreground`，不能让主值和说明堆叠到无法辨认。
5. `CopyCell` 的复制成功反馈在按钮内部完成：图标切换为绿色 check、`aria-label` 更新，必要时保留 tooltip；不要默认用 toast 表示单个 cell 复制成功。
6. 图标按钮必须有稳定尺寸，复制成功、hover、focus 状态不能改变单元格布局。
7. 浅色/暗色主题都使用语义 token，例如 `text-muted-foreground`、`border-border`、`bg-muted`、`text-emerald-600 dark:text-emerald-400`；不要写只适配单一主题的硬编码颜色。
8. 公共 cell 只接受值、展示选项和交互回调，不读取页面查询状态、路由状态或业务 store。

## 推荐骨架

```tsx
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";

type Row = {
  id: string;
  name: string;
  status: string;
};

type MobileMeta = {
  mobile?: {
    slot: "title" | "summary" | "status" | "metric" | "action" | "copy";
    priority?: number;
    hidden?: boolean;
  };
};

const columns: ColumnDef<Row, unknown>[] = [
  {
    accessorKey: "name",
    header: "名称",
    cell: ({ row }) => <TextCell value={row.original.name} />,
    meta: { mobile: { slot: "title", priority: 1 } } satisfies MobileMeta,
  },
  {
    accessorKey: "status",
    header: "状态",
    cell: ({ row }) => <BadgeCell value={row.original.status} />,
    meta: { mobile: { slot: "status", priority: 2 } } satisfies MobileMeta,
  },
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyCell value={row.original.id} />,
    meta: { mobile: { slot: "copy", priority: 3 } } satisfies MobileMeta,
  },
];

export function DataTableShell({ items }: { items: Row[] }) {
  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <>
      <div className="hidden md:block">
        <table>
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden">
        <MobileRecordCard items={items} columns={columns} />
      </div>
    </>
  );
}
```

## 快速决策

| 场景 | 做法 |
| --- | --- |
| 桌面端密集比较 | 用 `DataTableShell` + `Table` |
| 手机端摘要 | 用 `MobileRecordCard`，按 `columnDef.meta.mobile` 组装 |
| 文本、状态、指标、动作、复制 | 分别用 `TextCell`、`BadgeCell`、`MetricCell`、`ActionCell`、`CopyCell` |
| 需要隐藏移动端字段 | 给列加 `meta.mobile.hidden = true` |
| 需要固定移动端顺序 | 调整 `meta.mobile.priority`，不要另写第二套字段表 |
| 需要复制动作 | 用 `CopyCell`，不要把复制逻辑塞进普通 `TextCell` |
| 需要展示长文本 | 用摘要 + tooltip/详情入口，不让原文撑宽表格 |
| 输入/输出类指标 | 用方向图标 + `aria-label`，避免在窄列里堆文字前缀 |

## 常见错误

1. 把桌面表格和移动摘要拆成两份列定义，后续字段不同步。
2. 让 `flexRender` 承担查询、排序、分页或筛选状态。
3. 只在桌面端实现 `Table`，手机端没有同数据摘要。
4. 新增列后忘了补 `columnDef.meta.mobile`，导致手机端静默缺字段。
5. 让 `meta.mobile` 变成第二套业务逻辑，而不是展示契约。
6. 用 `TextCell` 直接塞长命令、完整错误全文或可编辑表单。
7. 为了“整齐”把 `DataTableShell` 做成页面级容器，结果 toolbar、table、空态、移动摘要混在一起。
8. 复制类字段不用 `CopyCell`，而是手写一堆不一致的按钮和 tooltip。
9. 复制成功用 toast 刷屏，而不是在复制按钮自身显示成功状态。
10. 长文本没有摘要和完整查看路径，导致一列撑开整个表格。
11. 指标列依赖冗长文字前缀，图标、`aria-label` 和视觉层级缺失。
12. 用多个 cell 内部固定 `w-*` 预测列宽，真实 viewport 下互相挤压。
13. `table-fixed`、全局 `whitespace-nowrap` 和长文本同时存在，导致内容覆盖相邻列。
14. 只看代码和 jsdom 测试，不用真实浏览器截图验证表格布局。

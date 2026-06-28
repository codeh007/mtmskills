# 数据表格

## 核心判断

datatable 是列表视图的一种特殊形式，只在用户确实需要逐列比较、排序、过滤、分页、列显隐、行选择或复制表格数据时使用。

在 gomtmui 中，优先使用 shadcn/ui `Table` 作为可访问表格外壳，使用 `@tanstack/react-table` 作为 headless 状态机。shadcn data-table 文档是组合指南，不是一个应该到处复制的通用组件。

## 必读来源

实现前重新核对官方文档和本地组件：

| 主题 | 来源 |
| --- | --- |
| shadcn data-table 组合模式 | `https://ui.shadcn.com/docs/components/data-table` |
| shadcn Table 外壳 | `https://ui.shadcn.com/docs/components/table` 和 `src/components/ui/table.tsx` |
| TanStack React adapter | `https://tanstack.com/table/latest/docs/framework/react/react-table` |
| 数据稳定引用 | `https://tanstack.com/table/latest/docs/guide/data` |
| 列定义、accessor、display column | `https://tanstack.com/table/latest/docs/guide/column-defs` |

依赖与本地组件检查使用仓库包管理器：

```bash
bunx --bun shadcn@latest info --json
bunx --bun shadcn@latest docs table
npm view @tanstack/react-table version
```

若 `bunx` 因缓存 link 失败，改用隔离缓存重试：

```bash
BUN_INSTALL_CACHE_DIR=/tmp/bun-cache-gomtmui bunx --bun shadcn@latest docs table
```

## 实施流程

1. 先读 [列表视图](list-view.md)，确认该页面真的需要 table。
2. 定义行类型 `TData`。真实后端数据用 schema、生成类型或适配层收窄；不要为了表格方便写 `as any`。
3. 判断数据规模和一致性要求：
   - 小数据、一次性加载：使用客户端 sorting/filtering/pagination row models。
   - 后端分页、审计记录、费用记录、运维列表：使用 `manualPagination`、`manualSorting`、`manualFiltering`，把状态写回 URL/query。
4. 把列定义与渲染拆到同域 `columns.tsx`。列必须是稳定引用：模块级常量、`useMemo`，或函数返回但由调用方 `useMemo` 包住。
5. 表格组件只负责 table instance、toolbar、table markup、empty/loading/error、pagination 和移动端替代表达。
6. 每个交互能力只接入需要的 TanStack state：`SortingState`、`ColumnFiltersState`、`VisibilityState`、`RowSelectionState`、`PaginationState`。
7. 宽表必须有移动端替代：桌面显示 `<Table>`，移动端显示同数据的 list/item/card 摘要；不要只靠横向滚动处理手机主流程。
8. 验证 `bun run check`。改了真实页面时补充组件测试或浏览器截图，至少覆盖空数据、长文本、分页边界和排序状态。

## gomtmui 组件边界

当前 gomtmui 使用 Next.js App Router、React、TypeScript、Tailwind、shadcn/ui 与 Base UI 组件封装。照搬官方示例前必须检查本地 `src/components/ui/*` 的 API。

特别注意：本仓库 `DropdownMenuTrigger` 是 Base UI wrapper，现有代码使用 `render={<Button ... />}`，不要直接复制 Radix 示例中的 `asChild`。

## 推荐骨架

```tsx
"use client";

import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
  type VisibilityState,
} from "@tanstack/react-table";
import { ChevronDown, Columns3 } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

type Row = {
  id: string;
  name: string;
  status: string;
};

type DataTableProps = {
  items: Row[];
  pageCount: number;
  onSort: (columnId: string) => void;
};

export function DataTable({ items, onSort, pageCount }: DataTableProps) {
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});

  const columns = useMemo<ColumnDef<Row>[]>(
    () => [
      {
        accessorKey: "name",
        header: () => (
          <Button type="button" variant="ghost" size="sm" onClick={() => onSort("name")}>
            名称
          </Button>
        ),
        cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
        enableHiding: false,
      },
      {
        accessorKey: "status",
        header: "状态",
        cell: ({ row }) => row.original.status,
      },
    ],
    [onSort],
  );

  const table = useReactTable({
    data: items,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    pageCount: Math.max(pageCount, 1),
    state: { columnVisibility },
    onColumnVisibilityChange: setColumnVisibility,
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button type="button" variant="outline" size="sm">
                <Columns3 />
                列
                <ChevronDown />
              </Button>
            }
          />
          <DropdownMenuContent align="end" className="w-44">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => (
                <DropdownMenuCheckboxItem
                  key={column.id}
                  checked={column.getIsVisible()}
                  onCheckedChange={(checked) => column.toggleVisibility(Boolean(checked))}
                >
                  {column.id}
                </DropdownMenuCheckboxItem>
              ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* 移动端必须提供同数据摘要视图，例如 <MobileRecords items={items} />。 */}

      <div className="hidden overflow-x-auto rounded-md border md:block">
        <Table aria-label="数据表" className="min-w-[48rem] table-fixed">
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-28 text-center text-muted-foreground">
                  暂无数据
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
```

## 快速决策

| 场景 | 做法 |
| --- | --- |
| 后端已经分页/排序 | `manualPagination: true`、`manualSorting: true`，不要引入对应客户端 row model |
| 客户端小表 | 加 `getPaginationRowModel`、`getSortedRowModel`、`getFilteredRowModel` |
| accessor 值要排序/过滤 | accessor 返回 primitive；复杂 JSX 放 `cell` |
| action/select/expand 列 | 用 display column，设置明确 `id`，通常 `enableHiding: false` |
| 列显隐菜单 | `VisibilityState` + `getAllColumns().filter(getCanHide)` |
| 长文本字段 | cell 内使用 `truncate`、`break-all` 或 `whitespace-normal`，并设置稳定宽度 |
| 手机端 | 用同数据的移动端摘要列表，不把密集表格硬塞进小屏 |
| 图标按钮 | 用 lucide 图标，纯图标按钮必须有 `aria-label` 或 `sr-only` 文本 |

## 常见错误

1. 直接复制 Radix 示例中的 `asChild` 到本仓库 Base UI 组件。
2. 在组件 render 内直接写 `const data = []` 或 `const columns = []` 后传给 `useReactTable`。
3. 服务端分页却启用客户端排序/过滤，导致只排序当前页。
4. 用 display-only JSX 做 accessor，后续排序过滤拿不到稳定 primitive。
5. 为了宽表嵌套 Card 或 card-in-card；表格外层使用普通 section/toolbar，只有重复记录或移动端摘要才用轻量 card。
6. 空状态只渲染空 `<tbody>`；必须提供可见空行或标准 empty state。
7. 分页、筛选、排序只存在客户端 state，刷新或分享 URL 后状态丢失。

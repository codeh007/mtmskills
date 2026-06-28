# 列表视图

## 核心判断

列表视图首先是“进入下一步操作的摘要入口”，不是把一条记录的全部字段铺满屏幕。

先判断用户在这个页面上的主要任务：

1. 如果主要任务是扫描对象、识别状态、执行常用动作、进入详情，优先做列表项视图。
2. 如果主要任务是逐列比较大量同构字段、排序、批量筛选、复制表格数据，才考虑 datatable；细节见 [数据表格](datatable.md)。

设备、任务、配置、联系人、账号、浏览器 profile 这类运营对象列表，默认更接近移动端优先的 item/list 组合，而不是 spreadsheet。

## 查询状态

查询参数、查询过滤器、数据库列表函数参数，本质上是同一个查询状态在不同层的表现。

1. 筛选框是表单。
2. 表单的本质是改变 Next.js route。
3. route query 是页面状态真相。
4. 数据库 `*_list_cursor(...)` / `*_list(...)` 参数是后端查询真相。
5. 页面应把两者直接映射，不要再发明一套前端专属筛选状态。

## URL 参数规则

1. URL 参数应涵盖当前列表页真实支持的全部查询参数，而不是只把某一个特殊筛选项放进 URL。
2. URL 缺少参数时，列表视图必须能使用默认值。
3. URL 出现未知参数时，列表视图应忽略未知项，而不是报错。
4. 新增筛选项时，先检查对应数据库列表函数或 API 是否已经支持该参数；后端还不支持时，不要先做前端专属 query 参数。

示例：

- 正确：`/some-module/products?status=active&platform=android&cursor=opaque123`
- 错误：只把 `deviceId` 放进 URL，其他筛选只存在本地 state
- 错误：前端先引入 `q`，但后端 `*_list_cursor(...)` 还没有对应 `p_query`

## 实现顺序

1. 找到这页对应的数据库列表函数或 API，例如 `device_task_list_cursor(...)`。
2. 确认这个函数当前真实支持哪些参数。
3. 让页面 route query 与这些参数一一对应。
4. 筛选表单改变时显式更新 route query，并清理过期 `cursor`。
5. page 从 `searchParams` 读取 query，再映射为 RPC/API 参数。

## Next.js Page 约定

在当前项目中，Next.js page 应优先遵循如下语法：

```tsx
export default async function SomeListPage({
  searchParams,
}: {
  searchParams: Promise<{
    status?: string;
    platform?: string;
    cursor?: string;
    limit?: string;
  }>;
}) {
  const resolvedSearchParams = await searchParams;

  const rpcArgs = {
    p_status: resolvedSearchParams.status ?? null,
    p_platform: resolvedSearchParams.platform ?? null,
    p_cursor: resolvedSearchParams.cursor ?? null,
    p_limit: resolvedSearchParams.limit ? Number(resolvedSearchParams.limit) : 20,
  };

  // 使用 rpcArgs 调用 *_list_cursor(...)
}
```

不要把 page 写成“同时手搓一套与 route 脱节的本地筛选状态机”。

## 客户端筛选表单

客户端筛选组件应显式更新 route query，而不是只改本地 state。例如：

```tsx
"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

function ListFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function updateFilter(name: string, value: string) {
    const next = new URLSearchParams(searchParams);

    if (value) {
      next.set(name, value);
    } else {
      next.delete(name);
    }

    next.delete("cursor");
    router.replace(`${pathname}?${next.toString()}`);
  }

  return null;
}
```

重置 `cursor` 很重要，因为筛选条件变化后，旧游标通常不再有效。

## 信息层级

列表项只显示摘要信息：

1. 主身份信息。
2. 1 到 3 个最重要的状态或分类标签。
3. 1 到 3 组辅助摘要。
4. 1 到 2 个高频动作。
5. 清晰的详情入口。

如果一个列表项需要完整展示所有字段，说明它正在错误承担详情页职责。

## 移动端优先

移动端下：

1. 信息纵向堆叠。
2. 标题和状态必须先出现。
3. 动作区在底部或右侧清晰聚合。
4. 不依赖横向滚动才能读懂一项。

桌面端只是在此基础上增加更舒展的分栏，而不是回退成宽表格。

## 详情入口

每个列表项至少应有一个清晰的主入口：查看详情、编辑、打开或继续处理。

详情承接优先级：

1. 独立详情页：适合设备、任务、配置等信息较多、动作较多的对象。
2. 对话框：适合轻量预览或少量补充信息。
3. 行内展开：只适合极少量附加信息，不适合完整详情。

如果详情包含完整命令、错误全文、长文本、多个次级动作，优先独立详情页。设备类列表默认优先独立详情页，不要先做弹窗。

## 列表项结构

健康的列表项通常分为 4 层：

1. Header：标题、次标识、紧邻状态 badge。
2. Summary facts：最近事件、最近心跳、接入摘要、平台、provider、关键 owner/category/group。
3. Optional warning block：短错误摘要或 1 到 2 行异常信息。
4. Footer actions：一个主动作，加 1 到 2 个次动作。

空间紧张时，保留标题、状态 badge、一个最关键分类、最近事件和最近心跳；降级次要标签、长接入摘要、错误全文和命令参考。

## 组件与样式

1. 优先用 shadcn/ui 组合或仓库已有 UI 组件。
2. `Badge` / `Bubble` 表示状态、类型、平台、权限。
3. `Switch` / `Toggle` 表示二元设置或模式切换。
4. `Tooltip` 解释图标按钮；图标按钮必须有 `aria-label` 或 `sr-only` 文本。
5. `Empty` 或现有空态组件表达空数据，不渲染空白区域。
6. `Collapsible` 承接低频附加信息。
7. `Button Group` 表达并列命令组。
8. 少写自定义样式，优先使用现有 spacing、typography、border、muted token。
9. 卡片只用于单个重复记录项或明确 framed tool；不要把整页 section 包成 card，不要 card-in-card。

## 设备类列表

设备类列表项推荐信息层级：

1. 主标题：设备名。
2. 次信息：设备 ID。
3. 分类 badge：平台、provider。
4. 状态 badge：在线/离线、业务状态。
5. 摘要信息：接入摘要、最近事件、最近心跳。
6. 条件性错误摘要：仅在存在错误时显示。
7. 动作：查看详情、归档设备或一个常用动作。

不推荐在设备列表项直接展示全量命令、错误全文、所有 metadata 字段、多段说明文案或大量同级按钮。这些应进入设备详情页。

## Table 反模式

以下情况通常是在滥用 table：

1. 页面本质是对象列表，却为了字段整齐硬做成多列表格。
2. 用户需要横向滚动才能看懂一个列表项。
3. 每行同时展示完整详情、完整错误、完整动作清单。
4. 所有列都同等强调，没有主次。
5. 列表项没有明显详情入口。
6. 操作列堆满命令文本、链接和按钮。

出现这些迹象时，优先把页面改回列表项组合。

## 设计前问题

写 JSX 前先回答：

1. 这一项的标题是什么？
2. 用户在 2 秒内最想知道的 3 件事是什么？
3. 用户在列表页最常做的 1 到 2 个动作是什么？
4. 哪些信息应推迟到详情页？
5. 移动端是否能在不横向滚动的前提下读懂一项？

回答不出来时，先不要实现页面。

## 验收清单

1. 这是不是列表项，而不是伪装成列表的详情页？
2. 移动端是否不依赖横向滚动？
3. 标题、状态、主动作是否足够突出？
4. 是否只展示摘要，而不是展示全部字段？
5. 是否有清晰详情入口？
6. 是否避免了把命令、长文本、低频信息塞进列表？
7. route query、服务端查询参数、RPC/API 参数是否一致？
8. 筛选变化后是否清理 `cursor`？
9. 是否优先使用 shadcn/ui 或仓库已有组件，而不是自定义样式堆叠？

## 反例

以下做法应视为错误：

1. `deviceId` 在 URL 中，但 `status`、`scriptType` 只保存在 React state。
2. page 不读 `searchParams`，而是客户端 mounted 后再补一套查询状态。
3. 数据库列表函数只有 `p_status` / `p_cursor`，前端却硬加 `q` 并假装已支持搜索。
4. 筛选变化后不清理 `cursor`，导致翻页状态污染。
5. 列表里铺开完整错误、命令参考、长 metadata，导致列表变成压缩详情页。
6. 为了桌面端整齐，把移动端主流程强行塞进横向滚动 table。

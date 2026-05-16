## 列表视图通用设计

### 核心原则

查询参数、查询过滤器、数据库列表函数参数，本质上是同一个查询状态在不同层的表现。

对列表页来说：

1. 筛选框是表单。
2. 表单的本质是改变 Next.js route。
3. route query 是页面状态真相。
4. 数据库 `*_list_cursor(...)` / `*_list(...)` 参数是后端查询真相。
5. 页面应把两者直接映射，而不是再发明一套前端专属筛选状态。

### URL 参数规则

1. URL 参数应当涵盖当前列表页真实支持的全部查询参数，而不是只把某一个特殊筛选项放进 URL。
2. 当 URL 缺少某些参数时，列表视图必须能正确使用默认值。
3. 当 URL 出现未知参数时，列表视图应忽略未知项，而不是报错。
4. 新增筛选项时，优先检查对应数据库列表函数是否已经支持该参数；如果数据库函数还不支持，不要先做前端专属 query 参数。

示例：

- 正确：`/some-module/products?status=active&platform=android&cursor=opaque123`
- 错误：只把 `deviceId` 放进 URL，其他筛选只存在本地 state
- 错误：前端先引入 `q` 搜索参数，但后端 `*_list_cursor(...)` 还没有对应 `p_query`

### 列表页实现思路

对于一个健康的列表页，应按这个顺序思考：

1. 这页对应的数据库列表函数是什么，例如 `device_task_list_cursor(...)`。
2. 这个函数当前真实支持哪些参数。
3. 页面 route query 应与这些参数一一对应。
4. 筛选表单改变时，应显式更新 route query。
5. page 从 `searchParams` 读取 query，再映射为 RPC 参数。

### Next.js page 约定

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

### 客户端筛选表单约定

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

### 与列表设计的关系

列表页不仅要查询状态正确，也要保证展示形态健康：

1. 列表优先展示摘要，而不是把完整详情铺平。
2. 需要完整脚本、长错误、完整 metadata 时，优先进入详情页。
3. 列表项的字段应服务于“快速扫描、识别状态、进入下一步操作”。

### 反例

以下做法应视为错误：

1. `deviceId` 在 URL 中，但 `status`、`scriptType` 只保存在 React state。
2. page 不读 `searchParams`，而是客户端 mounted 后再补一套查询状态。
3. 数据库列表函数只有 `p_status` / `p_cursor`，前端却硬加 `q` 并假装已支持搜索。
4. 筛选变化后不清理 `cursor`，导致翻页状态污染。

---
name: coding-standards
description: 适用于 TypeScript、JavaScript、React 和 Node.js 开发的通用编码规范、最佳实践与模式。
origin: ECC
---

# 编码规范与最佳实践

适用于所有项目的通用编码规范。

## 何时启用

- 开始一个新项目或模块时
- 审查代码质量与可维护性时
- 重构现有代码以符合约定时
- 需要统一命名、格式或结构一致性时
- 配置 lint、formatting 或 type-checking 规则时
- 为新贡献者介绍编码约定时

## 代码质量原则

### 1. 可读性优先
- 代码被阅读的次数远多于被编写的次数
- 使用清晰的变量名和函数名
- 优先使用自解释代码，而不是依赖注释
- 保持一致的格式

### 2. KISS (Keep It Simple, Stupid)
- 使用能工作的最简单方案
- 避免过度设计
- 不做过早优化
- 易于理解优于炫技式代码

### 3. DRY (Don't Repeat Yourself)
- 将公共逻辑提取为函数
- 创建可复用组件
- 在模块之间共享工具函数
- 避免复制粘贴式编程

### 4. YAGNI (You Aren't Gonna Need It)
- 不要在真正需要之前就构建功能
- 避免臆测式泛化
- 只在必要时引入复杂度
- 先从简单方案开始，需要时再重构

## TypeScript/JavaScript 规范

### 变量命名

```typescript
// PASS: GOOD: 具有描述性的命名
const marketSearchQuery = 'election'
const isUserAuthenticated = true
const totalRevenue = 1000

// FAIL: BAD: 含义不清的命名
const q = 'election'
const flag = true
const x = 1000
```

### 函数命名

```typescript
// PASS: GOOD: 动词-名词模式
async function fetchMarketData(marketId: string) { }
function calculateSimilarity(a: number[], b: number[]) { }
function isValidEmail(email: string): boolean { }

// FAIL: BAD: 含义不清或只有名词
async function market(id: string) { }
function similarity(a, b) { }
function email(e) { }
```

### 不可变性模式（关键）

```typescript
// PASS: 始终使用 spread 操作符
const updatedUser = {
  ...user,
  name: 'New Name'
}

const updatedArray = [...items, newItem]

// FAIL: 绝不要直接修改原对象
user.name = 'New Name'  // BAD
items.push(newItem)     // BAD
```

### 错误处理

```typescript
// PASS: GOOD: 完整的错误处理
async function fetchData(url: string) {
  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return await response.json()
  } catch (error) {
    console.error('Fetch failed:', error)
    throw new Error('Failed to fetch data')
  }
}

// FAIL: BAD: 没有错误处理
async function fetchData(url) {
  const response = await fetch(url)
  return response.json()
}
```

### Async/Await 最佳实践

```typescript
// PASS: GOOD: 能并行时就并行执行
const [users, markets, stats] = await Promise.all([
  fetchUsers(),
  fetchMarkets(),
  fetchStats()
])

// FAIL: BAD: 不必要的串行执行
const users = await fetchUsers()
const markets = await fetchMarkets()
const stats = await fetchStats()
```

### 类型安全

```typescript
// PASS: GOOD: 正确的类型定义
interface Market {
  id: string
  name: string
  status: 'active' | 'resolved' | 'closed'
  created_at: Date
}

function getMarket(id: string): Promise<Market> {
  // 实现
}

// FAIL: BAD: 使用 'any'
function getMarket(id: any): Promise<any> {
  // 实现
}
```

## React 最佳实践

### 组件结构

```typescript
// PASS: GOOD: 带类型的函数式组件
interface ButtonProps {
  children: React.ReactNode
  onClick: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}

export function Button({
  children,
  onClick,
  disabled = false,
  variant = 'primary'
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`btn btn-${variant}`}
    >
      {children}
    </button>
  )
}

// FAIL: BAD: 没有类型，结构不清晰
export function Button(props) {
  return <button onClick={props.onClick}>{props.children}</button>
}
```

### 自定义 Hooks

```typescript
// PASS: GOOD: 可复用的自定义 hook
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

// 用法
const debouncedQuery = useDebounce(searchQuery, 500)
```

### 状态管理

```typescript
// PASS: GOOD: 正确的状态更新方式
const [count, setCount] = useState(0)

// 当新状态依赖旧状态时，使用函数式更新
setCount(prev => prev + 1)

// FAIL: BAD: 直接引用当前 state
setCount(count + 1)  // 在异步场景下可能读到过期值
```

### 条件渲染

```typescript
// PASS: GOOD: 清晰的条件渲染
{isLoading && <Spinner />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// FAIL: BAD: 三元表达式地狱
{isLoading ? <Spinner /> : error ? <ErrorMessage error={error} /> : data ? <DataDisplay data={data} /> : null}
```

## API 设计规范

### REST API 约定

```
GET    /api/markets              # 列出所有 market
GET    /api/markets/:id          # 获取单个 market
POST   /api/markets              # 创建新 market
PUT    /api/markets/:id          # 更新 market（完整更新）
PATCH  /api/markets/:id          # 更新 market（部分更新）
DELETE /api/markets/:id          # 删除 market

# 用于筛选的查询参数
GET /api/markets?status=active&limit=10&offset=0
```

### 响应格式

```typescript
// PASS: GOOD: 一致的响应结构
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}

// 成功响应
return NextResponse.json({
  success: true,
  data: markets,
  meta: { total: 100, page: 1, limit: 10 }
})

// 错误响应
return NextResponse.json({
  success: false,
  error: 'Invalid request'
}, { status: 400 })
```

### 输入校验

```typescript
import { z } from 'zod'

// PASS: GOOD: 使用 Schema 校验
const CreateMarketSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().min(1).max(2000),
  endDate: z.string().datetime(),
  categories: z.array(z.string()).min(1)
})

export async function POST(request: Request) {
  const body = await request.json()

  try {
    const validated = CreateMarketSchema.parse(body)
    // 使用已校验的数据继续处理
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json({
        success: false,
        error: 'Validation failed',
        details: error.errors
      }, { status: 400 })
    }
  }
}
```

## 文件组织

### 项目结构

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API 路由
│   ├── markets/           # Market 页面
│   └── (auth)/           # 认证页面（route groups）
├── components/            # React 组件
│   ├── ui/               # 通用 UI 组件
│   ├── forms/            # 表单组件
│   └── layouts/          # 布局组件
├── hooks/                # 自定义 React hooks
├── lib/                  # 工具与配置
│   ├── api/             # API 客户端
│   ├── utils/           # 辅助函数
│   └── constants/       # 常量
├── types/                # TypeScript 类型
└── styles/              # 全局样式
```

### 文件命名

```
components/Button.tsx          # 组件使用 PascalCase
hooks/useAuth.ts              # hooks 使用 camelCase，并带 'use' 前缀
lib/formatDate.ts             # 工具函数使用 camelCase
types/market.types.ts         # 类型文件使用 camelCase，并带 .types 后缀
```

## 注释与文档

### 何时写注释

```typescript
// PASS: GOOD: 解释 WHY，而不是 WHAT
// 使用指数退避，避免在服务故障时压垮 API
const delay = Math.min(1000 * Math.pow(2, retryCount), 30000)

// 这里有意使用可变操作，以优化大数组场景下的性能
items.push(newItem)

// FAIL: BAD: 只是在重复显而易见的事情
// 将计数器加 1
count++

// 将 name 设为用户名称
name = user.name
```

### 公共 API 的 JSDoc

```typescript
/**
 * 使用语义相似度搜索 markets。
 *
 * @param query - 自然语言搜索查询
 * @param limit - 最大返回结果数（默认：10）
 * @returns 按相似度分数排序的 market 数组
 * @throws {Error} 当 OpenAI API 调用失败或 Redis 不可用时抛出
 *
 * @example
 * ```typescript
 * const results = await searchMarkets('election', 5)
 * console.log(results[0].name) // "Trump vs Biden"
 * ```
 */
export async function searchMarkets(
  query: string,
  limit: number = 10
): Promise<Market[]> {
  // 实现
}
```

## 性能最佳实践

### 记忆化

```typescript
import { useMemo, useCallback } from 'react'

// PASS: GOOD: 对高开销计算做记忆化
const sortedMarkets = useMemo(() => {
  return markets.sort((a, b) => b.volume - a.volume)
}, [markets])

// PASS: GOOD: 对回调做记忆化
const handleSearch = useCallback((query: string) => {
  setSearchQuery(query)
}, [])
```

### 懒加载

```typescript
import { lazy, Suspense } from 'react'

// PASS: GOOD: 懒加载重量级组件
const HeavyChart = lazy(() => import('./HeavyChart'))

export function Dashboard() {
  return (
    <Suspense fallback={<Spinner />}>
      <HeavyChart />
    </Suspense>
  )
}
```

### 数据库查询

```typescript
// PASS: GOOD: 只查询必要字段
const { data } = await supabase
  .from('markets')
  .select('id, name, status')
  .limit(10)

// FAIL: BAD: 查询所有字段
const { data } = await supabase
  .from('markets')
  .select('*')
```

## 测试规范

### 测试结构（AAA 模式）

```typescript
test('calculates similarity correctly', () => {
  // 准备
  const vector1 = [1, 0, 0]
  const vector2 = [0, 1, 0]

  // 执行
  const similarity = calculateCosineSimilarity(vector1, vector2)

  // 断言
  expect(similarity).toBe(0)
})
```

### 测试命名

```typescript
// PASS: GOOD: 具有描述性的测试名称
test('returns empty array when no markets match query', () => { })
test('throws error when OpenAI API key is missing', () => { })
test('falls back to substring search when Redis unavailable', () => { })

// FAIL: BAD: 含糊的测试名称
test('works', () => { })
test('test search', () => { })
```

## 代码坏味道识别

注意以下反模式：

### 1. 过长函数
```typescript
// FAIL: BAD: 函数超过 50 行
function processMarketData() {
  // 100 lines of code
}

// PASS: GOOD: 拆分为更小的函数
function processMarketData() {
  const validated = validateData()
  const transformed = transformData(validated)
  return saveData(transformed)
}
```

### 2. 过深嵌套
```typescript
// FAIL: BAD: 5 层以上嵌套
if (user) {
  if (user.isAdmin) {
    if (market) {
      if (market.isActive) {
        if (hasPermission) {
          // 执行业务逻辑
        }
      }
    }
  }
}

// PASS: GOOD: 使用提前返回
if (!user) return
if (!user.isAdmin) return
if (!market) return
if (!market.isActive) return
if (!hasPermission) return

// 执行业务逻辑
```

### 3. 魔法数字
```typescript
// FAIL: BAD: 没有解释的数字
if (retryCount > 3) { }
setTimeout(callback, 500)

// PASS: GOOD: 使用具名常量
const MAX_RETRIES = 3
const DEBOUNCE_DELAY_MS = 500

if (retryCount > MAX_RETRIES) { }
setTimeout(callback, DEBOUNCE_DELAY_MS)
```

**请记住**：代码质量不可妥协。清晰、可维护的代码，才能支撑快速开发与有把握的重构。

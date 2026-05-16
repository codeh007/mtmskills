# 重复检测 Prompt

将这个 prompt 与 **opus** 子代理搭配使用，以进行彻底的语义分析。

对于每个包含 3 个以上函数的分类，都要 **单独运行一次** 这个 prompt。

## Prompt 模板

```
你正在分析 "{CATEGORY}" 分类中的函数，以查找语义重复。

语义重复是指这些函数承担的是 SAME PURPOSE，即使：
- They have different names
- They use different implementations
- They have slightly different signatures
- One is more general than another

## 你的任务

1. 比较该分类中的所有函数
2. 找出做的是同一件事的函数组
3. 对每个重复组评估置信度并给出建议动作

## 输出格式

返回一个由重复组构成的 JSON 数组：

```json
[
  {
    "intent": "<what these functions all do>",
    "confidence": "HIGH|MEDIUM|LOW",
    "functions": [
      {
        "file": "<file path>",
        "name": "<function name>",
        "line": <line number>,
        "notes": "<implementation specifics>"
      }
    ],
    "differences": "<how implementations differ, if at all>",
    "recommendation": {
      "action": "CONSOLIDATE|INVESTIGATE|KEEP_SEPARATE",
      "survivor": "<which function to keep, if CONSOLIDATE>",
      "reason": "<why this recommendation>"
    }
  }
]
```

## 置信度等级

- **HIGH**: 基本可以确定是同一件事。输入→输出语义一致。
  示例：`formatDate(d)` 和 `dateToString(d)` 都以完全相同的方式格式化日期

- **MEDIUM**: 很可能是同一件事，但存在细微差异。
  示例：`validateEmail(s)` 使用正则，`checkEmail(s)` 使用库，但用途相同

- **LOW**: 可能相关，值得进一步调查。
  示例：`sanitizeInput(s)` 和 `escapeHtml(s)`，彼此相关，但用途可能不同

## 建议动作

- **CONSOLIDATE**: 这些函数是重复项。保留命名、实现或测试更好的那个。
- **INVESTIGATE**: 需要阅读完整实现后才能判断。标记给人工审查。
- **KEEP_SEPARATE**: 函数看起来相似，但用途不同。

## 指南

1. 仔细阅读上下文和实现片段
2. 考虑边界情况处理，例如两个函数在处理 null 时可能不同
3. 如果函数位于测试文件中，它们更不可能是真正的重复项
4. 通用工具函数（identity、noop、constant）往往是有意重复存在的
5. 如果拿不准，优先推荐 INVESTIGATE，而不是 CONSOLIDATE

## Functions in "{CATEGORY}" Category

<INSERT_CATEGORY_FUNCTIONS_HERE>
```

## 用法

1. 先运行分类步骤（见 `categorize-prompt.md`）
2. 过滤 `categorized.json`，取出某一个分类的函数：
   ```bash
   jq '[.[] | select(.category == "validation")]' categorized.json > validation-functions.json
   ```
3. 将 `{CATEGORY}` 替换为分类名称
4. 将 `<INSERT_CATEGORY_FUNCTIONS_HERE>` 替换为过滤后的 JSON
5. 使用该 prompt 派发 opus 子代理
6. 对每个包含 3 个以上函数的分类重复执行
7. 合并输出，生成最终报告

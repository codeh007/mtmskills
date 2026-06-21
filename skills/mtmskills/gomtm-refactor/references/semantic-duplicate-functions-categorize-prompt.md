# 函数分类 Prompt

将这个 prompt 与 **haiku** 子代理搭配使用，以低成本完成分类。

## Prompt 模板

```
读取位于 <CATALOG_PATH> 的函数目录，并对每个函数进行分类。

根据每个函数的主要用途，将其分配到且仅分配到 ONE 个分类中。

## Categories

- **file-ops**: Reading, writing, path manipulation, directory operations
- **string-utils**: Formatting, parsing, sanitization, case conversion, truncation
- **validation**: Input checking, schema validation, type guards, assertions
- **error-handling**: Error creation, wrapping, formatting, logging helpers
- **http-api**: Request building, response parsing, URL construction, headers
- **date-time**: Date formatting, parsing, comparison, timezone handling
- **data-transform**: Mapping, filtering, normalization, serialization
- **database**: Query building, connection management, migrations
- **logging**: Log formatting, debug helpers, telemetry
- **config**: Configuration loading, environment variables, settings
- **async-utils**: Promise helpers, retry logic, debounce, throttle
- **testing**: Test utilities, mocks, fixtures, assertions
- **ui-helpers**: DOM manipulation, event handling, component utilities
- **crypto**: Hashing, encryption, token generation
- **provider-impl**: AI provider interface implementations (createResponse, etc.)
- **tool-impl**: Tool interface implementations (executeValidated, etc.)
- **event-handling**: Event creation, emission, processing, subscription
- **session-management**: Session/thread/conversation lifecycle
- **compaction**: Message compaction, summarization, token management
- **other**: 不符合上述分类（在 purpose 中注明子类别）

## 输出格式

对每个函数，输出：
{"file": "...", "name": "...", "line": N, "category": "...", "purpose": "one sentence"}

## 指南

1. 关注函数做了 WHAT，而不是 HOW 实现的
2. 如果一个函数看起来适合多个分类，选择其主要用途
3. 构造函数：根据类的职责进行分类
4. 接口实现：视情况使用 provider-impl 或 tool-impl
5. `purpose` 描述要简洁但具体

## 重要

使用 Write 工具将完整的 JSON 数组保存到 <OUTPUT_PATH>。
不要截断或总结，必须写入 ALL 条目。
```

## 用法

1. 运行提取：`scripts/duplicate-functions/extract-functions.sh src/ -o catalog.json`
2. 使用上面的 prompt 派发 haiku 子代理，并替换：
   - 将 `<CATALOG_PATH>` 替换为 `catalog.json` 的路径
   - 将 `<OUTPUT_PATH>` 替换为期望的输出路径（例如 `categorized.json`）
3. 验证输出文件已创建，且包含所有条目

**关键：** 子代理必须使用 Write 工具保存输出。如果它只返回摘要，就用明确的文件写入指令重新提示它。

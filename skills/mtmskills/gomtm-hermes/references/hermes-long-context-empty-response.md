# Hermes 长上下文空回复排障

## 信号

```bash
grep -Ei "Empty response|pending tool result|No fallback available|context|Provider:" ~/.hermes/logs/errors.log | tail -80
```

典型链路：模型在 tool result 后返回空 assistant 内容；Hermes retry 后仍为空；没有 fallback provider 时会结束在 pending tool result，Telegram 看起来像“不再回复”。

## 快速修复

1. 备份配置：

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.$(date +%Y%m%d_%H%M%S).bak
```

2. 对自定义 OpenAI-compatible endpoint 使用真实稳定窗口，并保持所有路径一致。若供应商公开元数据/`/models` 明确支持百万级窗口（例如 gpt-5.5 为 `1050000`），不要下调成 256K；只有稳定窗口未知或 endpoint 实测不稳时才临时保守下调。配置细节以 `templates/config.yaml` 为权威模板，正文和本文档不再重复完整 YAML。

3. 对长工具链设置明确输出预算。`model.max_tokens` 是单次 assistant 输出上限（包含 `tool_calls[].function.arguments`），不是总上下文窗口；`model.context_length` 是输入+输出总窗口。复杂任务如果出现 `Response truncated due to output length limit`，先用官方配置命令确认输出预算：

```bash
hermes config set model.max_tokens 32768
```

如果 endpoint 拒绝或仍不稳定，再按实测降到 `16384` 或 `8192`。这只能降低因输出预算不足导致的截断概率；长文档仍应拆成短骨架 + 多次 patch，而不是一次性生成超长 `write_file` 参数。

4. 如果问题总在约 250K-300K 上下文附近复现，不要继续只调 `max_tokens`。这说明 custom endpoint / 中转层的实际稳定窗口可能低于 `context_length` 配置，或者大量 tool schema / tool result 让请求比屏幕估算更大。`compression.threshold` 乘以 `context_length` 才是自动压缩线；`1050000 * 0.5 = 525000`，因此 270K 附近不会自动压缩。此时应先把阈值调到触发点之前：

```bash
hermes config set compression.threshold 0.25
```

必要时临时把 `model.context_length` 也保守下调到实测稳定窗口，并同步 custom provider、alias、auxiliary compression 中的 context 配置。已经进入反复空回复 / 截断的旧会话，优先 `/compress` 或 `/new`，不要期待修改配置后旧 session 自动恢复。

5. 保持 `security.redact_secrets: true`，不要用 `HERMES_REDACT_SECRETS=false` 覆盖；否则 Hermes 会提示 secrets 可能进入 chat output、session JSONs 和 logs。

6. 不在服务/worker 环境设置 `HERMES_TUI=1`；非 TTY 验证显式使用 `HERMES_TUI=0`。

## 验证

```bash
hermes config check
HERMES_TUI=0 hermes chat --quiet -q '只输出 OK'
HERMES_TUI=0 hermes chat --quiet -q '读取当前 Hermes model/context 配置，只回复主要 context_length 数字和 OK。不要修改文件。'
grep -Ei "Empty response|pending tool result|No fallback available" ~/.hermes/logs/errors.log | tail -20
```

期望：短调用返回 `OK`；context 检查返回已配置的真实 `<context-length>` 和 `OK`；修复后的时间段没有新的空回复链。gateway 场景需重启 gateway 或开新 session。

## 判断规则

- 短请求正常不代表长工具链稳定。
- `context_length` 写小会让 `compression.threshold` 过早触发；写大于真实窗口会过晚触发。
- `max_tokens` 只管单次输出预算；长上下文空回复、`No fallback available` 或 270K 附近稳定复现，优先看实际稳定窗口、压缩阈值和 fallback。
- Hermes 未知模型 fallback 是 256000；看到 `256K` / `256,000` 通常表示当前 session 没读到显式配置或探测失败走了 fallback。
- 只改 `model.context_length` 不够；custom provider、alias 和 auxiliary compression 仍可能覆盖解析结果。
- 无 fallback provider 时，空回复不会自动切换模型。

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

3. 先确认真实运行时 provider / base URL。Hermes v0.14.0 已知存在上游问题：gateway、CLI、executor 等路径可能没有一致传播 `model.provider` / `model.base_url`，在存在 OpenRouter 或其他环境变量时发生路由漂移。参考 `NousResearch/hermes-agent#5358`。排障时不能只看 `config.yaml`，还要看日志中的 `provider=`、`base_url=`、`model=`。

4. 对长工具链设置输出预算只能作为受控实验。`model.max_tokens` 是单次 assistant 输出上限（包含 `tool_calls[].function.arguments`），不是总上下文窗口；`model.context_length` 是输入+输出总窗口。它不是当前现场的默认修复。本机曾尝试 `model.max_tokens: 32768` 加 `compression.threshold: 0.25`，重启 TUI 后 context 显示变成 0 且工具调用行为异常，已回滚。

如必须测试，先备份配置，并只在新 session 中验证：

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.$(date +%Y%m%d_%H%M%S).bak
hermes config set model.max_tokens 32768
```

若出现 context 计数为 0、provider/base_url 漂移、工具调用异常或 endpoint 拒绝，应立即恢复备份。长文档仍应拆成短骨架 + 多次 patch，而不是一次性生成超长 `write_file` 参数。

5. 如果问题总在约 250K-300K 上下文附近复现，`compression.threshold * context_length` 触发线仍是一个需要核对的方向，但不要直接把阈值降到 `0.25` 作为默认修复。本机已实测该组合导致 TUI 异常。更稳的操作是手动 `/compress` 或 `/new`，并收集 provider/base_url/context 显示与日志证据。

6. 保持 `security.redact_secrets: true`，不要用 `HERMES_REDACT_SECRETS=false` 覆盖；否则 Hermes 会提示 secrets 可能进入 chat output、session JSONs 和 logs。

7. 不在服务/worker 环境设置 `HERMES_TUI=1`；非 TTY 验证显式使用 `HERMES_TUI=0`。

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
- `max_tokens` 只管单次输出预算；当前现场不能把它作为默认修复。
- Hermes 未知模型 fallback 是 256000；看到 `256K` / `256,000` 通常表示当前 session 没读到显式配置或探测失败走了 fallback。
- 只改 `model.context_length` 不够；custom provider、alias 和 auxiliary compression 仍可能覆盖解析结果。
- 无 fallback provider 时，空回复不会自动切换模型。
- v0.14.0 存在 provider/base_url 配置解析漂移风险；看到异常时先核对日志中真实 provider/base_url。

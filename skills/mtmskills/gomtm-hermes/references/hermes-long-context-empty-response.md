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

2. 对自定义 OpenAI-compatible endpoint 使用真实稳定窗口，并保持所有路径一致。若供应商公开元数据/`/models` 明确支持百万级窗口（例如 OpenRouter `openai/gpt-5.5` 为 `1050000`），不要下调成 256K；只有稳定窗口未知或 endpoint 实测不稳时才临时保守下调：

```yaml
model:
  default: <model-id>
  model: <model-id>
  base_url: ${OPENAI_BASE_URL}
  api_key: ${OPENAI_API_KEY}
  api_mode: chat_completions
  context_length: <context-length>
  models:
    <model-id>:
      context_length: <context-length>

custom_providers:
  - name: <Provider Display Name>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    api_mode: chat_completions
    model: <model-id>
    context_length: <context-length>
    models:
      <model-id>:
        context_length: <context-length>

model_aliases:
  <model-id>:
    provider: custom
    model: <model-id>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    api_mode: chat_completions
    context_length: <context-length>

compression:
  enabled: true
  threshold: 0.5

auxiliary:
  compression:
    provider: custom
    model: <model-id>
    base_url: ${OPENAI_BASE_URL}
    api_key: ${OPENAI_API_KEY}
    timeout: 180
    extra_body: {}
```

3. 不在服务/worker 环境设置 `HERMES_TUI=1`；非 TTY 验证显式使用 `HERMES_TUI=0`。

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
- 只改 `model.context_length` 不够；custom provider 和 alias 仍可能覆盖解析结果。
- 无 fallback provider 时，空回复不会自动切换模型。

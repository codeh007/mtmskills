# Hermes 长上下文空回复排障

## 信号

```bash
grep -Ei "Empty response|pending tool result|No fallback available|context|Provider:" ~/.hermes/logs/errors.log | tail -80
```

典型链路：长会话接近 endpoint / 套餐真实窗口后，模型在 tool result 后返回空 assistant 内容，或 assistant 输出被截断；Hermes retry 后仍为空，Telegram 看起来像“不再回复”。

## 快速修复

1. 备份配置：

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.$(date +%Y%m%d_%H%M%S).bak
```

2. 对自定义 OpenAI-compatible endpoint 使用真实稳定窗口，并保持所有路径一致。当前 gomtm 默认 `gpt-5.5` relay 套餐链路按 400K 总窗口处理；不要把官方 API 的百万级窗口直接写进 relay 配置。配置细节以 `templates/config.yaml` 为权威模板，正文和本文档不再重复完整 YAML。

3. 先确认真实运行时 provider / base URL。排障时不能只看 `config.yaml`，还要看日志中的 `provider=`、`base_url=`、`model=`，确认实际请求走的是目标 relay。

4. `model.max_tokens` 是单次 assistant 输出上限，不是总上下文窗口；不能修复输入窗口被套餐或中转提前截断的问题。不要把它作为默认修复写进模板。

5. 如果问题总在约 250K-300K 输入附近复现，优先检查当前链路的真实输入上限。按 400K 总窗口、约 272K 输入 + 128K 输出的链路理解，这个故障点符合入口侧先到顶。

6. 长文档和复杂任务仍应拆成短骨架 + 多次 patch，必要时手动 `/compress` 或 `/new`，不要一次性生成超长工具参数。

7. 保持 `security.redact_secrets: true`，不要用 `HERMES_REDACT_SECRETS=false` 覆盖；否则 Hermes 会提示 secrets 可能进入 chat output、session JSONs 和 logs。

8. 不在服务/worker 环境设置 `HERMES_TUI=1`；非 TTY 验证显式使用 `HERMES_TUI=0`。

## 验证

```bash
hermes config check
HERMES_TUI=0 hermes chat --quiet -q '只输出 OK'
HERMES_TUI=0 hermes chat --quiet -q '读取当前 Hermes model/context 配置，只回复主要 context_length 数字和 OK。不要修改文件。'
grep -Ei "Empty response|pending tool result|No fallback available" ~/.hermes/logs/errors.log | tail -20
```

期望：短调用返回 `OK`；context 检查返回 `400000` 和 `OK`；修复后的时间段没有新的空回复链。gateway 场景需重启 gateway 或开新 session。

## 判断规则

- 短请求正常不代表长工具链稳定。
- `context_length` 写大于真实窗口会让 Hermes 误判可用上下文。
- `max_tokens` 只管单次输出预算，不能解决输入窗口上限。
- Hermes 未知模型 fallback 是 256000；看到 `256K` / `256,000` 通常表示当前 session 没读到显式配置或探测失败走了 fallback。
- 只改 `model.context_length` 不够；custom provider、alias 和 auxiliary compression 仍可能覆盖解析结果。
- fallback provider 不能扩大当前模型/套餐的输入窗口。

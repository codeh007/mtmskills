# OpenClaw 架构参考

OpenClaw 更适合由自身配置文件、状态目录、CLI、插件和渠道能力驱动。设计集成时，优先把 OpenClaw 当作独立 Agent runtime，而不是把它拆成大量外部状态机。

## 选择原则

1. 需要自然语言、多步推理、多渠道交互或工具调用时，优先让 OpenClaw 作为 Agent runtime 主导。
2. 需要确定性状态、审计、队列、权限或持久化时，使用外部系统保存 canonical data。
3. OpenClaw 配置应保留在 `openclaw.json` 或明确的配置管理系统中。
4. 不要把密钥、私有 endpoint、临时调试路径写入技能文档。

## 集成边界

- OpenClaw 负责推理、工具调用、会话和渠道交互。
- 外部系统负责稳定数据、权限边界和审计记录。
- 隧道或反向代理只负责暴露 endpoint，不应成为业务状态真相。

## 设计检查

在新增 OpenClaw 集成前确认：

1. 目标能力是否已经由 OpenClaw CLI、slash command、plugin 或 hook 支持。
2. 新状态是否必须持久化，还是可以保留在 OpenClaw 状态目录。
3. 多实例是否会共享同一渠道凭据、工作目录或配置文件。
4. 故障恢复依赖哪些文件、环境变量和外部服务。

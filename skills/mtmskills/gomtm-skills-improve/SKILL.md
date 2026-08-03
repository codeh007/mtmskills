---
name: gomtm-skills-improve
description: Use when creating or editing a gomtm skill or its resources, or reviewing/validating one without making changes.
---

# gomtm Skills Improve

## 工作边界

先从宿主已安装技能目录解析并读取 `writing-great-skills`，把它作为通用写作 reference；本技能只补充 gomtm 技能仓库的维护流程、资源边界和验收方式。若依赖无法解析，`edit` 模式暂停需要该规范的编辑和质量结论，只做明确标注的机械检查并生成“未解析依赖”后续任务；`review-only` 可继续只读诊断，但不得声称已完成通用规范验证。

默认读者是掌握公开通用知识的合格程序员。正文只记录会改变 agent 判断、操作或交付结果的仓库约束、领域规则、真实坑点和验收证据；命令只保留仓库特有的参数、顺序、权限或结果语义，省略常见命令和语法的教学。

## 工作模式

- `edit`：用户明确授权对指定范围落地修改。
- `review-only`：用户要求审查、解释或建议；只读并交付证据、结论和最小补丁建议。

先确定模式、目标文件、授权范围、验收条件和事实来源；授权不明确时按 `review-only` 处理。

## 1. 盘点

从仓库根目录开始，读取目标 `SKILL.md`、仓库级和目录级指引、README、CI/验证入口。确认目标是仓库 canonical 源码 `skills/**/<skill-name>/SKILL.md`；已安装的 `~/.agents`、`~/.codex` 或其他 agent 副本不是编辑目标。列出目标目录的 `references/**`、`templates/**`、`assets/**`、`scripts/**` 和可选的 `agents/openai.{yaml,yml}`，只读取当前分支直接需要的 reference/template；对 asset、script、元数据和 `copy`、`backup`、生成副本先核对存在性、入口与角色，只有验收或行为分析需要时才读取内容。副本只记录 canonical 角色；未经授权不删除、覆盖或重命名。

技能内路径使用 `references/...`、`templates/...`、`assets/...`、`scripts/...` 等相对形式；跨仓库路径使用仓库相对路径或 `<repo>`、`<service>`、`<host>` 占位符。涉及行为约束时回到真实源码、配置或脚本核对。

**完成：** 已列出授权范围、验收条件、调用分支、事实来源和目录资源；每个资源都标记为已读取、已核对存在性或明确不适用，并确认 canonical 文件和副本角色。

## 2. 诊断

把用户报告转换为可观察的验收检查，先按 `writing-great-skills` 的 Invocation、Information Hierarchy 和 Pruning 规则分类，再逐项核对 gomtm 事实：

- frontmatter `name` 与叶目录名一致；结合 `disable-model-invocation` 检查 `description` 的身份与触发信息，不复述正文流程；每个真实触发分支都有入口（步骤或 reference）、边界和完成证据；只有存在步骤时才要求步骤完成条件。
- 同一事实只有一个 canonical 来源；模板、脚本、资源、元数据和正文没有漂移；重复意义在 `edit` 中合并，`review-only` 中标出来源和最小合并建议；逐句执行 no-op 检查，`edit` 删除整句 no-op，`review-only` 提出删除建议，不用改写掩盖它。
- reference 只在对应分支通过可靠的 context pointer 读取，并把定义、规则和必要 caveat 共置；涉及行为的规则回到源码、配置或脚本确认。
- 按固定顺序解析引用：frontmatter 的 `related_skills`，正文明确的技能指针，Markdown 相对链接和本地路径字面量。仓内技能解析到 `skills/**/SKILL.md`；宿主技能核对已安装目录或依赖清单；本地相对路径按引用文件所在目录解析并逐项做大小写检查。忽略外部 URL、命令参数、环境变量值、代码示例中的占位符和 `<repo>` 等非文件文本；无法解析的引用进入后续任务。
- 示例、路径和命令保持可迁移；稳定 canonical 事实才使用真实名称。外部公开文档使用链接和摘要，不整段复制到 `references/`。

行为改动先冻结目标及直接受影响资源的旧快照（提交标识或校验和），为每个受影响分支保存稳定输入、上下文、期望判据和实际结果；在独立的新上下文以同一场景复测并比较可观察结果。纯措辞、路径或格式改动可用 frontmatter 解析、路径检查和授权范围 diff 作为基线。

**完成：** `edit` 已将每项修改追溯到用户要求、权威事实或失败检查，并完成适用分支的基线/复测；`review-only` 已为每项发现保存证据和最小补丁建议，没有把建议描述为已落地。

## 3. 编辑

仅在 `edit` 模式应用授权范围内的最小修改，保持原技能语言和结构；跨文件契约变化时同步唯一受影响的 reference、template、asset、script 或元数据，不顺手重构无关内容。依赖未解析且会影响判断时停止编辑并报告阻塞。

**完成：** `edit` 的 diff 只覆盖授权文件，canonical 源和引用资源没有新的重复权威源；`review-only` 不写文件，交付按影响排序的发现、来源、最小改法和仍需授权的验证。

## 4. 验证

在目标仓库根目录先对授权文件运行 `git diff --check`，再运行 README 和 CI 声明的入口。当前 `mtmskills` 的 canonical 发现命令是 `npx skills add <repo-root> --list --full-depth`；CI 还运行 `node --test .github/tests/mtm-image2-output.test.mjs` 和非递归发现检查。嵌套布局需要 `--full-depth`；只有在授权允许依赖下载、缓存写入和安装副作用时运行 npx，否则记录为待验证。

验证 frontmatter 可解析、技能只被发现一次、`name` 与叶目录一致、所有本地引用存在且大小写匹配；对存在的 template 使用对应解析器，对存在的 script 验证入口、调用方式和失败条件；按仓库已有 scanner 检查 secret 和不可迁移绝对路径，没有 scanner 时记录手工检查证据。行为修改复测第 2 步冻结快照中的同一场景。

按每个适用分支、文件或资源、命令、退出码、关键结果和授权状态记录证据，状态仅使用 `verified`、`pending` 或 `out of scope`。无关历史失败单独说明，不用它们掩盖本次范围内的失败。

**完成：** 所有修改文件和直接受影响资源均有验证证据；授权范围内没有未解释的失败，或已明确标记为待验证/阻塞及其原因。

## 5. 后续优化建议

收尾时检查目标直接引用的技能和本地文件；仅在发现跨文件影响、相邻技能/规格/`AGENTS.md` 可能重复或冲突，或用户明确要求时扩展到相关相邻目录。报告重复、术语不一致、规则冲突、权威来源不清和失效引用；没有发现时报告检查范围和“暂无后续建议”。

每条后续建议都包含：任务标题、证据路径和段落、当前权威来源、影响、目标变更、验收条件、授权边界和验证入口。建议任务不在当前授权内顺手实施；依赖或路径无法解析时也按此格式记录，恢复依赖后重新验证。

**完成：** 交付中已覆盖实际受影响的技能、规格、指引和本地引用检查；每条建议都有可执行的下一步，或明确记录检查范围内没有建议。

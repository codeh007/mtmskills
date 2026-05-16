# 说明

- 本仓库用于维护可在 Codex、hermes-agent 和其他标准 Agent 工具中安装的便携技能。
- `skills/<name>/SKILL.md` 是每个技能的规范入口，目录名必须和 frontmatter 的 `name` 一致。
- 优先编写简洁的 instruction-only 技能；只有在能减少真实重复劳动时，才加入 `scripts/`、`references/` 或 `assets/`。
- 不要提交密钥、本地环境文件、生成缓存或私有工作站路径。
- 新增或修改技能后，先运行 `scripts/validate-skills`，再用 `npx skills add /workspace/mtmskills --list` 确认 CLI 能发现技能。
- 推送主分支后，使用 `npx skills add codeh007/mtmskills --list` 确认远端仓库中的技能可被标准安装命令发现。

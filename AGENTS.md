# Repository Instructions

- Keep skills portable across Codex, hermes-agent, and other standards-based agent tools.
- Treat `skills/<name>/SKILL.md` as the canonical skill entry point.
- Keep each skill self-contained. Do not rely on `/workspace/gomtm` paths unless the skill is explicitly gomtm-project-only.
- Prefer concise instruction-only skills. Add `scripts/`, `references/`, or `assets/` only when they remove real repeated work.
- Do not commit secrets, local environment files, generated caches, or private workstation paths.
- Validate changed skills before publishing.

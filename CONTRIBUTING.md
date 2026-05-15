# Contributing

## Create a Skill

1. Choose a short lowercase `hyphen-case` name.
2. Create `skills/<name>/SKILL.md`.
3. Add YAML frontmatter with `name` and `description`.
4. Keep the body focused on the minimum workflow an agent needs.
5. Add `agents/openai.yaml` when Codex UI metadata is useful.
6. Run `scripts/validate-skills` before committing.

## Review Checklist

- The folder name matches `SKILL.md` `name`.
- The `description` explains when to use the skill.
- The skill does not depend on hidden local files or credentials.
- Resource directories exist only when they are needed.
- Instructions are specific enough to be useful but not project-history notes.

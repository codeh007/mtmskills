# mtmskills

Portable agent skills for MTM workflows.

This repository packages reusable skills outside the `gomtm` project so they can be installed by Codex, hermes-agent, and other tools that support the standard agent skills layout.

## Layout

```text
skills/
  gomtm-demo1/
    SKILL.md
    agents/openai.yaml
```

Each skill is a directory whose name matches the `name` in `SKILL.md`.

## Skill Requirements

- Use lowercase `hyphen-case` skill names.
- Keep `SKILL.md` frontmatter limited to `name` and `description` unless a target agent explicitly supports more fields.
- Keep `description` focused on when the skill should trigger.
- Keep `SKILL.md` concise and move detailed material into one-level `references/` files only when needed.
- Add `scripts/`, `references/`, or `assets/` only when the skill actually needs them.
- Use `agents/openai.yaml` for Codex-facing UI metadata and policy.

## Install

Use the open agent skills CLI for standard installs:

```bash
npx skills add codeh007/mtmskills --list
npx skills add codeh007/mtmskills --skill gomtm-demo1 -a codex
npx skills add codeh007/mtmskills --skill gomtm-demo1 -a hermes-agent
```

For a global install:

```bash
npx skills add codeh007/mtmskills --skill gomtm-demo1 -a codex -g
```

For local development, install from the checkout:

```bash
npx skills add /workspace/mtmskills --skill gomtm-demo1 -a codex
```

Manual install is also possible by copying or symlinking individual skill folders into the target agent's skills directory.

```bash
git clone https://github.com/codeh007/mtmskills.git
mkdir -p ~/.codex/skills
cp -R mtmskills/skills/gomtm-demo1 ~/.codex/skills/
```

The public GitHub install commands require the repository to be public, or a GitHub environment with access to the private repository.

## Validate

Validate a skill before publishing changes:

```bash
scripts/validate-skills
```

Use the target agent's own skill validator when it provides one.

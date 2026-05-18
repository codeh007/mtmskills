---
name: gomtm-installer
description: Use when initializing a Linux host for gomtm-adjacent work, preparing a development machine, diagnosing installer prerequisites, or deciding whether host setup belongs in gomtm-install instead of gomtm core.
---

# gomtm Installer

## Canonical Source

The canonical installer skill and scripts live in the public `gomtm-install` repository:

```text
/workspace/gomtm-install/skills/gomtm-installer/SKILL.md
/workspace/gomtm-install/scripts/
```

This `mtmskills` copy is a compatibility mirror so older skill installs still route agents to the right project.

## Core Rules

- Prefer `gomtm-install` for host provisioning, development environment setup, Agent tooling, VNC/browser setup, and future base image assembly.
- Treat the existing `gomtm install` command as gomtm-core compatibility during migration.
- Do not add new installer responsibilities to `gomtm/pkg/mtinstall/installers`.
- Use `gomtm-install` scripts first; its CLI is a thin dispatcher over scripts.
- Run `--dry-run` before changing a host when a dry-run mode exists.

## Commands

```bash
cd /workspace/gomtm-install
bin/gomtm-install doctor --json
bin/gomtm-install install base --dry-run
bin/gomtm-install install runtime-languages --dry-run
bin/gomtm-install install docker --dry-run
bin/gomtm-install install dev --dry-run
bin/gomtm-install install agent-tools --dry-run
bin/gomtm-install install vnc --dry-run
bin/gomtm-install remote bootstrap --dry-run user@host
tests/smoke.sh
```

## Install This Skill

Prefer installing the canonical public skill directly:

```bash
npx skills add https://github.com/codeh007/gomtm-install --skill gomtm-installer --global --yes
```

Use this repository only when installing the broader private skill bundle.

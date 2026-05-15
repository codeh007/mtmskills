---
name: gomtm-demo2
description: Use when verifying that mtmskills is installed correctly, testing agent skill discovery, or demonstrating the minimum shape of a portable agent skill without touching live gomtm systems.
---

# Gomtm Demo 2

## Overview

Use this skill as a small, harmless smoke test for the mtmskills repository. It proves that an agent can discover a skill, load its `SKILL.md`, and follow a short instruction set.

## Demo Response

When this skill is invoked, answer with:

1. A one-sentence confirmation that `gomtm-demo2` was loaded.
2. The current task summary in one sentence.
3. A short checklist showing:
   - `SKILL.md` frontmatter was readable.
   - No scripts, assets, or external services are required.
   - No gomtm production or development systems were changed.

## Boundaries

Do not run commands, call network services, modify files, or inspect secrets for this demo unless the user explicitly asks for a separate task that requires it.

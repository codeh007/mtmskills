---
name: mtm-image2
description: Use when a user wants GPT Image 2 / gpt-image-2 image generation, reference-image editing, inpainting, prompt engineering for professional images, or Codex app image workflows, especially with sub2api/OpenAI-compatible endpoints.
---

# mtm-image2

Use this skill to turn normal chat requests into professional `gpt-image-2` image generation or editing workflows. The output must come from `gpt-image-2` or a compatible image API; programmatically drawn placeholder images are not acceptable.

## First Decision

1. If the user wants an actual image now, verify an image API path exists. Prefer the current Codex/OpenAI-compatible config when available; otherwise use the setup guide.
2. If the user is in Codex desktop/app and cannot run scripts, act as a prompt director: produce a complete image brief and tell the Codex app agent exactly which bundled script/template to use when it has shell access.
3. If no API/tool path is available, do not pretend an image was generated. Save or return the final prompt and clearly state that execution still needs an image-capable runtime.

## Reference Map

- Fresh install, Windows, Codex app, and sub2api setup: `references/setup-and-environment.md`.
- Generation/editing workflow and mode selection: `references/workflow.md`.
- Prompt structure, templates, and quality rules: `references/prompting.md`.
- API boundaries, model routing, errors, and verification: `references/api-boundaries.md`.

Read only the files needed for the current task.

## Operating Loop

1. Classify the request as `generate`, `edit`, `inpaint`, `multi-reference edit`, or `prompt-only`.
2. Identify deliverable type: product photo, poster, UI mockup, character, diagram, infographic, social post, academic figure, map, storyboard, or other.
3. Capture required facts: subject, audience, style, exact text, aspect ratio/size, reference images, edit invariants, and quality/cost target.
4. Build a final prompt using `references/prompting.md`; ask at most one short clarification when missing facts would materially change the result.
5. Choose execution:
   - Windows/fresh Codex app host: `scripts/Invoke-MtmImage2.ps1`.
   - Developer shell with Python 3.10+: `scripts/mtm_image2.py`.
   - Host-native image tool: pass the final prompt and image references to that tool.
6. Before execution, confirm endpoint mode, model, size, quality, output path, and reference/mask files.
7. After execution, report saved image path(s), prompt path, model, and one concrete refinement option.

## Default Paths

Use the current workspace unless the user specifies a folder.

- Prompts: `mtm-image2-output/prompts/<slug>-<timestamp>.md`
- Images: `mtm-image2-output/images/<slug>-<timestamp>.<format>`
- Reports: `mtm-image2-output/reports/<slug>-<timestamp>.json`

Always preserve the final prompt. It is the reproducible source artifact.

## Model Rules

- Codex main model: use `gpt-5.5` or another text/coding model for reasoning and conversation.
- Image model: use `gpt-image-2` for actual image generation/editing.
- Do not configure `gpt-image-2` as the Codex agent's main chat model.
- With sub2api, default base URL is `https://sub2api.yuepa8.com`; scripts normalize it to `/v1`.

## Script Summary

- `scripts/Invoke-MtmImage2.ps1`: PowerShell 5.1+ script for Windows/macOS/Linux PowerShell. Uses only built-in PowerShell/.NET HTTP and multipart APIs.
- `scripts/mtm_image2.py`: optional Python helper using only the standard library. Good for Linux/macOS/WSL/developer shells.
- `templates/prompt-brief.md`: user-facing brief template for Codex desktop conversations.
- `templates/config.env.example`: non-secret environment template.

Never print API keys. Do not write secrets into the skill directory or repo.

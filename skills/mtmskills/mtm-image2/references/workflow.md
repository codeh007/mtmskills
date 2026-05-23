# Workflow

## Request Types

| Type | Trigger | Endpoint |
| --- | --- | --- |
| `generate` | Text prompt only | `/v1/images/generations` |
| `edit` | One or more reference images | `/v1/images/edits` |
| `inpaint` | Reference image plus mask | `/v1/images/edits` |
| `prompt-only` | No API/tool path available | No API call |

## Generation Checklist

Before calling the API, determine:

- Subject and scene.
- Intended use: poster, avatar, product photo, UI mockup, diagram, thumbnail, etc.
- Aspect ratio or exact size.
- Quality level: `low`, `medium`, `high`, or `auto`.
- Required visible text, exact spelling, and language.
- Negative constraints: avoid logos, watermarks, extra text, changed face, changed product shape, etc.
- Output path and prompt archive path.

## Editing Checklist

For edits, preserve what matters:

- Which image(s) are references.
- What must stay unchanged: identity, pose, product shape, composition, text, colors, background, lighting.
- What changes: object, background, style, camera angle, text, materials, local area.
- If using a mask, confirm it has alpha and matches the source dimensions.

## Size Guidance

Use exact API-supported sizes when possible.

| Use case | Size |
| --- | --- |
| Square social/product/avatar | `1024x1024` |
| Portrait poster/mobile cover | `1024x1536` |
| Landscape hero/product banner | `1536x1024` |
| 2K square final | `2048x2048` |
| 4K landscape | `3840x2160` |
| 4K portrait | `2160x3840` |

Use `high` for text-heavy images, product finals, UI mockups, diagrams, and brand assets. Use `low` for rough exploration.

## Codex App Flow For Non-Programmers

1. Convert the user's plain-language request into a structured image brief.
2. If references are needed, ask the user to attach images in Codex app or provide file paths.
3. Ask Codex to run `Invoke-MtmImage2.ps1` on Windows, or the Python helper on systems with Python.
4. After the command returns, tell the user where the file was saved.
5. For revisions, use the previous prompt and image path as the starting point; do not restart from a vague prompt.

## Failure Handling

- Missing API key: explain which credential is missing and where to place it. Do not ask the user to paste secrets into public issue threads.
- Unsupported endpoint: verify whether the gateway supports `/v1/images/generations` and `/v1/images/edits`.
- Model unavailable: list the requested model and suggest checking `/v1/models`.
- Refusal or moderation: surface the refusal reason at a high level and propose a compliant rewrite.
- Bad image output: preserve prompt/report, then revise specific prompt fields rather than changing everything.

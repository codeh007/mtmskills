# Setup And Environment

This document is intentionally separate from `SKILL.md` so the main skill stays small. Use it when the user needs installation, Windows, Codex desktop/app, or sub2api configuration help.

## Environment Types

| Environment | What to do |
| --- | --- |
| Codex CLI / developer shell | Use `scripts/mtm_image2.py` or `scripts/Invoke-MtmImage2.ps1` directly. |
| Codex desktop/app with shell access | Ask the agent to run the bundled PowerShell script on Windows, or Python/PowerShell on macOS/Linux. |
| Codex desktop/app without usable shell | Produce a complete prompt brief and tell the user the API/tool execution is still needed. |
| Fresh Windows machine | Prefer `Invoke-MtmImage2.ps1`; do not assume Python, Node.js, uv, npm, or Git are installed. |
| Host has native image tool | Use the host image tool with the final prompt and reference images. Still archive the prompt when possible. |

## Existing Codex Configuration

Codex user configuration normally lives in:

- Windows: `%USERPROFILE%\.codex\config.toml`
- macOS/Linux: `~/.codex/config.toml`

Credentials may live in:

- `%USERPROFILE%\.codex\auth.json`
- `~/.codex/auth.json`
- Process environment variables such as `OPENAI_API_KEY` or `SUB2API_API_KEY`

If a user already configured Codex to use an OpenAI-compatible provider, reuse that base URL and key. For the current gomtm/sub2api pattern:

```text
Base URL: https://sub2api.yuepa8.com
Chat model: gpt-5.5
Image model: gpt-image-2
Auth key location: usually ~/.codex/auth.json key OPENAI_API_KEY, or environment variable
```

Do not reveal key values. Confirm presence only.

## Fresh Windows Quick Start

PowerShell is available on new Windows installs. The script does not require Python or Node.js.

1. Install or open the latest Codex app.
2. Confirm API credentials exist in Codex settings or `%USERPROFILE%\.codex\auth.json`.
3. In a Codex task with workspace shell access, ask:

```text
Use the mtm-image2 skill. Generate an image with gpt-image-2 via my configured sub2api endpoint. If Windows has no Python or Node.js, use scripts/Invoke-MtmImage2.ps1.
```

4. If running manually in PowerShell:

```powershell
$env:OPENAI_API_KEY = "sk-..."
powershell -ExecutionPolicy Bypass -File .\scripts\Invoke-MtmImage2.ps1 `
  -Prompt "A premium studio product photo of a matte black smart ring on a white acrylic pedestal" `
  -BaseUrl "https://sub2api.yuepa8.com" `
  -Model "gpt-image-2" `
  -Size "1024x1024" `
  -Quality "high"
```

If execution policy blocks scripts, use `-ExecutionPolicy Bypass` for that one command. Do not change machine-wide policy unless the user explicitly asks.

## Codex Desktop User Prompt

For non-programmer users, give Codex app a goal-shaped request:

```text
Use mtm-image2 to create a professional image.
Subject: ...
Purpose: ...
Style: ...
Required text in the image: ...
Size/aspect ratio: ...
References attached: ...
Use gpt-image-2, not local drawing code. Save the final prompt and generated file path.
```

If the Codex app cannot access a shell or image API, the agent should return a final prompt brief rather than claiming image generation.

## API Base URL Rules

Scripts accept either root or `/v1` base URLs:

- `https://api.openai.com`
- `https://api.openai.com/v1`
- `https://sub2api.yuepa8.com`
- `https://sub2api.yuepa8.com/v1`

The script normalizes to one `/v1` prefix.

## Environment Variables

Preferred order:

1. Explicit command flags.
2. `OPENAI_API_KEY`.
3. `SUB2API_API_KEY`.
4. `~/.codex/auth.json` field `OPENAI_API_KEY`, if the script supports reading it.

Optional:

```text
OPENAI_BASE_URL=https://sub2api.yuepa8.com
OPENAI_IMAGE_MODEL=gpt-image-2
MTM_IMAGE2_OUTPUT_DIR=mtm-image2-output
```

Do not store secrets in `templates/config.env.example`; it is a shape-only file.

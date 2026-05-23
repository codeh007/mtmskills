# API Boundaries

## Core Boundary

`gpt-5.5` can understand text and image inputs in a Codex-style conversation. Actual image generation/editing must route to an image capability such as `gpt-image-2` through:

- `/v1/images/generations`
- `/v1/images/edits`
- A Responses API image generation tool, when the host supports it

Do not call local drawing libraries, HTML canvas, SVG renderers, matplotlib, PIL drawing, or screenshot tricks and present those as GPT Image 2 output.

## Endpoint Selection

| User request | Endpoint |
| --- | --- |
| "Generate/create/draw an image from this description" | `/v1/images/generations` |
| "Use this image as reference" | `/v1/images/edits` |
| "Change the background/object/style of this image" | `/v1/images/edits` |
| "Only change this part" with a mask | `/v1/images/edits` with mask |

## OpenAI-Compatible Gateway Expectations

An OpenAI-compatible gateway must support more than chat completions. For this skill, verify:

- `POST /v1/images/generations`
- `POST /v1/images/edits`
- multipart form upload for edits
- `model=gpt-image-2`
- base64 image response in `data[0].b64_json`, or an image URL if the script supports downloading it

If the gateway only supports `/v1/chat/completions` or `/v1/responses`, this skill may still write prompts but cannot guarantee actual `gpt-image-2` output.

## Common Errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| 401/403 | Missing or wrong key | Check env/auth location; do not print the key. |
| 404 on `/images/...` | Gateway lacks image endpoints or base URL is wrong | Try root base URL without duplicate `/v1`; check gateway docs. |
| "model not found" | `gpt-image-2` not enabled upstream | Query `/v1/models` or choose an enabled GPT Image model. |
| Multipart failure | Using JSON for edits | Use multipart form with `image[]`/`image` and optional `mask`. |
| No `b64_json` | Gateway returns URL only | Use script URL download support or inspect response JSON. |
| Bad text rendering | Model limitation or too much text | Shorten text, increase quality, or add final text in a design tool. |

## Verification Criteria

An image task is only complete when:

1. The final prompt is saved or shown.
2. The command/API call completed successfully.
3. The output image file path or host image artifact is reported.
4. The output is known to come from `gpt-image-2` or an explicitly compatible GPT Image model.

For prompt-only mode, say "prompt prepared" rather than "image generated".

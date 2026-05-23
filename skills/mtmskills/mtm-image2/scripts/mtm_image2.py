#!/usr/bin/env python3
"""Call a GPT Image 2 compatible API without third-party Python packages.

This helper intentionally uses only the Python standard library. It supports:
- text-to-image via /v1/images/generations
- reference-image edits and masks via /v1/images/edits

It never draws images locally; it only saves API-returned image bytes.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4


def read_codex_config() -> dict:
    path = Path.home() / ".codex" / "config.toml"
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib

        return tomllib.loads(text)
    except Exception:
        return parse_codex_config_fallback(text)


def parse_codex_config_fallback(text: str) -> dict:
    config: dict = {}
    current: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = [part.strip('"') for part in line.strip("[]").split(".")]
            node = config
            for part in current:
                node = node.setdefault(part, {})
            continue
        if "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        value = value.strip('"')
        node = config
        for part in current:
            node = node.setdefault(part, {})
        node[key] = value
    return config


def read_codex_base_url() -> str | None:
    config = read_codex_config()
    provider_name = config.get("model_provider")
    providers = config.get("model_providers", {})
    if provider_name and isinstance(providers, dict):
        provider = providers.get(provider_name)
        if isinstance(provider, dict) and provider.get("base_url"):
            return str(provider["base_url"])
    for provider in providers.values() if isinstance(providers, dict) else []:
        if isinstance(provider, dict) and provider.get("base_url"):
            return str(provider["base_url"])
    return None


def normalize_base_url(value: str | None) -> str:
    base = (
        value
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or read_codex_base_url()
        or "https://api.openai.com"
    ).rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def find_secret_value(data: object) -> str | None:
    if isinstance(data, dict):
        for name in ("OPENAI_API_KEY", "api_key", "apiKey"):
            value = data.get(name)
            if isinstance(value, str) and value:
                return value
        for value in data.values():
            found = find_secret_value(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_secret_value(value)
            if found:
                return found
    return None


def read_codex_key() -> str | None:
    path = Path.home() / ".codex" / "auth.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return find_secret_value(data)


def get_api_key(cli_key: str | None) -> str:
    key = cli_key or os.environ.get("OPENAI_API_KEY") or read_codex_key()
    if not key:
        raise SystemExit("Missing API key. Set OPENAI_API_KEY or configure ~/.codex/auth.json.")
    return key


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.lower()).strip("-")
    return (slug[:40].strip("-") or "image")


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if not args.prompt:
        raise SystemExit("Provide --prompt or --prompt-file.")
    return args.prompt


def save_prompt(prompt: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")


def request_json(url: str, key: str, payload: dict) -> dict:
    body = json.dumps({k: v for k, v in payload.items() if v is not None}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mtm-image2/1.0",
        },
        method="POST",
    )
    return read_response(req)


def build_generation_payload(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    n: int,
    output_format: str,
    output_compression: int | None,
    background: str | None,
    moderation: str,
    stream: bool,
    partial_images: int,
) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": n,
        "output_format": output_format,
        "output_compression": output_compression,
        "background": background,
        "moderation": moderation,
    }
    if stream:
        payload["stream"] = True
        payload["partial_images"] = partial_images
    return {k: v for k, v in payload.items() if v is not None}


def request_stream(url: str, key: str, payload: dict) -> list[dict]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "User-Agent": "mtm-image2/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            return list(parse_sse_events(resp))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API stream request failed ({exc.code}): {detail}") from exc


def parse_sse_events(lines) -> object:
    data_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
        line = line.rstrip("\r\n")
        if not line:
            if data_lines:
                data = "\n".join(data_lines)
                data_lines = []
                if data != "[DONE]":
                    yield json.loads(data)
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    if data_lines:
        data = "\n".join(data_lines)
        if data != "[DONE]":
            yield json.loads(data)


def multipart_body(fields: dict[str, str], files: list[tuple[str, Path]], mask: Path | None) -> tuple[bytes, str]:
    boundary = f"----mtm-image2-{uuid4().hex}"
    chunks: list[bytes] = []

    def add(value: bytes) -> None:
        chunks.append(value)

    for name, value in fields.items():
        add(f"--{boundary}\r\n".encode())
        add(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        add(str(value).encode())
        add(b"\r\n")

    for field_name, path in files:
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        add(f"--{boundary}\r\n".encode())
        add(f'Content-Disposition: form-data; name="{field_name}"; filename="{path.name}"\r\n'.encode())
        add(f"Content-Type: {ctype}\r\n\r\n".encode())
        add(path.read_bytes())
        add(b"\r\n")

    if mask is not None:
        ctype = mimetypes.guess_type(mask.name)[0] or "image/png"
        add(f"--{boundary}\r\n".encode())
        add(f'Content-Disposition: form-data; name="mask"; filename="{mask.name}"\r\n'.encode())
        add(f"Content-Type: {ctype}\r\n\r\n".encode())
        add(mask.read_bytes())
        add(b"\r\n")

    add(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), boundary


def request_multipart(url: str, key: str, fields: dict[str, str], image_paths: list[Path], mask: Path | None) -> dict:
    files: list[tuple[str, Path]] = []
    for image in image_paths:
        if not image.is_file():
            raise SystemExit(f"Image file not found: {image}")
        files.append(("image[]", image))
    if mask is not None and not mask.is_file():
        raise SystemExit(f"Mask file not found: {mask}")

    body, boundary = multipart_body(fields, files, mask)
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
            "User-Agent": "mtm-image2/1.0",
        },
        method="POST",
    )
    return read_response(req)


def read_response(req: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API request failed ({exc.code}): {detail}") from exc


def save_images(data: list[dict], output: Path) -> list[str]:
    if not data:
        raise SystemExit("API response did not include any image data.")
    output.parent.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for index, item in enumerate(data):
        target = output
        if len(data) > 1:
            target = output.with_name(f"{output.stem}-{index}{output.suffix}")
        if item.get("b64_json"):
            target.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            with urllib.request.urlopen(item["url"], timeout=300) as resp:
                target.write_bytes(resp.read())
        else:
            raise SystemExit(f"Response item {index} has neither b64_json nor url.")
        written.append(str(target))
    return written


def image_b64_from_event(event: dict) -> str | None:
    for key in ("b64_json", "partial_image_b64", "result"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    data = event.get("data")
    if isinstance(data, list) and data:
        return image_b64_from_event(data[0])
    if isinstance(data, dict):
        return image_b64_from_event(data)
    return None


def save_streamed_image_events(events: list[dict], output: Path) -> list[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    final_events = {
        "image_generation.completed",
        "image_generation.image",
        "response.image_generation_call.completed",
    }
    partial_events = {
        "image_generation.partial_image",
        "response.image_generation_call.partial_image",
    }

    for event in events:
        image_base64 = image_b64_from_event(event)
        if not image_base64:
            continue
        event_type = str(event.get("type", ""))
        if event_type in partial_events:
            index = event.get("partial_image_index", len(written))
            target = output.with_name(f"{output.stem}-partial-{index}{output.suffix}")
        elif event_type in final_events or not any(path.endswith(output.name) for path in written):
            target = output
        else:
            target = output.with_name(f"{output.stem}-{len(written)}{output.suffix}")
        target.write_bytes(base64.b64decode(image_base64))
        written.append(str(target))
    if not written:
        raise SystemExit("Stream completed without image data events.")
    if not output.exists():
        source = Path(written[-1])
        output.write_bytes(source.read_bytes())
        written.append(str(output))
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or edit images via gpt-image-2 compatible API.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--mask")
    parser.add_argument("--output")
    parser.add_argument("--prompt-output")
    parser.add_argument("--report-output")
    parser.add_argument("--output-dir", default=os.environ.get("MTM_IMAGE2_OUTPUT_DIR", "mtm-image2-output"))
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="high", choices=["auto", "low", "medium", "high"])
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--format", default="png", choices=["png", "jpeg", "webp"])
    parser.add_argument("--compression", type=int)
    parser.add_argument("--background", choices=["auto", "opaque"])
    parser.add_argument("--moderation", default="auto", choices=["auto", "low"])
    parser.add_argument("--stream", action="store_true", help="Stream Image API events and save partial images.")
    parser.add_argument("--partial-images", type=int, default=2, choices=[0, 1, 2, 3])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prompt = read_prompt(args)
    key = get_api_key(args.api_key)
    base = normalize_base_url(args.base_url)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    slug = slugify(prompt)
    output_dir = Path(args.output_dir)
    prompt_path = Path(args.prompt_output) if args.prompt_output else output_dir / "prompts" / f"{slug}-{stamp}.md"
    image_path = Path(args.output) if args.output else output_dir / "images" / f"{slug}-{stamp}.{args.format}"
    report_path = Path(args.report_output) if args.report_output else output_dir / "reports" / f"{slug}-{stamp}.json"
    save_prompt(prompt, prompt_path)

    if args.image:
        endpoint = f"{base}/images/edits"
        fields = {
            "model": args.model,
            "prompt": prompt,
            "size": args.size,
            "quality": args.quality,
            "n": str(args.n),
            "output_format": args.format,
        }
        if args.compression is not None:
            fields["output_compression"] = str(args.compression)
        if args.background:
            fields["background"] = args.background
        response = request_multipart(endpoint, key, fields, [Path(p) for p in args.image], Path(args.mask) if args.mask else None)
        mode = "edit"
    else:
        endpoint = f"{base}/images/generations"
        payload = build_generation_payload(
            model=args.model,
            prompt=prompt,
            size=args.size,
            quality=args.quality,
            n=args.n,
            output_format=args.format,
            output_compression=args.compression,
            background=args.background,
            moderation=args.moderation,
            stream=args.stream,
            partial_images=args.partial_images,
        )
        mode = "generate"

    if args.stream and not args.image:
        events = request_stream(endpoint, key, payload)
        written = save_streamed_image_events(events, image_path)
        response_summary = {
            "event_count": len(events),
            "event_types": sorted({str(event.get("type", "")) for event in events if event.get("type")}),
            "partial_images": args.partial_images,
        }
    else:
        response = request_json(endpoint, key, payload) if not args.image else response
        written = save_images(response.get("data", []), image_path)
        response_summary = {"data_count": len(response.get("data", []))}

    report = {
        "mode": mode,
        "endpoint": endpoint,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "stream": args.stream and not args.image,
        "prompt": str(prompt_path),
        "images": written,
        "report": str(report_path),
        "response": response_summary,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def normalize_base_url(value: str | None) -> str:
    base = (value or os.environ.get("OPENAI_BASE_URL") or "https://sub2api.yuepa8.com").rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def read_codex_key() -> str | None:
    path = Path.home() / ".codex" / "auth.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for name in ("OPENAI_API_KEY", "SUB2API_API_KEY", "api_key", "apiKey"):
        value = data.get(name)
        if value:
            return str(value)
    value = None
    return str(value) if value else None


def get_api_key(cli_key: str | None) -> str:
    key = cli_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("SUB2API_API_KEY") or read_codex_key()
    if not key:
        raise SystemExit("Missing API key. Set OPENAI_API_KEY or SUB2API_API_KEY, or configure ~/.codex/auth.json.")
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
        payload = {
            "model": args.model,
            "prompt": prompt,
            "size": args.size,
            "quality": args.quality,
            "n": args.n,
            "output_format": args.format,
            "output_compression": args.compression,
            "background": args.background,
            "moderation": args.moderation,
        }
        response = request_json(endpoint, key, payload)
        mode = "generate"

    written = save_images(response.get("data", []), image_path)
    report = {
        "mode": mode,
        "endpoint": endpoint,
        "model": args.model,
        "prompt": str(prompt_path),
        "images": written,
        "report": str(report_path),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate images with a GPT Image compatible streaming API.

This helper intentionally uses only the Python standard library. It calls
`/v1/images/generations` with `stream=true`, saves API-returned image bytes, and
never draws images locally.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NamedTuple


class OutputPaths(NamedTuple):
    image: Path
    prompt: Path
    report: Path


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def read_codex_config() -> dict:
    path = codex_home() / "config.toml"
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


def effective_codex_config(profile_name: str | None = None) -> dict:
    config = read_codex_config()
    active_profile = profile_name or config.get("profile")
    profiles = config.get("profiles", {})
    if active_profile and isinstance(profiles, dict):
        profile = profiles.get(str(active_profile))
        if isinstance(profile, dict):
            merged = dict(config)
            merged.update(profile)
            return merged
    return config


def get_active_provider(config: dict) -> dict:
    providers = config.get("model_providers", {}) if isinstance(config.get("model_providers", {}), dict) else {}
    provider_name = config.get("model_provider")
    if provider_name:
        provider = providers.get(provider_name)
        if isinstance(provider, dict):
            return provider
    if provider_name == "openai" or not provider_name:
        base_url = config.get("openai_base_url")
        if base_url:
            return {"base_url": base_url}
    for provider in providers.values():
        if isinstance(provider, dict) and provider.get("base_url"):
            return provider
    return {}


def read_codex_base_url(profile_name: str | None = None) -> str | None:
    provider = get_active_provider(effective_codex_config(profile_name))
    value = provider.get("base_url")
    return str(value) if value else None


def normalize_base_url(value: str | None, codex_profile: str | None = None) -> str:
    base = (
        value
        or os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or read_codex_base_url(codex_profile)
        or "https://api.openai.com"
    ).rstrip("/")
    return base if base.endswith("/v1") else f"{base}/v1"


def read_provider_env_key(codex_profile: str | None = None) -> tuple[str | None, str | None]:
    provider = get_active_provider(effective_codex_config(codex_profile))
    env_key = provider.get("env_key")
    if isinstance(env_key, str) and env_key:
        return os.environ.get(env_key), env_key
    token = provider.get("experimental_bearer_token")
    return (str(token), "experimental_bearer_token") if token else (None, None)


def get_api_key(cli_key: str | None, codex_profile: str | None = None) -> str:
    provider_key, provider_source = read_provider_env_key(codex_profile)
    key = cli_key or os.environ.get("OPENAI_API_KEY") or provider_key
    if not key:
        names = ["OPENAI_API_KEY"] + (
            [provider_source] if provider_source and provider_source != "experimental_bearer_token" else []
        )
        raise SystemExit(f"Missing API key. Set one of: {', '.join(names)}.")
    return key


def provider_headers(codex_profile: str | None = None) -> dict[str, str]:
    provider = get_active_provider(effective_codex_config(codex_profile))
    headers: dict[str, str] = {}
    static_headers = provider.get("http_headers")
    if isinstance(static_headers, dict):
        headers.update({str(k): str(v) for k, v in static_headers.items()})
    env_headers = provider.get("env_http_headers")
    if isinstance(env_headers, dict):
        headers.update(
            {str(header): value for header, env_name in env_headers.items() if (value := os.environ.get(str(env_name)))}
        )
    return headers


def provider_query_params(codex_profile: str | None = None) -> dict[str, str]:
    provider = get_active_provider(effective_codex_config(codex_profile))
    params = provider.get("query_params")
    if not isinstance(params, dict):
        return {}
    return {str(key): str(value) for key, value in params.items()}


def append_query_params(url: str, params: dict[str, str]) -> str:
    if not params:
        return url
    parts = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    query.extend(params.items())
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8")
    if not args.prompt:
        raise SystemExit("Provide --prompt or --prompt-file.")
    return args.prompt


def resolve_output_paths(args: argparse.Namespace) -> OutputPaths:
    if not args.output:
        raise SystemExit("Provide --output for the final image path.")
    image = Path(args.output)
    return OutputPaths(
        image=image,
        prompt=Path(args.prompt_output) if args.prompt_output else image.with_suffix(".prompt.md"),
        report=Path(args.report_output) if args.report_output else image.with_suffix(".report.json"),
    )


def save_prompt(prompt: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")


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
        "stream": True,
        "partial_images": partial_images,
    }
    return {k: v for k, v in payload.items() if v is not None}


def request_stream(url: str, key: str, payload: dict, extra_headers: dict[str, str] | None = None) -> list[dict]:
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "mtm-image-gen/1.0",
    }
    if extra_headers:
        headers.update(extra_headers)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers, method="POST"), timeout=900) as resp:
            return list(parse_sse_events(resp))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API stream request failed ({exc.code}): {redact_secret_fragments(detail)}") from exc


def parse_sse_events(lines) -> object:
    data_lines: list[str] = []

    def flush() -> dict | None:
        if not data_lines:
            return None
        data = "\n".join(data_lines)
        data_lines.clear()
        return None if data == "[DONE]" else json.loads(data)

    for raw_line in lines:
        line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
        line = line.rstrip("\r\n")
        if not line:
            event = flush()
            if event is not None:
                yield event
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
    event = flush()
    if event is not None:
        yield event


def redact_secret_fragments(text: str) -> str:
    text = re.sub(r"sk-[A-Za-z0-9_*.-]{12,}", "sk-***REDACTED***", text)
    return re.sub(r"(Bearer\s+)[A-Za-z0-9._~+/=-]{12,}", r"\1***REDACTED***", text, flags=re.IGNORECASE)


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

    for event in events:
        image_base64 = image_b64_from_event(event)
        if not image_base64:
            continue
        event_type = str(event.get("type", ""))
        if "partial_image" in event_type:
            index = event.get("partial_image_index", len(written))
            target = output.with_name(f"{output.stem}-partial-{index}{output.suffix}")
        elif event_type.endswith(("completed", "image")) or not any(path.endswith(output.name) for path in written):
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate images via gpt-image-2 compatible streaming API.")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--output", required=True, help="Final image path.")
    parser.add_argument("--prompt-output", help="Prompt archive path. Defaults beside --output.")
    parser.add_argument("--report-output", help="JSON report path. Defaults beside --output.")
    parser.add_argument("--base-url")
    parser.add_argument("--api-key")
    parser.add_argument("--codex-profile", help="Read provider settings from a named ~/.codex/config.toml profile.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2"))
    parser.add_argument("--size", default="1024x1024")
    parser.add_argument("--quality", default="high", choices=["auto", "low", "medium", "high"])
    parser.add_argument("--n", type=int, default=1)
    parser.add_argument("--format", default="png", choices=["png", "jpeg", "webp"])
    parser.add_argument("--compression", type=int)
    parser.add_argument("--background", choices=["auto", "opaque"])
    parser.add_argument("--moderation", default="auto", choices=["auto", "low"])
    parser.add_argument("--partial-images", type=int, default=2, choices=[0, 1, 2, 3])
    return parser


def parse_args() -> argparse.Namespace:
    return build_parser().parse_args()


def main() -> int:
    args = parse_args()
    prompt = read_prompt(args)
    paths = resolve_output_paths(args)
    key = get_api_key(args.api_key, args.codex_profile)
    base = normalize_base_url(args.base_url, args.codex_profile)
    endpoint = append_query_params(f"{base}/images/generations", provider_query_params(args.codex_profile))
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
        partial_images=args.partial_images,
    )

    save_prompt(prompt, paths.prompt)
    events = request_stream(endpoint, key, payload, provider_headers(args.codex_profile))
    written = save_streamed_image_events(events, paths.image)
    report = {
        "endpoint": endpoint,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "stream": True,
        "partial_images": args.partial_images,
        "prompt": str(paths.prompt),
        "images": written,
        "report": str(paths.report),
        "response": {
            "event_count": len(events),
            "event_types": sorted({str(event.get("type", "")) for event in events if event.get("type")}),
        },
    }
    paths.report.parent.mkdir(parents=True, exist_ok=True)
    paths.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3

from __future__ import annotations

import base64
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mtm_image2.py"
SPEC = importlib.util.spec_from_file_location("mtm_image2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mtm_image2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mtm_image2)


class StreamingImagesTest(unittest.TestCase):
    def test_normalize_base_url_reads_codex_home_profile_provider(self) -> None:
        config = """
profile = "relay"

[profiles.relay]
model_provider = "sub2api"

[model_providers.sub2api]
base_url = "https://relay.example.com"
env_key = "RELAY_API_KEY"
"""
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text(config, encoding="utf-8")

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}, clear=True):
                self.assertEqual(mtm_image2.normalize_base_url(None), "https://relay.example.com/v1")

    def test_get_api_key_uses_openai_api_key_before_provider_env_key(self) -> None:
        config = """
model_provider = "relay"

[model_providers.relay]
base_url = "https://relay.example.com/v1"
env_key = "RELAY_API_KEY"
"""
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text(config, encoding="utf-8")

            env = {
                "CODEX_HOME": str(codex_home),
                "RELAY_API_KEY": "relay-key",
                "OPENAI_API_KEY": "openai-key",
            }
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(mtm_image2.get_api_key(None), "openai-key")

    def test_get_api_key_falls_back_to_provider_env_key(self) -> None:
        config = """
model_provider = "relay"

[model_providers.relay]
base_url = "https://relay.example.com/v1"
env_key = "RELAY_API_KEY"
"""
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text(config, encoding="utf-8")

            env = {
                "CODEX_HOME": str(codex_home),
                "RELAY_API_KEY": "relay-key",
            }
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(mtm_image2.get_api_key(None), "relay-key")

    def test_provider_headers_and_query_params_resolve_from_codex_config(self) -> None:
        config = """
model_provider = "relay"

[model_providers.relay]
base_url = "https://relay.example.com/v1"

[model_providers.relay.http_headers]
X-Static = "static-value"

[model_providers.relay.env_http_headers]
X-Env = "RELAY_HEADER"

[model_providers.relay.query_params]
api-version = "2026-05-23"
"""
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / ".codex"
            codex_home.mkdir()
            (codex_home / "config.toml").write_text(config, encoding="utf-8")

            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home), "RELAY_HEADER": "env-value"}, clear=True):
                self.assertEqual(
                    mtm_image2.provider_headers(),
                    {"X-Static": "static-value", "X-Env": "env-value"},
                )
                self.assertEqual(mtm_image2.provider_query_params(), {"api-version": "2026-05-23"})
                self.assertEqual(
                    mtm_image2.append_query_params(
                        "https://relay.example.com/v1/images/generations",
                        mtm_image2.provider_query_params(),
                    ),
                    "https://relay.example.com/v1/images/generations?api-version=2026-05-23",
                )

    def test_redact_secret_fragments_masks_api_key_like_values(self) -> None:
        message = (
            "Incorrect API key provided: "
            "sk-1234567890abcdef*******************************1234. "
            "Authorization: Bearer abcdef1234567890"
        )

        redacted = mtm_image2.redact_secret_fragments(message)

        self.assertNotIn("1234567890abcdef", redacted)
        self.assertNotIn("abcdef1234567890", redacted)
        self.assertIn("sk-***REDACTED***", redacted)
        self.assertIn("Bearer ***REDACTED***", redacted)

    def test_build_generation_payload_includes_streaming_options(self) -> None:
        payload = mtm_image2.build_generation_payload(
            model="gpt-image-2",
            prompt="test image",
            size="2048x2048",
            quality="high",
            n=1,
            output_format="jpeg",
            output_compression=80,
            background=None,
            moderation="auto",
            stream=True,
            partial_images=2,
        )

        self.assertEqual(payload["stream"], True)
        self.assertEqual(payload["partial_images"], 2)
        self.assertEqual(payload["size"], "2048x2048")
        self.assertEqual(payload["output_format"], "jpeg")
        self.assertEqual(payload["output_compression"], 80)
        self.assertNotIn("background", payload)

    def test_parse_sse_events_ignores_done_and_comments(self) -> None:
        raw = b""": keepalive\n\nevent: image_generation.partial_image\ndata: {\"type\":\"image_generation.partial_image\",\"partial_image_index\":0}\n\ndata: [DONE]\n\n"""

        events = list(mtm_image2.parse_sse_events(raw.splitlines()))

        self.assertEqual(events, [{"type": "image_generation.partial_image", "partial_image_index": 0}])

    def test_save_streamed_image_events_writes_partial_and_final_images(self) -> None:
        image = base64.b64encode(b"fake-png").decode("ascii")
        events = [
            {"type": "image_generation.partial_image", "partial_image_index": 0, "b64_json": image},
            {"type": "image_generation.completed", "b64_json": image},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "images" / "demo.png"
            written = mtm_image2.save_streamed_image_events(events, output)

            self.assertEqual(len(written), 2)
            self.assertTrue(written[0].endswith("demo-partial-0.png"))
            self.assertTrue(written[1].endswith("demo.png"))
            self.assertEqual(Path(written[0]).read_bytes(), b"fake-png")
            self.assertEqual(Path(written[1]).read_bytes(), b"fake-png")

    def test_save_streamed_image_events_promotes_last_partial_to_final_output(self) -> None:
        first = base64.b64encode(b"partial").decode("ascii")
        last = base64.b64encode(b"final").decode("ascii")
        events = [
            {"type": "image_generation.partial_image", "partial_image_index": 0, "b64_json": first},
            {"type": "image_generation.partial_image", "partial_image_index": 1, "b64_json": last},
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "images" / "demo.png"
            written = mtm_image2.save_streamed_image_events(events, output)

            self.assertTrue(str(output) in written)
            self.assertEqual(output.read_bytes(), b"final")


if __name__ == "__main__":
    unittest.main()

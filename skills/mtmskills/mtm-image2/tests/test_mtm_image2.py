#!/usr/bin/env python3

from __future__ import annotations

import base64
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mtm_image2.py"
SPEC = importlib.util.spec_from_file_location("mtm_image2", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
mtm_image2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mtm_image2)


class StreamingImagesTest(unittest.TestCase):
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

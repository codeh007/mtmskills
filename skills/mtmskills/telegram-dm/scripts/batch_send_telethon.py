#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import random
import sys
from pathlib import Path
from urllib.parse import urlparse


DEPENDENCY_HINT = (
    "Telethon is required. Install it with: "
    "/usr/bin/python3 -m pip install --user -r "
    ".agent/skills/telegram-dm/scripts/requirements.txt"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch-send Telegram DMs using a saved Telethon session.",
    )
    parser.add_argument("--api-id", type=int, help="Telegram api_id")
    parser.add_argument("--api-hash", help="Telegram api_hash")
    parser.add_argument(
        "--session-dir",
        default="~/.telegram-dm/sessions",
        help="Directory used to store Telethon session files",
    )
    parser.add_argument(
        "--session-name",
        default="default",
        help="Logical session name without file suffix",
    )
    parser.add_argument(
        "--string-session-file",
        help="Optional file containing either a raw string session or JSON with a string_session field",
    )
    parser.add_argument(
        "--targets-file", required=True, help="Text file with one target per line"
    )
    parser.add_argument("--message", help="Message text to send")
    parser.add_argument(
        "--message-file", help="Path to a text file containing the message"
    )
    parser.add_argument(
        "--batch-size", type=int, default=20, help="Number of targets per batch"
    )
    parser.add_argument(
        "--batch-delay", type=int, default=300, help="Delay between batches in seconds"
    )
    parser.add_argument(
        "--min-delay", type=int, default=5, help="Minimum delay between messages"
    )
    parser.add_argument(
        "--max-delay", type=int, default=12, help="Maximum delay between messages"
    )
    parser.add_argument(
        "--max-flood-wait",
        type=int,
        default=600,
        help="Abort if Telegram asks to wait longer than this many seconds",
    )
    parser.add_argument("--report-json-out", help="Optional JSON report output path")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve targets without sending messages",
    )
    return parser


def load_settings(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> argparse.Namespace:
    if args.api_id is None:
        api_id = os.environ.get("TG_API_ID", "").strip()
        args.api_id = int(api_id) if api_id else None
    if not args.api_hash:
        args.api_hash = os.environ.get("TG_API_HASH", "").strip() or None

    missing: list[str] = []
    if args.api_id is None:
        missing.append("--api-id or TG_API_ID")
    if not args.api_hash:
        missing.append("--api-hash or TG_API_HASH")
    if missing:
        parser.error("missing required settings: " + ", ".join(missing))

    if bool(args.message) == bool(args.message_file):
        parser.error("use exactly one of --message or --message-file")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    if args.min_delay < 0 or args.max_delay < 0:
        parser.error("message delays must be >= 0")
    if args.min_delay > args.max_delay:
        parser.error("--min-delay cannot be greater than --max-delay")
    if args.batch_delay < 0:
        parser.error("--batch-delay must be >= 0")
    return args


def import_telethon():
    try:
        telegram_module = importlib.import_module("telethon")
        errors_module = importlib.import_module("telethon.errors")
        sessions_module = importlib.import_module("telethon.sessions")
    except ImportError as exc:
        raise SystemExit(DEPENDENCY_HINT) from exc
    TelegramClient = telegram_module.TelegramClient
    FloodWaitError = errors_module.FloodWaitError
    PeerFloodError = errors_module.PeerFloodError
    RPCError = errors_module.RPCError
    StringSession = sessions_module.StringSession
    return TelegramClient, FloodWaitError, PeerFloodError, RPCError, StringSession


def load_message(args: argparse.Namespace) -> str:
    if args.message is not None:
        message = args.message
    else:
        message = Path(args.message_file).expanduser().read_text(encoding="utf-8")
    message = message.strip()
    if not message:
        raise ValueError("message cannot be empty")
    return message


def load_targets(path_value: str) -> list[str]:
    targets: list[str] = []
    for raw_line in (
        Path(path_value).expanduser().read_text(encoding="utf-8").splitlines()
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        targets.append(normalize_target(line))
    if not targets:
        raise ValueError("targets file does not contain any usable targets")
    return targets


def normalize_target(value: str) -> str:
    if value.startswith("https://") or value.startswith("http://"):
        parsed = urlparse(value)
        value = parsed.path.strip("/")
    if value.startswith("t.me/"):
        value = value.split("/", 1)[1]
    value = value.lstrip("@")
    if not value:
        raise ValueError("target entry cannot be empty after normalization")
    return value


def load_string_session(path_value: str) -> str:
    raw = Path(path_value).expanduser().read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("string session file is empty")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict) and payload.get("string_session"):
        return str(payload["string_session"]).strip()
    raise ValueError("string session file must be raw text or JSON with string_session")


async def create_client(args: argparse.Namespace):
    TelegramClient, FloodWaitError, PeerFloodError, RPCError, StringSession = (
        import_telethon()
    )

    if args.string_session_file:
        session_string = load_string_session(args.string_session_file)
        client = TelegramClient(
            StringSession(session_string), args.api_id, args.api_hash
        )
    else:
        session_root = Path(args.session_dir).expanduser() / args.session_name
        client = TelegramClient(str(session_root), args.api_id, args.api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        await client.disconnect()
        raise SystemExit("Session is not authorized. Run login_telethon.py first.")
    return client, FloodWaitError, PeerFloodError, RPCError


async def process(args: argparse.Namespace) -> int:
    message = load_message(args)
    targets = load_targets(args.targets_file)
    client, FloodWaitError, PeerFloodError, RPCError = await create_client(args)

    report = {
        "mode": "dry-run" if args.dry_run else "send",
        "total_targets": len(targets),
        "success": 0,
        "failed": 0,
        "results": [],
    }
    stop_reason = None

    try:
        for index, target in enumerate(targets, start=1):
            batch_index = (index - 1) % args.batch_size
            batch_number = (index - 1) // args.batch_size + 1

            if batch_index == 0 and index > 1 and not args.dry_run:
                await asyncio.sleep(args.batch_delay)

            try:
                entity = await client.get_entity(target)
                resolved = getattr(entity, "username", None) or str(
                    getattr(entity, "id", target)
                )

                if args.dry_run:
                    report["success"] += 1
                    report["results"].append(
                        {
                            "target": target,
                            "status": "validated",
                            "resolved_as": resolved,
                            "batch": batch_number,
                        }
                    )
                else:
                    sent = await client.send_message(entity, message)
                    report["success"] += 1
                    report["results"].append(
                        {
                            "target": target,
                            "status": "sent",
                            "resolved_as": resolved,
                            "message_id": sent.id,
                            "batch": batch_number,
                        }
                    )
            except FloodWaitError as exc:
                report["failed"] += 1
                report["results"].append(
                    {
                        "target": target,
                        "status": "flood-wait",
                        "detail": f"wait {exc.seconds} seconds",
                        "batch": batch_number,
                    }
                )
                if exc.seconds > args.max_flood_wait:
                    stop_reason = f"Flood wait too long: {exc.seconds}s"
                    break
                if not args.dry_run:
                    await asyncio.sleep(exc.seconds + 3)
            except PeerFloodError:
                report["failed"] += 1
                report["results"].append(
                    {
                        "target": target,
                        "status": "peer-flood",
                        "detail": "Telegram rate-limited the account",
                        "batch": batch_number,
                    }
                )
                stop_reason = "PeerFloodError"
                break
            except RPCError as exc:
                report["failed"] += 1
                report["results"].append(
                    {
                        "target": target,
                        "status": "rpc-error",
                        "detail": str(exc),
                        "batch": batch_number,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                report["failed"] += 1
                report["results"].append(
                    {
                        "target": target,
                        "status": "error",
                        "detail": str(exc),
                        "batch": batch_number,
                    }
                )

            if not args.dry_run and index < len(targets):
                await asyncio.sleep(random.randint(args.min_delay, args.max_delay))
    finally:
        await client.disconnect()

    if stop_reason:
        report["stop_reason"] = stop_reason

    if args.report_json_out:
        report_path = Path(args.report_json_out).expanduser()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["failed"] == 0 else 1


def main() -> int:
    parser = build_parser()
    args = load_settings(parser.parse_args(), parser)
    try:
        return asyncio.run(process(args))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

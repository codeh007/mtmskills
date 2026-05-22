#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import getpass
import importlib
import json
import os
import sys
from pathlib import Path


DEPENDENCY_HINT = (
    "Telethon is required. Install it with: "
    "/usr/bin/python3 -m pip install --user -r "
    ".agent/skills/telegram-dm/scripts/requirements.txt"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive Telegram login using Telethon.",
    )
    parser.add_argument("--api-id", type=int, help="Telegram api_id")
    parser.add_argument("--api-hash", help="Telegram api_hash")
    parser.add_argument("--phone", help="Phone number in international format")
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
        "--string-session-out",
        help="Optional JSON file used to store an exported string session",
    )
    parser.add_argument(
        "--max-code-attempts",
        type=int,
        default=3,
        help="Maximum number of login code attempts",
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
    if not args.phone:
        args.phone = os.environ.get("TG_PHONE", "").strip() or None

    missing: list[str] = []
    if args.api_id is None:
        missing.append("--api-id or TG_API_ID")
    if not args.api_hash:
        missing.append("--api-hash or TG_API_HASH")
    if not args.phone:
        missing.append("--phone or TG_PHONE")
    if missing:
        parser.error("missing required settings: " + ", ".join(missing))
    if args.max_code_attempts < 1:
        parser.error("--max-code-attempts must be >= 1")
    return args


def import_telethon():
    try:
        telegram_module = importlib.import_module("telethon")
        errors_module = importlib.import_module("telethon.errors")
        sessions_module = importlib.import_module("telethon.sessions")
    except ImportError as exc:
        raise SystemExit(DEPENDENCY_HINT) from exc
    TelegramClient = telegram_module.TelegramClient
    PhoneCodeInvalidError = errors_module.PhoneCodeInvalidError
    SessionPasswordNeededError = errors_module.SessionPasswordNeededError
    StringSession = sessions_module.StringSession
    return (
        TelegramClient,
        PhoneCodeInvalidError,
        SessionPasswordNeededError,
        StringSession,
    )


async def login(args: argparse.Namespace) -> int:
    TelegramClient, PhoneCodeInvalidError, SessionPasswordNeededError, StringSession = (
        import_telethon()
    )

    session_dir = Path(args.session_dir).expanduser()
    session_dir.mkdir(parents=True, exist_ok=True)
    session_root = session_dir / args.session_name

    client = TelegramClient(str(session_root), args.api_id, args.api_hash)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            sent_code = await client.send_code_request(args.phone)
            authenticated = False
            needs_password = False

            for attempt in range(1, args.max_code_attempts + 1):
                code = input(
                    f"Telegram login code (attempt {attempt}/{args.max_code_attempts}): "
                ).strip()
                try:
                    await client.sign_in(
                        phone=args.phone,
                        code=code,
                        phone_code_hash=sent_code.phone_code_hash,
                    )
                    authenticated = True
                    break
                except SessionPasswordNeededError:
                    needs_password = True
                    break
                except PhoneCodeInvalidError:
                    if attempt == args.max_code_attempts:
                        raise
                    print("Invalid code, please try again.", file=sys.stderr)

            if needs_password:
                password = getpass.getpass("Telegram 2FA password: ")
                await client.sign_in(password=password)
            elif not authenticated:
                raise SystemExit("Login was not completed.")

        me = await client.get_me()
        result = {
            "ok": True,
            "session_file": f"{session_root}.session",
            "user": {
                "id": me.id,
                "username": me.username,
                "phone": me.phone,
                "display_name": " ".join(
                    part for part in [me.first_name, me.last_name] if part
                ),
            },
        }

        if args.string_session_out:
            string_session_path = Path(args.string_session_out).expanduser()
            string_session_path.parent.mkdir(parents=True, exist_ok=True)
            exported = {
                **result,
                "string_session": StringSession.save(client.session),
            }
            string_session_path.write_text(
                json.dumps(exported, ensure_ascii=True, indent=2) + "\n",
                encoding="utf-8",
            )
            result["string_session_file"] = str(string_session_path)

        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    parser = build_parser()
    args = load_settings(parser.parse_args(), parser)
    return asyncio.run(login(args))


if __name__ == "__main__":
    raise SystemExit(main())

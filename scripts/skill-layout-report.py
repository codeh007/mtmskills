#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^name:\s*([^\n]+)", re.M)
SKIP_PARTS = {"references", "backup", "backups"}


def parse_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding="utf-8", errors="replace")[:4000]
    match = NAME_RE.search(text)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def build_rows(root: Path, namespace: str, allow_pre_namespace: bool) -> tuple[list[dict], list[str]]:
    skills_dir = root / "skills"
    rows: list[dict] = []
    errors: list[str] = []
    if not skills_dir.exists():
        return rows, [f"skills directory not found: {skills_dir}"]

    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        rel_dir = skill_md.parent.relative_to(skills_dir)
        parts = rel_dir.parts
        name = parse_name(skill_md)
        flags: list[str] = []
        non_installable = any(part in SKIP_PARTS for part in parts)
        if non_installable:
            flags.append("non-installable-location")
        if not name:
            flags.append("missing-name")
            errors.append(f"missing name: {rel_dir}")
        elif skill_md.parent.name != name and not non_installable:
            flags.append("basename-name-mismatch")
            errors.append(f"basename/name mismatch: {rel_dir} != {name}")
        if not allow_pre_namespace and (not parts or parts[0] != namespace):
            flags.append(f"outside-{namespace}-namespace")
            errors.append(f"outside namespace: {rel_dir}")
        rows.append({"rel": str(rel_dir), "name": name, "flags": flags})
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Report and validate local skill layout")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--namespace", default="mtmskills")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--allow-pre-namespace", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    rows, errors = build_rows(root, args.namespace, args.allow_pre_namespace)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(f"# {args.namespace} skill layout")
        for row in rows:
            print(f"- `{row['rel']}` name=`{row['name']}` flags={','.join(row['flags']) or 'ok'}")
    if args.strict and errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

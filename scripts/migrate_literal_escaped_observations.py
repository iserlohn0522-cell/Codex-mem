#!/usr/bin/env python3
"""Dry-run or migrate literal-escaped JSON objects in observations.jsonl."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from memory_common import atomic_write_text, backup_file, sha256_file, utc_now_iso


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--apply", action="store_true", help="Apply the reviewed migration.")
    parser.add_argument(
        "--expected-before-sha256",
        help="Required with --apply; prevents applying to a changed source.",
    )
    args = parser.parse_args()
    if args.apply and not args.expected_before_sha256:
        parser.error("--apply requires --expected-before-sha256")
    return args


def decode_literal_escaped_object(raw_line: str) -> dict[str, Any] | None:
    if not raw_line.startswith(r"{\""):
        return None
    try:
        decoded_text = json.loads(f'"{raw_line}"')
        parsed = json.loads(decoded_text)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def normalize_candidate(record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    normalized = dict(record)
    supersedes = normalized.get("supersedes")
    changed = False
    if supersedes in (None, ""):
        normalized["supersedes"] = []
        changed = supersedes != []
    elif isinstance(supersedes, str):
        normalized["supersedes"] = [supersedes]
        changed = True
    return normalized, changed


def render_migration(original: str) -> tuple[str, list[dict[str, Any]]]:
    lines = original.splitlines()
    converted: list[dict[str, Any]] = []
    for index, raw_line in enumerate(lines):
        parsed = decode_literal_escaped_object(raw_line)
        if parsed is None:
            continue
        normalized, supersedes_normalized = normalize_candidate(parsed)
        lines[index] = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
        converted.append(
            {
                "line": index + 1,
                "id": str(normalized.get("id", "")),
                "fields": sorted(str(key) for key in normalized),
                "supersedes_normalized": supersedes_normalized,
            }
        )
    trailing_newline = "\n" if original.endswith(("\n", "\r")) else ""
    return "\n".join(lines) + trailing_newline, converted


def validate_rendered(text: str) -> tuple[int, list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc}")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"line {line_number}: JSONL record is not an object")
            continue
        record_id = str(parsed.get("id", "")).strip()
        if record_id:
            if record_id in seen_ids:
                duplicate_ids.add(record_id)
            seen_ids.add(record_id)
        records.append(parsed)
    errors.extend(f"duplicate id after migration: {record_id}" for record_id in sorted(duplicate_ids))
    return len(records), records, errors


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def migration_plan(path: Path) -> tuple[str, dict[str, Any]]:
    original = path.read_text(encoding="utf-8-sig")
    rendered, converted = render_migration(original)
    valid_records, _records, errors = validate_rendered(rendered)
    plan = {
        "path": str(path),
        "before_sha256": sha256_file(path),
        "after_sha256": sha256_text(rendered),
        "converted_count": len(converted),
        "converted": converted,
        "valid_records_after": valid_records,
        "validation_errors": errors,
    }
    return rendered, plan


def apply_migration(path: Path, rendered: str, plan: dict[str, Any]) -> dict[str, Any]:
    expected = str(plan["expected_before_sha256"]).casefold()
    actual = str(sha256_file(path) or "").casefold()
    if actual != expected:
        raise SystemExit(
            f"Source hash changed; expected {expected}, found {actual}. Nothing was written."
        )
    if plan["validation_errors"]:
        raise SystemExit("Migration validation failed. Nothing was written.")
    if not plan["converted_count"]:
        raise SystemExit("No literal-escaped records found. Nothing was written.")

    stamp = utc_now_iso().replace(":", "-")
    mem_dir = path.parent
    backup_dir = mem_dir / "backups" / f"observations-migration-{stamp}"
    backup_path = backup_file(path, backup_dir, "before")
    if backup_path is None:
        raise SystemExit("Could not create source backup. Nothing was written.")

    atomic_write_text(path, rendered)
    actual_after = sha256_file(path)
    if actual_after != plan["after_sha256"]:
        raise SystemExit(
            "Post-write hash mismatch. The backup is intact; manual rollback is required."
        )

    receipt = {
        "operation": "literal_escaped_observations_migration",
        "applied_at": utc_now_iso(),
        "source": str(path),
        "backup": str(backup_path),
        "before_sha256": plan["before_sha256"],
        "after_sha256": actual_after,
        "converted_count": plan["converted_count"],
        "converted": plan["converted"],
        "valid_records_after": plan["valid_records_after"],
    }
    receipt_path = mem_dir / "receipts" / f"observations-migration-{stamp}.json"
    atomic_write_text(
        receipt_path,
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
    )
    receipt["receipt"] = str(receipt_path)
    return receipt


def main() -> None:
    args = parse_args()
    path = Path(args.root) / ".codex-mem" / "observations.jsonl"
    if not path.exists():
        raise SystemExit(f"Missing observations file: {path}")
    rendered, plan = migration_plan(path)
    if not args.apply:
        print(json.dumps({"mode": "dry-run", **plan}, indent=2, ensure_ascii=False))
        if plan["validation_errors"]:
            raise SystemExit(2)
        return

    plan["expected_before_sha256"] = args.expected_before_sha256
    receipt = apply_migration(path, rendered, plan)
    print(json.dumps({"mode": "apply", **receipt}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

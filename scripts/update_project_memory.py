#!/usr/bin/env python3
"""Replace one project_memory.md section and optionally refresh its global card."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys

from memory_common import (
    CANONICAL_TOTAL_TOKEN_HIGH,
    DEFAULT_LOAD_TOKEN_HIGH,
    RETENTION_STATUSES,
    SECTION_TOKEN_HIGH,
    atomic_write_text,
    backup_file,
    compact_update_report,
    default_global_memory_root,
    project_memory_size_diagnostics,
    sha256_file,
    utc_now_iso,
)
from refresh_global_memory import run_refresh, update_retention_status


SECTION_HEADERS = [
    "## Project Identity",
    "## Current Operating State",
    "## Protected Human Decisions",
    "## Durable Decisions",
    "## Durable Constraints",
    "## Rejected Routes",
    "## Next-Step Anchor",
    "## Unresolved Issues",
    "## Canonical Docs",
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--section", choices=SECTION_HEADERS, help="Top-level section to replace in project_memory.md.")
    mode.add_argument("--global-project", help="Project name to update inside global routing memory.")
    parser.add_argument("--root", help="Project root directory.")
    parser.add_argument("--content-file", help="UTF-8 text file with replacement body.")
    parser.add_argument("--retention-status", choices=RETENTION_STATUSES, help="Global routing retention status.")
    parser.add_argument(
        "--global-memory-root",
        default=str(default_global_memory_root()),
        help="Directory containing global_memory.md and projects_index.jsonl.",
    )
    parser.add_argument(
        "--sync-global-card",
        action="store_true",
        help="After a project section update, refresh only this registered project's global card.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the reviewed change. Default is a no-write preview.",
    )
    parser.add_argument(
        "--expected-before-sha256",
        help="Required for a project_memory.md apply.",
    )
    parser.add_argument(
        "--allow-size-growth",
        action="store_true",
        help="Allow an explicitly reviewed write that grows an already-high memory.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the compact update report.")
    args = parser.parse_args()
    if args.section and (not args.root or not args.content_file):
        parser.error("--section requires --root and --content-file")
    if args.global_project and not args.retention_status:
        parser.error("--global-project requires --retention-status")
    if args.section and args.apply and not args.expected_before_sha256:
        parser.error(
            "--section --apply requires --expected-before-sha256"
        )
    if args.allow_size_growth and not args.apply:
        parser.error("--allow-size-growth requires --apply")
    return args


def replace_section(text: str, section: str, body: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(section)
    except ValueError as exc:
        raise SystemExit(f"Section not found: {section}") from exc

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    replacement = [section, "", *body.strip().splitlines(), ""]
    return "\n".join(lines[:start] + replacement + lines[end:]).rstrip() + "\n"


def size_growth_blockers(
    before: dict[str, object],
    after: dict[str, object],
) -> list[str]:
    blockers: list[str] = []
    metrics = (
        (
            "canonical_estimated_tokens",
            CANONICAL_TOTAL_TOKEN_HIGH,
            "canonical total",
        ),
        (
            "default_load_estimated_tokens",
            DEFAULT_LOAD_TOKEN_HIGH,
            "default-load sections",
        ),
    )
    for key, threshold, label in metrics:
        before_value = int(before[key])
        after_value = int(after[key])
        if after_value > threshold and after_value > before_value:
            blockers.append(
                f"{label} would grow from {before_value} to {after_value} "
                f"estimated tokens (high threshold {threshold})"
            )
    before_sections = dict(before["section_tokens"])
    after_sections = dict(after["section_tokens"])
    for heading, after_value in after_sections.items():
        before_value = int(before_sections.get(heading, 0))
        if (
            int(after_value) > SECTION_TOKEN_HIGH
            and int(after_value) > before_value
        ):
            blockers.append(
                f"section {heading!r} would grow from {before_value} to "
                f"{after_value} estimated tokens "
                f"(high threshold {SECTION_TOKEN_HIGH})"
            )
    return blockers


def bounded_diff(before: str, after: str, limit: int = 400) -> str:
    lines = list(
        difflib.unified_diff(
            before.splitlines(),
            after.splitlines(),
            fromfile="project_memory.md.before",
            tofile="project_memory.md.after",
            lineterm="",
        )
    )
    if len(lines) > limit:
        lines = lines[:limit] + [
            f"... diff truncated after {limit} lines ..."
        ]
    return "\n".join(lines) or "(no diff)"


def main() -> None:
    args = parse_args()
    if args.global_project:
        print(
            "warning: --global-project is a compatibility shim; use refresh_global_memory.py for new workflows.",
            file=sys.stderr,
        )
        if not args.apply:
            print(
                "dry-run: would update retention status for "
                f"{args.global_project!r} to {args.retention_status!r}; "
                "use --apply after review"
            )
            return
        update_retention_status(
            Path(args.global_memory_root),
            args.global_project,
            args.retention_status,
        )
        return

    root = Path(args.root)
    path = root / "project_memory.md"
    if not path.exists():
        raise SystemExit(f"Missing project_memory.md: {path}")

    original = path.read_text(encoding="utf-8")
    original_hash = sha256_file(path)
    content = Path(args.content_file).read_text(encoding="utf-8")
    updated = replace_section(original, args.section, content)
    before_size = project_memory_size_diagnostics(original)
    after_size = project_memory_size_diagnostics(updated)
    blockers = size_growth_blockers(before_size, after_size)

    if not args.apply:
        print("mode: dry-run")
        print(f"source_sha256: {original_hash}")
        print(
            "canonical_estimated_tokens: "
            f"{before_size['canonical_estimated_tokens']} -> "
            f"{after_size['canonical_estimated_tokens']}"
        )
        print(
            "default_load_estimated_tokens: "
            f"{before_size['default_load_estimated_tokens']} -> "
            f"{after_size['default_load_estimated_tokens']}"
        )
        for blocker in blockers:
            print(f"size_gate: {blocker}")
        print("diff:")
        print(bounded_diff(original, updated))
        return

    expected = str(args.expected_before_sha256).casefold()
    if str(original_hash or "").casefold() != expected:
        raise SystemExit(
            "project_memory.md changed after review; source hash mismatch"
        )
    if blockers and not args.allow_size_growth:
        raise SystemExit(
            "size growth gate blocked apply: " + "; ".join(blockers)
        )

    stamp = utc_now_iso().replace(":", "-")
    backup_dir = (
        root / ".codex-mem" / "backups" / f"memory-update-{stamp}"
    )
    backup_path = backup_file(path, backup_dir, "before")
    if backup_path is None:
        raise SystemExit("could not create project_memory.md backup")
    atomic_write_text(path, updated)
    after_hash = sha256_file(path)
    receipt = {
        "operation": "project_memory_section_update",
        "applied_at": utc_now_iso(),
        "section": args.section,
        "source": str(path),
        "backup": str(backup_path),
        "before_sha256": original_hash,
        "after_sha256": after_hash,
        "size_before": before_size,
        "size_after": after_size,
        "size_growth_override": bool(args.allow_size_growth),
    }
    receipt_path = (
        root
        / ".codex-mem"
        / "receipts"
        / f"project-memory-update-{stamp}.json"
    )
    atomic_write_text(
        receipt_path,
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n",
    )

    sync_note = "- global card refresh not requested"
    needs_review: list[str] = []
    if args.sync_global_card:
        refresh = run_refresh(Path(args.global_memory_root), project_selector=str(root), apply=True)
        if refresh.status == "success":
            sync_note = f"- targeted global card refresh: {refresh.report_path or 'no report path'}"
        elif refresh.status == "unregistered":
            sync_note = "- targeted global card refresh skipped: project is unregistered"
            needs_review.append("- Register the project through explicit maintain/discovery before global sync.")
        else:
            sync_note = f"- targeted global card refresh blocked: {refresh.status}"
            needs_review.extend(f"- {warning}" for warning in refresh.warnings)

    if not args.quiet:
        print(
            compact_update_report(
                updated=[
                    f"- replaced section: {args.section}",
                    f"- backup: {backup_path}",
                    f"- receipt: {receipt_path}",
                    sync_note,
                ],
                preserved=[
                    "- protected human decisions require explicit approval to change",
                    "- memory remains non-authorization context",
                ],
                current_anchor="- review project_memory.md Next-Step Anchor for current work",
                needs_review=needs_review,
            ),
            end="",
        )


if __name__ == "__main__":
    main()

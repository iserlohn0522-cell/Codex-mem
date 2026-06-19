#!/usr/bin/env python3
"""Replace one project_memory.md section and optionally refresh its global card."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from memory_common import RETENTION_STATUSES, atomic_write_text, compact_update_report
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
        default=str(Path.home() / ".codex" / "memory" / "codex-mem"),
        help="Directory containing global_memory.md and projects_index.jsonl.",
    )
    parser.add_argument(
        "--sync-global-card",
        action="store_true",
        help="After a project section update, refresh only this registered project's global card.",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress the compact update report.")
    args = parser.parse_args()
    if args.section and (not args.root or not args.content_file):
        parser.error("--section requires --root and --content-file")
    if args.global_project and not args.retention_status:
        parser.error("--global-project requires --retention-status")
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


def main() -> None:
    args = parse_args()
    if args.global_project:
        print(
            "warning: --global-project is a compatibility shim; use refresh_global_memory.py for new workflows.",
            file=sys.stderr,
        )
        update_retention_status(Path(args.global_memory_root), args.global_project, args.retention_status)
        return

    root = Path(args.root)
    path = root / "project_memory.md"
    if not path.exists():
        raise SystemExit(f"Missing project_memory.md: {path}")

    content = Path(args.content_file).read_text(encoding="utf-8")
    updated = replace_section(path.read_text(encoding="utf-8"), args.section, content)
    atomic_write_text(path, updated)

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
                updated=[f"- replaced section: {args.section}", sync_note],
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

#!/usr/bin/env python3
"""Replace one top-level section inside project_memory.md or update global routing status."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


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

RETENTION_STATUSES = ["active", "warm", "cold", "archived"]
GLOBAL_HEADERS = [
    "## Active Projects",
    "## Warm Projects",
    "## Cold Projects",
    "## Archived Projects",
    "## Shared Lessons",
    "## Routing Notes",
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


def ensure_global_memory(path: Path) -> None:
    if path.exists():
        return
    skeleton = "\n".join(
        [
            "# Global Memory",
            "",
            "## Active Projects",
            "",
            "- none",
            "",
            "## Warm Projects",
            "",
            "- none",
            "",
            "## Cold Projects",
            "",
            "- none",
            "",
            "## Archived Projects",
            "",
            "- none",
            "",
            "## Shared Lessons",
            "",
            "- none",
            "",
            "## Routing Notes",
            "",
            "- none",
            "",
        ]
    )
    path.write_text(skeleton, encoding="utf-8")


def replace_markdown_section(text: str, section: str, body_lines: list[str]) -> str:
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

    replacement = [section, "", *body_lines, ""]
    return "\n".join(lines[:start] + replacement + lines[end:]).rstrip() + "\n"


def load_projects_index(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing projects_index.jsonl: {path}")
    records: list[dict] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if raw_line.strip():
            records.append(json.loads(raw_line))
    return records


def write_projects_index(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def build_project_card(record: dict) -> str:
    project = record["project"]
    summary = record["summary"].strip()
    memory_path = record["memory_path"]
    stage_log_path = record["stage_log_path"]
    return (
        f"- `{project}` - {summary} "
        f"Use `{memory_path}` for current memory and `{stage_log_path}` for stage summaries."
    )


def update_global_status(global_root: Path, project: str, status: str) -> None:
    global_root.mkdir(parents=True, exist_ok=True)
    global_memory_path = global_root / "global_memory.md"
    projects_index_path = global_root / "projects_index.jsonl"
    ensure_global_memory(global_memory_path)
    records = load_projects_index(projects_index_path)

    target_record = None
    for record in records:
        if record.get("project") == project:
            target_record = record
            break
    if target_record is None:
        raise SystemExit(f"Project not found in projects_index.jsonl: {project}")

    target_record["status"] = status
    target_record["last_updated"] = date.today().isoformat()
    write_projects_index(projects_index_path, records)

    grouped: dict[str, list[str]] = {key: [] for key in RETENTION_STATUSES}
    for record in records:
        grouped[record.get("status", "active")].append(build_project_card(record))

    text = global_memory_path.read_text(encoding="utf-8")
    text = replace_markdown_section(text, "## Active Projects", grouped["active"] or ["- none"])
    text = replace_markdown_section(text, "## Warm Projects", grouped["warm"] or ["- none"])
    text = replace_markdown_section(text, "## Cold Projects", grouped["cold"] or ["- none"])
    text = replace_markdown_section(text, "## Archived Projects", grouped["archived"] or ["- none"])
    global_memory_path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.global_project:
        update_global_status(Path(args.global_memory_root), args.global_project, args.retention_status)
        return

    root = Path(args.root)
    path = root / "project_memory.md"
    if not path.exists():
        raise SystemExit(f"Missing project_memory.md: {path}")

    content = Path(args.content_file).read_text(encoding="utf-8")
    updated = replace_section(path.read_text(encoding="utf-8"), args.section, content)
    path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()

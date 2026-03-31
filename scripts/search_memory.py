#!/usr/bin/env python3
"""Search lean Codex-mem project files with substring matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--query", required=True, help="Case-insensitive search query.")
    return parser.parse_args()


def search_text(path: Path, query: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    hits: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if query in line.lower():
            hits.append(
                {
                    "source": str(path),
                    "line": str(line_number),
                    "text": line.strip(),
                }
            )
    return hits


def search_observations(path: Path, query: str) -> list[dict[str, str]]:
    if not path.exists():
        return []
    hits: list[dict[str, str]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        haystack_parts = [str(record.get(key, "")) for key in ("title", "summary", "details", "kind", "stage_id", "source")]
        tags = record.get("tags", [])
        if isinstance(tags, list):
            haystack_parts.extend(str(tag) for tag in tags)
        haystack = " ".join(haystack_parts)
        if query in haystack.lower():
            hits.append(
                {
                    "source": str(path),
                    "line": str(line_number),
                    "text": record.get("title", ""),
                }
            )
    return hits


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    query = args.query.lower()
    mem_dir = root / ".codex-mem"

    results = []
    results.extend(search_text(root / "project_memory.md", query))
    results.extend(search_text(root / "project_stage_log.md", query))
    results.extend(search_observations(mem_dir / "observations.jsonl", query))

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Append or replace one stage entry inside project_stage_log.md."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--stage-id", required=True, help="Stage identifier to update.")
    parser.add_argument("--entry-file", required=True, help="UTF-8 text file containing one full stage block.")
    return parser.parse_args()


def find_stage_bounds(lines: list[str], stage_id: str) -> tuple[int, int] | None:
    marker = f"- stage_id: {stage_id}"
    start = -1
    for index, line in enumerate(lines):
        if line.strip() == marker:
            probe = index
            while probe >= 0 and lines[probe].strip() != "### Stage":
                probe -= 1
            start = probe
            break
    if start < 0:
        return None

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].strip() == "### Stage":
            end = index
            break
    return start, end


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    path = root / "project_stage_log.md"
    if not path.exists():
        raise SystemExit(f"Missing project_stage_log.md: {path}")

    text = path.read_text(encoding="utf-8").rstrip() + "\n"
    lines = text.splitlines()
    entry = Path(args.entry_file).read_text(encoding="utf-8").strip().splitlines()
    bounds = find_stage_bounds(lines, args.stage_id)

    if bounds is None:
        if lines and lines[-1] != "":
            lines.append("")
        lines.extend(entry)
        lines.append("")
    else:
        start, end = bounds
        lines = lines[:start] + entry + [""] + lines[end:]

    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

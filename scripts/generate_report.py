#!/usr/bin/env python3
"""Generate a lightweight Codex-mem report from current project files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--kind", choices=["stage-report", "journey-report-lite"], default="journey-report-lite")
    parser.add_argument("--output", required=True, help="Output markdown path.")
    return parser.parse_args()


def tail_observations(path: Path, limit: int = 10) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    return rows[-limit:]


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    output = Path(args.output)
    mem_dir = root / ".codex-mem"

    memory_text = (root / "project_memory.md").read_text(encoding="utf-8") if (root / "project_memory.md").exists() else ""
    stage_text = (root / "project_stage_log.md").read_text(encoding="utf-8") if (root / "project_stage_log.md").exists() else ""
    observations = tail_observations(mem_dir / "observations.jsonl")

    lines = [
        f"# {args.kind}",
        "",
        "## Source Files",
        "",
        f"- project_memory.md: {'present' if memory_text else 'missing'}",
        f"- project_stage_log.md: {'present' if stage_text else 'missing'}",
        f"- observations used: {len(observations)}",
        "",
        "## Current Memory Snapshot",
        "",
        memory_text.strip() or "_No project_memory.md content available._",
        "",
        "## Stage Snapshot",
        "",
        stage_text.strip() or "_No project_stage_log.md content available._",
        "",
        "## Recent High-value Observations",
        "",
    ]

    if observations:
        for item in observations:
            lines.extend(
                [
                    f"- {item.get('title', 'untitled')} ({item.get('kind', 'unknown')})",
                    f"  - summary: {item.get('summary', '')}",
                    f"  - importance: {item.get('importance', '')}",
                ]
            )
    else:
        lines.append("_No observations available._")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

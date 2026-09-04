#!/usr/bin/env python3
"""Generate a lightweight Codex-mem report from current project files."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_common import JsonlLoad, load_jsonl


DEFAULT_MEMORY_SECTIONS = {
    "Project Identity",
    "Current Operating State",
    "Protected Human Decisions",
    "Next-Step Anchor",
    "Unresolved Issues",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--kind", choices=["stage-report", "journey-report-lite"], default="journey-report-lite")
    parser.add_argument("--output", required=True, help="Output markdown path.")
    parser.add_argument(
        "--max-memory-lines",
        type=int,
        default=180,
        help="Maximum selected canonical lines included in the report (20-400).",
    )
    parser.add_argument(
        "--max-stage-lines",
        type=int,
        default=120,
        help="Maximum lines from the latest stage block (20-300).",
    )
    return parser.parse_args()


def tail_observations(path: Path, limit: int = 10) -> tuple[list[dict[str, object]], JsonlLoad]:
    loaded = load_jsonl(path)
    return loaded.records[-limit:], loaded


def bounded_lines(lines: list[str], limit: int) -> tuple[list[str], bool]:
    if len(lines) <= limit:
        return lines, False
    return lines[:limit] + ["", "_Source excerpt truncated by report limit._"], True


def select_memory_sections(text: str, limit: int) -> tuple[str, int, bool]:
    selected: list[str] = []
    include = False
    for line in text.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            include = heading in DEFAULT_MEMORY_SECTIONS
        if include:
            selected.append(line)
    bounded, truncated = bounded_lines(selected, limit)
    return "\n".join(bounded).strip(), len(selected), truncated


def select_latest_stage(text: str, limit: int) -> tuple[str, int, bool]:
    lines = text.splitlines()
    stage_starts = [
        index
        for index, line in enumerate(lines)
        if line.strip() == "### Stage"
    ]
    selected = lines[stage_starts[-1] :] if stage_starts else lines
    bounded, truncated = bounded_lines(selected, limit)
    return "\n".join(bounded).strip(), len(selected), truncated


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    output = Path(args.output)
    mem_dir = root / ".codex-mem"

    memory_text = (root / "project_memory.md").read_text(encoding="utf-8") if (root / "project_memory.md").exists() else ""
    stage_text = (root / "project_stage_log.md").read_text(encoding="utf-8") if (root / "project_stage_log.md").exists() else ""
    max_memory_lines = min(400, max(20, args.max_memory_lines))
    max_stage_lines = min(300, max(20, args.max_stage_lines))
    memory_excerpt, selected_memory_lines, memory_truncated = select_memory_sections(
        memory_text,
        max_memory_lines,
    )
    stage_excerpt, selected_stage_lines, stage_truncated = select_latest_stage(
        stage_text,
        max_stage_lines,
    )
    observations_path = mem_dir / "observations.jsonl"
    observations, loaded = tail_observations(observations_path)
    malformed_lines = [line for line, _raw, _error in loaded.malformed_lines]

    lines = [
        f"# {args.kind}",
        "",
        "## Source Files",
        "",
        f"- project_memory.md: {'present' if memory_text else 'missing'}",
        f"- canonical lines selected: {selected_memory_lines} (limit {max_memory_lines})",
        f"- canonical excerpt truncated: {'yes' if memory_truncated else 'no'}",
        f"- project_stage_log.md: {'present' if stage_text else 'missing'}",
        f"- latest stage lines selected: {selected_stage_lines} (limit {max_stage_lines})",
        f"- stage excerpt truncated: {'yes' if stage_truncated else 'no'}",
        f"- observations.jsonl: {'present' if observations_path.exists() else 'missing'}",
        f"- observations valid: {len(loaded.records)}",
        f"- observations malformed: {len(loaded.malformed_lines)}",
        f"- observations used: {len(observations)}",
        "",
    ]
    if malformed_lines:
        lines.extend(
            [
                "## Data Quality Warning",
                "",
                (
                    "> WARNING: observation coverage is incomplete; "
                    f"{len(malformed_lines)} malformed JSONL line(s) were skipped "
                    f"(physical lines: {', '.join(str(line) for line in malformed_lines)})."
                ),
                "",
            ]
        )
    lines.extend(
        [
        "## Current Memory Snapshot",
        "",
        memory_excerpt or "_No selected project_memory.md content available._",
        "",
        "## Stage Snapshot",
        "",
        stage_excerpt or "_No project_stage_log.md content available._",
        "",
        "## Recent High-value Observations",
        "",
        ]
    )

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

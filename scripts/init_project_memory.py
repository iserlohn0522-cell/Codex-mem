#!/usr/bin/env python3
"""Initialize lean Codex-mem files inside a project root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_MEMORY_TEMPLATE = """# Project Memory

## Project Identity

- project:
- root:
- summary:

## Current Operating State

- current stage:
- immediate working objective:
- do not do yet:
- active stopping rule:

## Protected Human Decisions

- [confirmed] decision:
  - protection reason:
  - change requires explicit user approval:

## Durable Decisions

- [confirmed] decision:
  - why it matters:

## Durable Constraints

- [confirmed] constraint:
  - why it matters:

## Rejected Routes

- [rejected] route:
  - why rejected:
  - prevent recurrence by:

## Next-Step Anchor

- [confirmed] next-step anchor:
  - why this is the anchor:

## Unresolved Issues

- [unresolved] issue:
  - why it must stay visible:
  - what would resolve it:

## Canonical Docs

- readme:
- master plan:
- current plan:
- implementation plan:
- key reports:
"""


PROJECT_STAGE_LOG_TEMPLATE = """# Project Stage Log

## Stage Log

### Stage

- stage_id:
- status: active
- time_range:
- goal:
- short_conclusion:
- carry_forward:
- report_paths:
- key_observation_ids:
"""


EXECUTION_POINTERS_TEMPLATE = {"version": 2, "pointers": []}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    return parser.parse_args()


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def write_json_if_missing(path: Path, data: object) -> None:
    if path.exists():
        return
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = Path(args.root)

    if not root.exists():
        raise SystemExit(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Project root is not a directory: {root}")

    mem_dir = root / ".codex-mem"
    reports_dir = mem_dir / "reports"
    mem_dir.mkdir(exist_ok=True)
    reports_dir.mkdir(exist_ok=True)

    write_if_missing(root / "project_memory.md", PROJECT_MEMORY_TEMPLATE)
    write_if_missing(root / "project_stage_log.md", PROJECT_STAGE_LOG_TEMPLATE)
    write_if_missing(mem_dir / "observations.jsonl", "")
    write_json_if_missing(mem_dir / "execution_pointers.json", EXECUTION_POINTERS_TEMPLATE)


if __name__ == "__main__":
    main()

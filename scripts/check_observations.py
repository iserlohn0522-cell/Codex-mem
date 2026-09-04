#!/usr/bin/env python3
"""Run read-only integrity checks on one project's observations JSONL."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

from memory_common import load_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    return parser.parse_args()


def normalize_supersedes(value: Any) -> tuple[list[str], bool]:
    if value is None or value == "":
        return [], value not in (None, "")
    if isinstance(value, str):
        return [value], True
    if isinstance(value, list):
        normalized = [str(item).strip() for item in value if str(item).strip()]
        return normalized, False
    return [], True


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indexes[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in graph.get(node, set()):
            if target not in graph:
                continue
            if target not in indexes:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indexes[target])

        if lowlinks[node] != indexes[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            components.append(sorted(component))

    for node in sorted(graph):
        if node not in indexes:
            visit(node)
    return sorted(components)


def inspect_observations(path: Path) -> dict[str, Any]:
    loaded = load_jsonl(path)
    id_lines: dict[str, list[int]] = defaultdict(list)
    records_by_line: list[tuple[int, dict[str, Any], str]] = []
    missing_ids: list[int] = []
    invalid_supersedes_type: list[int] = []

    for line_number, record in loaded.record_lines:
        record_id = str(record.get("id", "")).strip()
        if record_id:
            id_lines[record_id].append(line_number)
        else:
            missing_ids.append(line_number)
        _targets, invalid_type = normalize_supersedes(record.get("supersedes"))
        if invalid_type:
            invalid_supersedes_type.append(line_number)
        records_by_line.append((line_number, record, record_id))

    known_ids = set(id_lines)
    graph: dict[str, set[str]] = {record_id: set() for record_id in known_ids}
    missing_targets: list[dict[str, Any]] = []
    self_supersedes: list[dict[str, Any]] = []
    duplicate_content: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for line_number, record, record_id in records_by_line:
        targets, _invalid_type = normalize_supersedes(record.get("supersedes"))
        for target in targets:
            if record_id and target == record_id:
                self_supersedes.append({"line": line_number, "id": record_id})
            elif target not in known_ids:
                missing_targets.append(
                    {"line": line_number, "id": record_id, "target": target}
                )
            elif record_id:
                graph[record_id].add(target)

        title = str(record.get("title", "")).strip().casefold()
        summary = str(record.get("summary", "")).strip().casefold()
        if title or summary:
            duplicate_content[(title, summary)].append(
                {"line": line_number, "id": record_id}
            )

    duplicate_ids = [
        {"id": record_id, "lines": lines}
        for record_id, lines in sorted(id_lines.items())
        if len(lines) > 1
    ]
    exact_duplicates = [
        {"records": records}
        for _key, records in duplicate_content.items()
        if len(records) > 1
    ]
    malformed_lines = [line for line, _raw, _error in loaded.malformed_lines]
    cycles = strongly_connected_components(graph)

    error_count = (
        len(malformed_lines)
        + len(missing_ids)
        + len(duplicate_ids)
        + len(self_supersedes)
        + len(cycles)
        + len(invalid_supersedes_type)
    )
    warning_count = len(missing_targets) + len(exact_duplicates)
    status = "error" if error_count else ("warning" if warning_count else "ok")
    return {
        "status": status,
        "path": str(path),
        "valid_records": len(loaded.records),
        "malformed_records": len(loaded.malformed_lines),
        "malformed_lines": malformed_lines,
        "missing_id_lines": missing_ids,
        "duplicate_ids": duplicate_ids,
        "invalid_supersedes_type_lines": invalid_supersedes_type,
        "missing_supersedes_targets": missing_targets,
        "self_supersedes": self_supersedes,
        "supersedes_cycles": cycles,
        "exact_duplicate_title_summary": exact_duplicates,
        "error_count": error_count,
        "warning_count": warning_count,
    }


def main() -> None:
    args = parse_args()
    path = Path(args.root) / ".codex-mem" / "observations.jsonl"
    result = inspect_observations(path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["status"] == "error":
        raise SystemExit(2)
    if result["status"] == "warning":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

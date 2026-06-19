#!/usr/bin/env python3
"""Discover Codex-mem projects without scanning entire drives by default."""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from memory_common import (
    IGNORE_DIR_NAMES,
    canonical_path_key,
    git_root_for,
    load_jsonl,
    parse_project_memory,
    resolved_path_key,
)


@dataclass
class DiscoveredProject:
    project: str
    root_path: str
    memory_path: str
    stage_log_path: str
    git_root: str
    exists: bool
    source: str
    status: str
    summary: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--global-memory-root",
        default=str(Path.home() / ".codex" / "memory" / "codex-mem"),
        help="Directory containing projects_index.jsonl.",
    )
    parser.add_argument("--current-project", help="Current project root, if known.")
    parser.add_argument("--workspace-root", action="append", default=[], help="Allowlisted workspace root.")
    parser.add_argument("--config", help="Optional JSON or line-based config containing workspace roots.")
    parser.add_argument("--max-depth", type=int, default=4, help="Bounded search depth under workspace roots.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a compact text table.")
    return parser.parse_args()


def load_config_roots(path: str | None) -> list[str]:
    if not path:
        return []
    config_path = Path(path)
    if not config_path.exists():
        raise SystemExit(f"Missing discovery config: {config_path}")
    text = config_path.read_text(encoding="utf-8-sig")
    if config_path.suffix.lower() == ".json":
        data = json.loads(text)
        roots = data.get("workspace_roots", []) if isinstance(data, dict) else data
        if not isinstance(roots, list):
            raise SystemExit("Discovery config JSON must contain a workspace_roots list or be a list.")
        return [str(root) for root in roots]
    return [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]


def project_from_root(root: Path, source: str, existing_record: dict[str, Any] | None = None) -> DiscoveredProject:
    memory_path = root / "project_memory.md"
    stage_log_path = root / "project_stage_log.md"
    parsed = parse_project_memory(memory_path)
    record = existing_record or {}
    project = parsed.get("project") or record.get("project") or root.name
    summary = parsed.get("summary") or record.get("summary", "")
    git_root = git_root_for(root)
    return DiscoveredProject(
        project=str(project),
        root_path=str(root),
        memory_path=str(record.get("memory_path") or memory_path),
        stage_log_path=str(record.get("stage_log_path") or stage_log_path),
        git_root=str(git_root) if git_root else "",
        exists=root.exists() and memory_path.exists(),
        source=source,
        status=str(record.get("status") or record.get("retention_status") or "active"),
        summary=str(summary),
    )


def root_from_record(record: dict[str, Any]) -> Path | None:
    root = record.get("root_path")
    if root:
        return Path(str(root))
    memory_path = record.get("memory_path")
    if memory_path:
        return Path(str(memory_path)).parent
    return None


def load_index_records(global_memory_root: Path) -> tuple[list[dict[str, Any]], list[tuple[int, str, str]]]:
    index_path = global_memory_root / "projects_index.jsonl"
    loaded = load_jsonl(index_path)
    return loaded.records, loaded.malformed_lines


def should_ignore_dir(path: Path) -> bool:
    return path.name.casefold() in IGNORE_DIR_NAMES


def bounded_project_memory_search(workspace_root: Path, max_depth: int) -> list[Path]:
    if not workspace_root.exists() or not workspace_root.is_dir():
        return []
    found: list[Path] = []
    queue: deque[tuple[Path, int]] = deque([(workspace_root, 0)])
    while queue:
        current, depth = queue.popleft()
        if should_ignore_dir(current):
            continue
        if (current / "project_memory.md").exists():
            found.append(current)
            continue
        if depth >= max_depth:
            continue
        try:
            children = [child for child in current.iterdir() if child.is_dir() and not should_ignore_dir(child)]
        except OSError:
            continue
        for child in sorted(children, key=lambda item: item.name.casefold()):
            queue.append((child, depth + 1))
    return found


def inferred_workspace_roots(records: list[dict[str, Any]]) -> list[Path]:
    roots: list[Path] = []
    for record in records:
        project_root = root_from_record(record)
        if not project_root:
            continue
        try:
            resolved = project_root.resolve()
        except OSError:
            resolved = project_root.absolute()
        parent = resolved.parent
        if parent == resolved or parent.parent == parent:
            continue
        if parent.exists():
            roots.append(parent)
    return roots


def discover_projects(
    global_memory_root: Path,
    current_project: str | None = None,
    workspace_roots: list[str] | None = None,
    config_path: str | None = None,
    max_depth: int = 4,
) -> tuple[list[DiscoveredProject], list[str]]:
    records, malformed = load_index_records(global_memory_root)
    warnings = [f"malformed projects_index.jsonl line {line}: {error}" for line, _raw, error in malformed]
    projects: list[DiscoveredProject] = []
    seen_roots: set[str] = set()
    seen_git_roots: set[str] = set()

    def add(project: DiscoveredProject) -> None:
        root_key = resolved_path_key(project.root_path) if project.exists else canonical_path_key(project.root_path)
        git_key = canonical_path_key(project.git_root) if project.git_root else ""
        if root_key in seen_roots:
            warnings.append(f"duplicate project root ignored: {project.root_path}")
            return
        if git_key and git_key in seen_git_roots:
            warnings.append(f"duplicate git root ignored: {project.root_path}")
            return
        seen_roots.add(root_key)
        if git_key:
            seen_git_roots.add(git_key)
        projects.append(project)

    for record in records:
        root = root_from_record(record)
        if root is None:
            warnings.append(f"index record without root_path or memory_path ignored: {record.get('project', '(unnamed)')}")
            continue
        add(project_from_root(root, "projects_index.jsonl", record))

    if current_project:
        add(project_from_root(Path(current_project), "current-project"))
    else:
        cwd = Path.cwd()
        if (cwd / "project_memory.md").exists():
            add(project_from_root(cwd, "current-project"))

    configured_roots = load_config_roots(config_path)
    explicit_roots = [Path(root) for root in (workspace_roots or []) + configured_roots]
    for workspace_root in explicit_roots:
        for root in bounded_project_memory_search(workspace_root, max_depth):
            add(project_from_root(root, f"workspace-root:{workspace_root}"))

    for workspace_root in inferred_workspace_roots(records):
        for root in bounded_project_memory_search(workspace_root, max_depth):
            add(project_from_root(root, f"inferred-root:{workspace_root}"))

    return projects, warnings


def main() -> None:
    args = parse_args()
    projects, warnings = discover_projects(
        Path(args.global_memory_root),
        current_project=args.current_project,
        workspace_roots=args.workspace_root,
        config_path=args.config,
        max_depth=args.max_depth,
    )
    if args.json:
        print(json.dumps({"projects": [asdict(project) for project in projects], "warnings": warnings}, indent=2, ensure_ascii=False))
        return
    for project in projects:
        state = "present" if project.exists else "missing"
        print(f"{project.project}\t{state}\t{project.status}\t{project.root_path}")
    for warning in warnings:
        print(f"warning: {warning}")


if __name__ == "__main__":
    main()

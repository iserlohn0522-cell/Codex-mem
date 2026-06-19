#!/usr/bin/env python3
"""Refresh global Codex-mem routing files safely."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from discover_projects import discover_projects
from memory_common import (
    RETENTION_STATUSES,
    atomic_write_text,
    backup_file,
    canonical_path_key,
    classify_activity,
    classify_freshness,
    datetime_to_iso,
    file_mtime_iso,
    git_root_for,
    latest_observation_time,
    load_jsonl,
    parse_iso_datetime,
    parse_project_memory,
    resolved_path_key,
    sha256_file,
    utc_now_iso,
    write_jsonl,
)


PROJECT_HEADERS = {
    "active": "## Active Projects",
    "warm": "## Warm Projects",
    "cold": "## Cold Projects",
    "archived": "## Archived Projects",
}

GLOBAL_HEADERS = [
    "## Active Projects",
    "## Warm Projects",
    "## Cold Projects",
    "## Archived Projects",
    "## Shared Lessons",
    "## Routing Notes",
]


ACTIVE_WARM_TARGET_MAX = 260
ACTIVE_WARM_ABSOLUTE_MAX = 320
COLD_ARCHIVED_ABSOLUTE_MAX = 180
SUMMARY_MAX = 180
COMPACT_STAGE_MAX = 80
COMPACT_OBJECTIVE_MAX = 100
COMPACT_ANCHOR_MAX = 120
STALE_REASON_MAX = 100
RAW_LONG_FIELD_MAX = {
    "current_stage": COMPACT_STAGE_MAX,
    "immediate_objective": COMPACT_OBJECTIVE_MAX,
    "next_step_anchor": COMPACT_ANCHOR_MAX,
}

OPERATIONAL_DETAIL_PATTERNS = [
    re.compile(r"\bjob\s*`?\d{6,}", re.IGNORECASE),
    re.compile(r"\b\d{7,}(?:\[\d+-\d+\])?\b"),
    re.compile(r"\b\d{1,3}(?:,\d{3})+/\d{1,3}(?:,\d{3})+\b"),
    re.compile(r"\bprompt(?:s|ed)?\b", re.IGNORECASE),
    re.compile(r"\bzero-mask\b", re.IGNORECASE),
    re.compile(r"\bMAE\s*=", re.IGNORECASE),
    re.compile(r"\bmedian absolute error\b", re.IGNORECASE),
    re.compile(r"\bsigned bias\b", re.IGNORECASE),
    re.compile(r"experiments_ignore_region_v\d+", re.IGNORECASE),
    re.compile(r"paper_facing_model_output", re.IGNORECASE),
    re.compile(r"material_state_report", re.IGNORECASE),
]


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def selector_points_to_project_root(selector: str | None) -> bool:
    if not selector:
        return False
    try:
        path = Path(selector)
    except (OSError, ValueError):
        return False
    return (path / "project_memory.md").exists()


@dataclass
class RefreshResult:
    status: str
    global_changed: bool
    index_changed: bool
    global_memory_path: str
    projects_index_path: str
    report_path: str
    backups: list[str]
    warnings: list[str]
    changed_projects: list[str]
    modified_files: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--global-memory-root",
        default=str(Path.home() / ".codex" / "memory" / "codex-mem"),
        help="Directory containing global_memory.md and projects_index.jsonl.",
    )
    parser.add_argument("--workspace-root", action="append", default=[], help="Allowlisted workspace root.")
    parser.add_argument("--config", help="Optional discovery config with workspace roots.")
    parser.add_argument("--current-project", help="Current project root for discovery.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--project", help="Target one registered project by name or root path.")
    scope.add_argument("--all-projects", action="store_true", help="Refresh all registered/discovered projects.")
    parser.add_argument("--max-depth", type=int, default=4)
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    parser.add_argument("--dry-run", action="store_true", help="Explicitly request dry-run mode. This is the default.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()
    if args.apply and args.dry_run:
        parser.error("--apply and --dry-run are mutually exclusive")
    return args


def ensure_global_memory_text(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return "\n".join(
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


def replace_markdown_section(text: str, header: str, body_lines: list[str]) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(header)
    except ValueError:
        if not lines or lines[-1] != "":
            lines.append("")
        lines.extend([header, "", *body_lines, ""])
        return "\n".join(lines).rstrip() + "\n"
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    replacement = [header, "", *body_lines, ""]
    return "\n".join(lines[:start] + replacement + lines[end:]).rstrip() + "\n"


def unified_diff(old: str, new: str, fromfile: str, tofile: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            old.splitlines(),
            new.splitlines(),
            fromfile=fromfile,
            tofile=tofile,
            lineterm="",
        )
    )


def git_latest_commit_time(root: Path) -> datetime | None:
    git_root = git_root_for(root)
    if not git_root:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(git_root), "log", "-1", "--format=%cI"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    return parse_iso_datetime(result.stdout.strip())


def git_has_changes(root: Path) -> bool:
    git_root = git_root_for(root)
    if not git_root:
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(git_root), "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return bool(result.stdout.strip())


def max_datetime(values: list[datetime | None]) -> datetime | None:
    filtered = [value for value in values if value is not None]
    if not filtered:
        return None
    return max(filtered)


def project_matches(record: dict[str, Any], selector: str) -> bool:
    lowered = selector.casefold()
    if str(record.get("project", "")).casefold() == lowered:
        return True
    paths = [record.get("root_path"), record.get("memory_path"), record.get("stage_log_path")]
    selector_key = canonical_path_key(selector)
    for path in paths:
        if path and canonical_path_key(str(path)) == selector_key:
            return True
    if Path(selector).exists():
        try:
            selector_resolved = resolved_path_key(selector)
        except OSError:
            selector_resolved = selector_key
        for path in paths:
            if path and Path(str(path)).exists() and resolved_path_key(str(path)) == selector_resolved:
                return True
    return False


def clean_routing_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"[`*_#>]+", "", text)
    text = re.sub(r"\[[A-Z]{2}\s+[^\]]+\]", "", text)
    text = re.sub(r"\[[A-Z]{2}\]", "", text)
    text = re.sub(r"\bjob\s*\d{6,}(?:\[\d+-\d+\])?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{7,}(?:\[\d+-\d+\])?\b", "", text)
    text = re.sub(r"\b\d{1,3}(?:,\d{3})+(?:/\d{1,3}(?:,\d{3})+)?\b", "", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\s*(?:eV|nm|px|%)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:MAE|IoU|mAP|AP50|RMSE)\s*=\s*\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b[A-Za-z]:\\[^\s,;]+", "", text)
    text = re.sub(r"(?:(?<=\s)|^)/(?:[^\s,;]+/)+[^\s,;]+", "", text)
    text = re.sub(r"\b[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+){2,}\b", "", text)
    text = re.sub(r"\s+", " ", text).strip(" .;,-")
    return text


SENTENCE_ABBREVIATIONS = (
    "Dr.",
    "Mr.",
    "Mrs.",
    "Ms.",
    "Prof.",
    "Fig.",
    "Eq.",
    "e.g.",
    "i.e.",
)


def first_sentence(value: str) -> str:
    text = clean_routing_text(value)
    if not text:
        return ""
    protected = text
    for index, abbreviation in enumerate(SENTENCE_ABBREVIATIONS):
        protected = protected.replace(abbreviation, f"__ABBR{index}__")
    parts = re.split(r"(?<=[.!?])\s+", protected, maxsplit=1)
    first = parts[0]
    for index, abbreviation in enumerate(SENTENCE_ABBREVIATIONS):
        first = first.replace(f"__ABBR{index}__", abbreviation)
    return first.strip(" .")


def truncate_deterministic(value: str, limit: int) -> str:
    text = clean_routing_text(value)
    if len(text) <= limit:
        return text
    cut = text[: max(0, limit - 3)]
    for separator in ("; ", ". ", ", ", " "):
        index = cut.rfind(separator)
        if index >= max(20, limit // 2):
            cut = cut[:index]
            break
    return cut.rstrip(" .;,-") + "..."


def compact_summary_for_project(project: str, summary: str, keywords: Any) -> str:
    candidate = first_sentence(summary) or clean_routing_text(summary)
    if candidate:
        return truncate_deterministic(candidate, SUMMARY_MAX)
    if isinstance(keywords, list) and keywords:
        return truncate_deterministic(" / ".join(str(item) for item in keywords[:5]), SUMMARY_MAX)
    return f"{project} project"


def compact_field(value: Any, limit: int) -> str:
    return truncate_deterministic(first_sentence(str(value or "")) or str(value or ""), limit)


def compact_stale_reason(value: Any) -> str:
    text = str(value or "memory freshness unknown").strip()
    if text == "project activity is newer than canonical project memory":
        text = "memory stale"
    return truncate_deterministic(text, STALE_REASON_MAX)


def compact_routing_hint(project: str, summary: str, keywords: Any) -> str:
    haystack = f"{project} {summary} {' '.join(str(item) for item in keywords) if isinstance(keywords, list) else ''}".casefold()
    if "ptkb" in haystack or "dft" in haystack or "pt anchoring" in haystack:
        return "DFT Pt anchoring/detachment routing"
    if "gan" in haystack or "tem" in haystack or "sam" in haystack or "particle" in haystack:
        return "TEM detector/SAM particle routing"
    return ""


def enforce_card_limit(card: str, limit: int, record: dict[str, Any]) -> str:
    if len(card) <= limit:
        return card
    project = record.get("project", "(unnamed)")
    status = record.get("status", "active")
    activity = record.get("activity_state") or "unknown"
    memory_path = record.get("memory_path", "")
    summary = truncate_deterministic(record.get("compact_summary") or record.get("summary") or "no summary", 90)
    stale = record.get("memory_freshness") == "stale"
    if stale:
        card = f"- `{project}` - {summary}. Status: {status}/{activity}; memory stale, read `{memory_path}` before project work."
    else:
        card = f"- `{project}` - {summary}. Status: {status}/{activity}; read `{memory_path}`."
    if len(card) <= limit:
        return card
    summary = truncate_deterministic(summary, 45)
    card = f"- `{project}` - {summary}. Status: {status}/{activity}; read `{memory_path}`."
    if len(card) <= limit:
        return card
    return card[: max(0, limit - 3)].rstrip(" .;,-") + "..."


def analyze_project(existing: dict[str, Any], scan_time: str) -> dict[str, Any]:
    record = dict(existing)
    root_path = Path(str(record.get("root_path") or Path(str(record.get("memory_path", ""))).parent))
    memory_path = Path(str(record.get("memory_path") or root_path / "project_memory.md"))
    stage_log_path = Path(str(record.get("stage_log_path") or root_path / "project_stage_log.md"))
    observations_path = root_path / ".codex-mem" / "observations.jsonl"
    exists = root_path.exists() and memory_path.exists()

    parsed = parse_project_memory(memory_path)
    if parsed.get("project"):
        record["project"] = parsed["project"]
    record.setdefault("project", root_path.name)
    raw_summary = parsed.get("summary") or record.get("summary", "")
    compact_summary = compact_summary_for_project(str(record.get("project", root_path.name)), raw_summary, record.get("keywords", []))
    record["summary"] = compact_summary
    record["compact_summary"] = compact_summary
    record["compact_stage"] = compact_field(parsed.get("current_stage"), COMPACT_STAGE_MAX)
    record["compact_objective"] = compact_field(parsed.get("immediate_objective"), COMPACT_OBJECTIVE_MAX)
    record["compact_anchor"] = compact_field(parsed.get("next_step_anchor"), COMPACT_ANCHOR_MAX)
    hint = compact_routing_hint(str(record.get("project", root_path.name)), compact_summary, record.get("keywords", []))
    if hint:
        record["routing_hint"] = hint
    else:
        record.pop("routing_hint", None)

    for raw_field in RAW_LONG_FIELD_MAX:
        if raw_field not in existing:
            record.pop(raw_field, None)

    record["root_path"] = str(root_path)
    record["memory_path"] = str(memory_path)
    record["stage_log_path"] = str(stage_log_path)
    record["status"] = record.get("status") or record.get("retention_status") or "active"
    if record["status"] not in RETENTION_STATUSES:
        record["status"] = "active"

    memory_time = parse_iso_datetime(file_mtime_iso(memory_path))
    stage_time = parse_iso_datetime(file_mtime_iso(stage_log_path))
    observation_time = latest_observation_time(observations_path)
    commit_time = git_latest_commit_time(root_path)
    dirty = git_has_changes(root_path)
    dirty_time = parse_iso_datetime(scan_time) if dirty else None
    latest_activity = max_datetime([memory_time, stage_time, observation_time, commit_time, dirty_time])
    freshness, stale_reason = classify_freshness(memory_time, latest_activity, exists)

    record["last_scanned"] = record.get("last_scanned") or scan_time
    if exists:
        record["last_verified"] = record.get("last_verified") or scan_time
    record["verified_path_exists"] = exists
    record["memory_last_updated"] = datetime_to_iso(memory_time)
    record["stage_log_last_updated"] = datetime_to_iso(stage_time)
    record["latest_observation_ts"] = datetime_to_iso(observation_time)
    record["git_latest_commit_time"] = datetime_to_iso(commit_time)
    record["git_has_changes"] = dirty
    record["activity_state"] = classify_activity(latest_activity, exists, parse_iso_datetime(scan_time))
    record["memory_freshness"] = freshness
    if stale_reason:
        record["stale_reason"] = compact_stale_reason(stale_reason)
    else:
        record.pop("stale_reason", None)
    record["memory_hash"] = sha256_file(memory_path)
    return record


def compact_project_card(record: dict[str, Any]) -> str:
    project = record.get("project", "(unnamed)")
    summary = record.get("compact_summary") or record.get("summary") or "no summary"
    status = record.get("status", "active")
    activity = record.get("activity_state") or "unknown"
    memory_path = record.get("memory_path", "")
    freshness = record.get("memory_freshness", "unknown")
    limit = COLD_ARCHIVED_ABSOLUTE_MAX if status in {"cold", "archived"} else ACTIVE_WARM_ABSOLUTE_MAX

    if status in {"cold", "archived"}:
        card = f"- `{project}` - {summary}. Memory: `{memory_path}`."
        return enforce_card_limit(card, limit, record)

    if freshness == "stale":
        card = f"- `{project}` - {summary}. Status: {status}/{activity}; memory stale, read `{memory_path}` before project work."
        return enforce_card_limit(card, limit, record)

    parts = [f"- `{project}` - {summary}. Status: {status}/{activity}."]
    if record.get("compact_stage"):
        parts.append(f"Stage: {record['compact_stage']}.")
    if record.get("compact_objective"):
        parts.append(f"Objective: {record['compact_objective']}.")
    if record.get("compact_anchor"):
        parts.append(f"Anchor: {record['compact_anchor']}.")
    parts.append(f"Memory: `{memory_path}`.")
    card = " ".join(parts)
    return enforce_card_limit(card, limit, record)


def validate_global_card(project: str, status: str, freshness: str, card: str) -> list[str]:
    errors: list[str] = []
    limit = COLD_ARCHIVED_ABSOLUTE_MAX if status in {"cold", "archived"} else ACTIVE_WARM_ABSOLUTE_MAX
    if len(card) > limit:
        errors.append(f"{project}: global card has {len(card)} chars; max is {limit}")
    for pattern in OPERATIONAL_DETAIL_PATTERNS:
        if pattern.search(card):
            errors.append(f"{project}: global card contains operational detail pattern: {pattern.pattern}")
    if freshness == "stale" and any(marker in card for marker in ("Stage:", "Objective:", "Anchor:")):
        errors.append(f"{project}: stale project rendered detailed state fields")
    return errors


def validate_refresh_plan(old_records: list[dict[str, Any]], new_records: list[dict[str, Any]], global_text: str) -> list[str]:
    errors: list[str] = []
    old_by_project = {str(record.get("project")): record for record in old_records}
    for record in new_records:
        project = str(record.get("project", "(unnamed)"))
        status = record.get("status", "active")
        old_status = old_by_project.get(project, {}).get("status")
        if old_status is not None and old_status != status:
            errors.append(f"{project}: retention status changed from {old_status} to {status}")
        for field, limit in RAW_LONG_FIELD_MAX.items():
            if field not in old_by_project.get(project, {}) and len(str(record.get(field, ""))) > limit:
                errors.append(f"{project}: refresh newly wrote long raw field {field}")
        for field, limit in (
            ("summary", SUMMARY_MAX),
            ("compact_summary", SUMMARY_MAX),
            ("compact_stage", COMPACT_STAGE_MAX),
            ("compact_objective", COMPACT_OBJECTIVE_MAX),
            ("compact_anchor", COMPACT_ANCHOR_MAX),
            ("stale_reason", STALE_REASON_MAX),
        ):
            value = str(record.get(field, ""))
            if len(value) > limit:
                errors.append(f"{project}: {field} has {len(value)} chars; max is {limit}")
        card = compact_project_card(record)
        errors.extend(validate_global_card(project, status, str(record.get("memory_freshness", "unknown")), card))
    return errors


def render_global_memory(existing_text: str, records: list[dict[str, Any]]) -> str:
    text = existing_text
    grouped: dict[str, list[str]] = {status: [] for status in RETENTION_STATUSES}
    for record in records:
        status = record.get("status", "active")
        if status not in grouped:
            status = "active"
        grouped[status].append(compact_project_card(record))
    for status, header in PROJECT_HEADERS.items():
        text = replace_markdown_section(text, header, grouped[status] or ["- none"])
    return text


def load_index(global_root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    loaded = load_jsonl(global_root / "projects_index.jsonl")
    warnings = [f"malformed projects_index.jsonl line {line}: {error}" for line, _raw, error in loaded.malformed_lines]
    return loaded.records, warnings


def find_or_register_discovered(
    records: list[dict[str, Any]],
    discovered: list[dict[str, Any]],
    selector: str | None,
    all_projects: bool,
) -> tuple[list[dict[str, Any]], list[str], str]:
    warnings: list[str] = []
    by_root = {canonical_path_key(item.get("root_path", "")): item for item in records if item.get("root_path")}

    if all_projects:
        merged = [dict(record) for record in records]
        for project in discovered:
            root_key = canonical_path_key(project.get("root_path", ""))
            if root_key and root_key not in by_root:
                merged.append(dict(project))
                by_root[root_key] = project
        return merged, warnings, "ok"

    if selector:
        selected = [dict(record) for record in records if project_matches(record, selector)]
        if selected:
            return selected, warnings, "ok"
        discovered_match = [project for project in discovered if project_matches(project, selector)]
        if discovered_match:
            if len(discovered_match) > 1:
                warnings.append(f"project selector is ambiguous among discovered projects: {selector}")
                return [], warnings, "ambiguous_project"
            warnings.append(f"project was unregistered; targeted refresh will register it: {selector}")
            return [dict(discovered_match[0])], warnings, "ok"
        warnings.append(f"project not found: {selector}")
        return [], warnings, "not_found"

    return [dict(record) for record in records], warnings, "ok"


def build_refresh_plan(
    global_root: Path,
    project_selector: str | None = None,
    all_projects: bool = False,
    workspace_roots: list[str] | None = None,
    config_path: str | None = None,
    current_project: str | None = None,
    max_depth: int = 4,
    stamp: str | None = None,
) -> tuple[str, str, list[dict[str, Any]], list[str], list[str], str]:
    stamp = stamp or utc_now_iso()
    index_path = global_root / "projects_index.jsonl"
    global_memory_path = global_root / "global_memory.md"
    records, index_warnings = load_index(global_root)
    effective_current_project = current_project
    if project_selector and current_project is None and selector_points_to_project_root(project_selector):
        effective_current_project = project_selector
    discovered, discovery_warnings = discover_projects(
        global_root,
        current_project=effective_current_project,
        workspace_roots=workspace_roots or [],
        config_path=config_path,
        max_depth=max_depth,
    )
    discovered_records = [asdict(item) for item in discovered]
    selected, selection_warnings, selection_status = find_or_register_discovered(
        records, discovered_records, project_selector, all_projects
    )
    warnings = index_warnings + discovery_warnings + selection_warnings
    if index_warnings:
        return "", "", records, warnings, [], "malformed_index"
    if selection_status != "ok":
        return "", "", records, warnings, [], selection_status

    selected_keys = {canonical_path_key(record.get("root_path", "")) for record in selected if record.get("root_path")}
    updated_by_key = {
        canonical_path_key(record.get("root_path", "")): analyze_project(record, stamp)
        for record in selected
        if record.get("root_path")
    }
    final_records: list[dict[str, Any]] = []
    changed_projects: list[str] = []
    existing_keys: set[str] = set()
    for record in records:
        key = canonical_path_key(record.get("root_path", ""))
        if key in updated_by_key:
            updated = updated_by_key[key]
            if updated != record:
                changed_projects.append(str(updated.get("project", key)))
            final_records.append(updated)
            existing_keys.add(key)
        else:
            final_records.append(record)
    if all_projects or project_selector:
        for key, updated in updated_by_key.items():
            if key not in existing_keys:
                changed_projects.append(str(updated.get("project", key)))
                final_records.append(updated)
    elif not project_selector and not all_projects:
        # Default scope is registered projects only.
        pass

    old_index_text = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    new_index_text = "".join(json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n" for record in final_records)
    old_global_text = ensure_global_memory_text(global_memory_path)
    new_global_text = render_global_memory(old_global_text, final_records)
    validation_errors = validate_refresh_plan(records, final_records, new_global_text)
    if validation_errors:
        return new_global_text, new_index_text, final_records, warnings + validation_errors, changed_projects, "validation_failed"
    return new_global_text, new_index_text, final_records, warnings, changed_projects, "ok"


def write_report(
    report_path: Path,
    result: RefreshResult,
    global_diff: str,
    index_diff: str,
    dry_run: bool,
) -> None:
    lines = [
        "# Codex-mem Global Refresh Report",
        "",
        f"- status: {result.status}",
        f"- mode: {'apply' if not dry_run else 'dry-run'}",
        f"- global memory: {result.global_memory_path}",
        f"- projects index: {result.projects_index_path}",
        "",
        "## Changed Projects",
        "",
        *(f"- {project}" for project in result.changed_projects),
    ]
    if not result.changed_projects:
        lines.append("- none")
    lines.extend(["", "## Backups", ""])
    lines.extend([f"- {path}" for path in result.backups] or ["- none"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {warning}" for warning in result.warnings] or ["- none"])
    lines.extend(["", "## Global Memory Diff", "", "```diff", global_diff or "(no diff)", "```"])
    lines.extend(["", "## Projects Index Diff", "", "```diff", index_diff or "(no diff)", "```", ""])
    atomic_write_text(report_path, "\n".join(lines))


def run_refresh(
    global_root: Path,
    project_selector: str | None = None,
    all_projects: bool = False,
    workspace_roots: list[str] | None = None,
    config_path: str | None = None,
    current_project: str | None = None,
    max_depth: int = 4,
    apply: bool = False,
    stamp: str | None = None,
) -> RefreshResult:
    stamp = stamp or utc_now_iso().replace(":", "-")
    global_root.mkdir(parents=True, exist_ok=True)
    global_memory_path = global_root / "global_memory.md"
    projects_index_path = global_root / "projects_index.jsonl"
    old_global_text = ensure_global_memory_text(global_memory_path)
    old_index_text = projects_index_path.read_text(encoding="utf-8") if projects_index_path.exists() else ""
    new_global_text, new_index_text, _records, warnings, changed_projects, plan_status = build_refresh_plan(
        global_root,
        project_selector=project_selector,
        all_projects=all_projects,
        workspace_roots=workspace_roots or [],
        config_path=config_path,
        current_project=current_project,
        max_depth=max_depth,
        stamp=stamp,
    )
    if plan_status != "ok":
        return RefreshResult(
            status=plan_status,
            global_changed=False,
            index_changed=False,
            global_memory_path=str(global_memory_path),
            projects_index_path=str(projects_index_path),
            report_path="",
            backups=[],
            warnings=warnings,
            changed_projects=[],
            modified_files=[],
        )

    global_changed = old_global_text != new_global_text
    index_changed = old_index_text != new_index_text
    backups: list[str] = []
    modified_files: list[str] = []
    report_path = ""
    if apply:
        backup_dir = global_root / "backups" / f"refresh-{stamp}"
        for path in (global_memory_path, projects_index_path):
            backup = backup_file(path, backup_dir, f"pre-refresh-{stamp}")
            if backup:
                backups.append(str(backup))
                modified_files.append(str(backup))
        if global_changed:
            atomic_write_text(global_memory_path, new_global_text)
            modified_files.append(str(global_memory_path))
        if index_changed:
            atomic_write_text(projects_index_path, new_index_text)
            modified_files.append(str(projects_index_path))
        report_dir = global_root / "refresh_reports"
        report_path_obj = report_dir / f"refresh-{stamp}.md"
        result = RefreshResult(
            status="success",
            global_changed=global_changed,
            index_changed=index_changed,
            global_memory_path=str(global_memory_path),
            projects_index_path=str(projects_index_path),
            report_path=str(report_path_obj),
            backups=backups,
            warnings=warnings,
            changed_projects=changed_projects,
            modified_files=modified_files + [str(report_path_obj)],
        )
        write_report(
            report_path_obj,
            result,
            unified_diff(old_global_text, new_global_text, "global_memory.md.before", "global_memory.md.after"),
            unified_diff(old_index_text, new_index_text, "projects_index.jsonl.before", "projects_index.jsonl.after"),
            dry_run=False,
        )
        report_path = str(report_path_obj)
        modified_files.append(report_path)
    return RefreshResult(
        status="success",
        global_changed=global_changed,
        index_changed=index_changed,
        global_memory_path=str(global_memory_path),
        projects_index_path=str(projects_index_path),
        report_path=report_path,
        backups=backups,
        warnings=warnings,
        changed_projects=changed_projects,
        modified_files=modified_files,
    )


def update_retention_status(global_root: Path, project: str, status: str, stamp: str | None = None) -> RefreshResult:
    if status not in RETENTION_STATUSES:
        raise SystemExit(f"Invalid retention status: {status}")
    index_path = global_root / "projects_index.jsonl"
    loaded = load_jsonl(index_path)
    if loaded.malformed_lines:
        raise SystemExit(f"Cannot update retention with malformed projects_index.jsonl: {index_path}")
    found = False
    records = []
    for record in loaded.records:
        updated = dict(record)
        if str(updated.get("project", "")).casefold() == project.casefold():
            updated["status"] = status
            found = True
        records.append(updated)
    if not found:
        raise SystemExit(f"Project not found in projects_index.jsonl: {project}")
    backup_dir = global_root / "backups" / f"retention-{stamp or utc_now_iso().replace(':', '-')}"
    backup = backup_file(index_path, backup_dir, "pre-retention")
    write_jsonl(index_path, records)
    return run_refresh(global_root, project_selector=project, apply=True, stamp=stamp)


def main() -> None:
    configure_utf8_stdio()
    args = parse_args()
    result = run_refresh(
        Path(args.global_memory_root),
        project_selector=args.project,
        all_projects=args.all_projects,
        workspace_roots=args.workspace_root,
        config_path=args.config,
        current_project=args.current_project,
        max_depth=args.max_depth,
        apply=args.apply,
    )
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return
    mode = "apply" if args.apply else "dry-run"
    print(f"status: {result.status}")
    print(f"mode: {mode}")
    print(f"global_changed: {result.global_changed}")
    print(f"index_changed: {result.index_changed}")
    if result.report_path:
        print(f"report: {result.report_path}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    if result.status != "success":
        raise SystemExit(2)


if __name__ == "__main__":
    main()

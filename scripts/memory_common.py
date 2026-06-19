#!/usr/bin/env python3
"""Shared helpers for Codex-mem scripts.

The helpers intentionally use only the Python standard library so the skill can
run in a minimal local environment.
"""

from __future__ import annotations

import hashlib
import json
import ntpath
import os
import posixpath
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RETENTION_STATUSES = ("active", "warm", "cold", "archived")
ACTIVITY_STATES = ("hot", "recent", "idle", "missing")
FRESHNESS_STATES = ("fresh", "stale", "unknown")

IGNORE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".cache",
    "__pycache__",
    "node_modules",
    "venv",
    "env",
    "dist",
    "build",
    "out",
    "target",
    "tmp",
    "temp",
    "$recycle.bin",
    "system volume information",
    ".trash",
}

KNOWN_PROVENANCE = {
    "human",
    "codex",
    "claude",
    "antigravity",
    "native-codex-memory",
    "native-claude-memory",
    "chronicle",
    "external-tool",
}

PROVENANCE_ALIASES = {
    "user": "human",
    "person": "human",
    "openai-codex": "codex",
    "codex.ai": "codex",
    "codex-cli": "codex",
    "cc": "claude",
    "claude-code": "claude",
    "claude code": "claude",
    "anthropic-claude": "claude",
    "ag": "antigravity",
    "antigravity-worker": "antigravity",
    "codex-native-memory": "native-codex-memory",
    "claude-auto-memory": "native-claude-memory",
    "claude-native-memory": "native-claude-memory",
}


@dataclass(frozen=True)
class JsonlLoad:
    records: list[dict[str, Any]]
    malformed_lines: list[tuple[int, str, str]]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_is_windows_style(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z]:[\\/]", value)) or "\\" in value


def canonical_path_key(value: str | Path) -> str:
    """Return a stable comparison key for Windows or POSIX-like paths."""

    raw = str(value).strip().strip('"')
    if not raw:
        return ""
    if path_is_windows_style(raw):
        normalized = ntpath.normpath(raw.replace("/", "\\"))
        return ntpath.normcase(normalized)
    normalized = posixpath.normpath(raw.replace("\\", "/"))
    return normalized.casefold()


def resolved_path_key(path: str | Path) -> str:
    candidate = Path(path)
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate.absolute()
    return canonical_path_key(resolved)


def git_root_for(path: str | Path) -> Path | None:
    candidate = Path(path)
    if candidate.is_file():
        candidate = candidate.parent
    try:
        candidate = candidate.resolve()
    except OSError:
        candidate = candidate.absolute()
    for current in (candidate, *candidate.parents):
        git_marker = current / ".git"
        if git_marker.exists():
            return current
    return None


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime_to_iso(datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc))


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.tmp.", dir=str(path.parent), text=True)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def backup_file(path: Path, backup_dir: Path, label: str) -> Path | None:
    if not path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{path.name}.{label}.bak"
    shutil.copy2(path, backup_path)
    return backup_path


def backup_tree(root: Path, backup_parent: Path, label: str) -> Path:
    backup_parent.mkdir(parents=True, exist_ok=True)
    target = backup_parent / f"{root.name}.{label}.bak"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(root, target)
    return target


def normalize_provenance(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    lower = text.casefold()
    if lower in KNOWN_PROVENANCE:
        return lower
    if lower in PROVENANCE_ALIASES:
        return PROVENANCE_ALIASES[lower]
    return text


def detect_provenance_markers(text: str) -> set[str]:
    found: set[str] = set()
    if "[AG]" in text:
        found.add("antigravity")
    if "[CC]" in text:
        found.add("claude")
    return found


def load_jsonl(path: Path) -> JsonlLoad:
    if not path.exists():
        return JsonlLoad([], [])
    records: list[dict[str, Any]] = []
    malformed: list[tuple[int, str, str]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            malformed.append((line_number, raw_line, str(exc)))
            continue
        if isinstance(parsed, dict):
            records.append(parsed)
        else:
            malformed.append((line_number, raw_line, "JSONL record is not an object"))
    return JsonlLoad(records, malformed)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    text = "".join(json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n" for record in records)
    atomic_write_text(path, text)


def parse_markdown_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return sections


def clean_field_value(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1].strip()
    return text


def find_field(lines: list[str], field: str) -> str:
    pattern = re.compile(rf"^\s*-\s*{re.escape(field)}\s*:\s*(.*)$", re.IGNORECASE)
    for line in lines:
        match = pattern.match(line)
        if match:
            return clean_field_value(match.group(1))
    return ""


def first_meaningful_bullet(lines: list[str]) -> str:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- ") and stripped != "- none":
            return stripped[2:].strip()
    return ""


def parse_project_memory(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    sections = parse_markdown_sections(text)
    identity = sections.get("Project Identity", [])
    state = sections.get("Current Operating State", [])
    anchor = sections.get("Next-Step Anchor", [])
    return {
        "project": find_field(identity, "project"),
        "summary": find_field(identity, "summary") or find_field(identity, "scope"),
        "current_stage": find_field(state, "current stage"),
        "immediate_objective": find_field(state, "immediate working objective"),
        "active_stopping_rule": find_field(state, "active stopping rule"),
        "next_step_anchor": first_meaningful_bullet(anchor),
    }


def latest_observation_time(path: Path) -> datetime | None:
    loaded = load_jsonl(path)
    latest: datetime | None = None
    for record in loaded.records:
        parsed = parse_iso_datetime(record.get("ts"))
        if parsed and (latest is None or parsed > latest):
            latest = parsed
    return latest


def classify_activity(latest_activity: datetime | None, exists: bool, now: datetime | None = None) -> str:
    if not exists:
        return "missing"
    if latest_activity is None:
        return "idle"
    now = now or datetime.now(timezone.utc)
    age_days = max(0.0, (now - latest_activity.astimezone(timezone.utc)).total_seconds() / 86400)
    if age_days <= 2:
        return "hot"
    if age_days <= 30:
        return "recent"
    return "idle"


def classify_freshness(memory_time: datetime | None, latest_activity: datetime | None, exists: bool) -> tuple[str, str]:
    if not exists or memory_time is None:
        return "unknown", "canonical memory missing or unavailable"
    if latest_activity and latest_activity > memory_time:
        return "stale", "project activity is newer than canonical project memory"
    return "fresh", ""


def compact_update_report(
    updated: list[str],
    preserved: list[str],
    current_anchor: str,
    needs_review: list[str] | None = None,
) -> str:
    lines = ["## Memory Updated", ""]
    lines.extend(updated or ["- none"])
    lines.extend(["", "## Preserved / Not Changed", ""])
    lines.extend(preserved or ["- none"])
    lines.extend(["", "## Current Anchor", "", current_anchor or "- not recorded"])
    if needs_review:
        lines.extend(["", "## Needs Review", ""])
        lines.extend(needs_review)
    return "\n".join(lines).rstrip() + "\n"

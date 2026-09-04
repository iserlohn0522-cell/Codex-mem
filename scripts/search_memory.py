#!/usr/bin/env python3
"""Search lean Codex-mem project files with substring matching."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from memory_common import load_jsonl, parse_iso_datetime


HISTORY_TERMS = (
    "以前",
    "上次",
    "曾经",
    "历史",
    "失败",
    "为什么不用",
    "之前",
    "prior",
    "previous",
    "history",
    "historical",
    "failed",
    "rejected",
    "why not",
)
DEEP_HISTORY_TERMS = (
    "完整历史",
    "全部历史",
    "很久以前",
    "最早",
    "deep history",
    "full history",
    "earliest",
)
SUPERSEDED_TERMS = (
    "取代",
    "被替代",
    "冲突",
    "来源",
    "superseded",
    "conflict",
    "provenance",
)
CURRENT_HEADING_PRIORITY = {
    "Current Operating State": 0,
    "Protected Human Decisions": 1,
    "Next-Step Anchor": 2,
    "Unresolved Issues": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="Project root directory.")
    parser.add_argument("--query", required=True, help="Case-insensitive search query.")
    parser.add_argument(
        "--history",
        choices=["auto", "none", "recent", "all"],
        default="auto",
        help="Historical retrieval scope. Default detects explicit historical intent.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum results to return (1-20, default 5).",
    )
    return parser.parse_args()


def search_text(
    path: Path,
    query: str,
    source_type: str = "canonical",
) -> list[dict[str, str]]:
    if not path.exists():
        return []
    hits: list[dict[str, str]] = []
    heading = ""
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("## "):
            heading = line[3:].strip()
        elif line.startswith("### ") and source_type == "stage_log":
            heading = line[4:].strip()
        if query in line.lower():
            hits.append(
                {
                    "source": str(path),
                    "line": str(line_number),
                    "text": line.strip(),
                    "source_type": source_type,
                    "heading": heading,
                    "age_band": "timeless" if source_type == "canonical" else "unspecified",
                    "status": "current" if source_type == "canonical" else "historical",
                    "retrieval_stage": (
                        "canonical_current"
                        if source_type == "canonical"
                        else "stage_history"
                    ),
                }
            )
    return hits


def observation_age_band(record: dict[str, object], now: datetime) -> str:
    parsed = parse_iso_datetime(record.get("ts"))
    if parsed is None:
        return "unknown"
    age_days = max(0.0, (now - parsed).total_seconds() / 86400)
    if age_days <= 30:
        return "recent"
    if age_days <= 90:
        return "quiet"
    if age_days <= 180:
        return "historical"
    return "deep_history"


def superseded_ids(records: list[dict[str, object]]) -> set[str]:
    superseded: set[str] = set()
    for record in records:
        value = record.get("supersedes")
        if isinstance(value, str) and value.strip():
            superseded.add(value.strip())
        elif isinstance(value, list):
            superseded.update(str(item).strip() for item in value if str(item).strip())
    return superseded


def search_observations(
    path: Path,
    query: str,
    warnings: list[str] | None = None,
    allowed_age_bands: set[str] | None = None,
    include_superseded: bool = False,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    if not path.exists():
        return []
    hits: list[dict[str, str]] = []
    loaded = load_jsonl(path)
    if loaded.malformed_lines and warnings is not None:
        line_numbers = ", ".join(str(line) for line, _raw, _error in loaded.malformed_lines)
        warnings.append(
            f"{path}: skipped {len(loaded.malformed_lines)} malformed JSONL line(s): {line_numbers}"
        )
    now = now or datetime.now(timezone.utc)
    superseded = superseded_ids(loaded.records)
    for line_number, record in loaded.record_lines:
        record_id = str(record.get("id", "")).strip()
        is_superseded = record_id in superseded
        if is_superseded and not include_superseded:
            continue
        age_band = observation_age_band(record, now)
        if allowed_age_bands is not None and age_band not in allowed_age_bands:
            continue
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
                    "text": str(record.get("title", "")),
                    "source_type": "observation",
                    "heading": str(record.get("kind", "")),
                    "age_band": age_band,
                    "status": "superseded" if is_superseded else str(record.get("kind", "")),
                    "retrieval_stage": f"observation_{age_band}",
                }
            )
    return hits


def history_scope(query: str, requested: str) -> str:
    if requested == "none":
        return "none"
    if requested == "recent":
        return "recent"
    if requested == "all":
        return "deep"
    if any(term in query for term in DEEP_HISTORY_TERMS):
        return "deep"
    if any(term in query for term in HISTORY_TERMS):
        return "historical"
    return "none"


def sort_canonical_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        hits,
        key=lambda item: (
            CURRENT_HEADING_PRIORITY.get(item.get("heading", ""), 10),
            int(item["line"]),
        ),
    )


def append_unique(
    target: list[dict[str, str]],
    candidates: list[dict[str, str]],
    limit: int,
) -> None:
    seen = {(item["source"], item["line"]) for item in target}
    for item in candidates:
        key = (item["source"], item["line"])
        if key in seen:
            continue
        target.append(item)
        seen.add(key)
        if len(target) >= limit:
            return


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    query = args.query.lower()
    limit = min(20, max(1, args.limit))
    mem_dir = root / ".codex-mem"

    results = sort_canonical_hits(
        search_text(root / "project_memory.md", query, "canonical")
    )
    results = results[:limit]
    warnings: list[str] = []
    scope = history_scope(query, args.history)
    if scope != "none" and len(results) < limit:
        append_unique(
            results,
            search_text(root / "project_stage_log.md", query, "stage_log"),
            limit,
        )
    if scope != "none" and len(results) < limit:
        age_cascade = [{"recent"}]
        if scope in {"historical", "deep"}:
            age_cascade.extend([{"quiet"}, {"historical"}])
        if scope == "deep":
            age_cascade.extend([{"deep_history"}, {"unknown"}])
        include_superseded = (
            scope == "deep"
            or any(term in query for term in SUPERSEDED_TERMS)
        )
        for age_bands in age_cascade:
            append_unique(
                results,
                search_observations(
                    mem_dir / "observations.jsonl",
                    query,
                    warnings,
                    allowed_age_bands=age_bands,
                    include_superseded=include_superseded,
                ),
                limit,
            )
            if len(results) >= limit:
                break

    print(json.dumps(results, indent=2, ensure_ascii=False))
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()

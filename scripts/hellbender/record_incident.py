#!/usr/bin/env python3
"""Append one Hellbender incident to a project run-artifact JSONL file."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INCIDENT_STATUSES = (
    "success",
    "failed",
    "stopped",
    "unresolved",
    "open",
    "retried",
    "resolved",
    "not-retried",
)
CAUSE_STATUSES = ("confirmed", "likely", "unknown", "not-applicable")
PROTECTED_MEMORY_NAMES = {
    "project_memory.md",
    "project_stage_log.md",
    "observations.jsonl",
    ".hellbender-project-memory.md",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def validate_log_path(log_path: Path) -> None:
    if log_path.name.casefold() in {name.casefold() for name in PROTECTED_MEMORY_NAMES}:
        raise ValueError(
            f"Incident records are run artifacts, not memory; refusing log path: {log_path}"
        )


def append_incident(log_path: Path, record: dict[str, Any]) -> None:
    validate_log_path(log_path)
    existing = log_path.read_text(encoding="utf-8-sig") if log_path.exists() else ""
    if existing and not existing.endswith("\n"):
        existing += "\n"
    atomic_write_text(
        log_path,
        existing + json.dumps(record, ensure_ascii=False, sort_keys=False) + "\n",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, help="Project run-artifact JSONL path.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--system", required=True)
    parser.add_argument("--calculation-type", required=True)
    parser.add_argument("--incident-status", required=True, choices=INCIDENT_STATUSES)
    parser.add_argument("--failure-stage", required=True)
    parser.add_argument("--symptom", required=True)
    parser.add_argument("--cause-status", required=True, choices=CAUSE_STATUSES)
    parser.add_argument("--cause")
    parser.add_argument("--timestamp", help="Explicit ISO timestamp; defaults to current UTC.")
    parser.add_argument("--job-id")
    parser.add_argument("--retry-action")
    parser.add_argument("--workdir")
    parser.add_argument("--input-signature")
    parser.add_argument("--resource-request")
    parser.add_argument("--stderr-hint")
    parser.add_argument("--lesson-candidate")
    parser.add_argument("--evidence-path", action="append", default=[])
    parser.add_argument("--notes")
    return parser.parse_args()


def record_from_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.cause_status == "confirmed" and not args.cause:
        raise ValueError("--cause is required when --cause-status is confirmed")
    record: dict[str, Any] = {
        "timestamp": args.timestamp or utc_now_iso(),
        "project": args.project,
        "system": args.system,
        "calculation_type": args.calculation_type,
        "incident_status": args.incident_status,
        "failure_stage": args.failure_stage,
        "symptom": args.symptom,
        "cause_status": args.cause_status,
    }
    optional = {
        "job_id": args.job_id,
        "cause": args.cause,
        "retry_action": args.retry_action,
        "workdir": args.workdir,
        "input_signature": args.input_signature,
        "resource_request": args.resource_request,
        "stderr_hint": args.stderr_hint,
        "lesson_candidate": args.lesson_candidate,
        "evidence_paths": args.evidence_path or None,
        "notes": args.notes,
    }
    record.update({key: value for key, value in optional.items() if value not in (None, [], "")})
    return record


def main() -> None:
    args = parse_args()
    try:
        record = record_from_args(args)
        log_path = Path(args.log)
        append_incident(log_path, record)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Appended Hellbender incident artifact: {log_path}")


if __name__ == "__main__":
    main()

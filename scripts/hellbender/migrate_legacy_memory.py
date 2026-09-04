#!/usr/bin/env python3
"""Create a read-only plan for legacy Hellbender memory migration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {"keep", "merge", "promote", "demote", "supersede", "forget", "blocked"}
ALLOWED_SOURCE_KINDS = {"project", "shared"}
ALLOWED_AUTHORITIES = {
    "canonical-root",
    "legacy-read-only",
    "worktree-support",
    "legacy-support",
}
PROTECTED_STATUS_RE = re.compile(
    r"\b(STOPPED|UNRESOLVED|FAILED|NOT_EVALUATED|NOT_DETECTED|"
    r"negative|null|inconclusive|blocked|held|timeout|pending)\b",
    re.IGNORECASE,
)
RUN_DETAIL_PATTERNS = (
    ("job-id", re.compile(r"\b(?:job(?:\s+id)?\s*[:#]?\s*)\d{6,}\b", re.IGNORECASE)),
    ("long-numeric-id-review", re.compile(r"\b\d{7,10}\b")),
    ("timestamp", re.compile(r"\b20\d{2}-\d{2}-\d{2}(?:[T ][0-9:.+-Z]+)?\b")),
    ("sha256", re.compile(r"\b[a-fA-F0-9]{64}\b")),
    ("absolute-path", re.compile(r"(?:[A-Za-z]:\\|/home/|/scratch/|/data/|/tmp/)")),
)
SCIENCE_RE = re.compile(
    r"\b(?:eV|Ha|energy|force|SCF|METHOD_LOCK|POTCAR|WAVECAR|"
    r"scientific acceptance|adsorption|geometry|spin)\b",
    re.IGNORECASE,
)
PRIVATE_RE = re.compile(
    r"\b(?:private key|identity file|credential|token|password|ssh alias)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceSpec:
    source_path: str
    source_kind: str
    authority: str
    project_root: str = ""
    destination_root: str = ""
    note: str = ""


@dataclass
class Candidate:
    candidate_id: str
    normalized_proposition: str
    canonical_source: str
    source_path: str
    source_sha256: str
    line_start: int
    line_end: int
    source_section: str
    project_root: str
    current_layer: str
    proposed_layer: str
    action: str
    reason: str
    destination_or_witness: str
    conflicts: list[str]
    approval_need: str
    flags: list[str]
    proposition_hash: str
    exact_duplicate_count: int = 1


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def normalize_proposition(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def comparison_key(text: str) -> str:
    return normalize_proposition(text).casefold()


def parse_legacy_blocks(path: Path) -> list[tuple[str, int, int, str]]:
    """Return section, line start/end, and one bullet or paragraph per block."""

    lines = path.read_text(encoding="utf-8-sig").splitlines()
    section = "Preamble"
    subsection = ""
    blocks: list[tuple[str, int, int, str]] = []
    current_lines: list[str] = []
    current_start = 0

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_start
        if not current_lines:
            return
        cleaned = list(current_lines)
        cleaned[0] = re.sub(r"^\s*[-*]\s+", "", cleaned[0])
        text = normalize_proposition(" ".join(line.strip() for line in cleaned if line.strip()))
        if text:
            label = section if not subsection else f"{section} / {subsection}"
            blocks.append((label, current_start, end_line, text))
        current_lines = []
        current_start = 0

    for number, line in enumerate(lines, start=1):
        if line.startswith("## "):
            flush(number - 1)
            section = line[3:].strip()
            subsection = ""
            continue
        if line.startswith("### "):
            flush(number - 1)
            subsection = line[4:].strip()
            continue
        if line.startswith("# "):
            flush(number - 1)
            continue
        if re.match(r"^\s*[-*]\s+\S", line):
            flush(number - 1)
            current_start = number
            current_lines = [line]
            continue
        if not line.strip():
            flush(number - 1)
            continue
        if current_lines:
            current_lines.append(line)
        else:
            current_start = number
            current_lines = [line]
    flush(len(lines))
    return blocks


def load_scope(scope_path: Path) -> tuple[dict[str, Any], list[SourceSpec]]:
    data = json.loads(scope_path.read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != "1.0":
        raise ValueError("scope schema_version must be 1.0")
    if not data.get("candidate_prefix") or not data.get("as_of"):
        raise ValueError("scope requires candidate_prefix and deterministic as_of")
    raw_sources = data.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValueError("scope requires a non-empty sources list")
    sources: list[SourceSpec] = []
    for raw in raw_sources:
        spec = SourceSpec(**raw)
        if spec.source_kind not in ALLOWED_SOURCE_KINDS:
            raise ValueError(f"unsupported source_kind: {spec.source_kind}")
        if spec.authority not in ALLOWED_AUTHORITIES:
            raise ValueError(f"unsupported authority: {spec.authority}")
        if spec.source_kind == "project" and not spec.destination_root:
            raise ValueError(f"project source requires destination_root: {spec.source_path}")
        if Path(spec.source_path).name.casefold() == "private-access.md":
            raise ValueError("private-access.md must never be a migration source")
        sources.append(spec)
    return data, sources


def detect_flags(text: str) -> list[str]:
    flags: list[str] = []
    if PROTECTED_STATUS_RE.search(text):
        flags.append("protected-adverse-or-held-status")
    if "[CC]" in text:
        flags.append("claude-provenance")
    if "[AG]" in text:
        flags.append("antigravity-provenance")
    for name, pattern in RUN_DETAIL_PATTERNS:
        if pattern.search(text):
            flags.append(name)
    if SCIENCE_RE.search(text):
        flags.append("scientific-content-review")
    if PRIVATE_RE.search(text):
        flags.append("private-access-review")
    return flags


def project_destination(section: str, destination_root: Path) -> tuple[str, Path]:
    lower = section.casefold()
    if "project scope" in lower or "project identity" in lower:
        return "project-only:Project Identity", destination_root / "project_memory.md"
    if any(token in lower for token in ("stable submission", "constraint", "exclusion")):
        return "project-only:Durable Constraints", destination_root / "project_memory.md"
    if any(token in lower for token in ("resource", "heuristic", "known-good", "launcher")):
        return "project-only:Durable Decisions", destination_root / "project_memory.md"
    if any(token in lower for token in ("failure", "failed", "fix", "retry", "do not repeat")):
        return "project-only:Rejected Routes or Unresolved Issues", destination_root / "project_memory.md"
    if "current" in lower or "status" in lower:
        return "project-only:Current Operating State", destination_root / "project_memory.md"
    if "next" in lower:
        return "project-only:Next-Step Anchor", destination_root / "project_memory.md"
    if any(token in lower for token in ("history", "job", "incident", "run log")):
        return "support-artifact", destination_root
    return "blocked:manual section adjudication", destination_root / "project_memory.md"


def shared_destination(
    section: str,
    module_root: Path,
    dg04_path: Path,
) -> tuple[str, Path]:
    lower = section.casefold()
    if "partition" in lower or "official" in lower:
        return "module-reference", module_root / "official-rules.md"
    if "environment" in lower or "access" in lower:
        return "module-reference", module_root / "router.md"
    if "shared operational" in lower or "failure" in lower:
        return "deep-triggered", dg04_path
    if "exclusion" in lower or "memory" in lower:
        return "module-reference", module_root / "memory-routing.md"
    return "blocked:manual shared adjudication", dg04_path


def destination_contains(destination: Path, proposition: str) -> bool:
    if not destination.is_file() or len(comparison_key(proposition)) < 32:
        return False
    destination_key = comparison_key(destination.read_text(encoding="utf-8-sig"))
    return comparison_key(proposition) in destination_key


def classify_candidate(
    prefix: str,
    spec: SourceSpec,
    source_sha: str,
    section: str,
    line_start: int,
    line_end: int,
    proposition: str,
    module_root: Path,
    dg04_path: Path,
) -> Candidate:
    flags = detect_flags(proposition)
    conflicts: list[str] = []
    if spec.source_kind == "shared":
        proposed_layer, destination = shared_destination(section, module_root, dg04_path)
        current_layer = "legacy-hellbender-shared"
        action = "merge"
        reason = "Review and normalize legacy shared guidance into one on-demand module or DG-04 destination."
        approval = "required before destination write or legacy retirement"
    else:
        destination_root = Path(spec.destination_root)
        proposed_layer, destination = project_destination(section, destination_root)
        current_layer = "legacy-hellbender-project"
        action = "merge"
        reason = "Review one proposition against the designated project authority before destination-first merge."
        approval = "required before canonical write or legacy retirement"
        canonical_exists = (destination_root / "project_memory.md").is_file()
        stage_exists = (destination_root / "project_stage_log.md").is_file()
        if spec.authority == "worktree-support":
            action = "blocked"
            reason = "A worktree support copy cannot establish project truth."
            conflicts.append("worktree source is non-authoritative until matched to the project root")
        elif spec.authority == "legacy-read-only":
            action = "blocked"
            reason = "The source project is read-only legacy evidence; active-authority review is required."
            conflicts.append("legacy source cannot authorize writes to the active destination")
        elif not canonical_exists or not stage_exists:
            action = "blocked"
            reason = "The designated destination lacks the complete canonical project-memory pair."
            conflicts.append("missing project_memory.md or project_stage_log.md")
        elif proposed_layer.startswith("blocked:"):
            action = "blocked"
            reason = "The legacy section has no safe deterministic canonical mapping."
            conflicts.append("manual destination-section adjudication required")
        elif proposed_layer == "support-artifact":
            action = "keep"
            reason = "Run-specific history remains an artifact; durable memory may contain only a compact pointer."

    sensitive_flags = {
        "job-id",
        "long-numeric-id-review",
        "timestamp",
        "sha256",
        "absolute-path",
        "scientific-content-review",
        "private-access-review",
    }
    if action == "merge" and sensitive_flags.intersection(flags):
        action = "blocked"
        reason = "The proposition mixes durable guidance with run-specific, scientific, or private detail."
        conflicts.append("manual split required; retain the exact source witness")

    if action == "merge" and destination_contains(destination, proposition):
        action = "supersede"
        reason = "The exact normalized proposition is already present at the proposed destination."
        approval = "required before legacy retirement"

    proposition_hash = sha256_bytes(comparison_key(proposition).encode("utf-8"))
    identity = (
        f"{comparison_key(spec.source_path)}|{source_sha}|{line_start}|{line_end}|"
        f"{section}|{comparison_key(proposition)}"
    )
    candidate_id = f"{prefix}-{sha256_bytes(identity.encode('utf-8'))[:12].upper()}"
    if action not in ALLOWED_ACTIONS:
        raise AssertionError(f"invalid action: {action}")
    return Candidate(
        candidate_id=candidate_id,
        normalized_proposition=proposition,
        canonical_source=f"{spec.source_path}:{line_start}-{line_end}",
        source_path=spec.source_path,
        source_sha256=source_sha,
        line_start=line_start,
        line_end=line_end,
        source_section=section,
        project_root=spec.project_root,
        current_layer=current_layer,
        proposed_layer=proposed_layer,
        action=action,
        reason=reason,
        destination_or_witness=str(destination),
        conflicts=conflicts,
        approval_need=approval,
        flags=flags,
        proposition_hash=proposition_hash,
    )


def escape_table(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ")


def build_preview(
    scope: dict[str, Any],
    inventories: list[dict[str, Any]],
    candidates: list[Candidate],
    duplicate_source_groups: list[list[str]],
) -> str:
    action_counts = Counter(candidate.action for candidate in candidates)
    layer_counts = Counter(candidate.proposed_layer for candidate in candidates)
    blocked_reason_counts = Counter(
        candidate.reason for candidate in candidates if candidate.action == "blocked"
    )
    duplicate_proposition_groups = len(
        {
            candidate.proposition_hash
            for candidate in candidates
            if candidate.exact_duplicate_count > 1
        }
    )
    lines = [
        "# Hellbender Legacy Memory Migration Dry Run",
        "",
        f"- candidate: `{scope['candidate_prefix']}`",
        f"- as of: `{scope['as_of']}`",
        "- mode: read-only dry-run",
        "- canonical writes: 0",
        "- legacy-source writes: 0",
        "- private-access files read: 0",
        f"- source files: {len(inventories)}",
        f"- proposition candidates: {len(candidates)}",
        f"- exact duplicate proposition groups: {duplicate_proposition_groups}",
        "",
        "## Disposition Summary",
        "",
        "| Action | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| `{action}` | {count} |" for action, count in sorted(action_counts.items()))
    lines.extend(
        [
            "",
            "## Proposed Layer Summary",
            "",
            "| Proposed layer | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| `{escape_table(layer)}` | {count} |" for layer, count in sorted(layer_counts.items()))
    lines.extend(
        [
            "",
            "## Blocking Reason Summary",
            "",
            "| Reason | Count |",
            "| --- | ---: |",
        ]
    )
    if blocked_reason_counts:
        lines.extend(
            f"| {escape_table(reason)} | {count} |"
            for reason, count in sorted(
                blocked_reason_counts.items(),
                key=lambda item: (-item[1], item[0]),
            )
        )
    else:
        lines.append("| none | 0 |")
    lines.extend(
        [
            "",
            "## Source Inventory",
            "",
            "| Source | Authority | SHA-256 | Candidates | Destination state |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    for item in inventories:
        destination_state = item.get("destination_state", "n/a")
        lines.append(
            f"| `{escape_table(item['source_path'])}` | `{item['authority']}` | "
            f"`{item['sha256']}` | {item['candidate_count']} | {escape_table(destination_state)} |"
        )
    lines.extend(["", "## Exact Duplicate Source Groups", ""])
    if duplicate_source_groups:
        for group in duplicate_source_groups:
            lines.append(f"- {len(group)} byte-identical sources:")
            lines.extend(f"  - `{path}`" for path in group)
    else:
        lines.append("- none")
    blocked = [candidate for candidate in candidates if candidate.action == "blocked"]
    lines.extend(["", "## Blocking Preview", ""])
    if blocked:
        for candidate in blocked[:30]:
            lines.append(
                f"- `{candidate.candidate_id}` — {candidate.reason} "
                f"Source: `{candidate.canonical_source}`"
            )
        if len(blocked) > 30:
            lines.append(f"- … {len(blocked) - 30} additional blocked rows are retained in the JSONL ledger.")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Apply Boundary",
            "",
            "This dry run does not authorize or perform canonical-memory edits, DG-04 edits, "
            "legacy-file retirement, installed-skill deployment, Git commit/push, SSH, "
            "submission, retry, cancellation, cleanup, publication, or transfer.",
            "",
        ]
    )
    return "\n".join(lines)


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_output_location(
    output_dir: Path,
    sources: list[SourceSpec],
    module_root: Path,
    dg04_path: Path,
) -> None:
    forbidden_roots = {module_root.resolve(), dg04_path.parent.resolve()}
    for spec in sources:
        if spec.project_root:
            forbidden_roots.add(Path(spec.project_root).resolve())
        if spec.destination_root:
            forbidden_roots.add(Path(spec.destination_root).resolve())
        if spec.source_kind == "shared":
            forbidden_roots.add(Path(spec.source_path).parent.resolve())
    resolved_output = output_dir.resolve()
    for root in forbidden_roots:
        if path_is_within(resolved_output, root):
            raise ValueError(
                f"output directory must be outside every source/destination authority: {output_dir}"
            )


def run_plan(scope_path: Path, output_dir: Path) -> dict[str, Any]:
    scope, sources = load_scope(scope_path)
    module_root = Path(scope["module_root"])
    dg04_path = Path(scope["dg04_path"])
    prefix = scope["candidate_prefix"]
    validate_output_location(output_dir, sources, module_root, dg04_path)

    tracked_paths: list[Path] = [scope_path, dg04_path]
    tracked_paths.extend(Path(spec.source_path) for spec in sources)
    tracked_paths.extend(module_root / name for name in (
        "router.md",
        "memory-routing.md",
        "official-rules.md",
        "failure-taxonomy.md",
        "resource-templates.md",
        "incident-schema.md",
    ))
    before_hashes = {
        str(path): sha256_file(path)
        for path in tracked_paths
        if path.is_file()
    }

    inventories: list[dict[str, Any]] = []
    candidates: list[Candidate] = []
    source_hash_groups: dict[str, list[str]] = defaultdict(list)
    for spec in sources:
        source_path = Path(spec.source_path)
        if not source_path.is_file():
            raise ValueError(f"source file does not exist: {source_path}")
        source_sha = sha256_file(source_path)
        source_hash_groups[source_sha].append(spec.source_path)
        blocks = parse_legacy_blocks(source_path)
        start = len(candidates)
        for section, line_start, line_end, proposition in blocks:
            candidates.append(
                classify_candidate(
                    prefix,
                    spec,
                    source_sha,
                    section,
                    line_start,
                    line_end,
                    proposition,
                    module_root,
                    dg04_path,
                )
            )
        destination_state = "n/a"
        if spec.source_kind == "project":
            destination_root = Path(spec.destination_root)
            canonical_exists = (destination_root / "project_memory.md").is_file()
            stage_exists = (destination_root / "project_stage_log.md").is_file()
            destination_state = (
                "canonical pair present"
                if canonical_exists and stage_exists
                else "canonical pair incomplete"
            )
        inventories.append(
            {
                **asdict(spec),
                "sha256": source_sha,
                "bytes": source_path.stat().st_size,
                "candidate_count": len(candidates) - start,
                "destination_state": destination_state,
            }
        )

    proposition_counts = Counter(candidate.proposition_hash for candidate in candidates)
    for candidate in candidates:
        candidate.exact_duplicate_count = proposition_counts[candidate.proposition_hash]
        if candidate.exact_duplicate_count > 1:
            candidate.flags.append("exact-proposition-duplicate")

    duplicate_source_groups = [
        sorted(paths)
        for paths in source_hash_groups.values()
        if len(paths) > 1
    ]
    duplicate_source_groups.sort(key=lambda group: (len(group), group), reverse=True)

    preview = build_preview(scope, inventories, candidates, duplicate_source_groups)
    ledger_text = "".join(
        json.dumps(asdict(candidate), ensure_ascii=False, sort_keys=False) + "\n"
        for candidate in candidates
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "HELLBENDER_MEMORY_MIGRATION_PREVIEW.md"
    ledger_path = output_dir / "HELLBENDER_MEMORY_MIGRATION_LEDGER.jsonl"
    receipt_path = output_dir / "HELLBENDER_MEMORY_MIGRATION_DRY_RUN_RECEIPT.json"
    atomic_write_text(preview_path, preview + "\n")
    atomic_write_text(ledger_path, ledger_text)

    after_hashes = {
        str(path): sha256_file(path)
        for path in tracked_paths
        if path.is_file()
    }
    if before_hashes != after_hashes:
        raise RuntimeError("a source or destination changed during dry-run planning")

    receipt = {
        "schema_version": "1.0",
        "candidate_prefix": prefix,
        "as_of": scope["as_of"],
        "mode": "dry-run",
        "canonical_write_count": 0,
        "legacy_source_write_count": 0,
        "private_access_files_read": 0,
        "scope_path": str(scope_path),
        "scope_sha256": sha256_file(scope_path),
        "source_inventory": inventories,
        "source_hashes_unchanged": True,
        "candidate_count": len(candidates),
        "action_counts": dict(sorted(Counter(candidate.action for candidate in candidates).items())),
        "proposed_layer_counts": dict(
            sorted(Counter(candidate.proposed_layer for candidate in candidates).items())
        ),
        "duplicate_source_groups": duplicate_source_groups,
        "output_paths": {
            "preview": str(preview_path),
            "ledger": str(ledger_path),
        },
        "output_hashes": {
            "preview": sha256_file(preview_path),
            "ledger": sha256_file(ledger_path),
        },
    }
    atomic_write_text(
        receipt_path,
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
    )
    return {**receipt, "receipt_path": str(receipt_path)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, help="Explicit JSON scope manifest.")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for preview, ledger, and receipt artifacts.",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        receipt = run_plan(Path(args.scope), Path(args.output_dir))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.json:
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=False))
    else:
        print("mode: dry-run")
        print(f"candidates: {receipt['candidate_count']}")
        print(f"canonical_writes: {receipt['canonical_write_count']}")
        print(f"preview: {receipt['output_paths']['preview']}")
        print(f"ledger: {receipt['output_paths']['ledger']}")
        print(f"receipt: {receipt['receipt_path']}")


if __name__ == "__main__":
    main()

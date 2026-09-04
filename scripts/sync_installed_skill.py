#!/usr/bin/env python3
"""Synchronize a validated Codex-mem repository tree into an installed skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from memory_common import atomic_write_text, backup_tree, sha256_file, utc_now_iso


SYNC_DIRS = ("agents", "references", "scripts", "multi-agent")
SYNC_FILES = ("SKILL.md", "README.md", "LICENSE")
SKIP_DIR_NAMES = {".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".codex-mem", "tests"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".pyd"}


@dataclass
class SyncResult:
    status: str
    backup_path: str
    copied_files: list[str]
    preserved_installed_only: list[str]
    hashes: dict[str, str]
    report_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--installed-root", required=True)
    parser.add_argument("--backup-root", help="Directory for installed skill backups.")
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def should_skip(path: Path) -> bool:
    if any(part in SKIP_DIR_NAMES for part in path.parts):
        return True
    return path.suffix.lower() in SKIP_SUFFIXES


def iter_sync_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for name in SYNC_FILES:
        path = repo_root / name
        if path.exists():
            files.append(path)
    for dirname in SYNC_DIRS:
        root = repo_root / dirname
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not should_skip(path.relative_to(repo_root)):
                files.append(path)
    return sorted(files, key=lambda item: str(item.relative_to(repo_root)).casefold())


def installed_only_files(repo_root: Path, installed_root: Path) -> list[str]:
    repo_rel = {str(path.relative_to(repo_root)).replace("\\", "/") for path in iter_sync_files(repo_root)}
    found: list[str] = []
    if not installed_root.exists():
        return found
    for path in installed_root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(installed_root)
        if should_skip(rel_path):
            continue
        rel = str(rel_path).replace("\\", "/")
        if rel not in repo_rel:
            found.append(str(path))
    return sorted(found)


def safe_backup_root(installed_root: Path, backup_root: Path | None) -> Path:
    discovery_root = installed_root.parent.expanduser().resolve(strict=False)
    selected = backup_root or (
        installed_root.parent.parent
        / "skill-archives"
        / f"{installed_root.name}-install-backups"
    )
    selected = selected.expanduser().resolve(strict=False)
    try:
        common = Path(os.path.commonpath((discovery_root, selected)))
    except ValueError:
        return selected
    if os.path.normcase(str(common)) == os.path.normcase(str(discovery_root)):
        raise SystemExit(
            "Backup root must be outside the active skill discovery root: "
            f"{discovery_root}"
        )
    return selected


def sync_installed_skill(
    repo_root: Path,
    installed_root: Path,
    backup_root: Path | None = None,
    apply: bool = False,
    stamp: str | None = None,
) -> SyncResult:
    if not (repo_root / "SKILL.md").exists():
        raise SystemExit(f"Repository root is missing SKILL.md: {repo_root}")
    stamp = stamp or utc_now_iso().replace(":", "-")
    backup_root = safe_backup_root(installed_root, backup_root)
    files = iter_sync_files(repo_root)
    preserved = installed_only_files(repo_root, installed_root)
    copied: list[str] = []
    hashes: dict[str, str] = {}
    backup_path = ""
    report_path = ""

    if apply:
        if installed_root.exists():
            backup_path = str(backup_tree(installed_root, backup_root, stamp))
        installed_root.mkdir(parents=True, exist_ok=True)
        for source in files:
            rel = source.relative_to(repo_root)
            target = installed_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.suffix.lower() in {".md", ".yaml", ".yml", ".py", ".txt"}:
                atomic_write_text(target, source.read_text(encoding="utf-8"))
            else:
                shutil.copy2(source, target)
            copied.append(str(target))
            digest = sha256_file(target)
            if digest:
                hashes[str(rel).replace("\\", "/")] = digest
        report_path_obj = backup_root / f"sync-report-{stamp}.md"
        lines = [
            "# Codex-mem Installed Skill Sync Report",
            "",
            f"- status: success",
            f"- repo root: {repo_root}",
            f"- installed root: {installed_root}",
            f"- backup path: {backup_path or '(installed root did not exist)'}",
            "",
            "## Copied Files",
            "",
            *(f"- {path}" for path in copied),
            "",
            "## Preserved Installed-Only Files",
            "",
            *(f"- {path}" for path in preserved),
            "",
            "## Hashes",
            "",
            "```json",
            json.dumps(hashes, indent=2, ensure_ascii=False, sort_keys=True),
            "```",
            "",
        ]
        atomic_write_text(report_path_obj, "\n".join(lines))
        report_path = str(report_path_obj)

    return SyncResult(
        status="success",
        backup_path=backup_path,
        copied_files=copied,
        preserved_installed_only=preserved,
        hashes=hashes,
        report_path=report_path,
    )


def main() -> None:
    args = parse_args()
    result = sync_installed_skill(
        Path(args.repo_root),
        Path(args.installed_root),
        backup_root=Path(args.backup_root) if args.backup_root else None,
        apply=args.apply,
    )
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
        return
    print(f"status: {result.status}")
    print(f"backup: {result.backup_path or '(none; dry-run or new install)'}")
    print(f"copied_files: {len(result.copied_files)}")
    print(f"preserved_installed_only: {len(result.preserved_installed_only)}")
    if result.report_path:
        print(f"report: {result.report_path}")


if __name__ == "__main__":
    main()

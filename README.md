# Codex-mem

`Codex-mem` is a lean durable-memory skill for long-lived technical and research work.

Core invariant:

`memory is a durable decision layer, not a chronological notebook and not an execution authorization layer.`

## What It Stores

Canonical project truth lives only in:

- `project_memory.md`
- `project_stage_log.md`

Non-canonical support layers include:

- `.codex-mem/observations.jsonl`
- `.codex-mem/execution_pointers.json`
- local indexes and caches
- `global_memory.md`
- `projects_index.jsonl`
- Codex native memory
- Claude auto memory
- conversation summaries and generated reports

## Collaboration Model

Codex is the primary agent. Claude Code is the secondary collaborator. Antigravity remains supported through a compatibility adapter.

Agent provenance is metadata, not a separate source of truth. Existing `[CC]`, `[AG]`, `source`, and tag markers are preserved where useful.

## Repository Layout

```text
Codex-mem/
  SKILL.md
  agents/
  references/
  scripts/
  tests/
```

Key scripts:

- `scripts/init_project_memory.py`
- `scripts/update_project_memory.py`
- `scripts/update_stage_log.py`
- `scripts/search_memory.py`
- `scripts/generate_report.py`
- `scripts/discover_projects.py`
- `scripts/refresh_global_memory.py`
- `scripts/sync_installed_skill.py`
- `scripts/hellbender/record_incident.py`
- `scripts/hellbender/migrate_legacy_memory.py`

## Progressive Hellbender Module

Codex-mem includes an on-demand University of Missouri Hellbender operations
module under `references/modules/hellbender/`. It is loaded only for a clear
Hellbender operational request, not for a generic SLURM, HPC, DFT, or ML
mention.

The module keeps four kinds of information separate:

- durable project state in `project_memory.md` and `project_stage_log.md`
- cross-project reusable method guidance in the trigger-only DG-04 package
- current cluster rules and private access details in on-demand references
- exact jobs, logs, commands, receipts, and resource evidence in project run
  artifacts

The router can additionally load `transfer-preflight.md` for Windows-to-remote
or container-boundary work and `cp2k.md` for CP2K-specific operational
diagnosis. Neither file is loaded for ordinary scientific interpretation.

Task-end extraction may update durable project memory when the operational
state is explicit and the project authority is clear. Cross-project promotion,
deduplication, and retirement of legacy `.hellbender-project-memory.md` files
remain preview-first `maintain` work.

## Project Discovery

Discovery is deterministic and bounded. It checks:

1. records already present in `projects_index.jsonl`
2. the current project
3. explicitly supplied `--workspace-root` values
4. workspace roots from an optional config file
5. parent workspace roots inferred from verified existing index records
6. bounded-depth search for `project_memory.md`

It never scans an entire drive by default.

## Retention, Activity, Freshness

Retention status is human-controlled:

- `active`
- `warm`
- `cold`
- `archived`

Activity state is automatically observed:

- `hot`
- `recent`
- `idle`
- `missing`

Memory freshness is diagnostic:

- `fresh`
- `stale`
- `unknown`

Refresh never changes retention status silently and never redefines `last_updated` as scan time.

## Global Refresh

Dry-run is the default:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem
```

Apply requires `--apply`; run dry-run first for broad refreshes:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --all-projects --dry-run
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --all-projects --apply
```

Targeted refresh after a canonical memory update:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --project C:\path\to\project --dry-run
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --project C:\path\to\project --apply
```

A targeted root path with `project_memory.md` can register one unregistered project after dry-run review. For section replacement flows, `update_project_memory.py --sync-global-card` remains available for already registered projects.

Refresh may update only global routing files, backups, and refresh reports. It never edits canonical project memory.

## Installation Sync

After repository tests pass, synchronize the installed skill with:

```powershell
python scripts/sync_installed_skill.py --repo-root C:\path\to\Codex-mem --installed-root C:\path\to\installed\codex-mem --apply
```

The sync script creates a timestamped installed-tree backup, preserves installed-only files, and records hashes for synchronized files.

## Validation

Run:

```powershell
python -m compileall -q scripts
python -m unittest discover -s tests
```

The GitHub workflow also verifies the skill layout and core invariant.

## Deferred

This phase intentionally does not implement native-memory extraction,
Chronicle ingestion, hooks, background scheduling, Headroom integration,
profile deployment, automatic edits to `AGENTS.md` or `CLAUDE.md`, automatic
cross-project Hellbender promotion, or vector-memory infrastructure.

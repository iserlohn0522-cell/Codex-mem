# Global Routing Refresh

Use `scripts/refresh_global_memory.py` to refresh global routing safely.

Default behavior is dry-run:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem
```

With no `--project` or `--all-projects`, the command re-renders cards from the
registered index without rescanning project roots or changing scan metadata.
Use an explicit project selector for bounded re-verification, or
`--all-projects` for reviewed broad maintenance. This makes the default
render-only dry-run deterministic and avoids timestamp-only index churn.

Apply requires an explicit flag. Review a dry-run before applying broad changes:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --all-projects --dry-run
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --all-projects --apply
```

Target one project by name or root path. Dry-run first; apply only after the proposed card and index diff are acceptable:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --project C:\path\to\project --dry-run
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem --project C:\path\to\project --apply
```

A targeted root path that contains `project_memory.md` may register one previously unregistered project. Dry-run previews the new global card and index row without writing. If the selector is ambiguous or the path is not a canonical project root, stop and resolve it instead of scanning the whole drive.

Discovery supports explicit workspace roots:

```powershell
python scripts/discover_projects.py --workspace-root D:\projects --max-depth 4
```

## Compact Card Limits

Global project cards are routing cards, not project reports.

Hard limits:

- active/warm target: 260 characters
- active/warm maximum: 320 characters
- cold/archived maximum: 180 characters
- summary or compact_summary: 180 characters
- compact_stage: 80 characters
- compact_objective: 100 characters
- compact_anchor: 120 characters
- stale_reason: 100 characters

Refresh writes bounded compact fields instead of raw long project state:

- `compact_summary`
- `compact_stage`
- `compact_objective`
- `compact_anchor`
- `routing_hint`

Cards label human-controlled retention and observed activity separately, for
example `Retention: warm; activity: idle`. Activity records recent filesystem
or memory evidence; it is not a declaration that a project is the current
authoritative workbench.

For stale projects, global cards do not render detailed stage/objective/anchor state. They show a stable routing identity plus a short stale warning pointing to canonical project memory.

Validation fails before dry-run/apply succeeds if a card exceeds its cap, contains obvious operational run details, changes retention status, or newly writes long raw fields such as `current_stage`, `immediate_objective`, or `next_step_anchor`.

The refresh command may update only:

- `global_memory.md`
- `projects_index.jsonl`
- timestamped backups
- timestamped refresh reports

It never edits `project_memory.md`, `project_stage_log.md`, observations, or project source files.

Refresh preserves:

- retention status
- unknown JSON fields
- unknown provenance strings
- the complete marker-bounded `MANUAL_RULES` block

## Global Memory Ownership Markers

New global-memory scaffolds contain two ownership blocks:

```text
<!-- MANUAL_RULES:BEGIN -->
## Global Hot Rules
## Deep Memory Routing
## Deferred Deep Migration
<!-- MANUAL_RULES:END -->

<!-- GENERATED_PROJECT_CARDS:BEGIN source=projects_index.jsonl DO_NOT_EDIT -->
## Active Projects
## Warm Projects
## Cold Projects
## Archived Projects
<!-- GENERATED_PROJECT_CARDS:END -->
```

Refresh replaces only the four project sections inside
`GENERATED_PROJECT_CARDS`. The section parser stops at either the next level-2
heading or a valid `...:END` marker, so the final Archived section cannot erase
the generated-block terminator.

If any ownership marker is present, validation requires all four markers
exactly once, in order, with every project header inside the generated block.
The `MANUAL_RULES` substring must be unchanged after rendering. A malformed
layout returns `validation_failed` and writes no global/index file, backup, or
refresh report. Legacy unmarked files remain supported until an explicitly
reviewed maintenance migration adds the ownership blocks.

Refresh separates:

- retention status: human-controlled
- activity state: observed from filesystem, Git, and memory support files
- memory freshness: diagnostic status of canonical memory

After `remember`, use targeted refresh only when useful:

```powershell
python scripts/update_project_memory.py --root C:\path\to\project --section "## Current Operating State" --content-file update.md --sync-global-card
```

If the project is unregistered, the command reports that fact and does not scan all projects.

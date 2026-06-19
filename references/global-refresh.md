# Global Routing Refresh

Use `scripts/refresh_global_memory.py` to refresh global routing safely.

Default behavior is dry-run:

```powershell
python scripts/refresh_global_memory.py --global-memory-root C:\path\to\codex-mem
```

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
- `Shared Lessons`
- `Routing Notes`

Refresh separates:

- retention status: human-controlled
- activity state: observed from filesystem, Git, and memory support files
- memory freshness: diagnostic status of canonical memory

After `remember`, use targeted refresh only when useful:

```powershell
python scripts/update_project_memory.py --root C:\path\to\project --section "## Current Operating State" --content-file update.md --sync-global-card
```

If the project is unregistered, the command reports that fact and does not scan all projects.

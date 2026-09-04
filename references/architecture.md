# Codex-mem v2 Architecture

`codex-mem` is one skill with five internal operating modes:

- `remember`
- `search`
- `explore`
- `report`
- `maintain`

These are workflow modes, not separate peer skills.

## Core Invariant

`memory is durable decision layer, not chronological notebook, not execution authorization.`

## Design Priorities

1. Keep default context tiny.
2. Keep durable truth in human-readable files.
3. Treat caches and indexes as non-canonical.
4. Preserve explicit human control over critical decisions.
5. Prefer stable schema over feature breadth.
6. Avoid worker-style infrastructure.
7. Keep agent provenance neutral and backward compatible.

## Canonical Truth

Only these project files are canonical:

- `project_memory.md`
- `project_stage_log.md`

Everything else is support infrastructure:

- `.codex-mem/observations.jsonl`
- `.codex-mem/execution_pointers.json`
- `.codex-mem/index.sqlite`
- `~/.codex/memory/codex-mem/global_memory.md`
- `~/.codex/memory/codex-mem/projects_index.jsonl`
- `~/.codex/memory/codex-mem/global_index.sqlite`
- Codex native memory
- Claude auto memory
- conversation summaries and generated reports

Canonical files hold durable project truth. Non-canonical files exist to speed search, reporting, and routing.

## Storage Layout

### Skill directory

```text
codex-mem/
  SKILL.md
  agents/openai.yaml
  references/
    architecture.md
    schema.md
    update-policy.md
    search-policy.md
    maintenance-policy.md
    modules/
      hellbender/
        router.md
        memory-routing.md
        official-rules.md
        failure-taxonomy.md
        resource-templates.md
        incident-schema.md
        transfer-preflight.md
        cp2k.md
        private-access.example.md
  scripts/
    init_project_memory.py
    update_project_memory.py
    update_stage_log.py
    search_memory.py
    generate_report.py
    discover_projects.py
    refresh_global_memory.py
    sync_installed_skill.py
    hellbender/
      record_incident.py
      migrate_legacy_memory.py
```

### Project-local storage

```text
<project-root>/
  project_memory.md
  project_stage_log.md
  .codex-mem/
    observations.jsonl
    execution_pointers.json
    index.sqlite
    reports/
```

### Global routing storage

```text
~/.codex/memory/codex-mem/
  global_memory.md
  projects_index.jsonl
  global_index.sqlite
```

## Mode Responsibilities

### `remember`

Update durable project memory when future work would benefit from it.

### `search`

Recover prior project memory using a current-project-first policy.

### `explore`

Inspect the structure of memory assets before loading details.

### `report`

Generate stage or journey summaries without treating reports as canonical memory.

### `maintain`

Prune, archive, refresh, and repair memory assets explicitly.

Global refresh is dry-run by default and requires `--apply` to write. It may update only global routing files, backups, and reports.

## Progressive Domain Modules

A domain module is a trigger-specific operating layer inside Codex-mem. It
does not create another canonical memory file or another default-loaded global
memory.

The Hellbender module uses this loading order:

1. Load only its compact router after a clear Hellbender operational trigger.
2. Load current rules, resources, failure classification, incident schema,
   transfer preflight, application guidance, or installed-only access
   configuration only when the request needs them.
3. Read project canonical memory and trigger-only DG-04 guidance as appropriate.
4. Keep exact run evidence in project artifacts.
5. Extract durable project state only after the task has an explicit
   operational outcome. Route cross-project promotion through explicit
   layered maintenance.

Module loading and memory recall never authorize cluster access, submission,
retry, cancellation, spending, cleanup, publication, or transfer.

## Non-goals

`codex-mem` is not:

- a daemon
- a background hook system
- a vector memory platform
- a run log collector
- an authorization layer
- a profile deployment system
- a native-memory ingestion daemon

Memory records context and durable state. It does not authorize execution, submission, escalation, or irreversible actions.

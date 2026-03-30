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
  scripts/
    init_project_memory.py
    update_project_memory.py
    update_stage_log.py
    search_memory.py
    generate_report.py
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

## Non-goals

`codex-mem` is not:

- a daemon
- a background hook system
- a vector memory platform
- a run log collector
- an authorization layer

Memory records context and durable state. It does not authorize execution, submission, escalation, or irreversible actions.

# Codex-mem v2 Schema

## Canonical Project Files

### `project_memory.md`

This is the default bootstrap file for a fresh session.

Top-level sections:

1. `Project Identity`
2. `Current Operating State`
3. `Protected Human Decisions`
4. `Durable Decisions`
5. `Durable Constraints`
6. `Rejected Routes`
7. `Next-Step Anchor`
8. `Unresolved Issues`
9. `Canonical Docs`

Rules:

- keep the file short and stable
- update sections in place
- do not turn it into a diary
- do not store shell logs or speculative notes
- `[AG]`-prefixed bullets from a trusted Antigravity writer are valid in-place updates, not schema violations

### `Current Operating State`

This section must always include:

- `current stage`
- `immediate working objective`
- `do not do yet`
- `active stopping rule`

### `Protected Human Decisions`

Use this section for decisions that must remain explicitly human-controlled.

Examples:

- user-approved designs
- frozen naming conventions
- manually corrected scientific structures
- human-reviewed submission or execution gates

### `Canonical Docs`

Store only durable document pointers that are part of the project's canonical reading path.

Examples:

- README
- master plan
- current plan
- implementation plan
- key report paths that have become canonical reference points

Do not use this section as a discovery cache. Discovery caches belong in `.codex-mem/execution_pointers.json`.

### `project_stage_log.md`

This stores stage-level summaries only.

Per-stage fields:

- `stage_id`
- `status`
- `time_range`
- `goal`
- `short_conclusion`
- `carry_forward`
- `report_paths`
- `key_observation_ids`

Rules:

- keep entries short
- summarize stage outcomes, not every action
- promote only durable conclusions into `project_memory.md`
- `[AG]`-prefixed entries are valid stage facts if they follow the same section structure

## Non-canonical Support Files

### `.codex-mem/observations.jsonl`

Searchable detail layer for future recall and reports.

Fields:

- `id`
- `ts`
- `project`
- `kind`
- `stage_id`
- `title`
- `summary`
- `details`
- `tags`
- `files`
- `source`
- `importance`
- `supersedes`

Rules:

- only store items that affect future work
- keep details short
- supersede old records instead of appending duplicates
- never use this as a raw run log
- trusted auxiliary writers may set `source: "antigravity"` and include `"ag"` in `tags`

### `.codex-mem/execution_pointers.json`

Resolved cache of discovered execution pointers.

Fields:

- `label`
- `kind`
- `path`
- `status`
- `first_seen`
- `last_resolved`
- `notes`

Rules:

- non-canonical cache only
- high-confidence entries only
- refresh on failure or explicit request
- preserve trusted provenance notes such as `[AG]` unless the pointer is removed or superseded

### Indexes

- `.codex-mem/index.sqlite`
- `~/.codex/memory/codex-mem/global_index.sqlite`

Indexes are rebuildable and non-canonical.

## Global Routing Files

### `global_memory.md`

Compressed routing memory across projects.

Sections:

1. `Active Projects`
2. `Warm Projects`
3. `Cold Projects`
4. `Archived Projects`
5. `Shared Lessons`
6. `Routing Notes`

Rules:

- keep it extremely short
- store project cards, not project histories
- keep only reusable cross-project lessons
- keep `cold` and `archived` projects out of normal deep search

### `projects_index.jsonl`

One record per project:

- `project`
- `root_path`
- `summary`
- `keywords`
- `status`
- `last_updated`
- `memory_path`
- `stage_log_path`
- `index_path`
- `archive_path`

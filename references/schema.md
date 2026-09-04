# Codex-mem Schema

## Canonical Project Files

Only these files hold canonical project truth:

- `project_memory.md`
- `project_stage_log.md`

All other files are support, routing, search, or cache layers.

### `project_memory.md`

Required top-level sections:

1. `Project Identity`
2. `Current Operating State`
3. `Protected Human Decisions`
4. `Durable Decisions`
5. `Durable Constraints`
6. `Rejected Routes`
7. `Next-Step Anchor`
8. `Unresolved Issues`
9. `Canonical Docs`

`Current Operating State` must include:

- `current stage`
- `immediate working objective`
- `do not do yet`
- `active stopping rule`

Rules:

- keep the file short and stable
- update sections in place
- do not turn it into a diary
- do not store shell logs or speculative notes
- preserve trusted provenance markers such as `[CC]` or `[AG]` when retaining a fact

### `project_stage_log.md`

Stores stage-level summaries only.

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

- summarize stage outcomes, not every action
- promote only durable conclusions into `project_memory.md`
- preserve valid `[CC]` and `[AG]` provenance markers

## Non-canonical Support Files

### `.codex-mem/observations.jsonl`

Searchable high-value detail for future recall and reports.

Common fields:

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

- preserve unknown fields during round trips
- preserve unknown future `source` strings
- do not use observations as a raw run log
- supersede stale records instead of appending duplicates
- write `supersedes` as `list[str]`; readers may treat a legacy empty string as
  an empty list, but new records must not emit the string form

### `.codex-mem/execution_pointers.json`

Resolved cache of high-confidence pointers.

Common fields:

- `label`
- `kind`
- `path`
- `status`
- `first_seen`
- `last_resolved`
- `notes`

This file is non-canonical. Refresh it on failure or explicit request.

## Global Routing Files

### `global_memory.md`

Compressed routing memory across projects.

Handwritten sections live inside an explicit ownership block:

```text
<!-- MANUAL_RULES:BEGIN -->
## Global Hot Rules
## Deep Memory Routing
## Deferred Deep Migration
<!-- MANUAL_RULES:END -->
```

Index-generated project cards live inside a separate ownership block:

```text
<!-- GENERATED_PROJECT_CARDS:BEGIN source=projects_index.jsonl DO_NOT_EDIT -->
## Active Projects
## Warm Projects
## Cold Projects
## Archived Projects
<!-- GENERATED_PROJECT_CARDS:END -->
```

Global project cards are routing hints, not project truth. Refresh may replace
only the four generated project sections. It must preserve the complete
`MANUAL_RULES` block exactly and fail closed if markers are missing, duplicated,
misordered, or place a project section outside the generated block. Legacy
files without markers remain readable for backward compatibility; intentional
maintenance should migrate them to the marker-bounded layout before apply.

`Deferred Deep Migration` is transitional. It keeps reviewed content visible
until a named deep package exists; it must not become a second permanent hot
rule list.

### `deep/DG-*.md`

Trigger-only, non-canonical cross-project method packages. Each package states
its triggers, scope, reusable tests, route-change conclusions, and invalidation
conditions. Do not store project-current hashes, job IDs, receipts, exact
timestamps, or other run evidence in deep packages.

### `projects_index.jsonl`

One record per project. Existing fields remain supported:

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

New backward-compatible fields may include:

- `last_scanned`
- `last_verified`
- `verified_path_exists`
- `memory_last_updated`
- `stage_log_last_updated`
- `latest_observation_ts`
- `git_latest_commit_time`
- `git_has_changes`
- `activity_state`
- `memory_freshness`
- `stale_reason`
- `memory_hash`
- `compact_summary`
- `compact_stage`
- `compact_objective`
- `compact_anchor`
- `routing_hint`

`last_updated` is preserved as historical metadata and must not be redefined as scan time.

## Retention, Activity, Freshness

Retention status is human-controlled:

- `active`
- `warm`
- `cold`
- `archived`

Activity state is observed:

- `hot`
- `recent`
- `idle`
- `missing`

Generated cards label these concepts separately as `Retention` and `activity`.
Neither label by itself establishes the current authoritative workbench; the
short project summary and canonical project memory provide that routing role.

Memory freshness is diagnostic:

- `fresh`
- `stale`
- `unknown`

If project activity is newer than canonical project memory, keep the last verified project card, mark memory stale, and record a concise stale reason. Do not infer a new current state from file names, Git commits, or timestamps.

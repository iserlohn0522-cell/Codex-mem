---
name: codex-mem
description: "Maintain lean durable project memory for long-lived technical and research work using one stable skill with internal modes: remember, search, explore, report, and maintain. Use when preserving current operating state, protected human decisions, durable decisions, durable constraints, rejected routes, next-step anchors, unresolved issues, compact stage summaries, or searchable observations that affect future work. Use it also when recovering prior project memory, exploring memory structure, generating lightweight memory reports, or performing explicit memory maintenance. Do not use it as a raw run log, diary, or execution authorization layer."
---

# Codex-mem

Use this skill to maintain durable project memory with low drift and low token overhead.

Treat memory as a durable decision layer, not as a chronological notebook and not as an execution authorization layer.

## Origin

- Inspired in part by `Claude-mem`: https://github.com/thedotmack/claude-mem
- This `Codex-mem` skill is written for Codex and fully created in Codex.

`codex-mem` is one skill with five internal modes:

- `remember`
- `search`
- `explore`
- `report`
- `maintain`

These are workflow modes, not standalone peer skills.

## Canonical Truth

Project truth lives only in:

- `project_memory.md`
- `project_stage_log.md`

Indexes, caches, and searchable detail are non-canonical support layers.

## Use When

- A durable project fact should survive future sessions.
- A protected human decision must remain explicit and stable.
- The current operating state changed.
- A durable decision or constraint should guide future work.
- A rejected route should be prevented from recurring.
- A next-step anchor or unresolved issue must remain visible.
- The user asks how something was solved before.
- The user needs to inspect the structure of stored memory before loading details.
- The user asks for a stage or journey-style memory report.
- Memory needs explicit pruning, refresh, archive review, or repair.

## Do Not Use When

- The content is a raw shell log or chronological diary.
- The content is speculative, low-confidence, or obviously transient.
- The information is already clear in canonical memory and does not need another record.
- The memory would be treated as authorization to submit, run, escalate, or publish work.

## Internal Modes

### `remember`

Use when durable state changes and future work should inherit that context.

Write only what will matter later.

### `search`

Use when recovering prior project memory.

Search the current project first if the scope is already known.

### `explore`

Use when the user needs a structural view of memory assets before detail is loaded.

### `report`

Use when the user asks for stage summaries or journey-style project memory reports.

### `maintain`

Use for explicit memory hygiene, global retention-status review, archive review, pointer refresh, and de-duplication.

## Operating Rules

1. Keep `project_memory.md` short and stable.
2. Keep `project_stage_log.md` focused on stage conclusions.
3. Treat caches and indexes as non-canonical.
4. Update sections in place whenever possible.
5. Preserve human-in-the-loop control.
6. Never auto-overwrite or silently reinterpret protected human decisions.
7. Prefer superseding stale observation records over appending duplicates.
8. Never store secrets, credentials, or private keys.
9. Memory is not execution authorization.

## Core Invariant

Always keep this rule explicit:

`memory is durable decision layer, not chronological notebook, not execution authorization.`

## Required Reading Order

Read these references as needed:

- `references/architecture.md`
- `references/schema.md`
- `references/update-policy.md`
- `references/search-policy.md`
- `references/maintenance-policy.md`

## Project File Rules

### `project_memory.md`

Use this file for current durable truth only.

It must contain these top-level sections:

- `Project Identity`
- `Current Operating State`
- `Protected Human Decisions`
- `Durable Decisions`
- `Durable Constraints`
- `Rejected Routes`
- `Next-Step Anchor`
- `Unresolved Issues`
- `Canonical Docs`

`Current Operating State` must always include:

- current stage
- immediate working objective
- do not do yet
- active stopping rule

### `project_stage_log.md`

Use this file for stage-level summaries only.

### `.codex-mem/observations.jsonl`

Use this only for searchable high-value detail that affects future work.

Do not use it as a raw run log.

### `.codex-mem/execution_pointers.json`

Use this as a cache of high-confidence execution pointers.

Do not place execution pointer cache entries inside `project_memory.md`.

## Required Output Sections

When you make a memory update, return these sections:

1. `Why This Belongs In Memory`
2. `Canonical Memory Changes`
3. `Stage Log Changes`
4. `Observation Changes`
5. `Pointer Cache Changes`
6. `Pruned or Superseded Items`
7. `Current-State Check`
8. `Protected Human Decision Check`
9. `Non-Authorization Reminder`

## Search Discipline

Default search order is:

1. current project memory
2. current project stage log
3. current project observations
4. global routing memory only when scope is unclear or cross-project recall is requested

Archived deep memory should stay out of normal search unless the user explicitly requests exhaustive recall.

## Retention Discipline

Retention statuses are:

- `active`
- `warm`
- `cold`
- `archived`

Change them only during explicit maintenance work or on clear user instruction.

The lightweight global status action uses the existing script:

`scripts/update_project_memory.py --global-project <name> --retention-status <active|warm|cold|archived>`

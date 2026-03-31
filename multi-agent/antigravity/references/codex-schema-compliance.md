# Codex Schema Compliance for Antigravity

This reference defines the strict field schemas and operating rules Antigravity must follow when reading or writing into Codex's memory ecosystem.

## 1. `project_memory.md` (Canonical)
- **Structure**: Must maintain exactly these 9 top-level sections: `Project Identity`, `Current Operating State`, `Protected Human Decisions`, `Durable Decisions`, `Durable Constraints`, `Rejected Routes`, `Next-Step Anchor`, `Unresolved Issues`, `Canonical Docs`.
- **Update Rule**: `update sections in place`.
- **Restrictions**: 
  - Do NOT append new top-level sections.
  - Do NOT append to the bottom of the file.
  - Do NOT turn it into a chronological diary.

## 2. `project_stage_log.md` (Canonical)
- **Schema Fields**: `stage_id`, `status`, `time_range`, `goal`, `short_conclusion`, `carry_forward`, `report_paths`, `key_observation_ids`.
- **Update Rule**: Track conclusions, not every attempt. Only update when a stage starts, ends, materially changes direction, stalls, or produces a canonical report.

## 3. `.codex-mem/observations.jsonl` (Non-canonical)
- **JSON Schema**: `{"id": "", "ts": "", "project": "", "kind": "", "stage_id": "", "title": "", "summary": "", "details": "", "tags": [], "files": [], "source": "", "importance": "", "supersedes": ""}`
- **AG-Specific Rules**:
  - `source`: MUST be set to `"antigravity"`.
  - `tags`: MUST include `"ag"` in the array.
  - `supersedes`: Use this to supersede stale observations instead of appending duplicates.
- **Restrictions**: Never use this as a raw run log.

## 4. `.codex-mem/execution_pointers.json` (Non-canonical)
- **JSON Schema**: `{"label": "", "kind": "", "path": "", "status": "", "first_seen": "", "last_resolved": "", "notes": ""}`
- **AG-Specific Rules**:
  - High-confidence entries only.
  - MUST include `[AG]` in the `notes` field for traceability.

## 5. Antigravity Tagging Examples

**Bad (Appended string at file bottom):**
```markdown
[AG] Fixed null pointer in tests.
```

**Good (In-place update in project_memory.md):**
```markdown
### Unresolved Issues
- Issue with database connection pooling
- [AG] Null pointer exception in tests (Resolved)
```

**Good (observations.jsonl entry):**
```json
{"id": "obs-123", "ts": "2026-03-31T12:00:00Z", "project": "example", "kind": "insight", "stage_id": "stage-2", "title": "Database connection pooling solution", "summary": "Found that pooling size needs to be >20", "details": "When using the new AG-written script...", "tags": ["database", "ag"], "files": [], "source": "antigravity", "importance": "high", "supersedes": ""}
```

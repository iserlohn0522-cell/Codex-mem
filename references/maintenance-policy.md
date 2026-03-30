# Codex-mem v2 Maintenance Policy

## Goal

Keep memory compact, current, and trustworthy.

Maintenance exists to reduce drift, not to rewrite project truth aggressively.

## Retention Statuses

Each project may be labeled:

- `active`
- `warm`
- `cold`
- `archived`

Meaning:

- `active`: normal project, full default search
- `warm`: still relevant, normal search
- `cold`: visible by project card, no deep search by default
- `archived`: hidden from deep search unless explicitly requested

## Status Change Rule

Status changes must not happen silently.

Change project status only when:

- the user explicitly requests it
- `maintain` mode is intentionally invoked for review or archive work

Do not change retention status during ordinary remember/search/report work.

## Allowed Maintenance Actions

- merge duplicate observations
- mark stale observations as superseded
- compress stage summaries
- rebuild indexes
- refresh broken execution pointers
- archive completed or obsolete projects
- promote reusable lessons into global memory
- update global retention status explicitly through `update_project_memory.py --global-project <name> --retention-status <status>`

## Archive Rules

When archiving a project:

- keep a short project card in global memory
- keep deep memory accessible, but not in default search
- preserve reusable lessons in `Shared Lessons`
- do not delete canonical project files unless the user explicitly chooses deletion
- route status changes through explicit maintenance work; never archive silently during remember/search/report

## Pointer Maintenance

`execution_pointers.json` is a cache and may be refreshed.

Refresh only when:

- a cached path fails
- a user requests pointer refresh
- explicit maintenance is being performed

## Drift Controls

If memory grows noisy:

- prune observations before expanding canonical memory
- remove duplicates before adding new summaries
- prefer replacing or superseding stale items over stacking new ones
- keep protected human decisions stable unless explicitly approved for change

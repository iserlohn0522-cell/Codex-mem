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
- merge, demote, supersede, or forget redundant non-canonical global/deep content through the layered maintenance workflow
- rebalance hot, deep, routing-only, and project-only read priority without silently changing project retention
- update global retention status explicitly through `update_project_memory.py --global-project <name> --retention-status <status>` or a targeted `refresh_global_memory.py` maintenance flow

## Layered Promotion, Forgetting, and Priority

For project-to-global extraction, global/deep consolidation, forgetting, or
priority changes, follow `layered-maintenance.md`.

- Extract propositions from canonical project memory; do not copy project
  narratives wholesale.
- Compare `AGENTS.md` first, then existing global rules, deep packages, routing
  cards, and other selected project candidates.
- Create and verify the retained destination before removing or demoting a
  support-layer copy.
- Keep the default-loaded hot layer within a reviewed budget; it must not grow
  silently merely because more projects were scanned.
- Treat project retention separately from lesson priority.
- Native Memory is Codex App-owned and outside all Codex-mem maintenance write
  sets. OpenViking and similar recall systems may help discover candidates but
  are never canonical sources or destinations.

## Initializing Missing Canonical Files

When maintenance finds a project with no canonical memory files, treat initialization as a reviewable add-file operation.

- Create `.MISSING.txt` backup markers for absent `project_memory.md`, `project_stage_log.md`, observations, or execution pointers so the report does not imply previous content existed.
- Summarize the proposed add-file contents before writing when the user asked for preview or maintenance review.
- Populate only durable project truth, protected decisions, constraints, rejected routes, unresolved issues, next-step anchors, and reusable stage conclusions.
- Do not run global refresh apply automatically after initialization. Run a targeted dry-run first, then apply only after the new short routing card is approved.

## Windows and UTF-8 Notes

Use Windows-safe and encoding-explicit commands during maintenance.

- Prefer `New-Item -ItemType Directory -Force -Path <dir>` in PowerShell examples; if `-LiteralPath` fails in a local shell, fall back to `-Path` with a quoted exact path.
- For Python helpers that print Unicode paths or Chinese report text, configure UTF-8 stdout/stderr or set `PYTHONIOENCODING=utf-8`.
- Avoid raw non-ASCII regex literals in piped one-off shell scripts when the terminal code page is uncertain. Read UTF-8 files through a script or command that declares encoding explicitly.
- Treat terminal mojibake as a display issue until direct file inspection confirms actual file corruption.

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
- run `scripts/check_observations.py --root <project>` before consolidation or
  migration; malformed lines, duplicate IDs, invalid/missing supersedes targets,
  cycles, and exact duplicate title/summary pairs must remain visible
- do not auto-repair malformed JSONL during search, report, or global refresh

## Trusted Auxiliary Writers

Codex, Claude Code, Antigravity, and future tools may write compatible memory records when the user has allowed that workflow.

During `maintain`:

- treat valid provenance markers as useful evidence, not clutter
- preserve `[CC]`, `[AG]`, `source`, and tag provenance when retaining a fact
- preserve unknown future source strings unless an explicit migration says otherwise
- do not delete a valid durable fact only because it came from another trusted agent
- keep agent identity subordinate to explicit user instructions and canonical project memory

See `provenance.md` and `compatibility.md`.

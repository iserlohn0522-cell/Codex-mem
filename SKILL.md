---
name: codex-mem
description: "Maintain lean durable project memory for long-lived technical and research work. Use when preserving or recovering current operating state, protected human decisions, durable constraints, rejected routes, next-step anchors, unresolved issues, stage summaries, or compact global routing."
---

# Codex-mem

Use this skill to maintain durable project memory with low drift and low context cost.

Core invariant:

`memory is a durable decision layer, not a chronological notebook and not an execution authorization layer.`

## Modes

- `remember`: update durable project memory when future work needs the state.
- `search`: recover prior memory, current project first when known.
- `explore`: inspect memory structure before loading details.
- `report`: generate compact stage or journey reports.
- `maintain`: refresh, prune, archive, repair, or review memory assets explicitly.

These are workflow modes inside one skill, not separate peer skills.

## Authority

- New explicit user instructions override stored memory.
- Project truth lives only in `project_memory.md` and `project_stage_log.md`.
- Protected Human Decisions remain stable until the user explicitly changes them.
- `global_memory.md`, `projects_index.jsonl`, observations, execution pointers, native memories, summaries, and generated reports are non-canonical support layers.
- Memory never authorizes execution, submission, publication, escalation, spending, hazardous work, or irreversible stage transitions.

## Default Loading

- For substantial new or resumed sessions, read `~/.codex/memory/codex-mem/global_memory.md` once for routing and cross-project lessons.
- For project-scoped work, read only the relevant sections of `project_memory.md`: Project Identity, Current Operating State, Protected Human Decisions, Next-Step Anchor, and Unresolved Issues.
- Read the latest relevant `project_stage_log.md` entry when stage context is needed.
- Do not load cold or archived project detail unless the user asks for it.

## Write Rules

- Store only durable state, decisions, constraints, rejected routes, unresolved issues, next-step anchors, and reusable lessons.
- Keep `project_memory.md` short and update sections in place.
- Keep `project_stage_log.md` focused on stage-level conclusions.
- Do not store secrets, credentials, private keys, sensitive personal details, raw logs, speculative notes, or transient project facts.
- Preserve valid provenance markers such as `[CC]` and `[AG]` when keeping the underlying fact.
- Keep retention status human-controlled: `active`, `warm`, `cold`, `archived`.

## Global Routing

- Use `scripts/discover_projects.py` for bounded project discovery.
- Use `scripts/refresh_global_memory.py` for safe global routing refresh.
- Global refresh is dry-run by default; `--apply` is required to write.
- Refresh may update only `global_memory.md`, `projects_index.jsonl`, backups, and refresh reports.
- For a newly initialized project, use targeted `--project <root> --dry-run` first; apply only after the short routing card is acceptable.
- Do not refresh all projects after every memory write. After `remember`, use an explicit targeted current-project refresh only when useful.

## Default Response

For normal memory updates, use a compact report:

1. `Memory Updated`
2. `Preserved / Not Changed`
3. `Current Anchor`
4. `Needs Review` only when non-empty

Use verbose audit sections only for explicit maintenance, debugging, or requested review.

## References

Read only the reference needed for the task:

- `references/architecture.md`
- `references/schema.md`
- `references/provenance.md`
- `references/global-refresh.md`
- `references/update-policy.md`
- `references/search-policy.md`
- `references/maintenance-policy.md`
- `references/installation-sync.md`
- `references/compatibility.md`

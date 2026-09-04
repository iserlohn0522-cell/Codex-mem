---
name: codex-mem
description: "Use codex-mem for substantial or resumed long-lived work, canonical project memory, and explicit layered maintenance. Automatically use its Hellbender module for clear University of Missouri Hellbender operations: prepare, submit, monitor, transfer, diagnose, retry, or access/account/resource checks. Also route an explicit hellbender-runbook or Hellbender Runbook invocation to this module. Do not infer from generic SLURM, HPC, DFT, or ML work. Also trigger on codex-mem, Codex Memo, or memory skill. Memory never authorizes execution."
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
- `maintain`: promote, merge, demote, forget, reprioritize, refresh, archive, repair, or review memory assets explicitly.

These are workflow modes inside one skill, not separate peer skills.

## Progressive Domain Modules

Domain modules provide trigger-specific operating guidance without creating a
second memory authority.

### Hellbender

- Treat an explicit `hellbender-runbook` or `Hellbender Runbook` invocation as
  a legacy-name alias for this module. Do not load or recreate the former
  Skill's second ruleset.
- Load `references/modules/hellbender/router.md` only when the request clearly
  targets University of Missouri Hellbender and includes an operational intent:
  prepare, submit, monitor, transfer, diagnose, retry, or check access,
  account, partition, walltime, quota, or resources.
- Do not load the module for a historical mention of Hellbender, generic
  SLURM/HPC work, ordinary DFT or ML analysis, or scientific interpretation
  without a Hellbender operation.
- The router progressively selects current-rule, resource, failure, incident,
  private-access, and memory-routing references. Do not load them all by
  default.
- After a meaningful Hellbender task reaches an explicit operational state,
  extract only durable project information under the normal write rules.
  Exact jobs, commands, logs, receipts, resources, and timestamps remain in
  project run artifacts.
- Cross-project promotion and legacy-memory retirement remain explicit
  `maintain` work with a candidate ledger; they are never an automatic
  consequence of an ordinary Hellbender task.

## Authority

- New explicit user instructions override stored memory.
- Project truth lives only in `project_memory.md` and `project_stage_log.md`.
- Protected Human Decisions remain stable until the user explicitly changes them.
- `global_memory.md`, `projects_index.jsonl`, deep packages, observations, execution pointers, summaries, and generated reports are non-canonical support layers.
- Native Memory is Codex App-owned. Codex-mem may treat injected Native content as a discovery hint, but must never edit, compact, curate, deduplicate, prioritize, or use Native as a promotion destination.
- OpenViking and other semantic-recall systems are discovery support only. Verify every candidate against project canonical or live designated authority; do not write, prune, migrate, or reindex those systems as part of Codex-mem maintenance.
- Memory never authorizes execution, submission, publication, escalation, spending, hazardous work, or irreversible stage transitions.

## Default Loading

- For substantial new or resumed sessions, read
  `$CODEX_HOME/memory/codex-mem/global_memory.md` once for routing and
  cross-project lessons. When a WSL process serves Windows Codex Desktop,
  pass the Desktop support root through `CODEX_HOME`; do not silently use a
  second WSL-home root.
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
- For Hellbender tasks, preserve `SUCCESS`, `FAILED`, `STOPPED`,
  `UNRESOLVED`, negative, null, and inconclusive outcomes. Never convert an
  untested correction or scheduler completion into a resolved operational or
  scientific conclusion.

## Global Routing

- Use `scripts/discover_projects.py` for bounded project discovery.
- Use `scripts/refresh_global_memory.py` for safe global routing refresh.
- The scripts resolve the default support root from `CODEX_HOME`; an explicit
  `--global-memory-root` remains authoritative.
- Global refresh is dry-run by default; `--apply` is required to write.
- Refresh may update only `global_memory.md`, `projects_index.jsonl`, backups, and refresh reports.
- For a newly initialized project, use targeted `--project <root> --dry-run` first; apply only after the short routing card is acceptable.
- Do not refresh all projects after every memory write. After `remember`, use an explicit targeted current-project refresh only when useful.
- Use `scripts/check_observations.py` for read-only JSONL integrity checks.
  `scripts/migrate_literal_escaped_observations.py` is dry-run by default and
  requires both `--apply` and the reviewed source SHA-256 before it writes.

## Layered Memory Maintenance

When the user asks to promote project memory, consolidate or forget global
memory, change memory priority, or review retention, read and follow
`references/layered-maintenance.md`.

- A full layered pass is explicit `maintain` work, not an automatic side effect
  of ordinary `remember`.
- Use this order: scope and freeze; extract from canonical project memory;
  deduplicate and identify forgetting candidates; rebalance read priority;
  apply destination-first and verify.
- Default to a clustered human-readable preview plus a detailed candidate
  ledger before demotion, forgetting, archival, or broad priority changes.
- Keep lesson priority separate from project retention. Hot, deep, routing-only,
  project-only, and forget/supersede are content dispositions; `active`, `warm`,
  `cold`, and `archived` remain human-controlled project statuses.
- Never include Native Memory in the write set. OpenViking may surface a
  candidate but cannot establish or receive canonical truth.

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
- `references/layered-maintenance.md`
- `references/installation-sync.md`
- `references/compatibility.md`
- `references/modules/hellbender/router.md`

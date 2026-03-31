# Codex-mem

`Codex-mem` is a Codex-native skill for lean, durable project memory.

Core invariant:

`memory is durable decision layer, not chronological notebook, not execution authorization.`

## Overview

This repository packages one Codex skill with five internal modes:

- `remember`
- `search`
- `explore`
- `report`
- `maintain`

The design goal is to keep memory useful across long-lived technical or research work without turning it into a diary, a run log, or an implicit approval system.

## Design Principles

- keep canonical truth small and human-readable
- preserve explicit human control over protected decisions
- separate durable memory from search/index support layers
- avoid worker-style infrastructure and heavy background services
- prefer stable schema over feature sprawl

## Canonical vs Non-Canonical Layers

Canonical project truth lives only in:

- `project_memory.md`
- `project_stage_log.md`

Non-canonical support layers include:

- `.codex-mem/observations.jsonl`
- `.codex-mem/execution_pointers.json`
- `.codex-mem/index.sqlite`
- global routing files under `~/.codex/memory/codex-mem/`

## Repository Layout

```text
Codex-mem/
  SKILL.md
  agents/
    openai.yaml
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

## Installation

Clone or copy this repository into your Codex skills directory so the repository root becomes the skill root:

```text
~/.codex/skills/codex-mem/
```

The installed directory should contain `SKILL.md` at its root.

## Quick Start

1. Install the skill into your Codex skills directory.
2. Initialize a project memory scaffold:

```powershell
python scripts/init_project_memory.py --root C:\path\to\project
```

3. Use the skill in Codex when you want to:
   - preserve durable project state
   - search prior memory
   - inspect memory structure
   - generate lightweight reports
   - perform explicit maintenance

## Maintenance Model

Retention states are:

- `active`
- `warm`
- `cold`
- `archived`

Retention changes are explicit maintenance actions. They are not supposed to happen silently during normal remember/search/report use.

The lightweight global status command is:

```powershell
python scripts/update_project_memory.py --global-project <name> --retention-status <active|warm|cold|archived>
```

## Validation

This repository is intended to validate as a Codex skill bundle. Before publishing changes, run your normal local skill validation flow against the repository root.

## Multi-Agent Collaboration

`codex-mem` now supports collaboration with Antigravity and similar sub-worker agents that write into the same memory ecosystem under explicit provenance rules.

See:

- `multi-agent/antigravity/`

## Attribution

This project borrows ideas and inspiration from `Claude-mem`:

- [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)

`Codex-mem` itself is a Codex-native skill and was fully created in Codex.

## Privacy

This repository intentionally excludes personal project memory, private working state, and user-specific memory files.

## Contributing

This repository is kept intentionally small. Changes should:

- preserve the durable-decision model
- avoid adding heavy infrastructure
- keep schemas and scripts easy to maintain
- protect human-in-the-loop control

See `CONTRIBUTING.md` for the lightweight contribution rules used by this repository.

# Codex-mem

`Codex-mem` is a personal Codex skill for lean, durable project memory.

Core rule:

`memory is durable decision layer, not chronological notebook, not execution authorization.`

## What It Is

- One skill with five internal modes: `remember`, `search`, `explore`, `report`, `maintain`
- Canonical truth lives only in `project_memory.md` and `project_stage_log.md`
- Search, reports, routing, and pointer caches are explicitly non-canonical support layers

## Structure

- `SKILL.md`
- `agents/openai.yaml`
- `references/`
- `scripts/`

## Attribution

- Borrowed ideas and inspiration from `Claude-mem`: [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
- This repository's `Codex-mem` skill is a Codex-native skill, fully created in Codex for personal Codex use

## Notes

- This skill is designed to stay lightweight and human-in-the-loop
- It avoids worker-style infrastructure and treats retention changes as explicit maintenance actions
- No personal project memory or private working data is included in this repository

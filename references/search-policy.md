# Codex-mem v2 Search Policy

## Search Order

If the current project is already known, search the current project first:

1. `project_memory.md`
2. `project_stage_log.md`
3. `.codex-mem/observations.jsonl`

Use global routing memory first only when:

- scope is unclear
- the user asks for cross-project recall
- the user does not know which project contains the answer

## Default Flow

Use a three-step flow:

1. `search`
2. `context`
3. `fetch`

### `search`

Return short results only:

- section match
- stage match
- observation hit
- report pointer
- trusted auxiliary artifact hit when the user explicitly asks about a specific agent or tool output

Do not load large bodies yet.

### `context`

Show nearby stage or related observation context for shortlisted results.

Use this to narrow the candidate set before loading full details.

### `fetch`

Load only the final target content:

- selected project memory section
- selected stage entry
- selected observation record
- selected report file

## Execution Pointer Search

Execution pointers are not part of canonical search by default.

Use `.codex-mem/execution_pointers.json` only when:

- the user asks for a known plan/report/readme-like file
- a canonical doc pointer is missing
- a previously known execution pointer path failed

Do not rescan the whole project for pointers unless:

- the cached path failed during a real read
- the user explicitly requests refresh or rebuild

Respect trusted auxiliary provenance:

- `[CC]`, `[AG]`, `source`, and tag markers are provenance, not discard reasons
- unknown future source strings should remain visible
- provenance does not override canonical project memory

## Agent Artifact Search

If the user asks to inspect or review a specific agent's latest work, use the relevant compatibility adapter or provenance marker as a shortlist.

Use that scan as a fast shortlist for:

- reports
- notebooks
- scripts
- manifests
- intermediate audit documents

## Archive Policy

Archived projects are excluded from default deep search.

Include archived deep search only when the user clearly requests:

- full recall
- full history
- archive search
- exhaustive memory search

## Token Discipline

- search should return compressed results
- context should stay local and selective
- fetch should load only what is needed
- do not load full reports or full observation history by default

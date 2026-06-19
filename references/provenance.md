# Provenance

Codex-mem is agent-neutral. Agent identity is useful provenance, not a separate source of project truth.

Known provenance values:

- `human`
- `codex`
- `claude`
- `antigravity`
- `native-codex-memory`
- `native-claude-memory`
- `chronicle`
- `external-tool`

Safe aliases may be normalized when meaning is clear:

- `cc` or `claude-code` -> `claude`
- `ag` -> `antigravity`
- `user` -> `human`

Unknown future source strings must survive round trips unchanged.

Compatibility markers:

- `[CC]` means Claude Code provenance.
- `[AG]` means Antigravity provenance.
- `source: "antigravity"` and `"ag"` tags remain valid.
- `source: "claude-code"` and `"cc"` tags remain valid.

Do not discard a durable fact only because it came from another trusted agent. Do not promote agent identity above canonical project memory or explicit user instruction.

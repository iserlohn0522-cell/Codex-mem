# Compatibility

## Current Collaboration Guidance

Codex is the primary agent. Claude Code is the secondary collaborator. Antigravity compatibility remains available as an adapter.

This guidance is not a schema requirement. Project truth still comes from explicit user instructions and canonical project memory.

## Claude Code

- Preserve `[CC]` markers where useful.
- Treat Claude auto memory as advisory evidence, not authority.
- `source: "claude-code"` and `"cc"` tags are valid provenance.

## Antigravity

Antigravity-specific details are compatibility behavior, not the central workflow.

- Preserve `[AG]` markers where useful.
- Treat `source: "antigravity"` and `"ag"` tags as valid provenance.
- Existing Antigravity adapter files under `multi-agent/antigravity/` remain historical compatibility references.

## Deferred Integrations

These are documented but intentionally not implemented in this phase:

- automatic extraction from all Codex or Claude native memories
- Chronicle ingestion
- SessionStart hooks
- hook installers
- background scheduling
- Headroom integration
- profile audit or deployment
- automatic editing of `AGENTS.md` or `CLAUDE.md`
- vector-memory infrastructure

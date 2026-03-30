# Contributing

## Scope

This repository is intentionally narrow. Contributions should improve the Codex skill itself, not turn the repository into a general memory platform.

## Repository Standards

- keep the skill lightweight
- keep memory human-readable
- avoid background workers or service-heavy architecture
- preserve the invariant that memory is not execution authorization
- prefer stable schema changes over clever abstractions

## Change Guidelines

- update `references/` when behavior or policy changes
- keep scripts deterministic and minimal
- avoid adding new scripts unless there is a clear maintenance payoff
- do not add personal memory files, private project state, or user-specific examples

## Validation

Before opening or merging changes:

- validate the skill bundle from the repository root
- check that the repository still installs cleanly as one Codex skill
- confirm no private paths, project names, or personal memory content were added

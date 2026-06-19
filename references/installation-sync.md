# Installed Skill Synchronization

Repository development happens in a normal Git working tree. The installed skill is a deployed copy.

Before synchronizing:

1. Verify the repository branch and working-tree status.
2. Run automated tests and script compilation.
3. Compare repository and installed trees.
4. Preserve any installed-only files.

Dry-run:

```powershell
python scripts/sync_installed_skill.py --repo-root C:\path\to\Codex-mem --installed-root C:\path\to\installed\codex-mem
```

Apply:

```powershell
python scripts/sync_installed_skill.py --repo-root C:\path\to\Codex-mem --installed-root C:\path\to\installed\codex-mem --apply
```

The sync script:

- creates a timestamped backup of the installed skill tree before writing
- copies only skill files, references, agents, and scripts
- skips `.git`, `.github`, tests, caches, and bytecode
- preserves installed-only files
- records synchronized file hashes in a report

Do not use installation sync to modify user-level `AGENTS.md`, `CLAUDE.md`, settings, hooks, permissions, native memory, global memory, or project memory.

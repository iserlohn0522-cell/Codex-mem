# Hellbender Private Access Example

Copy this file to `private-access.md` in the installed module only. The copied
file is ignored by Git and must never be committed, promoted into memory, or
quoted in a user-facing report.

## Preferred Access Path

- SSH alias: `<local-alias>`
- Host name: `<official-login-host>`
- User: `<campus-account>`
- Identity file: `<local-private-key-path>`
- `IdentitiesOnly`: `yes`

## Local Notes

- Prefer the user's existing key-based route.
- If access fails, distinguish alias, key, network/VPN, cluster account, and
  service-state failures before changing job files.
- Never copy credential or private-key contents into prompts, logs, artifacts,
  memory, or reports.

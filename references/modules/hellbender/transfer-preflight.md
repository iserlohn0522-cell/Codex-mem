# Hellbender Transfer and Cross-Platform Preflight

Load this file only for Windows-authored scripts or packages, remote transfer
or harvest, archive transport, container path translation, or a transfer-stage
failure.

## Before Transfer

- Resolve the exact source and destination. Confirm which side is authoritative
  and whether replacement, cleanup, or transfer needs separate approval.
- Emit Bash, Slurm, and application text with LF explicitly. Check line endings
  again in the execution environment.
- Prevent a local shell from expanding variables intended for the remote shell.
  Prefer a transferred script or a quoted argument array over a nested
  quote-heavy one-liner.
- Do not let `sbatch` consume the same stdin stream that carries a remote loop.
  Isolate scheduler calls and count every intended unit and returned receipt.
- Record and test the exact interpreter visible inside the execution
  environment. Do not infer an absolute interpreter path from a command found
  by another shell.
- For canonical sorted inventories, use an explicit stable locale such as
  `LC_ALL=C` and record the comparison method.

## After Transfer

Verify all of the following before submission:

- exact destination and expected package-directory count
- required-file and relative-path inventory
- file identities when identity matters
- required directories exist, are traversable, and pass a bounded write test
- application-critical tokens or sections survived transport
- every host path was translated to a declared container alias and every
  required in-container path is visible with the exact image

A successful copy command, visible host path, parser-only check, or partial
local tree does not establish complete transfer or workload visibility.

## Content-Addressed Destinations

At an exact immutable target:

- reuse a regular non-symlink file or directory only when its verified identity
  matches;
- stage and atomically bind it when the target is absent; and
- stop on a type or identity mismatch.

If a verifier binds identity to a release-directory basename, bind the verified
pending inventory to the absent identity directory before canonical
verification. A temporary-alias rejection is a route mismatch, not evidence
that the content is wrong. Never overwrite merely to satisfy an absence check.

## Failed Harvest or Partial Transfer

If recursive harvest fails after remote computation completed, use a bounded
short local mapping or an archive transport route and compare complete
relative-path and identity inventories. Treat a partial local tree as a
transfer failure, not a compute failure and not a reason to rerun.

Do not delete or replace a partial destination without exact target validation
and current authorization. Keep computation, publication, transfer, parsing,
and scientific acceptance as separate states.

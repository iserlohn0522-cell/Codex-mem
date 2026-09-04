# Hellbender Domain Router

## Purpose

This is the only default-loaded Hellbender module file. It routes a clearly
operational University of Missouri Hellbender request to the smallest needed
references while preserving Codex-mem as the sole memory lifecycle.

## Trigger Contract

Load this router only when both conditions hold:

1. The target is University of Missouri Hellbender.
2. The requested work is operational: prepare, submit, monitor, transfer,
   diagnose, retry, or check access, account, partition, walltime, quota, or
   resources.

Do not trigger merely because a request mentions SLURM, HPC, DFT, ML, a past
Hellbender run, or scientific interpretation. A generic cluster task without a
confirmed Hellbender target does not qualify.

## Progressive Loading

| Need | Load |
| --- | --- |
| Current cluster policy or partition limits | `official-rules.md` |
| Resource-shape planning | `resource-templates.md` |
| Failure or early-death diagnosis | `failure-taxonomy.md` |
| Structured run-evidence capture | `incident-schema.md` |
| Durable extraction or legacy-memory work | `memory-routing.md` |
| Windows-authored scripts, transfer, harvest, or container paths | `transfer-preflight.md` |
| CP2K syntax, restart, timeout, OOM, BAND, or XYZ behavior | `cp2k.md` |
| Local SSH/access details | `private-access.md` only if it exists in the installed copy |
| Cross-project reusable failure lessons | `$CODEX_HOME/memory/codex-mem/deep/DG-04-hpc-vasp-execution.md` |

Never infer or invent private access details when `private-access.md` is absent.
Never expose its contents in a user-facing summary.

## Operational Flow

1. Confirm the project root, workload family, operation type, and authority
   boundary.
2. Read the relevant project canonical sections and the smallest references
   selected above.
3. Check current official and live scheduler state when a value can drift.
4. Separate scheduler state, application state, convergence, publication,
   transfer, parsing, and scientific acceptance.
5. For a failure, identify the earliest confirmed stage and distinguish a
   confirmed cause from a hypothesis.
6. When reusing history, name only matched prior failure cases and
   identity-valid checks. Do not reopen unrelated cases or fixed scientific
   definitions merely because they share a cluster.
7. Recommend the smallest justified next action. Do not repeat the same failed
   route unchanged.
8. Keep exact run evidence in a project-designated artifact.
9. At an explicit terminal or held state, apply `memory-routing.md` to any
   future-relevant project update. A no-change outcome produces no memory write.

## Authorization Boundary

Loading this module, recalling memory, drafting commands, or finding a prior
successful route does not authorize SSH, submission, retry, cancellation,
resource spending, cleanup, publication, licensed-file movement, or data
transfer. Apply the current project and user authorization gates separately.

## Result Discipline

Preserve `SUCCESS`, `FAILED`, `STOPPED`, `UNRESOLVED`, negative, null, and
inconclusive outcomes. Scheduler completion, exit code zero, a hash match, or a
completed workflow does not establish scientific acceptance.

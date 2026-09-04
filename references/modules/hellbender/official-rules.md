# Hellbender Official Rules

Last checked against the public Hellbender documentation: 2026-09-04.

Primary source:

- https://docs.itrss.umsystem.edu/pub/hpc/hellbender

## Stable Rules

- Hellbender uses SLURM. Run real workloads through the scheduler, not on the
  login node.
- Use an interactive allocation for interactive debugging or compilation that
  would burden the login node.
- Use the GPU partition only for work that uses a GPU for most of the run.
- Requeue jobs may be preempted and must be safe to restart or resume.
- Investor accounts and priority partitions require the correct authorized
  account and partition.
- Use Globus or the designated data-transfer route for material data movement;
  do not perform large transfers on the login node.
- Each user uses their own account and access credentials.

## Public Partition Snapshot

These public maximums were visible on 2026-09-04 and are a convenience snapshot,
not submission evidence:

| Partition | Public maximum |
| --- | --- |
| `general` | 2 days |
| `requeue` | 2 days |
| `gpu` | 2 days |
| `interactive` | 4 hours |
| `logical_cpu` | 2 days |
| authorized priority partitions | 28 days |

Before relying on a value, query the live cluster with
`scontrol show part <partition>` and verify account/QOS access. If the live
configuration and this snapshot differ, the live official configuration wins.

## Operational Consequences

- Do not infer queue priority or start time from remembered behavior.
- Treat scheduler completion, application completion, artifact publication,
  parsing, and scientific acceptance as separate states.
- Preserve an independent recoverable copy of important data. Cluster
  availability is not a substitute for project backup policy.
- Output files may appear asynchronously after short jobs; inspect actual
  scheduler and filesystem state before declaring loss or retrying.

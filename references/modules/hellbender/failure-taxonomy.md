# Hellbender Failure Taxonomy

Classify the earliest confirmed failure stage, not the loudest downstream
symptom.

## Stages

- `preflight`: missing input, malformed command, wrong path, unsafe line
  endings, invalid package, or failed authorization/resource check before
  submission.
- `access-account`: authentication, account, QOS, partition permission, or
  credential-route failure.
- `scheduler`: submission rejection, dependency hold, unfillable request,
  pending mismatch, cancellation, or scheduler-side launch failure.
- `launch`: environment activation, module, executable, MPI, container, or
  working-directory failure before useful application work.
- `runtime-application`: the application starts but exits or stalls for a
  workload-specific reason.
- `runtime-resource`: measured memory, filesystem, node, signal, or other
  infrastructure limit.
- `timeout`: walltime expires; preserve whether useful checkpoints exist.
- `publication`: computation may finish, but required output copying, atomic
  binding, validation, ready-marker creation, or dependency release fails.
- `transfer`: remote/local collection or inventory verification fails after
  source artifacts exist.
- `postprocess`: parsing or downstream analysis fails on retained outputs.
- `unknown`: evidence does not establish an earlier stage.

## Cause Status

- `confirmed`: direct evidence establishes the operational cause.
- `likely`: evidence favors a cause but does not prove it.
- `unknown`: no defensible cause is established.
- `not-applicable`: the record is a success, stop, hold, or other non-failure
  state.

Keep cause status separate from incident status. An untested repair does not
turn `likely` or `unknown` into `confirmed`.

## Evidence Traps

- An `sbatch` controller or socket timeout is an ambiguous submission state,
  not proof that no job exists. Reconcile the live scheduler by a unique job
  name or receipt before retrying, and submit only units proven missing.
- Record every failed predicate of a multi-condition numerical guard. An
  opaque guard failure does not establish overflow, OOM, bad data, or
  scientific failure and cannot justify changing frozen numerical settings.
- When Slurm records a cgroup OOM, later MPI peer-reset or collective errors
  are downstream symptoms. Without direct OOM evidence, keep the cause
  `likely` or `unknown`.
- A walltime expiry does not by itself identify a scheduler, resource,
  convergence, or scientific cause. Inspect application progress and retained
  checkpoints before classifying it.
- A scheduler state, exit code, or MaxRSS value alone does not prove that a
  representative workload unit completed.

## Route-Change Rule

After two failures from the same root cause, change the route. Cosmetic command
variation is not a new route. A new attempt is justified only when new evidence
changes the diagnosis, precondition, or available route and the attempt has
current authorization.

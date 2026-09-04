# Hellbender CP2K Operational Guidance

Load this file only when the target is University of Missouri Hellbender and
the operation involves CP2K input compatibility, launch, restart, timeout,
memory topology, BAND/NEB, or generated XYZ parsing. The current project method
lock and live installed build outrank every historical example here.

## Exact-Build Preflight

- Run the syntax and compatibility check with the exact live CP2K executable,
  module, and input intended for the job.
- Use parser-safe `PROJECT` identifiers.
- Derive the element inventory from the actual coordinate bytes. Do not infer
  composition from a filename, historical label, or builder intent.
- Validate every required `KIND`, basis, and pseudopotential valence pairing
  against the frozen project method and the exact installed data files.
- A parser pass does not prove transferred-byte identity, coordinate semantics,
  scientific compatibility, container visibility, or production resources.

### Version-gated CP2K 2023.1 evidence

The following behaviors were observed with one historical Hellbender CP2K
2023.1 build and must be rechecked before reuse:

- `TRUST_RADIUS` was accepted under `GEO_OPT/BFGS`, not directly under
  `GEO_OPT`.
- `BACKUP_COPIES` was not accepted under `MOTION/PRINT/TRAJECTORY` in the tested
  input shape.
- `RESTART_PROJECT_NAME` was rejected in `EXT_RESTART`; the tested recovery
  used build-supported restart fields or a separately validated checkpoint
  route.
- accepted `BAND_TYPE` values included `D-NEB` and `CI-NEB`.
- `MAX_ITER` was not accepted directly under `OPTIMIZE_BAND`; an explicit step
  bound had to use the optimizer's supported subsection.

These are compatibility witnesses, not current module inventory or a frozen
scientific method.

## Continuation and Timeout

- Reconcile the package directory, internal `cd`, scheduler `WorkDir` and
  `Command`, and the directory receiving live output.
- Identify the last checkpoint preceded by confirmed convergence. Do not copy
  or rename the newest WFN merely because it exists when the tail contains an
  incomplete or nonconverged SCF.
- Preserve which output belongs to the original run and which belongs to a
  restart. Read and report the output that actually contains the accepted
  continuation state.
- A walltime expiry is not automatically a chemistry, convergence, or memory
  failure. Inspect SCF status, force and step criteria, and checkpoint
  completeness separately.
- Do not use an incomplete timeout frame as a final single-point endpoint and
  do not continue without current authorization.

## Distributed Memory Diagnosis

- When Slurm records a cgroup OOM, classify later MPI peer-reset or collective
  errors as downstream symptoms.
- Per-task memory alone may not predict the peak. Rank count, placement,
  decomposition, replica layout, grids, spin channels, and temporary arrays can
  change each rank's burden.
- MaxRSS below the nominal request does not prove safety.
- A parser or image-start smoke does not validate a multi-replica resource
  topology. Define a representative completion point and required checkpoint
  prospectively.

## Generated XYZ Files

Keep line 2 short, simple, and ASCII, then run the exact installed parser.
Correct atom and line counts alone do not prove that an imported trajectory
comment or generated title is accepted.

## Result Boundary

An accepted parser, completed launch, converged SCF, finished optimization,
checkpoint, or scheduler state proves only its named layer. Scientific endpoint
acceptance still follows the current project protocol and evidence gates.

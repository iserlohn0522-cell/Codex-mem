# Hellbender Resource Templates

These are decision shapes, not fixed requests or authorization.

## Small Validation

- Use for syntax, environment, import, parser, or first-launch checks.
- Request the minimum useful CPU/GPU, memory, and walltime.
- Do not call a nonexecuting scheduler check a workload result.

Name the validation layer and give it its own pass criteria:

- parser: the exact installed parser accepts the input
- launcher: the intended executable starts through the intended launcher
- method sanity: the frozen method reaches its predeclared diagnostic point
- resource topology: a representative unit completes without a measured
  resource failure
- production-like: the bounded unit produces its required checkpoint or
  receipt

Passing one layer does not validate another.

## Established CPU Workload

- Start from the nearest project-authorized successful launcher.
- Keep resource changes evidence-based and isolate one operational variable
  when diagnosing a failure.

## Established GPU Workload

- Use a GPU only when it is used for most of the runtime.
- Request the minimum justified GPU count and enough CPU/memory to feed it.
- Validate the actual lazy imports, model construction, and runtime path rather
  than relying on package inventory alone.

## Heavy or Multi-Node Work

- Require smaller measured evidence or an existing project-approved route.
- Balance walltime and resources against queue delay without treating a
  scheduler projection as a measurement.
- Define output budgets and verify both run and publication capacity before
  launch.
- Do not infer usable memory from exclusive node placement. Request memory
  explicitly when required and verify the live job TRES and partition
  configuration.
- Per-task memory is not a complete model for distributed workloads. Rank
  count, placement, decomposition, replica layout, and temporary arrays may
  change the peak. MaxRSS below the nominal request does not prove safety.

## Adjustment Rules

- Increase walltime only after timeout evidence.
- Increase memory only after measured memory evidence.
- Change launcher or placement only after launch/scaling evidence.
- Keep unrelated scientific settings fixed when isolating an operational cause.
- Re-check live partition, account, QOS, and resource limits before use.

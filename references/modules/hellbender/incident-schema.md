# Hellbender Incident Artifact Schema

A Hellbender incident record is project run evidence, not canonical or global
memory. Store it in a project-designated artifact directory.

## Required Fields

- `timestamp`
- `project`
- `system`
- `calculation_type`
- `incident_status`
- `failure_stage`
- `symptom`
- `cause_status`

## Optional Fields

- `job_id`
- `cause`
- `retry_action`
- `workdir`
- `input_signature`
- `resource_request`
- `stderr_hint`
- `lesson_candidate`
- `evidence_paths`
- `notes`

## Incident Status Values

- `success`
- `failed`
- `stopped`
- `unresolved`
- `open`
- `retried`
- `resolved`
- `not-retried`

`resolved` means that the operational cause and corrective route have evidence;
it does not mean the scientific result is accepted.

## Privacy and Memory Boundaries

- Never store credentials, private keys, tokens, or private-key contents.
- Exact paths, job IDs, resources, hashes, and stderr belong here only when the
  project permits them.
- Do not use `project_memory.md`, `project_stage_log.md`,
  `observations.jsonl`, or `.hellbender-project-memory.md` as the incident-log
  path.
- Promote only a concise, future-relevant proposition through
  `memory-routing.md`.

## Failure Capsule Before Cleanup

If a wrapper can clean ephemeral scratch, it must first publish a bounded,
durable capsule containing only the last reached stage, terminal status, and
exception class or short message. Clean scratch only after either a verified
success receipt or a verified failure capsule exists. Otherwise retain the
scratch state for controlled recovery.

The capsule is operational evidence. It does not establish a scientific cause,
validate an endpoint, or authorize a retry.

Use `scripts/hellbender/record_incident.py` for a small JSONL artifact when a
project does not already have a stronger run-evidence format.

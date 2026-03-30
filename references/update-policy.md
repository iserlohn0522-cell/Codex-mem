# Codex-mem v2 Update Policy

`memory is durable decision layer, not chronological notebook, not execution authorization.`

## Core Rule

Update only what will matter in a future session.

If the information does not change later decisions, later search, later reporting, or later handoff quality, do not store it.

## `project_memory.md`

Update this file only when one of these changed:

- current operating state
- protected human decision
- durable decision
- durable constraint
- rejected route worth preventing
- next-step anchor
- unresolved issue that must stay visible
- canonical doc pointer that became part of the stable project reading path

Rules:

- update sections in place
- prefer concise bullets over narrative
- do not append new top-level sections
- keep historical detail out unless it changes future work

## `project_stage_log.md`

Update this file only when:

- a stage starts
- a stage ends
- a stage materially changes direction
- a stage stalls in a way that affects later work
- a report becomes the accepted stage reference

Rules:

- one short stage summary is better than many small edits
- stage log tracks conclusions, not every attempt

## `.codex-mem/observations.jsonl`

Write an observation only if all are true:

- it affects future work
- it is specific enough to retrieve later
- it is not already clear in canonical memory

Write rules:

- keep `summary` and `details` short
- prefer one strong observation to several weak ones
- supersede stale observations instead of appending duplicates
- use observations for search/report support, not for raw history

## Protected Human Decisions

This policy is strict.

Protected human decisions:

- must stay explicit
- must not be auto-overwritten
- must not be silently reinterpreted
- require explicit user approval to change

If a proposed change conflicts with a protected decision, stop and ask.

## Non-authorization Rule

Memory is not operational approval.

No memory entry authorizes:

- submission
- execution
- escalation
- publication
- irreversible stage transition

Those still require the normal project gates and explicit human control.

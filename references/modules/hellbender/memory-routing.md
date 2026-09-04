# Hellbender Memory Routing

## Single-Authority Rule

Hellbender does not own a separate project or shared memory. Project truth lives
only in `project_memory.md` and `project_stage_log.md`. DG-04 is the
trigger-only cross-project method layer. Current rules, private configuration,
and run evidence are not memory.

## Task-End Extraction

After a meaningful Hellbender task reaches an explicit operational state:

1. Keep commands, job IDs, logs, node names, exact resources, timestamps,
   hashes, receipts, and raw scheduler/application output in a
   project-designated run or incident artifact.
2. Extract only information that will change future work.
3. Update an existing canonical section in place only when the project root and
   authority are clear.
4. Preserve `[CC]`, `[AG]`, source pointers, uncertainty, and adverse states.
5. If the cause or authority is unresolved, record an unresolved issue or leave
   a review candidate. Do not initialize a new project memory silently.
6. If no durable fact changed, make no memory write.

## Destination Map

| Information | Primary destination |
| --- | --- |
| Stable project submission or publication constraint | `Durable Constraints` |
| Evidence-supported project resource or launcher decision | `Durable Decisions` |
| Confirmed failed route that should not recur unchanged | `Rejected Routes` |
| Unknown cause, untested repair, held retry, or missing authority | `Unresolved Issues` |
| Current operational stage, hold, or stopping rule | `Current Operating State` |
| Next explicitly allowed read-only or operational decision | `Next-Step Anchor` |
| Stage-level operational conclusion | `project_stage_log.md` |
| Searchable high-value detail not already canonical | `.codex-mem/observations.jsonl` |
| Stable cross-project method lesson | DG-04 candidate under explicit `maintain` |
| Current partition/account/access rule | On-demand module or installed-only configuration |
| Exact job/run evidence | Project run or incident artifact |

Observations are never a raw run log. Use stable IDs and `supersedes` rather
than appending paraphrased duplicates.

## Cross-Project Promotion

Ordinary Hellbender tasks may identify a cross-project lesson candidate but
must not automatically rewrite DG-04 or global memory. Promotion, semantic
deduplication, demotion, and retirement require:

- a normalized proposition
- a canonical or designated-live source
- a unique destination
- conflict and qualification review
- a candidate ledger
- destination-first verification

When preparing a new task, name only the matched prior failure cases and
identity-valid reused checks. Do not re-review unrelated cases or reopen fixed
scientific definitions. Case review remains evidence selection, not execution
authorization.

## Legacy `.hellbender-project-memory.md`

Treat every legacy file as a source witness, not current authority.

- Inventory explicit paths and hashes; do not scan an entire drive by default.
- Map propositions individually rather than concatenating files.
- Treat worktree copies as support copies until their authority is proven.
- Keep scientific claims, exact results, licensed-file references, private
  paths, and mixed operational/scientific propositions blocked for project
  review.
- Preserve `STOPPED`, `UNRESOLVED`, negative, null, failed, and inconclusive
  records plus their provenance.
- Create and verify the retained destination before any legacy file is
  superseded or archived.
- Re-run the same dry-run and require stable candidate IDs and dispositions.

Use `scripts/hellbender/migrate_legacy_memory.py` to create a read-only preview,
candidate ledger, and source-hash receipt. The tool does not modify canonical
or legacy files.

# Layered Memory Maintenance

## Purpose

Turn recent project memory into compact cross-project guidance without turning
global memory into a second project log. Reduce drift and default context cost
by merging duplicates, demoting narrow rules, and forgetting support-layer
copies only after their retained destination or historical witness is verified.

This workflow covers Codex-mem project canonical files, global manual rules,
deep trigger packages, `projects_index.jsonl`, generated project cards, and
observations. Codex App-owned Native Memory is out of scope. OpenViking and
other semantic-recall systems may surface candidates, but they are neither
authority nor a write destination.

## When to run

Run a full pass only when the user explicitly requests promotion, consolidation,
forgetting, reprioritization, retention review, or broad memory maintenance; or
when explicit maintenance has identified routing drift or a noisy hot layer.

Do not run a full pass after every ordinary `remember`. A single project update
may receive a targeted project-card dry-run and refresh without opening global
content adjudication.

## Required outputs

Produce two views before a broad apply:

1. A short human preview grouped by theme and proposed action so the user does
   not need to inspect every source line.
2. A candidate ledger for auditability. Each row records `candidate_id`,
   normalized proposition, canonical source, current layer, proposed layer,
   action, reason, destination or witness, conflicts, and approval need.

Allowed actions are `keep`, `merge`, `promote`, `demote`, `supersede`, `forget`,
and `blocked`. `Forget` means removing an unnecessary non-canonical support
copy; it never silently deletes canonical project history.

## Phase 1: Scope and freeze

1. Declare the selected projects, time window, authority roots, candidate
   layers, and allowed write set.
2. Read applicable `AGENTS.md`, workspace routing authority, each selected
   project's `Project Identity`, current state, protected decisions, durable
   decisions and constraints, rejected routes, next-step anchor, unresolved
   issues, and latest relevant stage entry.
3. Read the current global manual block, project index, generated-card markers,
   and only the deep packages relevant to candidate themes.
4. Record pre-change hashes and recoverable copies for any support file whose
   content may be removed, demoted, or overwritten.
5. Exclude Native Memory, OpenViking storage/configuration, sessions, protected
   application databases, credentials, and unrelated project files.

If authority, root identity, or freshness conflicts, mark affected candidates
`blocked`; do not resolve uncertainty by choosing the newest timestamp alone.

## Phase 2: Extract and normalize

For each selected project:

1. Extract only future-relevant propositions: stable decisions, constraints,
   reusable failure patterns, route-change lessons, protected negative/null
   outcomes, and cross-project interaction preferences.
2. Rewrite each proposition independently of its source narrative while
   retaining the source pointer and any claim-critical qualification.
3. Keep project versions, precise paths, hashes, job IDs, receipts, timestamps,
   current counts, thresholds, model checkpoints, and active-stage detail in
   project canonical records unless a routing card needs a compact root/role.
4. Do not convert workflow completion, test success, scheduler completion, or
   empty findings into scientific acceptance.
5. Treat OpenViking, summaries, observations, and generated cards as discovery
   hints. A candidate survives only after canonical or designated live-source
   verification.

## Phase 3: Deduplicate and forget

Compare every normalized proposition in this order:

1. Applicable `AGENTS.md` rules.
2. Existing global hot rules.
3. Existing deep packages.
4. Routing cards and aliases.
5. Other selected project candidates.

Prefer one precise rule at the highest appropriate authority over paraphrases
across several layers. A non-canonical copy may be forgotten only when at least
one condition is verified:

- it duplicates an equal or higher authority without adding meaning;
- a current replacement fully supersedes it;
- it is run-specific evidence already retained in project canonical history;
- it is an expired migration reminder whose destination now exists and resolves;
- it is unsupported speculation or transient noise that never qualified for
  durable storage.

Do not forget protected human decisions, unresolved issues that still affect
work, negative/null/failed/inconclusive outcomes, the only surviving provenance
witness, or a rule whose replacement is unverified. Prefer `supersede` or
`demote` over deletion when historical meaning still matters. Deleting canonical
files, observations, or archives requires its own explicit authorization.

## Phase 4: Rebalance priority

Assign each surviving proposition to exactly one primary disposition:

| Disposition | Use when | Default loading |
| --- | --- | --- |
| `hot-global` | Stable, cross-project, frequently relevant, costly to miss, concise, and not already covered by `AGENTS.md` | Loaded by default |
| `deep-triggered` | Stable and reusable across projects but limited to a recognizable domain or failure pattern | Loaded only on matching triggers |
| `routing-only` | Identifies an authoritative project root, current workbench, family alias, or where to look next | Compact card or routing note |
| `project-only` | Project-specific, volatile, numeric, stage-bound, or evidence-heavy | Read from project canonical files |
| `forget/supersede` | Redundant, replaced, expired, or transient support content with a verified destination or witness | Not loaded |

The hot layer has a reviewed context budget. Do not grow it by default: merge
with an existing rule, demote a lower-value rule, or state why the budget must
change. Promote from deep to hot only when ordinary cross-project work repeatedly
needs the rule; demote hot to deep when it has clear triggers; demote to project
when it no longer generalizes.

Project retention is a separate axis. `active`, `warm`, `cold`, and `archived`
describe how a project is searched, not how valuable one reusable lesson is.
Change retention only through explicit user direction or an intentional
retention review, never as an inferred consequence of priority rebalance.

## Phase 5: Apply and verify

Apply destination-first:

1. Create or update the retained project/deep destination and verify it.
2. Edit only the manual global block for hot/deep routing changes; never hand
   edit generated project cards.
3. Update `projects_index.jsonl` or refresh inputs for routing changes. Run a
   targeted `refresh_global_memory.py --project <root> --dry-run` before apply.
4. Only after the destination and route resolve, remove, demote, or supersede
   the old support copy.
5. Run observation integrity checks before any observation consolidation. Do
   not auto-repair malformed JSONL during this workflow.

Verification must show:

- project canonical facts and protected decisions remain intact;
- every deep route resolves and no proposition has conflicting primary homes;
- the global manual block stays within the reviewed budget and generated-card
  ownership markers remain valid;
- retention changes, if any, exactly match explicit decisions;
- the touched-file allowlist excludes Native Memory and OpenViking;
- a final default global refresh dry-run is idempotent and warning-free.

Report the outcome in plain language: what was promoted, merged, demoted,
forgotten, blocked, and left unchanged; then list evidence paths. Do not claim
that the memory system is scientifically correct merely because structural
validation passed.

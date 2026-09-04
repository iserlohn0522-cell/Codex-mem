from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from hellbender.migrate_legacy_memory import run_plan  # noqa: E402
from hellbender.record_incident import append_incident, record_from_args  # noqa: E402
from sync_installed_skill import sync_installed_skill  # noqa: E402


PROJECT_MEMORY = """# Project Memory

## Project Identity

- project: Demo

## Current Operating State

- current stage: held

## Protected Human Decisions

- retries require approval

## Durable Decisions

- use the verified launcher

## Durable Constraints

- keep outputs recoverable

## Rejected Routes

- do not repeat an unchanged failed route

## Next-Step Anchor

- inspect evidence

## Unresolved Issues

- exact cause remains unresolved

## Canonical Docs

- runbook:
"""


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="codex-mem-hb-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class HellbenderContractTests(unittest.TestCase):
    def test_progressive_router_and_single_memory_authority(self) -> None:
        skill = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
        router = (
            REPO_ROOT / "references" / "modules" / "hellbender" / "router.md"
        ).read_text(encoding="utf-8")
        memory_routing = (
            REPO_ROOT / "references" / "modules" / "hellbender" / "memory-routing.md"
        ).read_text(encoding="utf-8")
        transfer = (
            REPO_ROOT / "references" / "modules" / "hellbender" / "transfer-preflight.md"
        ).read_text(encoding="utf-8")
        cp2k = (
            REPO_ROOT / "references" / "modules" / "hellbender" / "cp2k.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Progressive Domain Modules", skill)
        self.assertIn("University of Missouri Hellbender", skill)
        self.assertIn("explicit `hellbender-runbook`", skill)
        self.assertIn("Do not infer from generic SLURM", skill)
        self.assertIn("only default-loaded Hellbender module file", router)
        self.assertIn("does not authorize SSH", router)
        self.assertIn("Project truth lives", memory_routing)
        self.assertIn("only in `project_memory.md`", memory_routing)
        self.assertIn("must not automatically rewrite DG-04", memory_routing)
        self.assertIn("transfer-preflight.md", router)
        self.assertIn("cp2k.md", router)
        self.assertIn("A successful copy command", transfer)
        self.assertIn("Never overwrite", transfer)
        self.assertIn("Version-gated CP2K 2023.1 evidence", cp2k)
        self.assertIn("does not prove safety", cp2k)
        self.assertNotIn(
            "Create it with `scripts/init_project_memory.py`".replace("`", ""),
            skill,
        )

    def test_migrated_module_excludes_run_and_private_details(self) -> None:
        module_root = REPO_ROOT / "references" / "modules" / "hellbender"
        tracked_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in module_root.glob("*.md")
            if path.name != "private-access.example.md"
        )
        for forbidden in (
            "13219374",
            "-1251.5963511045",
            "gxzmd@",
            "2000 K",
            "4 nodes x 8 tasks",
        ):
            self.assertNotIn(forbidden, tracked_text)

    def test_private_access_is_ignored(self) -> None:
        ignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("references/modules/hellbender/private-access.md", ignore)


class IncidentTests(TempCase):
    def make_args(self, **overrides: object) -> argparse.Namespace:
        values: dict[str, object] = {
            "project": "Demo",
            "system": "Hellbender",
            "calculation_type": "validation",
            "incident_status": "unresolved",
            "failure_stage": "unknown",
            "symptom": "No defensible cause",
            "cause_status": "unknown",
            "cause": None,
            "timestamp": "2026-09-04T12:00:00Z",
            "job_id": "12345678",
            "retry_action": "held",
            "workdir": None,
            "input_signature": None,
            "resource_request": None,
            "stderr_hint": None,
            "lesson_candidate": "Do not retry unchanged",
            "evidence_path": ["artifacts/incident.json"],
            "notes": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_incident_is_artifact_and_preserves_unresolved_state(self) -> None:
        log_path = self.tmp / "artifacts" / "hellbender-incidents.jsonl"
        record = record_from_args(self.make_args())
        append_incident(log_path, record)
        stored = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["incident_status"], "unresolved")
        self.assertEqual(stored["cause_status"], "unknown")
        self.assertEqual(stored["job_id"], "12345678")

    def test_incident_refuses_memory_destinations(self) -> None:
        with self.assertRaises(ValueError):
            append_incident(self.tmp / "project_memory.md", {"status": "failed"})
        with self.assertRaises(ValueError):
            append_incident(self.tmp / "observations.jsonl", {"status": "failed"})

    def test_confirmed_cause_requires_cause_text(self) -> None:
        with self.assertRaises(ValueError):
            record_from_args(self.make_args(cause_status="confirmed", cause=None))


class LegacyMigrationDryRunTests(TempCase):
    def test_dry_run_is_destination_safe_and_idempotent(self) -> None:
        project = self.tmp / "project"
        project.mkdir()
        memory = project / "project_memory.md"
        stage = project / "project_stage_log.md"
        legacy = project / ".hellbender-project-memory.md"
        memory.write_text(PROJECT_MEMORY, encoding="utf-8")
        stage.write_text("# Project Stage Log\n", encoding="utf-8")
        legacy.write_text(
            "# Hellbender Project Memory\n\n"
            "## Stable Submission Rules\n\n"
            "- Keep outputs recoverable before cleanup.\n\n"
            "## Failure Patterns and Fixes\n\n"
            "- FAILED job 12345678 remains UNRESOLVED; energy -1.2 eV is not accepted.\n",
            encoding="utf-8",
        )

        missing = self.tmp / "missing"
        missing.mkdir()
        missing_legacy = missing / ".hellbender-project-memory.md"
        missing_legacy.write_text(
            "# Hellbender Project Memory\n\n## Resource Heuristics\n\n- Use a small validation first.\n",
            encoding="utf-8",
        )

        support = self.tmp / "support"
        support.mkdir()
        support_legacy = support / ".hellbender-project-memory.md"
        shutil.copy2(legacy, support_legacy)

        module_root = REPO_ROOT / "references" / "modules" / "hellbender"
        dg04 = self.tmp / "global" / "deep" / "DG-04.md"
        dg04.parent.mkdir(parents=True)
        dg04.write_text("# DG-04\n\n- Do not repeat an unchanged failed route.\n", encoding="utf-8")
        shared = self.tmp / "shared" / "global-memory.md"
        shared.parent.mkdir()
        shared.write_text(
            "# Global Memory\n\n## Shared Operational Lessons\n\n"
            "- Do not repeat an unchanged failed route.\n",
            encoding="utf-8",
        )
        scope = {
            "schema_version": "1.0",
            "candidate_prefix": "HB-TEST",
            "as_of": "2026-09-04T12:00:00Z",
            "module_root": str(module_root),
            "dg04_path": str(dg04),
            "sources": [
                {
                    "source_path": str(shared),
                    "source_kind": "shared",
                    "authority": "legacy-support",
                },
                {
                    "source_path": str(legacy),
                    "source_kind": "project",
                    "authority": "canonical-root",
                    "project_root": str(project),
                    "destination_root": str(project),
                },
                {
                    "source_path": str(missing_legacy),
                    "source_kind": "project",
                    "authority": "canonical-root",
                    "project_root": str(missing),
                    "destination_root": str(missing),
                },
                {
                    "source_path": str(support_legacy),
                    "source_kind": "project",
                    "authority": "worktree-support",
                    "project_root": str(support),
                    "destination_root": str(project),
                },
            ],
        }
        scope_path = self.tmp / "scope.json"
        scope_path.write_text(json.dumps(scope, indent=2), encoding="utf-8")
        output = self.tmp / "output"
        before = {
            path: path.read_bytes()
            for path in (memory, stage, legacy, missing_legacy, support_legacy, dg04, shared)
        }

        first = run_plan(scope_path, output)
        first_ledger = (output / "HELLBENDER_MEMORY_MIGRATION_LEDGER.jsonl").read_bytes()
        second = run_plan(scope_path, output)
        second_ledger = (output / "HELLBENDER_MEMORY_MIGRATION_LEDGER.jsonl").read_bytes()

        self.assertEqual(first_ledger, second_ledger)
        self.assertEqual(first["action_counts"], second["action_counts"])
        self.assertEqual(first["canonical_write_count"], 0)
        self.assertTrue(first["source_hashes_unchanged"])
        self.assertTrue(first["duplicate_source_groups"])
        for path, content in before.items():
            self.assertEqual(path.read_bytes(), content)

        rows = [
            json.loads(line)
            for line in first_ledger.decode("utf-8").splitlines()
        ]
        candidate_ids = [row["candidate_id"] for row in rows]
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)))
        self.assertTrue(any(row["action"] == "blocked" for row in rows))
        self.assertTrue(
            any("protected-adverse-or-held-status" in row["flags"] for row in rows)
        )
        self.assertTrue(all(row["approval_need"] for row in rows))

    def test_private_access_source_and_target_output_are_rejected(self) -> None:
        project = self.tmp / "project"
        project.mkdir()
        (project / "project_memory.md").write_text(PROJECT_MEMORY, encoding="utf-8")
        (project / "project_stage_log.md").write_text("# Project Stage Log\n", encoding="utf-8")
        private = project / "private-access.md"
        private.write_text("- Identity file: secret\n", encoding="utf-8")
        dg04 = self.tmp / "global" / "DG-04.md"
        dg04.parent.mkdir()
        dg04.write_text("# DG-04\n", encoding="utf-8")
        base_scope = {
            "schema_version": "1.0",
            "candidate_prefix": "HB-TEST",
            "as_of": "2026-09-04T12:00:00Z",
            "module_root": str(REPO_ROOT / "references" / "modules" / "hellbender"),
            "dg04_path": str(dg04),
            "sources": [
                {
                    "source_path": str(private),
                    "source_kind": "project",
                    "authority": "canonical-root",
                    "project_root": str(project),
                    "destination_root": str(project),
                }
            ],
        }
        scope_path = self.tmp / "private-scope.json"
        scope_path.write_text(json.dumps(base_scope), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "private-access"):
            run_plan(scope_path, self.tmp / "output")

        legacy = project / ".hellbender-project-memory.md"
        legacy.write_text("# Memory\n\n## Stable Submission Rules\n\n- Keep outputs.\n", encoding="utf-8")
        base_scope["sources"][0]["source_path"] = str(legacy)
        scope_path.write_text(json.dumps(base_scope), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside every source"):
            run_plan(scope_path, project / "migration-output")


class HellbenderSyncBoundaryTests(TempCase):
    def test_nested_module_sync_preserves_installed_private_access(self) -> None:
        repo = self.tmp / "repo"
        installed = self.tmp / "active" / "skills" / "codex-mem"
        backups = self.tmp / "archive" / "backups"
        module = repo / "references" / "modules" / "hellbender"
        module.mkdir(parents=True)
        (repo / "SKILL.md").write_text("---\nname: codex-mem\n---\n", encoding="utf-8")
        (module / "router.md").write_text("# Router\n", encoding="utf-8")
        installed_module = installed / "references" / "modules" / "hellbender"
        installed_module.mkdir(parents=True)
        private = installed_module / "private-access.md"
        private.write_text("# local only\n", encoding="utf-8")

        dry = sync_installed_skill(repo, installed, backup_root=backups)
        self.assertIn(str(private), dry.preserved_installed_only)
        applied = sync_installed_skill(
            repo,
            installed,
            backup_root=backups,
            apply=True,
            stamp="stamp",
        )
        self.assertTrue((installed_module / "router.md").is_file())
        self.assertEqual(private.read_text(encoding="utf-8"), "# local only\n")
        self.assertIn(str(private), applied.preserved_installed_only)


if __name__ == "__main__":
    unittest.main()

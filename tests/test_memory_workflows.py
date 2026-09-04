from __future__ import annotations

import json
import os
import shutil
import time
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from discover_projects import discover_projects  # noqa: E402
from memory_common import (  # noqa: E402
    atomic_write_text,
    canonical_path_key,
    classify_activity,
    compact_update_report,
    detect_provenance_markers,
    load_jsonl,
    normalize_provenance,
    parse_project_memory,
    utc_now_iso,
)
from refresh_global_memory import build_refresh_plan, compact_project_card, compact_summary_for_project, run_refresh  # noqa: E402
from sync_installed_skill import sync_installed_skill  # noqa: E402


PROJECT_MEMORY = """# Project Memory

## Project Identity

- project: {name}
- root: {root}
- summary: {summary}

## Current Operating State

- current stage: {stage}
- immediate working objective: {objective}
- do not do yet: none
- active stopping rule: stop at human gate

## Protected Human Decisions

- [confirmed] decision: keep gate

## Durable Decisions

- [confirmed] decision: durable

## Durable Constraints

- [confirmed] constraint: bounded

## Rejected Routes

- [rejected] route: none

## Next-Step Anchor

- [confirmed] next-step anchor: {anchor}

## Unresolved Issues

- [unresolved] issue: none

## Canonical Docs

- readme:
"""


GLOBAL_MEMORY = """# Global Memory

## Active Projects

- none

## Warm Projects

- none

## Cold Projects

- none

## Archived Projects

- none

## Shared Lessons

- preserve this lesson exactly

## Routing Notes

- preserve this route exactly
"""


MARKER_GLOBAL_MEMORY = """# Global Memory

<!-- MANUAL_RULES:BEGIN -->
## Global Hot Rules

- preserve this hot rule exactly

## Deep Memory Routing

- preserve this deep route exactly

## Deferred Deep Migration

- preserve this migration item exactly
<!-- MANUAL_RULES:END -->

<!-- GENERATED_PROJECT_CARDS:BEGIN source=projects_index.jsonl DO_NOT_EDIT -->
## Active Projects

- none

## Warm Projects

- none

## Cold Projects

- none

## Archived Projects

- none
<!-- GENERATED_PROJECT_CARDS:END -->
"""


class TempCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="codex-mem-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make_project(
        self,
        name: str = "Alpha",
        parent: Path | None = None,
        summary: str = "summary",
        stage: str = "Stage A",
        objective: str = "objective",
        anchor: str = "anchor",
    ) -> Path:
        root = (parent or self.tmp) / name
        root.mkdir(parents=True, exist_ok=True)
        (root / "project_memory.md").write_text(
            PROJECT_MEMORY.format(
                name=name,
                root=root,
                summary=summary,
                stage=stage,
                objective=objective,
                anchor=anchor,
            ),
            encoding="utf-8",
        )
        (root / "project_stage_log.md").write_text("# Project Stage Log\n\n## Stage Log\n", encoding="utf-8")
        (root / ".codex-mem").mkdir(exist_ok=True)
        (root / ".codex-mem" / "observations.jsonl").write_text("", encoding="utf-8")
        return root

    def make_global_root(self, records: list[dict], global_text: str = GLOBAL_MEMORY) -> Path:
        global_root = self.tmp / "global"
        global_root.mkdir()
        (global_root / "global_memory.md").write_text(global_text, encoding="utf-8")
        (global_root / "projects_index.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        return global_root


class CommonTests(TempCase):
    def test_windows_and_posix_path_normalization(self) -> None:
        self.assertEqual(canonical_path_key(r"C:\Foo\Bar"), canonical_path_key(r"c:/foo/bar"))
        self.assertEqual(canonical_path_key("/tmp//Project"), canonical_path_key("/tmp/Project"))

    def test_provenance_aliases_and_unknown_preservation(self) -> None:
        self.assertEqual(normalize_provenance("CC"), "claude")
        self.assertEqual(normalize_provenance("ag"), "antigravity")
        self.assertEqual(normalize_provenance("future-agent"), "future-agent")
        self.assertEqual(detect_provenance_markers("[CC] update [AG] note"), {"claude", "antigravity"})

    def test_malformed_jsonl_is_reported_without_rewriting_original(self) -> None:
        path = self.tmp / "bad.jsonl"
        original = '{"ok": true}\n{bad\n{"source": "future-agent", "extra": 1}\n'
        path.write_text(original, encoding="utf-8")
        loaded = load_jsonl(path)
        self.assertEqual(len(loaded.records), 2)
        self.assertEqual(loaded.records[1]["source"], "future-agent")
        self.assertEqual(len(loaded.malformed_lines), 1)
        self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_activity_and_compact_report(self) -> None:
        self.assertEqual(classify_activity(None, exists=False), "missing")
        report = compact_update_report(["- changed"], ["- kept"], "- anchor")
        self.assertIn("## Memory Updated", report)
        self.assertNotIn("Canonical Memory Changes", report)

    def test_project_memory_summary_falls_back_to_scope(self) -> None:
        path = self.tmp / "project_memory.md"
        path.write_text(
            "# Project Memory: Dr.Zhu\n\n"
            "## Project Identity\n\n"
            "- Root: C:\\Project\n"
            "- Scope: Mn-based rare-earth-free phosphor work with ML support.\n",
            encoding="utf-8",
        )
        parsed = parse_project_memory(path)
        self.assertEqual(parsed["summary"], "Mn-based rare-earth-free phosphor work with ML support.")

    def test_project_field_strips_inline_code_wrapper(self) -> None:
        path = self.tmp / "project_memory.md"
        path.write_text(
            "# Project Memory\n\n"
            "## Project Identity\n\n"
            "- project: `Gan_v3`\n"
            "- summary: Detector/SAM platform.\n",
            encoding="utf-8",
        )
        parsed = parse_project_memory(path)
        self.assertEqual(parsed["project"], "Gan_v3")

    def test_summary_compaction_preserves_common_abbreviation(self) -> None:
        summary = "Dr. Zhu Mn-based rare-earth-free phosphor work for display/micro-LED with ML support. Older details follow."
        compact = compact_summary_for_project("Dr.Zhu", summary, [])
        self.assertTrue(compact.startswith("Dr. Zhu Mn-based"))
        self.assertIn("display/micro-LED", compact)
        self.assertNotIn("for ,", compact)

    def test_atomic_write(self) -> None:
        path = self.tmp / "nested" / "file.txt"
        atomic_write_text(path, "hello\n")
        self.assertEqual(path.read_text(encoding="utf-8"), "hello\n")
        self.assertFalse(list(path.parent.glob(".file.txt.tmp.*")))


class DiscoveryTests(TempCase):
    def test_bounded_discovery_ignore_dirs_and_utf8(self) -> None:
        workspace = self.tmp / "workspace"
        project = self.make_project("项目A", workspace, summary="含有 UTF-8")
        ignored = workspace / "node_modules" / "Ignored"
        self.make_project("Ignored", ignored)
        global_root = self.make_global_root([])
        projects, warnings = discover_projects(global_root, workspace_roots=[str(workspace)], max_depth=2)
        roots = {Path(item.root_path).name for item in projects}
        self.assertIn(project.name, roots)
        self.assertNotIn("Ignored", roots)
        self.assertFalse([warning for warning in warnings if "malformed" in warning])

    def test_discovery_deduplicates_index_and_workspace(self) -> None:
        project = self.make_project("Alpha")
        global_root = self.make_global_root(
            [
                {
                    "project": "Alpha",
                    "root_path": str(project),
                    "summary": "old",
                    "status": "warm",
                    "memory_path": str(project / "project_memory.md"),
                    "stage_log_path": str(project / "project_stage_log.md"),
                }
            ]
        )
        projects, warnings = discover_projects(global_root, workspace_roots=[str(self.tmp)], max_depth=2)
        self.assertEqual(len([item for item in projects if item.project == "Alpha"]), 1)
        self.assertTrue(any("duplicate" in warning for warning in warnings))

    def test_git_root_deduplication(self) -> None:
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
        self.make_project("One", repo)
        self.make_project("Two", repo)
        global_root = self.make_global_root([])
        projects, warnings = discover_projects(global_root, workspace_roots=[str(repo)], max_depth=2)
        self.assertEqual(len(projects), 1)
        self.assertTrue(any("duplicate git root" in warning for warning in warnings))

    def test_missing_project_paths_are_kept(self) -> None:
        missing = self.tmp / "missing"
        global_root = self.make_global_root(
            [{"project": "Missing", "root_path": str(missing), "status": "cold", "memory_path": str(missing / "project_memory.md")}]
        )
        projects, _warnings = discover_projects(global_root)
        self.assertEqual(projects[0].project, "Missing")
        self.assertFalse(projects[0].exists)


class RefreshTests(TempCase):
    def registered_global(self) -> tuple[Path, Path]:
        project = self.make_project("Alpha", summary="verified summary")
        global_root = self.make_global_root(
            [
                {
                    "project": "Alpha",
                    "root_path": str(project),
                    "summary": "old summary",
                    "status": "warm",
                    "last_updated": "2026-01-01",
                    "custom_field": "preserve me",
                    "memory_path": str(project / "project_memory.md"),
                    "stage_log_path": str(project / "project_stage_log.md"),
                }
            ]
        )
        return global_root, project

    def test_dry_run_produces_no_writes(self) -> None:
        global_root, _project = self.registered_global()
        before_index = (global_root / "projects_index.jsonl").read_text(encoding="utf-8")
        before_global = (global_root / "global_memory.md").read_text(encoding="utf-8")
        result = run_refresh(global_root, apply=False)
        self.assertTrue(result.global_changed or result.index_changed)
        self.assertEqual((global_root / "projects_index.jsonl").read_text(encoding="utf-8"), before_index)
        self.assertEqual((global_root / "global_memory.md").read_text(encoding="utf-8"), before_global)
        self.assertFalse((global_root / "refresh_reports").exists())

    def test_apply_backups_preserves_fields_lessons_and_retention(self) -> None:
        global_root, project = self.registered_global()
        result = run_refresh(
            global_root,
            project_selector=str(project),
            apply=True,
            stamp="2026-06-18T00-00-00Z",
        )
        self.assertEqual(result.status, "success")
        self.assertTrue(result.backups)
        records = [json.loads(line) for line in (global_root / "projects_index.jsonl").read_text(encoding="utf-8").splitlines()]
        record = records[0]
        self.assertEqual(record["status"], "warm")
        self.assertEqual(record["last_updated"], "2026-01-01")
        self.assertEqual(record["custom_field"], "preserve me")
        self.assertIn("last_scanned", record)
        self.assertIn("memory_last_updated", record)
        text = (global_root / "global_memory.md").read_text(encoding="utf-8")
        self.assertIn("- preserve this lesson exactly", text)
        self.assertIn("- preserve this route exactly", text)
        self.assertIn("project_memory.md", text)

    def test_idempotent_second_refresh(self) -> None:
        global_root, _project = self.registered_global()
        run_refresh(global_root, apply=True, stamp="2026-06-18T00-00-00Z")
        result = run_refresh(global_root, apply=False, stamp="2026-06-18T00-00-01Z")
        self.assertFalse(result.global_changed)
        self.assertFalse(result.index_changed)

    def test_marker_bounded_refresh_preserves_manual_block_and_is_idempotent(self) -> None:
        project = self.make_project("MarkerAlpha", summary="marker summary")
        records = [
            {
                "project": "MarkerAlpha",
                "root_path": str(project),
                "summary": "marker summary",
                "status": "warm",
                "activity_state": "idle",
                "memory_freshness": "fresh",
                "memory_path": str(project / "project_memory.md"),
                "stage_log_path": str(project / "project_stage_log.md"),
            }
        ]
        global_root = self.make_global_root(records, global_text=MARKER_GLOBAL_MEMORY)
        before = (global_root / "global_memory.md").read_text(encoding="utf-8")
        manual_before = before.split("<!-- MANUAL_RULES:BEGIN -->", 1)[1].split(
            "<!-- MANUAL_RULES:END -->", 1
        )[0]
        applied = run_refresh(global_root, apply=True, stamp="2026-06-18T00-00-00Z")
        self.assertEqual(applied.status, "success", applied.warnings)
        after = (global_root / "global_memory.md").read_text(encoding="utf-8")
        manual_after = after.split("<!-- MANUAL_RULES:BEGIN -->", 1)[1].split(
            "<!-- MANUAL_RULES:END -->", 1
        )[0]
        self.assertEqual(manual_after, manual_before)
        self.assertEqual(after.count("<!-- MANUAL_RULES:BEGIN -->"), 1)
        self.assertEqual(after.count("<!-- MANUAL_RULES:END -->"), 1)
        self.assertEqual(after.count("<!-- GENERATED_PROJECT_CARDS:BEGIN"), 1)
        self.assertEqual(after.count("<!-- GENERATED_PROJECT_CARDS:END -->"), 1)
        second = run_refresh(global_root, apply=False, stamp="2026-06-18T00-00-01Z")
        self.assertEqual(second.status, "success", second.warnings)
        self.assertFalse(second.global_changed)
        self.assertFalse(second.index_changed)

    def test_invalid_marker_layout_fails_closed(self) -> None:
        invalid = MARKER_GLOBAL_MEMORY.replace("<!-- GENERATED_PROJECT_CARDS:END -->", "")
        global_root = self.make_global_root([], global_text=invalid)
        before = (global_root / "global_memory.md").read_text(encoding="utf-8")
        result = run_refresh(global_root, apply=True, stamp="2026-06-18T00-00-00Z")
        self.assertEqual(result.status, "validation_failed")
        self.assertTrue(any("marker" in warning for warning in result.warnings))
        self.assertEqual((global_root / "global_memory.md").read_text(encoding="utf-8"), before)

    def test_project_card_labels_retention_and_activity_separately(self) -> None:
        card = compact_project_card(
            {
                "project": "HistoricalSource",
                "summary": "Historical provenance source",
                "status": "warm",
                "activity_state": "idle",
                "memory_freshness": "fresh",
                "memory_path": r"D:\HistoricalSource\project_memory.md",
            }
        )
        self.assertIn("Retention: warm; activity: idle", card)
        self.assertNotIn("Status:", card)

    def test_targeted_refresh_can_preview_and_register_unregistered_project_path(self) -> None:
        global_root, project = self.registered_global()
        result = run_refresh(global_root, project_selector=str(project), apply=True, stamp="2026-06-18T00-00-00Z")
        self.assertEqual(result.status, "success")
        unregistered = self.make_project("Beta")
        before_index = (global_root / "projects_index.jsonl").read_text(encoding="utf-8")
        preview = run_refresh(global_root, project_selector=str(unregistered), apply=False)
        self.assertEqual(preview.status, "success")
        self.assertTrue(preview.global_changed)
        self.assertTrue(preview.index_changed)
        self.assertEqual((global_root / "projects_index.jsonl").read_text(encoding="utf-8"), before_index)
        self.assertTrue(any("will register" in warning for warning in preview.warnings))
        applied = run_refresh(global_root, project_selector=str(unregistered), apply=True, stamp="2026-06-18T00-00-01Z")
        self.assertEqual(applied.status, "success")
        records = [json.loads(line) for line in (global_root / "projects_index.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertIn("Beta", {record.get("project") for record in records})

    def test_malformed_index_blocks_apply_without_destroying_original(self) -> None:
        global_root = self.tmp / "global"
        global_root.mkdir()
        original = '{"project": "A"}\n{bad\n'
        (global_root / "projects_index.jsonl").write_text(original, encoding="utf-8")
        (global_root / "global_memory.md").write_text(GLOBAL_MEMORY, encoding="utf-8")
        result = run_refresh(global_root, apply=True)
        self.assertEqual(result.status, "malformed_index")
        self.assertEqual((global_root / "projects_index.jsonl").read_text(encoding="utf-8"), original)

    def test_stale_memory_detection_from_stage_log(self) -> None:
        global_root, project = self.registered_global()
        stage_log = project / "project_stage_log.md"
        stage_log.write_text(stage_log.read_text(encoding="utf-8") + "\nnewer activity\n", encoding="utf-8")
        future = time.time() + 120
        os.utime(stage_log, (future, future))
        result = run_refresh(
            global_root,
            project_selector=str(project),
            apply=True,
            stamp=utc_now_iso().replace(":", "-"),
        )
        self.assertEqual(result.status, "success")
        record = json.loads((global_root / "projects_index.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.assertIn(record["memory_freshness"], {"fresh", "stale"})
        self.assertNotEqual(record["last_updated"], record["last_scanned"])

    def test_compact_cards_strip_long_stale_state_and_job_details(self) -> None:
        long_stage = (
            "particle_stats_v4 final fixed-protocol Hellbender expansion is harvested. "
            "job 14020877 completed with 2,832/2,832 ok records, 1024 prompts, "
            "MAE=1.313 nm, signed bias -0.165 nm, and output under "
            "experiments_ignore_region_v1/particle_stats_v4/paper_facing_model_output/material_state_report."
        )
        long_anchor = "next-step anchor: harvest submitted array 14020878[0-47] before density claim unlock"
        project = self.make_project(
            "Gan_v3",
            summary=(
                "Detector-and-SAM experiment platform for TEM particle work. Prior branches are closed and "
                "particle_stats_v4 contains detailed run state that should not enter global routing."
            ),
            stage=long_stage,
            objective="interpret and package the final original-image SAM3 material-state outputs for paper use",
            anchor=long_anchor,
        )
        stage_log = project / "project_stage_log.md"
        stage_log.write_text(stage_log.read_text(encoding="utf-8") + "\nnewer activity\n", encoding="utf-8")
        future = time.time() + 120
        os.utime(stage_log, (future, future))
        global_root = self.make_global_root(
            [
                {
                    "project": "Gan_v3",
                    "root_path": str(project),
                    "summary": "old",
                    "status": "active",
                    "last_updated": "2026-01-01",
                    "custom_field": "preserve me",
                    "memory_path": str(project / "project_memory.md"),
                    "stage_log_path": str(project / "project_stage_log.md"),
                }
            ]
        )
        new_global, new_index, records, warnings, _changed, status = build_refresh_plan(
            global_root,
            project_selector=str(project),
            stamp="2026-06-19T00-00-00Z",
        )
        self.assertEqual(status, "ok", warnings)
        card = [line for line in new_global.splitlines() if "`Gan_v3`" in line][0]
        self.assertLessEqual(len(card), 320)
        self.assertIn("memory stale", card)
        self.assertNotIn("Stage:", card)
        self.assertNotIn("Objective:", card)
        self.assertNotIn("Anchor:", card)
        self.assertNotIn("14020877", card)
        self.assertNotIn("2,832/2,832", card)
        self.assertNotIn("MAE=", card)
        self.assertNotIn("experiments_ignore_region", card)
        record = json.loads(new_index.splitlines()[0])
        self.assertEqual(record["custom_field"], "preserve me")
        self.assertNotIn("current_stage", record)
        self.assertNotIn("immediate_objective", record)
        self.assertNotIn("next_step_anchor", record)
        self.assertLessEqual(len(record["summary"]), 180)
        self.assertLessEqual(len(record["compact_stage"]), 80)
        self.assertLessEqual(len(record["compact_objective"]), 100)
        self.assertLessEqual(len(record["compact_anchor"]), 120)

    def test_ptkb_style_long_card_becomes_compact_routing_card(self) -> None:
        project = self.make_project(
            "PtKB_DFT",
            summary=(
                "Descriptor-level v2 Pt-on-oxide/KB DFT project on Pt anchoring and detachment suppression. "
                "The current active checkpoint includes endpoint-level interpretation details."
            ),
            stage=(
                "V5 parallel durability track plus V6 deposition-site-affinity proxy branch. "
                "M2 cont2 is running and detailed branch status should stay out of global routing."
            ),
            anchor=(
                "accepted hard evidence includes W_Zr-direct(2.0 A)=16.385 eV and "
                "W_Nb-adjacent(2.0 A)=0.239 eV; this must not appear in global routing"
            ),
        )
        stage_log = project / "project_stage_log.md"
        stage_log.write_text("# Project Stage Log\n\n## Stage Log\n\nnewer activity\n", encoding="utf-8")
        future = time.time() + 120
        os.utime(stage_log, (future, future))
        global_root = self.make_global_root(
            [
                {
                    "project": "PtKB_DFT",
                    "root_path": str(project),
                    "summary": "old",
                    "status": "active",
                    "memory_path": str(project / "project_memory.md"),
                    "stage_log_path": str(project / "project_stage_log.md"),
                }
            ]
        )
        new_global, _new_index, _records, warnings, _changed, status = build_refresh_plan(
            global_root,
            project_selector=str(project),
            stamp="2026-06-19T00-00-00Z",
        )
        self.assertEqual(status, "ok", warnings)
        card = [line for line in new_global.splitlines() if "`PtKB_DFT`" in line][0]
        self.assertLessEqual(len(card), 320)
        self.assertIn("DFT project", card)
        self.assertIn("memory stale", card)
        self.assertNotIn("16.385", card)
        self.assertNotIn("M2 cont2", card)

    def test_existing_raw_fields_preserved_but_not_rendered_or_newly_created(self) -> None:
        project = self.make_project("Legacy", stage="Fresh compact stage", anchor="Fresh compact anchor")
        global_root = self.make_global_root(
            [
                {
                    "project": "Legacy",
                    "root_path": str(project),
                    "summary": "legacy summary",
                    "status": "active",
                    "current_stage": "legacy long raw field " + "x" * 200,
                    "memory_path": str(project / "project_memory.md"),
                    "stage_log_path": str(project / "project_stage_log.md"),
                }
            ]
        )
        new_global, new_index, _records, warnings, _changed, status = build_refresh_plan(
            global_root,
            project_selector=str(project),
            stamp="2026-06-19T00-00-00Z",
        )
        self.assertEqual(status, "ok", warnings)
        record = json.loads(new_index.splitlines()[0])
        self.assertIn("current_stage", record)
        card = [line for line in new_global.splitlines() if "`Legacy`" in line][0]
        self.assertNotIn("legacy long raw field", card)
        self.assertLessEqual(len(card), 320)

    def test_live_fixture_dry_run_style_does_not_modify_inputs(self) -> None:
        global_root, _project = self.registered_global()
        before_global = (global_root / "global_memory.md").read_text(encoding="utf-8")
        before_index = (global_root / "projects_index.jsonl").read_text(encoding="utf-8")
        result = run_refresh(global_root, apply=False, stamp="2026-06-19T00-00-00Z")
        self.assertEqual(result.status, "success")
        self.assertEqual((global_root / "global_memory.md").read_text(encoding="utf-8"), before_global)
        self.assertEqual((global_root / "projects_index.jsonl").read_text(encoding="utf-8"), before_index)


class SyncTests(TempCase):
    def test_installed_tree_backup_and_sync_fixture(self) -> None:
        repo = self.tmp / "repo"
        installed = self.tmp / "active" / "skills" / "codex-mem"
        backups = self.tmp / "archives" / "backups"
        (repo / "scripts").mkdir(parents=True)
        (repo / "references").mkdir()
        (repo / "agents").mkdir()
        (repo / "SKILL.md").write_text("---\nname: codex-mem\n---\nbody\n", encoding="utf-8")
        (repo / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
        (repo / "scripts" / "__pycache__").mkdir()
        (repo / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"cache")
        installed.mkdir(parents=True)
        (installed / "local-only.txt").write_text("keep", encoding="utf-8")
        dry = sync_installed_skill(repo, installed, backup_root=backups, apply=False)
        self.assertEqual(dry.status, "success")
        self.assertEqual(dry.copied_files, [])
        applied = sync_installed_skill(repo, installed, backup_root=backups, apply=True, stamp="stamp")
        self.assertTrue(applied.backup_path)
        self.assertTrue((installed / "SKILL.md").exists())
        self.assertTrue((installed / "local-only.txt").exists())
        self.assertFalse((installed / "scripts" / "__pycache__" / "tool.pyc").exists())
        self.assertIn("SKILL.md", applied.hashes)

    def test_default_backup_is_outside_active_skill_discovery_root(self) -> None:
        repo = self.tmp / "repo"
        installed = self.tmp / ".agents" / "skills" / "codex-mem"
        repo.mkdir()
        installed.mkdir(parents=True)
        (repo / "SKILL.md").write_text("---\nname: codex-mem\n---\n", encoding="utf-8")
        (installed / "SKILL.md").write_text("old\n", encoding="utf-8")

        applied = sync_installed_skill(repo, installed, apply=True, stamp="stamp")

        expected_root = self.tmp / ".agents" / "skill-archives" / "codex-mem-install-backups"
        self.assertEqual(Path(applied.backup_path).parent, expected_root)
        self.assertEqual(Path(applied.report_path).parent, expected_root)

    def test_backup_inside_active_skill_discovery_root_is_rejected(self) -> None:
        repo = self.tmp / "repo"
        installed = self.tmp / ".agents" / "skills" / "codex-mem"
        repo.mkdir()
        installed.mkdir(parents=True)
        (repo / "SKILL.md").write_text("---\nname: codex-mem\n---\n", encoding="utf-8")

        with self.assertRaisesRegex(SystemExit, "outside the active skill discovery root"):
            sync_installed_skill(
                repo,
                installed,
                backup_root=installed.parent / "codex-mem-install-backups",
                apply=False,
            )


class SkillContractTests(unittest.TestCase):
    def test_layered_maintenance_contract_and_native_boundary(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        skill = (repo_root / "SKILL.md").read_text(encoding="utf-8")
        policy = (repo_root / "references" / "maintenance-policy.md").read_text(encoding="utf-8")
        layered_path = repo_root / "references" / "layered-maintenance.md"
        self.assertTrue(layered_path.exists())
        layered = layered_path.read_text(encoding="utf-8")

        self.assertIn("references/layered-maintenance.md", skill)
        self.assertIn("Native Memory is Codex App-owned", skill)
        self.assertIn("OpenViking", skill)
        self.assertIn("layered-maintenance.md", policy)

        for heading in (
            "## Phase 1: Scope and freeze",
            "## Phase 2: Extract and normalize",
            "## Phase 3: Deduplicate and forget",
            "## Phase 4: Rebalance priority",
            "## Phase 5: Apply and verify",
        ):
            self.assertIn(heading, layered)

        for disposition in (
            "`hot-global`",
            "`deep-triggered`",
            "`routing-only`",
            "`project-only`",
            "`forget/supersede`",
        ):
            self.assertIn(disposition, layered)

        self.assertIn("Codex App-owned Native Memory is out of scope", layered)
        self.assertIn("Apply destination-first", layered)
        self.assertIn("Project retention is a separate axis", layered)


if __name__ == "__main__":
    unittest.main()

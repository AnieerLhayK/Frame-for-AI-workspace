from __future__ import annotations

import subprocess
import unittest

from scripts.verify_change_scope import (
    collect_changes,
    scope_matches,
    verify_changes,
)


def completed(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], returncode, stdout, "")


class FakeGit:
    def __init__(self, outputs: dict[tuple[str, ...], str]) -> None:
        self.outputs = outputs
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, arguments: tuple[str, ...] | list[str]) -> subprocess.CompletedProcess[str]:
        key = tuple(arguments)
        self.calls.append(key)
        return completed(self.outputs.get(key, ""))


def resolved(write_scope: list[str], status: str = "PASS") -> dict:
    return {
        "status": status,
        "task": {"id": "demo"},
        "context": {"write_scope": write_scope},
    }


class ChangeScopeVerificationTests(unittest.TestCase):
    def test_all_changes_inside_scope_pass(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "scripts/tool.py\n",
                ("diff", "--name-status", "--find-renames"): "M\tscripts/tool.py\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["allowed_files"], ["scripts/tool.py"])

    def test_staged_unstaged_and_untracked_are_combined(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "scripts/a.py\n",
                ("diff", "--name-status", "--find-renames"): "M\tscripts/a.py\n",
                ("diff", "--cached", "--name-only"): "scripts/b.py\n",
                ("diff", "--cached", "--name-status", "--find-renames"): "A\tscripts/b.py\n",
                ("ls-files", "--others", "--exclude-standard"): "scripts/c.py\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["actual_changes"]), 3)

    def test_include_flags_skip_staged_and_untracked(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "",
                ("diff", "--name-status", "--find-renames"): "",
            }
        )
        branch, changes = collect_changes(
            include_staged=False,
            include_untracked=False,
            runner=git,
        )
        self.assertEqual(branch, "codex/demo")
        self.assertEqual(changes, [])
        self.assertNotIn(("diff", "--cached", "--name-only"), git.calls)

    def test_explicit_out_of_scope_is_error_and_preserved(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "shared/policy.md\n",
                ("diff", "--name-status", "--find-renames"): "M\tshared/policy.md\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/"]),
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["out_of_scope_files"], ["shared/policy.md"])
        self.assertEqual(result["destructive_actions_performed"], [])

    def test_declared_high_risk_path_can_pass(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "workspace_manifest.yaml\n",
                ("diff", "--name-status", "--find-renames"): "M\tworkspace_manifest.yaml\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["workspace_manifest.yaml"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["risk_level"], "high")
        self.assertFalse(result["confirmation_required"])
        self.assertFalse(result["worktree_recommended"])
        self.assertTrue(result["high_risk_files"][0]["declared"])

    def test_ordinary_document_is_normal_risk(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "README.md\n",
                ("diff", "--name-status", "--find-renames"): "M\tREADME.md\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["README.md"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["risk_level"], "normal")
        self.assertFalse(result["confirmation_required"])
        self.assertFalse(result["worktree_recommended"])

    def test_permission_boundary_script_is_high_risk(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "scripts/agent_governance.py\n",
                ("diff", "--name-status", "--find-renames"): (
                    "M\tscripts/agent_governance.py\n"
                ),
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/agent_governance.py"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["risk_level"], "high")
        self.assertFalse(result["worktree_recommended"])

    def test_platform_projection_change_recommends_worktree_and_confirmation(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): ".claude/skills/demo/SKILL.md\n",
                ("diff", "--name-status", "--find-renames"): (
                    "M\t.claude/skills/demo/SKILL.md\n"
                ),
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved([".claude/skills/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["confirmation_required"])
        self.assertTrue(result["worktree_recommended"])

    def test_undeclared_high_risk_path_is_error(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "shared/policy.md\n",
                ("diff", "--name-status", "--find-renames"): "M\tshared/policy.md\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["README.md"]),
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["high_risk_files"][0]["declared"], False)

    def test_declarative_scope_produces_warning(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "",
                ("diff", "--name-status", "--find-renames"): "",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(
                ["scripts/", "explicitly approved paths only"]
            ),
        )
        self.assertEqual(result["status"], "WARNING")

    def test_non_pass_task_status_produces_warning(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "",
                ("diff", "--name-status", "--find-renames"): "",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/"], status="WARN"),
        )
        self.assertEqual(result["status"], "WARNING")
        self.assertIn("Task resolver status is WARN", result["warnings"][0])

    def test_placeholder_binding_is_forwarded_to_resolver(self) -> None:
        seen: list[list[str]] = []

        def resolver(_task: str, bindings: list[str]) -> dict:
            seen.append(bindings)
            return resolved(["skills/demo/SKILL.md"])

        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "",
                ("diff", "--name-status", "--find-renames"): "",
            }
        )
        verify_changes(
            "skill_metadata_update",
            ["target-skill=skills/demo"],
            runner=git,
            task_resolver=resolver,
        )
        self.assertEqual(seen, [["target-skill=skills/demo"]])

    def test_unknown_task_failure_is_not_hidden(self) -> None:
        with self.assertRaises(RuntimeError):
            verify_changes(
                "missing",
                [],
                runner=FakeGit({}),
                task_resolver=lambda *_: (_ for _ in ()).throw(
                    RuntimeError("unknown task")
                ),
            )

    def test_empty_worktree_passes(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "",
                ("diff", "--name-status", "--find-renames"): "",
            }
        )
        result = verify_changes(
            "demo",
            [],
            include_staged=False,
            include_untracked=False,
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["actual_changes"], [])

    def test_windows_case_and_separators_are_normalized(self) -> None:
        self.assertTrue(scope_matches(r"Scripts\Tests\Demo.py", "scripts/"))
        self.assertTrue(
            scope_matches(
                r"PROJECT_CONTEXT\TASK_REGISTRY.yaml",
                "project_context/task_registry.yaml",
            )
        )

    def test_skill_deletion_is_high_risk(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "skills/demo/SKILL.md\n",
                ("diff", "--name-status", "--find-renames"): "D\tskills/demo/SKILL.md\n",
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["skills/demo/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertIn(
            "Skill or package deletion/move",
            result["high_risk_files"][0]["reasons"],
        )
        self.assertTrue(result["confirmation_required"])
        self.assertTrue(result["worktree_recommended"])

    def test_editing_migration_tool_does_not_claim_migration_is_running(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "scripts/migration_dry_run.py\n",
                ("diff", "--name-status", "--find-renames"): (
                    "M\tscripts/migration_dry_run.py\n"
                ),
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/migration_dry_run.py"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["risk_level"], "high")
        self.assertFalse(result["confirmation_required"])
        self.assertFalse(result["worktree_recommended"])

    def test_large_rename_recommends_worktree_and_confirmation(self) -> None:
        names = "\n".join(
            [
                "docs/old-a.md",
                "docs/new-a.md",
                "docs/old-b.md",
                "docs/new-b.md",
                "docs/old-c.md",
                "docs/new-c.md",
            ]
        )
        statuses = "\n".join(
            [
                "R100\tdocs/old-a.md\tdocs/new-a.md",
                "R100\tdocs/old-b.md\tdocs/new-b.md",
                "R100\tdocs/old-c.md\tdocs/new-c.md",
            ]
        )
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): names,
                ("diff", "--name-status", "--find-renames"): statuses,
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["docs/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["risk_level"], "high")
        self.assertTrue(result["confirmation_required"])
        self.assertTrue(result["worktree_recommended"])

    def test_boundary_test_file_is_not_high_risk_by_name_alone(self) -> None:
        git = FakeGit(
            {
                ("branch", "--show-current"): "codex/demo\n",
                ("diff", "--name-only"): "scripts/tests/test_verify_change_scope.py\n",
                ("diff", "--name-status", "--find-renames"): (
                    "M\tscripts/tests/test_verify_change_scope.py\n"
                ),
            }
        )
        result = verify_changes(
            "demo",
            [],
            runner=git,
            task_resolver=lambda *_: resolved(["scripts/tests/"]),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["high_risk_files"], [])

    def test_agent_authority_can_reject_a_task_scoped_change(self) -> None:
        path = (
            "packages/character-system/runtime/characters/zyc/"
            "references/voice_card.md"
        )
        git = FakeGit(
            {
                ("branch", "--show-current"): "main\n",
                ("diff", "--name-only"): f"{path}\n",
                ("diff", "--name-status", "--find-renames"): f"M\t{path}\n",
            }
        )
        result = verify_changes(
            "runtime_drift_fix",
            [],
            agent_id="hermes",
            acting_skill="zyc",
            runner=git,
            task_resolver=lambda *_: resolved(
                ["packages/character-system/runtime/characters/zyc/"]
            ),
        )
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["authorization_denied_files"], [path])

    def test_agent_and_skill_authority_allow_diagnosis_record(self) -> None:
        path = (
            "packages/character-system/reports/runtime-loop/"
            "diagnoses/DIAG-demo.md"
        )
        git = FakeGit(
            {
                ("branch", "--show-current"): "main\n",
                ("diff", "--name-only"): f"{path}\n",
                ("diff", "--name-status", "--find-renames"): f"M\t{path}\n",
            }
        )
        result = verify_changes(
            "runtime_drift_fix",
            [],
            agent_id="hermes",
            acting_skill="style-doctor",
            runner=git,
            task_resolver=lambda *_: resolved(
                ["packages/character-system/reports/runtime-loop/"]
            ),
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["authorization_denied_files"], [])


if __name__ == "__main__":
    unittest.main()
